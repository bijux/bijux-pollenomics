"""Compare two private Rootsi workbooks with their Neotoma sample records."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

import xlrd


REPOSITORY = Path(__file__).resolve().parents[5]
LEDGER = REPOSITORY / "docs/report/source-relations/rootsi-landclim-overlap/overlap.csv"
RAW_PART = (
    REPOSITORY / "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json"
)
RAW_SHA256 = "9cdcb2d394bc8ef23bf2b4b5e3f1f3ae5916aae16db71542c58f4b80a2dd1134"
DATASETS = {"FLINK": (54024, 28889, 38438, 1, 100), "STAV": (54003, 28873, 38423, 4, 1)}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _neotoma() -> dict[int, dict[str, object]]:
    if _sha256(RAW_PART) != RAW_SHA256:
        raise ValueError("Neotoma source bytes changed")
    source = json.loads(RAW_PART.read_text())
    if source["part_number"] != 8:
        raise ValueError("Neotoma part identity changed")
    return {
        site["dataset"]["datasetid"]: site
        for row in source["rows"]
        if (site := row["site"])["dataset"]["datasetid"] in (54024, 54003)
    }


def build(source_root: Path) -> dict[str, object]:
    """Retain exact depth, age and explicit count evidence without source cells."""
    with LEDGER.open(newline="") as stream:
        ledger = {row["publication_sequence"]: row for row in csv.DictReader(stream)}
    archive = _neotoma()
    findings: list[dict[str, object]] = []
    for sequence, (
        dataset_id,
        site_id,
        chronology_id,
        start,
        scale,
    ) in DATASETS.items():
        claim = ledger[sequence]
        workbook = source_root / claim["typed_workbook_member"]
        if _sha256(workbook) != claim["typed_workbook_sha256"]:
            raise ValueError(f"Workbook source bytes changed: {sequence}")
        sheet = xlrd.open_workbook(str(workbook)).sheet_by_index(0)
        site = archive[dataset_id]
        if site["siteid"] != site_id:
            raise ValueError(f"Neotoma site changed: {sequence}")
        unit = site["collectionunit"]
        if unit["defaultchronology"] != chronology_id:
            raise ValueError(f"Neotoma chronology changed: {sequence}")
        samples = unit["dataset"]["samples"]
        if len(samples) != int(claim["site_samples"]) or sheet.nrows - start != len(
            samples
        ):
            raise ValueError(f"Sample denominator changed: {sequence}")
        by_depth = {float(sample["depth"]): sample for sample in samples}
        if len(by_depth) != len(samples):
            raise ValueError(f"Neotoma sample depths repeat: {sequence}")
        workbook_depths = {
            round(float(sheet.cell_value(index, 0)) * scale, 3): index
            for index in range(start, sheet.nrows)
        }
        if len(workbook_depths) != len(samples) or set(workbook_depths) != set(
            by_depth
        ):
            raise ValueError(f"Source depth axes differ: {sequence}")
        ages = []
        for depth, sample in by_depth.items():
            age_rows = sample["ages"]
            if len(age_rows) != 1:
                raise ValueError(f"Sample age multiplicity changed: {sequence}")
            age = age_rows[0]
            if (
                age["chronologyid"] != chronology_id
                or age["agetype"] != "Calibrated radiocarbon years BP"
                or age["ageolder"] is not None
                or age["ageyounger"] is not None
            ):
                raise ValueError(f"Sample age semantics changed: {sequence}")
            ages.append(float(age["age"]))
        finding: dict[str, object] = {
            "sequence": sequence,
            "workbook_member": claim["typed_workbook_member"],
            "workbook_sha256": claim["typed_workbook_sha256"],
            "neotoma_dataset_id": dataset_id,
            "neotoma_site_id": site_id,
            "neotoma_chronology_id": chronology_id,
            "neotoma_chronology_notes": unit["chronologies"][0]["chronology"][
                "chronology"
            ]["notes"],
            "workbook_sample_rows": len(workbook_depths),
            "neotoma_sample_rows": len(samples),
            "numeric_depth_scale_to_neotoma_cm": scale,
            "paired_depth_rows": len(workbook_depths),
            "neotoma_age_type": "Calibrated radiocarbon years BP",
            "neotoma_age_min_bp": min(ages),
            "neotoma_age_max_bp": max(ages),
            "neotoma_samples_with_age_bounds": 0,
            "historical_landclim_input_authenticated": False,
            "lra_admitted_samples": 0,
        }
        if sequence == "FLINK":
            if sheet.cell_value(0, 1) != "Sample age (cal AD/BC)":
                raise ValueError("FLINK workbook age header changed")
            anchor_taxa = {2: "Betula", 3: "Pinus", 4: "Populus"}
            for column, taxon in anchor_taxa.items():
                if not str(sheet.cell_value(0, column)).startswith(f"\\i{taxon}\\i "):
                    raise ValueError("FLINK count-anchor header changed")
            count_status: Counter[str] = Counter()
            for depth, index in workbook_depths.items():
                pollen: dict[str, list[float]] = {}
                for datum in by_depth[depth]["datum"]:
                    if datum["units"] == "NISP" and datum["element"] == "pollen":
                        pollen.setdefault(datum["variablename"], []).append(
                            float(datum["value"])
                        )
                for column, taxon in anchor_taxa.items():
                    value = float(sheet.cell_value(index, column))
                    source_values = pollen.get(taxon, [])
                    if len(source_values) == 1:
                        status = (
                            "explicit_agreement"
                            if value == source_values[0]
                            else "explicit_difference"
                        )
                    elif len(source_values) > 1:
                        status = "ambiguous_source_name"
                    else:
                        status = (
                            "absent_source_positive"
                            if value > 0
                            else "absent_source_zero"
                        )
                    count_status[status] += 1
            differences = []
            for depth, index in workbook_depths.items():
                source_age = float(sheet.cell_value(index, 1))
                neotoma_age = float(by_depth[depth]["ages"][0]["age"])
                differences.append((index + 1, depth, source_age, 1950 - neotoma_age))
            matched = [row for row in differences if abs(row[2] - row[3]) <= 0.0500001]
            unmatched = [row for row in differences if abs(row[2] - row[3]) > 0.0500001]
            finding.update(
                {
                    "diagnostic_conversion": "1950 - Neotoma calibrated BP, compared numerically with workbook AD/BC label",
                    "age_labels_within_0_05": len(matched),
                    "max_absolute_difference_among_matched": max(
                        abs(row[2] - row[3]) for row in matched
                    ),
                    "selected_count_anchor_taxa": list(anchor_taxa.values()),
                    "selected_count_cell_status": dict(sorted(count_status.items())),
                    "unmatched_age_rows": [
                        {
                            "workbook_sheet_row": row[0],
                            "depth_cm": row[1],
                            "workbook_age_label": row[2],
                            "neotoma_implied_ad_bc": row[3],
                            "neotoma_age_bp": float(by_depth[row[1]]["ages"][0]["age"]),
                            "neotoma_sample_id": by_depth[row[1]]["sampleid"],
                        }
                        for row in unmatched
                    ],
                }
            )
        else:
            if sheet.cell_value(2, 0) != "Sample":
                raise ValueError("STAV workbook header changed")
            headers = [
                str(sheet.cell_value(2, column)).strip()
                for column in range(1, sheet.ncols)
            ]
            if len(headers) != len(set(headers)) or any(not label for label in headers):
                raise ValueError("STAV workbook count axis changed")
            status: Counter[str] = Counter()
            for depth, index in workbook_depths.items():
                pollen: dict[str, list[float]] = {}
                for datum in by_depth[depth]["datum"]:
                    if datum["units"] == "NISP" and datum["element"] == "pollen":
                        pollen.setdefault(datum["variablename"], []).append(
                            float(datum["value"])
                        )
                for column, name in enumerate(headers, start=1):
                    value = float(sheet.cell_value(index, column))
                    source_values = pollen.get(name, [])
                    if len(source_values) == 1:
                        status[
                            "explicit_agreement"
                            if value == source_values[0]
                            else "explicit_difference"
                        ] += 1
                    elif len(source_values) > 1:
                        status["ambiguous_source_name"] += 1
                    else:
                        status[
                            "absent_source_positive"
                            if value > 0
                            else "absent_source_zero"
                        ] += 1
            finding.update(
                {
                    "workbook_age_column": False,
                    "exact_workbook_count_labels": len(headers),
                    "count_cell_status": dict(sorted(status.items())),
                    "neotoma_age_vector_transfer": "candidate_only_no_workbook_age_field",
                }
            )
        findings.append(finding)
    return {
        "schema_version": "rootsi-neotoma-chronology-witness.v1",
        "overlap_ledger_sha256": _sha256(LEDGER),
        "neotoma_raw_part_sha256": RAW_SHA256,
        "findings": findings,
        "interpretation": "Depth and selected pollen counts show shared EPD source lineage, not independent chronology validation. Neotoma point ages witness a FLINK workbook sign discrepancy and provide an STAV candidate age vector; source rights, historical input identity, uncertainty, basin geometry and complete target denominator remain unresolved.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build(args.source_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
