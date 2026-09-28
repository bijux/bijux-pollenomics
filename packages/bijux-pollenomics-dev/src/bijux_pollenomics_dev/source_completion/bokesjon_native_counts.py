"""Pair retained Bökesjön workbook cells with explicit Neotoma NISP rows."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from math import isfinite
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.collection.sources.rootsi.cells.decoding import parser

DATASET_ID = 54001
SITE_ID = 28872
RAW_SHA256 = "9cdcb2d394bc8ef23bf2b4b5e3f1f3ae5916aae16db71542c58f4b80a2dd1134"
WORKBOOK_SHA256 = "d95da5626a877b340e365317769fa0ef39cf371687b84004a996c30353dc4bc4"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _number(value: object, label: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
    ):
        raise ValueError(f"{label} is not finite and numeric")
    return float(value)


def _count(value: object, label: str) -> int:
    number = _number(value, label)
    if number < 0 or int(number) != number:
        raise ValueError(f"{label} is not an exact nonnegative count")
    return int(number)


def _workbook(path: Path) -> tuple[list[str], list[dict[str, object]]]:
    if _digest(path) != WORKBOOK_SHA256:
        raise ValueError("Bökesjön workbook bytes differ from retained receipt")
    book = parser().open_workbook(file_contents=path.read_bytes(), formatting_info=True)
    try:
        sheets = book.sheets()
        if len(sheets) != 1 or sheets[0].nrows != 53 or sheets[0].ncols != 168:
            raise ValueError("Bökesjön workbook axes differ")
        sheet = sheets[0]
        if (
            sheet.cell(0, 0).value != "Sample depth (cm)"
            or sheet.cell(0, 1).value != "Sample age (LANDCLIM)"
        ):
            raise ValueError("Bökesjön workbook header differs")
        raw_taxa = [sheet.cell(0, column).value for column in range(2, sheet.ncols)]
        if (
            any(not isinstance(value, str) or not value for value in raw_taxa)
            or len(set(raw_taxa)) != 166
        ):
            raise ValueError("Bökesjön workbook taxon axis differs")
        taxa = [str(value) for value in raw_taxa]
        rows = [
            {
                "sample_depth_label": _number(
                    sheet.cell(position, 0).value, "workbook depth"
                ),
                "age_label": _number(sheet.cell(position, 1).value, "workbook age"),
                "counts": {
                    taxon: _count(sheet.cell(position, column).value, "workbook count")
                    for column, taxon in enumerate(taxa, start=2)
                },
            }
            for position in range(1, sheet.nrows)
        ]
        if len({row["sample_depth_label"] for row in rows}) != 52:
            raise ValueError("Bökesjön workbook depth labels repeat")
        return taxa, rows
    finally:
        book.release_resources()


def _source_samples(path: Path) -> list[dict[str, Any]]:
    if _digest(path) != RAW_SHA256:
        raise ValueError("Neotoma raw part bytes differ from retained receipt")
    raw = json.loads(path.read_text())
    if raw["part_number"] != 8:
        raise ValueError("Neotoma raw part identity differs")
    sites = [
        row["site"]
        for row in raw["rows"]
        if row["site"]["dataset"]["datasetid"] == DATASET_ID
    ]
    if len(sites) != 1 or sites[0]["siteid"] != SITE_ID:
        raise ValueError("Neotoma site or dataset identity differs")
    samples = sites[0]["collectionunit"]["dataset"]["samples"]
    if len(samples) != 52:
        raise ValueError("Neotoma sample denominator differs")
    return cast(list[dict[str, Any]], samples)


def compare_cells(
    taxa: list[str],
    workbook_rows: list[dict[str, object]],
    samples: list[dict[str, Any]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Keep explicit agreement, discrepancies and absent source rows distinct."""
    if not taxa or len(taxa) != len(set(taxa)):
        raise ValueError("Workbook taxon axis repeats or is empty")
    source_by_depth: dict[float, dict[str, Any]] = {}
    source_taxa: set[str] = set()
    for sample in samples:
        depth = _number(sample["depth"], "Neotoma depth")
        if depth in source_by_depth:
            raise ValueError("Neotoma depth label repeats")
        source_by_depth[depth] = sample
        source_taxa.update(str(datum["variablename"]) for datum in sample["datum"])
    workbook_by_depth = {
        _number(row["sample_depth_label"], "workbook depth"): row
        for row in workbook_rows
    }
    if len(workbook_by_depth) != len(workbook_rows) or set(workbook_by_depth) != set(
        source_by_depth
    ):
        raise ValueError("Workbook and Neotoma depth axes differ")
    shared = sorted(set(taxa) & source_taxa)
    if not shared:
        raise ValueError("No exact taxon labels overlap")
    cells: list[dict[str, object]] = []
    totals: Counter[str] = Counter()
    age_differences: list[float] = []
    for depth in sorted(workbook_by_depth):
        row = workbook_by_depth[depth]
        sample = source_by_depth[depth]
        counts = row["counts"]
        if not isinstance(counts, dict) or set(counts) != set(taxa):
            raise ValueError("Workbook count axis differs")
        datums: dict[str, list[dict[str, Any]]] = {}
        for datum in sample["datum"]:
            name = str(datum["variablename"])
            datums.setdefault(name, []).append(datum)
        ages = sample["ages"]
        if (
            len(ages) != 1
            or ages[0]["chronologyname"] != "LANDCLIM"
            or ages[0]["agetype"] != "Calibrated radiocarbon years BP"
            or ages[0]["ageolder"] is not None
            or ages[0]["ageyounger"] is not None
        ):
            raise ValueError("Neotoma age claim differs from retained scope")
        age_differences.append(
            _number(row["age_label"], "workbook age")
            - _number(ages[0]["age"], "Neotoma age")
        )
        for taxon in shared:
            workbook_count = _count(counts[taxon], "workbook count")
            matching = datums.get(taxon, [])
            if not matching:
                status = (
                    "absent_source_workbook_zero"
                    if workbook_count == 0
                    else "absent_source_workbook_positive"
                )
                source_count: int | None = None
            elif len(matching) > 1:
                status = "ambiguous_source_duplicate"
                source_count = None
            else:
                datum = matching[0]
                if datum["units"] != "NISP":
                    raise ValueError("Matched Neotoma datum has no NISP count unit")
                source_count = _count(datum["value"], "Neotoma NISP")
                status = (
                    "explicit_agreement"
                    if workbook_count == source_count
                    else "explicit_difference"
                )
                totals["explicit_neotoma_mass"] += source_count
                totals["workbook_mass_on_explicit_pairs"] += workbook_count
            totals[status] += 1
            cells.append(
                {
                    "sample_depth_label": depth,
                    "neotoma_sample_id": sample["sampleid"],
                    "taxon_exact_label": taxon,
                    "workbook_count": workbook_count,
                    "neotoma_explicit_nisp": source_count
                    if source_count is not None
                    else "",
                    "ambiguous_source_values": json.dumps(
                        [
                            {
                                "value": datum["value"],
                                "units": datum["units"],
                                "element": datum["element"],
                                "elementtype": datum["elementtype"],
                            }
                            for datum in matching
                        ],
                        sort_keys=True,
                    )
                    if len(matching) > 1
                    else "",
                    "status": status,
                }
            )
    return cells, {
        "samples": len(workbook_rows),
        "workbook_taxon_labels": len(taxa),
        "neotoma_taxon_labels": len(source_taxa),
        "exact_shared_taxon_labels": len(shared),
        "workbook_only_taxon_labels": sorted(set(taxa) - source_taxa),
        "neotoma_only_taxon_labels": sorted(source_taxa - set(taxa)),
        "cell_status_counts": dict(sorted(totals.items())),
        "max_absolute_numeric_age_label_difference": max(map(abs, age_differences)),
        "age_labels_within_0_05_of_neotoma": sum(
            abs(difference) <= 0.05 for difference in age_differences
        ),
        "workbook_age_header": "Sample age (LANDCLIM)",
        "neotoma_age_type": "Calibrated radiocarbon years BP",
        "age_model_identity": "not_established",
        "basin_radius_transfer": "refused",
        "lra_admitted_samples": 0,
    }


