"""Derive workbook/raw-record comparisons independently of maintained producer code."""

from __future__ import annotations

from collections import Counter
import math
from typing import Any

from contracts import require

WITNESS_INTERPRETATION = "Depth and selected pollen counts show shared EPD source lineage, not independent chronology validation. Neotoma point ages witness a FLINK workbook sign discrepancy and provide an STAV candidate age vector; source rights, historical input identity, uncertainty, basin geometry and complete target denominator remain unresolved."
AGE_INTERPRETATION = "The 1950-minus-age integer endpoint comparison is an arithmetic diagnostic of metadata labels, not an authorized AD/BC-to-BP conversion or correction. Source-native cells are point labels, not verified age-model intervals. Reversals are preserved; no interpolation, uncertainty, event date, or historical-input identity is inferred."


def number(value: Any) -> float:
    require(
        type(value) in (int, float) and math.isfinite(value),
        "Finite source numeric cell required",
    )
    return float(value)


def endpoints(values: list[float]) -> list[int]:
    require(bool(values), "Nonempty source age vector required")
    return [math.floor(1950 - max(values) + 0.5), math.floor(1950 - min(values) + 0.5)]


def workbook_age_findings(
    sheets: dict[str, Any], ledger: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    findings = []
    for sequence in ("FLINK", "HOLK", "RANV", "STAV"):
        sheet = sheets[sequence]
        claim = ledger[sequence]
        start = 4 if sequence == "STAV" else 1
        header_index = 2 if sequence == "STAV" else 0
        first, second = (
            str(sheet.cell_value(header_index, column)).strip() for column in (0, 1)
        )
        age_basis = "Sample age (cal AD/BC)" if sequence in ("FLINK", "HOLK") else None
        require(
            first == "Sample"
            and (
                second == age_basis if age_basis else second != "Sample age (cal AD/BC)"
            ),
            "Source age-column header differs",
        )
        require(
            sheet.nrows - start == int(claim["site_samples"]),
            "Source sample denominator differs",
        )
        if sequence == "STAV":
            require(not any(sheet.row_values(3)), "STAV separator row changed")
        ages = []
        if age_basis:
            for index in range(start, sheet.nrows):
                cell = sheet.cell(index, 1)
                require(cell.ctype == 2, "Source age must have numeric XLS type")
                ages.append((index + 1, number(cell.value)))
        reversals = []
        for index in range(1, len(ages)):
            previous, current = ages[index - 1], ages[index]
            if current[1] > previous[1]:
                reversals.append(
                    {
                        "preceding_sheet_row": previous[0],
                        "preceding_age": previous[1],
                        "following_sheet_row": current[0],
                        "following_age": current[1],
                    }
                )
        metadata = [int(claim["source_top_bp"]), int(claim["source_bottom_bp"])]
        values = [value for _, value in ages]
        diagnostic = None
        if age_basis and len(reversals) == 1:
            excluded = reversals[0]["following_sheet_row"]
            remaining = [value for index, value in ages if index != excluded]
            diagnostic = {
                "omitted_sheet_row": excluded,
                "numeric_1950_minus_age_endpoints_bp": endpoints(remaining),
                "matches_metadata_bounds": endpoints(remaining) == metadata,
                "status": "diagnostic_only_not_an_age_correction",
            }
        findings.append(
            {
                "sequence": sequence,
                "workbook_member": claim["typed_workbook_member"],
                "workbook_sha256": claim["typed_workbook_sha256"],
                "sheet": sheet.name,
                "sample_rows": int(claim["site_samples"]),
                "second_column_header": second,
                "source_age_basis": age_basis,
                "numeric_source_ages": len(ages),
                "source_age_min": min(values) if values else None,
                "source_age_max": max(values) if values else None,
                "strict_age_reversals_in_sheet_order": reversals if age_basis else None,
                "exact_duplicate_source_ages": len(ages) - len(set(values))
                if age_basis
                else None,
                "source_metadata_bounds_bp": metadata,
                "numeric_1950_minus_age_extrema_bp": endpoints(values)
                if age_basis
                else None,
                "all_age_extrema_match_metadata": endpoints(values) == metadata
                if age_basis
                else None,
                "single_reversal_row_omission_diagnostic": diagnostic,
                "dated_event_admitted": False,
            }
        )
    return findings


def count_status(value: float, choices: list[float]) -> str:
    require(value >= 0 and all(item >= 0 for item in choices), "Negative pollen count")
    if len(choices) > 1:
        return "ambiguous_source_name"
    if len(choices) == 1:
        return "explicit_agreement" if choices[0] == value else "explicit_difference"
    return "absent_source_positive" if value > 0 else "absent_source_zero"


def neotoma_findings(
    sheets: dict[str, Any], ledger: dict[str, dict[str, str]], raw: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    require(
        type(raw["part_number"]) is int and raw["part_number"] == 8,
        "Raw Neotoma part identity differs",
    )
    findings = []
    joins = {}
    for sequence, dataset, site_id, chronology, start, scale in [
        ("FLINK", 54024, 28889, 38438, 1, 100),
        ("STAV", 54003, 28873, 38423, 4, 1),
    ]:
        sites = [
            row["site"]
            for row in raw["rows"]
            if row["site"]["dataset"]["datasetid"] == dataset
        ]
        require(len(sites) == 1, "Unique actual Neotoma dataset required")
        site = sites[0]
        unit = site["collectionunit"]
        samples = unit["dataset"]["samples"]
        sheet = sheets[sequence]
        claim = ledger[sequence]
        require(
            site["siteid"] == site_id and unit["defaultchronology"] == chronology,
            "Site/chronology identity differs",
        )
        require(
            len(samples) == int(claim["site_samples"]) == sheet.nrows - start,
            "Workbook/Neotoma sample denominator differs",
        )
        source_depths = {
            round(number(sheet.cell_value(index, 0)) * scale, 3): index
            for index in range(start, sheet.nrows)
        }
        native_depths = {number(sample["depth"]): sample for sample in samples}
        require(
            len(source_depths) == len(native_depths) == len(samples)
            and set(source_depths) == set(native_depths),
            "Duplicate or different source depth axes",
        )
        ages = []
        for sample in samples:
            require(len(sample["ages"]) == 1, "One native point age required")
            age = sample["ages"][0]
            require(
                age["chronologyid"] == chronology
                and age["agetype"] == "Calibrated radiocarbon years BP"
                and age["ageolder"] is None
                and age["ageyounger"] is None,
                "Native source age semantics/bounds differ",
            )
            ages.append(number(age["age"]))
        finding = {
            "sequence": sequence,
            "workbook_member": claim["typed_workbook_member"],
            "workbook_sha256": claim["typed_workbook_sha256"],
            "neotoma_dataset_id": dataset,
            "neotoma_site_id": site_id,
            "neotoma_chronology_id": chronology,
            "neotoma_chronology_notes": unit["chronologies"][0]["chronology"][
                "chronology"
            ]["notes"],
            "workbook_sample_rows": len(source_depths),
            "neotoma_sample_rows": len(samples),
            "numeric_depth_scale_to_neotoma_cm": scale,
            "paired_depth_rows": len(source_depths),
            "neotoma_age_type": "Calibrated radiocarbon years BP",
            "neotoma_age_min_bp": min(ages),
            "neotoma_age_max_bp": max(ages),
            "neotoma_samples_with_age_bounds": 0,
            "historical_landclim_input_authenticated": False,
            "lra_admitted_samples": 0,
        }
        if sequence == "FLINK":
            require(
                sheet.cell_value(0, 1) == "Sample age (cal AD/BC)",
                "FLINK age header differs",
            )
            labels = ["Betula", "Pinus", "Populus"]
            for column, label in enumerate(labels, 2):
                require(
                    str(sheet.cell_value(0, column)).startswith("\\i" + label + "\\i "),
                    "FLINK literal count-anchor differs",
                )
            axes = list(enumerate(labels, 2))
            status_key = "selected_count_cell_status"
        else:
            require(sheet.cell_value(2, 0) == "Sample", "STAV source header differs")
            labels = [
                str(sheet.cell_value(2, index)).strip()
                for index in range(1, sheet.ncols)
            ]
            require(
                bool(labels) and all(labels) and len(labels) == len(set(labels)),
                "STAV literal count axis invalid",
            )
            axes = list(enumerate(labels, 1))
            status_key = "count_cell_status"
        statuses: Counter[str] = Counter()
        differences = []
        for depth, index in source_depths.items():
            sample = native_depths[depth]
            by_name: dict[str, list[float]] = {}
            for datum in sample["datum"]:
                if datum["units"] == "NISP" and datum["element"] == "pollen":
                    by_name.setdefault(datum["variablename"], []).append(
                        number(datum["value"])
                    )
            for column, label in axes:
                statuses[
                    count_status(
                        number(sheet.cell_value(index, column)), by_name.get(label, [])
                    )
                ] += 1
            if sequence == "FLINK":
                workbook_age = number(sheet.cell_value(index, 1))
                implied = 1950 - number(sample["ages"][0]["age"])
                differences.append((index + 1, depth, workbook_age, implied, sample))
        finding[status_key] = dict(sorted(statuses.items()))
        if sequence == "FLINK":
            matched = [row for row in differences if abs(row[2] - row[3]) <= 0.0500001]
            unmatched = [row for row in differences if abs(row[2] - row[3]) > 0.0500001]
            require(bool(matched), "Source age-label diagnostic has no matched rows")
            finding.update(
                diagnostic_conversion="1950 - Neotoma calibrated BP, compared numerically with workbook AD/BC label",
                age_labels_within_0_05=len(matched),
                max_absolute_difference_among_matched=max(
                    abs(row[2] - row[3]) for row in matched
                ),
                selected_count_anchor_taxa=labels,
                unmatched_age_rows=[
                    {
                        "workbook_sheet_row": row[0],
                        "depth_cm": row[1],
                        "workbook_age_label": row[2],
                        "neotoma_implied_ad_bc": row[3],
                        "neotoma_age_bp": number(row[4]["ages"][0]["age"]),
                        "neotoma_sample_id": row[4]["sampleid"],
                    }
                    for row in unmatched
                ],
            )
        else:
            finding.update(
                workbook_age_column=False,
                exact_workbook_count_labels=len(labels),
                neotoma_age_vector_transfer="candidate_only_no_workbook_age_field",
            )
        joins[sequence] = {
            "native_sample_ids": [sample["sampleid"] for sample in samples],
            "matched_depth_rows": len(source_depths),
            "compared_count_cells": sum(statuses.values()),
            "count_axis_labels": labels,
            "source_age_bounds_present": False,
        }
        require(
            len({sample["sampleid"] for sample in samples}) == len(samples),
            "Duplicate native sample IDs",
        )
        findings.append(finding)
    return findings, joins
