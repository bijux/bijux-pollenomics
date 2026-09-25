"""Compare retained Abborrtjärnen workbook counts with Neotoma observations."""

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

DATASET_ID = 19913
SITE_ID = 13338
RAW_SHA256 = "d96046c88b497ba07082120e446fecacad0d9b5533d8960bdbc03811976ea435"
WORKBOOK_SHA256 = "205e7f77adde19b2c590d222acdd526d472e76ac22d0b8f27f7728acf451fa49"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _integer(value: object, label: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
        or value < 0
        or int(value) != value
    ):
        raise ValueError(f"{label} is not an exact nonnegative integer")
    return int(value)


def _workbook_rows(path: Path) -> tuple[list[str], list[dict[str, object]]]:
    if _digest(path) != WORKBOOK_SHA256:
        raise ValueError("Abborrtjärnen workbook bytes differ from retained receipt")
    book = parser().open_workbook(file_contents=path.read_bytes(), formatting_info=True)
    try:
        sheets = book.sheets()
        if len(sheets) != 1 or sheets[0].nrows != 111 or sheets[0].ncols != 96:
            raise ValueError("Abborrtjärnen workbook sheet axes differ")
        sheet = sheets[0]
        if sheet.cell(2, 0).value != "Sample" or sheet.cell(2, 1).value != "Sample age":
            raise ValueError("Abborrtjärnen workbook header differs")
        headers = [sheet.cell(2, column).value for column in range(2, sheet.ncols)]
        if (
            any(not isinstance(value, str) or not value for value in headers)
            or len(set(headers)) != 94
        ):
            raise ValueError("Abborrtjärnen workbook taxon labels are incomplete")
        taxa = [str(value) for value in headers]
        rows = []
        for position in range(4, sheet.nrows):
            sample = _integer(sheet.cell(position, 0).value, "workbook sample label")
            age = sheet.cell(position, 1).value
            if (
                isinstance(age, bool)
                or not isinstance(age, (int, float))
                or not isfinite(age)
            ):
                raise ValueError("Workbook age label is not finite and numeric")
            counts = {
                taxon: _integer(sheet.cell(position, column).value, "workbook count")
                for column, taxon in enumerate(taxa, start=2)
            }
            rows.append(
                {"sample_label": sample, "age_label": float(age), "counts": counts}
            )
        if len(rows) != 107 or len({row["sample_label"] for row in rows}) != 107:
            raise ValueError("Abborrtjärnen workbook sample labels do not close")
        return taxa, rows
    finally:
        book.release_resources()


def _source_samples(path: Path) -> list[dict[str, Any]]:
    if _digest(path) != RAW_SHA256:
        raise ValueError("Neotoma raw part bytes differ from retained receipt")
    raw = json.loads(path.read_text())
    if raw["part_number"] != 4:
        raise ValueError("Neotoma raw part identity differs")
    sites = [
        row["site"]
        for row in raw["rows"]
        if row["site"]["dataset"]["datasetid"] == DATASET_ID
    ]
    if len(sites) != 1 or sites[0]["siteid"] != SITE_ID:
        raise ValueError("Neotoma site or dataset identity differs")
    samples = sites[0]["collectionunit"]["dataset"]["samples"]
    if len(samples) != 107:
        raise ValueError("Neotoma sample denominator differs")
    return cast(list[dict[str, Any]], samples)