def main() -> int:
    parser_ = argparse.ArgumentParser(description=__doc__)
    parser_.add_argument("--workbook", type=Path, required=True)
    parser_.add_argument("--raw-part", type=Path, required=True)
    parser_.add_argument("--output", type=Path, required=True)
    args = parser_.parse_args()
    taxa, workbook_rows = _workbook(args.workbook)
    cells, summary = compare_cells(taxa, workbook_rows, _source_samples(args.raw_part))
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "cell-correspondence.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(cells[0]))
        writer.writeheader()
        writer.writerows(cells)
    report = {
        "schema_version": "bokesjon-native-count-correspondence.v1",
        "neotoma_dataset_id": DATASET_ID,
        "neotoma_site_id": SITE_ID,
        "rootsi_archive_member": "rootsi/BOKE.xls",
        "input_sha256": {
            "neotoma_raw_part": RAW_SHA256,
            "rootsi_workbook": WORKBOOK_SHA256,
        },
        **summary,
    }
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    status = cast(dict[str, int], summary["cell_status_counts"])
    discrepancies = [row for row in cells if row["status"] == "explicit_difference"]
    (args.output / "REPORT.md").write_text(
        "# Bökesjön native count correspondence\n\n"
        f"All {summary['samples']} numeric workbook depth labels match Neotoma dataset {DATASET_ID}, "
        "including the two fractional labels. On exact shared taxon names, "
        f"{status['explicit_agreement']}/{status['explicit_agreement'] + status['explicit_difference']} "
        "explicit NISP cells agree. "
        f"The {len(discrepancies)} differences are "
        + ", ".join(
            f"{row['taxon_exact_label']} at depth {row['sample_depth_label']:g}: workbook {row['workbook_count']}, Neotoma {row['neotoma_explicit_nisp']}"
            for row in discrepancies
        )
        + ". "
        f"There are {status['absent_source_workbook_zero']} workbook-zero cells and "
        f"{status['absent_source_workbook_positive']} workbook-positive cells without a Neotoma row; "
        f"{status['ambiguous_source_duplicate']} cells have repeated Neotoma taxon labels with distinct source elements. "
        "None is converted to a Neotoma zero or merged count.\n\n"
        f"All {summary['age_labels_within_0_05_of_neotoma']} numeric age labels are within 0.05 of their depth-matched Neotoma age; "
        f"the largest absolute difference is {summary['max_absolute_numeric_age_label_difference']:.6f}. "
        "The workbook names LANDCLIM in its age header and Neotoma names a LANDCLIM chronology, "
        "but the workbook does not state an age unit and neither source gives interpolated sample-age bounds. The unmatched taxon "
        "labels, denominator, core/basin identity, 80 m published radius applicability, method "
        "parameters and analytical-use rights remain unqualified. No LRA sample is admitted.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
