"""Compare uniquely casefolded Bussjösjön workbook and Neotoma counts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from math import isfinite
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.collection.sources.rootsi.cells.decoding import parser

DATASET_ID = 53995
SITE_ID = 28869
RAW_SHA256 = "9cdcb2d394bc8ef23bf2b4b5e3f1f3ae5916aae16db71542c58f4b80a2dd1134"
WORKBOOK_SHA256 = "f807c5dc0b624db382ce81959ea7d48c348b637018faa873b7ab9ad1f23e197e"


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
        raise ValueError("Bussjösjön workbook bytes differ from retained receipt")
    book = parser().open_workbook(file_contents=path.read_bytes(), formatting_info=True)
    try:
        sheets = book.sheets()
        if len(sheets) != 1 or sheets[0].nrows != 73 or sheets[0].ncols != 116:
            raise ValueError("Bussjösjön workbook axes differ")
        sheet = sheets[0]
        if (
            sheet.cell(0, 0).value != "raw pollen data Bussjosjon_depth in cm"
            or sheet.cell(2, 0).value != "Sample"
        ):
            raise ValueError("Bussjösjön workbook header differs")
        raw_headers = [sheet.cell(2, column).value for column in range(1, sheet.ncols)]
        if any(not isinstance(value, str) or not value for value in raw_headers):
            raise ValueError("Bussjösjön workbook taxon headers are incomplete")
        headers = [str(value) for value in raw_headers]
        rows = [
            {
                "sample_label": _number(
                    sheet.cell(position, 0).value, "workbook sample label"
                ),
                "counts": [
                    _count(sheet.cell(position, column).value, "workbook count")
                    for column in range(1, sheet.ncols)
                ],
            }
            for position in range(4, sheet.nrows)
        ]
        if len(rows) != 69 or len({row["sample_label"] for row in rows}) != 69:
            raise ValueError("Bussjösjön workbook sample labels do not close")
        return headers, rows
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
    if len(samples) != 69:
        raise ValueError("Neotoma sample denominator differs")
    return cast(list[dict[str, Any]], samples)


def compare_casefold_counts(
    headers: list[str],
    workbook_rows: list[dict[str, object]],
    samples: list[dict[str, Any]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Use only unique casefold labels and explicit source NISP observations."""
    if not headers or any(not header for header in headers):
        raise ValueError("Workbook count header is empty")
    header_positions: dict[str, list[int]] = defaultdict(list)
    for column, header in enumerate(headers):
        header_positions[header.casefold()].append(column)
    source_by_label: dict[float, dict[str, Any]] = {}
    source_names: dict[str, set[str]] = defaultdict(set)
    for sample in samples:
        label = _number(sample["depth"], "Neotoma depth")
        if label in source_by_label:
            raise ValueError("Neotoma sample label repeats")
        source_by_label[label] = sample
        for datum in sample["datum"]:
            source_names[str(datum["variablename"]).casefold()].add(
                str(datum["variablename"])
            )
    workbook_by_label = {
        _number(row["sample_label"], "workbook sample label"): row
        for row in workbook_rows
    }
    if len(workbook_by_label) != len(workbook_rows) or set(workbook_by_label) != set(
        source_by_label
    ):
        raise ValueError("Workbook and Neotoma sample-label axes differ")
    shared = sorted(
        key
        for key, positions in header_positions.items()
        if len(positions) == 1 and len(source_names.get(key, set())) == 1
    )
    if not shared:
        raise ValueError("No unique casefold source labels overlap")
    cells: list[dict[str, object]] = []
    totals: Counter[str] = Counter()
    for label in sorted(workbook_by_label):
        row = workbook_by_label[label]
        counts = row["counts"]
        if not isinstance(counts, list) or len(counts) != len(headers):
            raise ValueError("Workbook count row width differs")
        sample = source_by_label[label]
        datums: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for datum in sample["datum"]:
            datums[str(datum["variablename"]).casefold()].append(datum)
        for key in shared:
            column = header_positions[key][0]
            workbook_count = _count(counts[column], "workbook count")
            matches = datums.get(key, [])
            if not matches:
                status = (
                    "absent_source_workbook_zero"
                    if workbook_count == 0
                    else "absent_source_workbook_positive"
                )
                source_count: int | None = None
            elif len(matches) > 1:
                status = "ambiguous_source_duplicate"
                source_count = None
            else:
                datum = matches[0]
                if datum["units"] != "NISP":
                    raise ValueError("Matched Neotoma datum has no NISP count unit")
                source_count = _count(datum["value"], "Neotoma NISP")
                status = (
                    "explicit_agreement"
                    if source_count == workbook_count
                    else "explicit_difference"
                )
                totals["explicit_neotoma_mass"] += source_count
                totals["workbook_mass_on_explicit_pairs"] += workbook_count
            totals[status] += 1
            cells.append(
                {
                    "sample_label": label,
                    "neotoma_sample_id": sample["sampleid"],
                    "workbook_taxon_label": headers[column],
                    "neotoma_taxon_label": next(iter(source_names[key])),
                    "workbook_count": workbook_count,
                    "neotoma_explicit_nisp": source_count
                    if source_count is not None
                    else "",
                    "status": status,
                }
            )
    zero_duplicate_candidates: list[dict[str, object]] = []
    for key, positions in sorted(header_positions.items()):
        if len(positions) != 2 or len(source_names.get(key, set())) != 1:
            continue
        column_mass = [
            sum(
                _count(
                    cast(list[object], row["counts"])[column],
                    "duplicate workbook count",
                )
                for row in workbook_rows
            )
            for column in positions
        ]
        if sum(mass > 0 for mass in column_mass) != 1:
            continue
        retained_column = positions[
            next(i for i, mass in enumerate(column_mass) if mass)
        ]
        source_pairs = equal_pairs = source_mass = 0
        for label in sorted(workbook_by_label):
            row = workbook_by_label[label]
            sample = source_by_label[label]
            matches = [
                datum
                for datum in sample["datum"]
                if str(datum["variablename"]).casefold() == key
            ]
            if len(matches) != 1 or matches[0]["units"] != "NISP":
                raise ValueError(f"Duplicate-column source identity changed: {key}")
            source_count = _count(matches[0]["value"], "duplicate source count")
            workbook_count = _count(
                cast(list[object], row["counts"])[retained_column],
                "duplicate workbook count",
            )
            source_pairs += 1
            equal_pairs += source_count == workbook_count
            source_mass += source_count
        zero_duplicate_candidates.append(
            {
                "casefold_label": key,
                "workbook_positions": positions,
                "workbook_column_mass": column_mass,
                "source_pairs": source_pairs,
                "equal_pairs": equal_pairs,
                "source_mass": source_mass,
                "status": "unapplied_zero_only_duplicate_column_candidate",
            }
        )
    return cells, {
        "samples": len(workbook_rows),
        "workbook_header_columns": len(headers),
        "unique_casefold_shared_taxon_labels": len(shared),
        "excluded_duplicate_workbook_labels": {
            key: positions
            for key, positions in sorted(header_positions.items())
            if len(positions) > 1
        },
        "zero_only_duplicate_column_candidates": zero_duplicate_candidates,
        "cell_status_counts": dict(sorted(totals.items())),
        "comparison_rule": "unique casefold labels only; no semantic taxon mapping",
        "workbook_age_column": "absent",
        "basin_radius_transfer": "refused",
        "lra_admitted_samples": 0,
    }