def compare_native_counts(
    taxa: list[str],
    workbook_rows: list[dict[str, object]],
    source_samples: list[dict[str, Any]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Pair explicit exact-name NISP cells; retain absent rows and age claims."""
    if len(taxa) != len(set(taxa)) or not taxa:
        raise ValueError("Workbook taxon axis is repeated or empty")
    source_by_label: dict[int, dict[str, Any]] = {}
    source_names: set[str] = set()
    for sample in source_samples:
        label = _integer(sample["depth"], "Neotoma depth label")
        if label in source_by_label:
            raise ValueError("Neotoma depth label is repeated")
        source_by_label[label] = sample
        source_names.update(str(datum["variablename"]) for datum in sample["datum"])
    workbook_labels = [
        _integer(row["sample_label"], "workbook sample label") for row in workbook_rows
    ]
    if len(workbook_labels) != len(set(workbook_labels)) or set(workbook_labels) != set(
        source_by_label
    ):
        raise ValueError("Workbook and Neotoma sample-label axes differ")
    shared = set(taxa) & source_names
    if not shared:
        raise ValueError("No exact source taxon labels overlap")
    totals: Counter[str] = Counter()
    results: list[dict[str, object]] = []
    differences: list[float] = []
    for row in workbook_rows:
        label = _integer(row["sample_label"], "workbook sample label")
        sample = source_by_label[label]
        counts = row["counts"]
        if not isinstance(counts, dict) or set(counts) != set(taxa):
            raise ValueError("Workbook count axis differs")
        datums: dict[str, dict[str, Any]] = {}
        for datum in sample["datum"]:
            name = str(datum["variablename"])
            if name in datums:
                raise ValueError("Neotoma sample repeats a taxon label")
            datums[name] = datum
        ages = sample["ages"]
        if (
            len(ages) != 1
            or ages[0]["agetype"] != "Calibrated radiocarbon years BP"
            or ages[0]["ageolder"] is not None
            or ages[0]["ageyounger"] is not None
        ):
            raise ValueError("Neotoma sample age claim differs from retained scope")
        neotoma_age = ages[0]["age"]
        workbook_age = row["age_label"]
        if (
            not isinstance(neotoma_age, (int, float))
            or not isfinite(neotoma_age)
            or not isinstance(workbook_age, (int, float))
            or not isfinite(workbook_age)
        ):
            raise ValueError("Sample age label is not finite")
        difference = float(workbook_age) - float(neotoma_age)
        differences.append(difference)
        matched = absent = absent_zero = discrepant = mass = workbook_mass = 0
        for taxon in shared:
            workbook_count = _integer(counts[taxon], "workbook count")
            datum = datums.get(taxon)
            if datum is None:
                absent += 1
                absent_zero += workbook_count == 0
                continue
            if datum["units"] != "NISP":
                raise ValueError("Matched Neotoma datum has no NISP count unit")
            source_count = _integer(datum["value"], "Neotoma count")
            matched += 1
            mass += source_count
            workbook_mass += workbook_count
            discrepant += workbook_count != source_count
        totals["explicit_pairs"] += matched
        totals["equal_explicit_pairs"] += matched - discrepant
        totals["discrepant_explicit_pairs"] += discrepant
        totals["explicit_neotoma_mass"] += mass
        totals["workbook_mass_on_explicit_pairs"] += workbook_mass
        totals["absent_neotoma_rows"] += absent
        totals["absent_rows_with_workbook_zero"] += absent_zero
        results.append(
            {
                "sample_label": label,
                "neotoma_sample_id": sample["sampleid"],
                "workbook_age_label_unqualified": workbook_age,
                "neotoma_calibrated_age_bp_claim": neotoma_age,
                "numeric_age_label_difference_unqualified": difference,
                "explicit_exact_name_pairs": matched,
                "discrepant_explicit_pairs": discrepant,
                "explicit_neotoma_nisp_mass": mass,
                "absent_neotoma_rows": absent,
                "absent_rows_with_workbook_zero": absent_zero,
            }
        )
    return results, {
        "samples": len(results),
        "workbook_taxon_labels": len(taxa),
        "neotoma_taxon_labels": len(source_names),
        "exact_shared_taxon_labels": len(shared),
        "workbook_only_taxon_labels": sorted(set(taxa) - source_names),
        "neotoma_only_taxon_labels": sorted(source_names - set(taxa)),
        "counts": dict(sorted(totals.items())),
        "numeric_age_label_difference_range_unqualified": [
            min(differences),
            max(differences),
        ],
        "equal_numeric_age_labels": sum(value == 0 for value in differences),
        "source_age_unit": "Calibrated radiocarbon years BP",
        "workbook_age_unit": "not_documented_in_selected_header",
        "count_scope": "explicit NISP observations with exact taxon-label matches only",
        "basin_radius_transfer": "refused",
        "lra_admitted_samples": 0,
    }


def main() -> int:
    parser_ = argparse.ArgumentParser(description=__doc__)
    parser_.add_argument("--workbook", type=Path, required=True)
    parser_.add_argument("--raw-part", type=Path, required=True)
    parser_.add_argument("--output", type=Path, required=True)
    args = parser_.parse_args()
    taxa, workbook_rows = _workbook_rows(args.workbook)
    rows, summary = compare_native_counts(
        taxa, workbook_rows, _source_samples(args.raw_part)
    )
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    with (output / "sample-correspondence.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "schema_version": "abborrtjarne-native-count-correspondence.v1",
        "neotoma_dataset_id": DATASET_ID,
        "neotoma_site_id": SITE_ID,
        "rootsi_archive_member": "rootsi/ABB.xls",
        "input_sha256": {
            "neotoma_raw_part": RAW_SHA256,
            "rootsi_workbook": WORKBOOK_SHA256,
        },
        **summary,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    count = cast(dict[str, int], summary["counts"])
    age_range = cast(
        list[float], summary["numeric_age_label_difference_range_unqualified"]
    )
    (output / "REPORT.md").write_text(
        "# Abborrtjärnen native count correspondence\n\n"
        f"All {summary['samples']} numeric ABB workbook sample labels match Neotoma dataset {DATASET_ID} depth labels. "
        f"Among {summary['exact_shared_taxon_labels']} exact shared taxon labels, "
        f"{count['equal_explicit_pairs']}/{count['explicit_pairs']} explicitly observed NISP pairs agree, "
        f"with {count['explicit_neotoma_mass']} matched NISP count units. "
        f"Another {count['absent_neotoma_rows']} workbook positions have no Neotoma observation row; "
        "their workbook zeros are retained as absent-row evidence, not imputed Neotoma zeros.\n\n"
        f"Workbook numeric age labels minus Neotoma calibrated-BP claims range from "
        f"{age_range[0]:g} to {age_range[1]:g}. "
        "The workbook column has no documented unit in its selected header, so these "
        "numeric differences do not establish a common chronology. The distinct taxon "
        "labels remain unmapped. This count correspondence strengthens the core-identity "
        "lead but does not establish basin geometry transfer, source rights, a selected "
        "denominator, taxon/PPE profile or LRA admission.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