def main() -> int:
    parser_ = argparse.ArgumentParser(description=__doc__)
    parser_.add_argument("--workbook", type=Path, required=True)
    parser_.add_argument("--raw-part", type=Path, required=True)
    parser_.add_argument("--output", type=Path, required=True)
    args = parser_.parse_args()
    headers, workbook_rows = _workbook(args.workbook)
    cells, summary = compare_casefold_counts(
        headers, workbook_rows, _source_samples(args.raw_part)
    )
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "cell-correspondence.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(cells[0]))
        writer.writeheader()
        writer.writerows(cells)
    report = {
        "schema_version": "bussjosjon-native-count-correspondence.v1",
        "neotoma_dataset_id": DATASET_ID,
        "neotoma_site_id": SITE_ID,
        "rootsi_archive_member": "rootsi/BUS.xls",
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
    duplicate_candidates = cast(
        list[dict[str, object]], summary["zero_only_duplicate_column_candidates"]
    )
    (args.output / "REPORT.md").write_text(
        "# Bussjösjön native count correspondence\n\n"
        f"All {summary['samples']} numeric workbook sample labels match Neotoma dataset {DATASET_ID} depth labels. "
        f"For {summary['unique_casefold_shared_taxon_labels']} unique casefold-only taxon labels, "
        f"{status['explicit_agreement']}/{status['explicit_agreement'] + status.get('explicit_difference', 0)} "
        f"explicit NISP cells agree, with {status['explicit_neotoma_mass']} matched count units. "
        f"The {status['absent_source_workbook_zero']} workbook-zero cells without Neotoma rows "
        "remain absent source observations, not imputed zeros. Duplicated BETULA and PINUS "
        "workbook columns are excluded from the label join.\n\n"
        "The workbook has no sample-age column. "
        f"A separate unapplied zero-only duplicate-column check finds {sum(cast(int, row['equal_pairs']) for row in duplicate_candidates)} matching source cells; "
        "it does not change the primary unique-label count denominator. "
        "This orthographic count correspondence does not establish a taxon/PPE profile, selected chronology, count denominator, "
        "physical core/basin identity, 69 m published radius applicability or analytical-use "
        "rights. No LRA sample is admitted.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
