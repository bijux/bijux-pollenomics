"""Validate retained calculation, source scope and subsequent account admission."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.author_snapshot import (
    validated_author_snapshot,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_paths import safe_source_file

from .authority import (
    CAPTURE,
    CAPTURE_SHA256,
    DESCRIPTOR,
    DESCRIPTOR_SHA256,
    SOURCE_ID,
    SOURCE_SHA256,
)

METHODS = [
    "empirical_compositional_correction",
    "uncorrected_pollen",
    "training_mapped_composition",
]
AXES = ["Acacia", "Dichrostachys", "Grewia", "Poaceae", "Combretaceae"]
RADII = list(range(100, 1501, 100))
SITES = [f"Namibia_T{i}" for i in range(1, 11)]
GROUPS = (
    [[s] for s in SITES[:3]] + [["Namibia_T4", "Namibia_T5"]] + [[s] for s in SITES[5:]]
)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate Namibia source JSON key")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError("nonfinite Namibia source JSON constant: " + value)


def read_json(body: bytes) -> Any:
    result = json.loads(body, object_pairs_hook=_pairs, parse_constant=_constant)

    def finite(value: Any) -> None:
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("nonfinite Namibia source JSON value")
        if isinstance(value, dict):
            for child in value.values():
                finite(child)
        elif isinstance(value, list):
            for child in value:
                finite(child)

    finite(result)
    return result


def _count(value: Any, expected: int) -> bool:
    return type(value) is int and value == expected


def _row_keys(rows: list[dict[str, Any]]) -> set[tuple[str, int, str]]:
    return {(r["site"], r["radius_label_m"], r["method"]) for r in rows}


def validate(values: dict[str, Any]) -> None:
    """Check saved authority and exact populations; do not recompute predictions/losses."""
    terminal = values["native-terminal.json"]
    if not (
        _count(terminal["native_exit_code"], 0)
        and terminal["status"] == "PASS_PENDING_SOURCE_CAPTURE_ADMISSION"
        and terminal["custody_after_checked"] is True
        and terminal["custody_after_unchanged"] is True
        and terminal["resource_failure"] is None
        and terminal["custody_errors"] == []
        and terminal["owned_survivors"] == {}
        and terminal["plan_sha256"] == SOURCE_SHA256["study-plan.json"]
    ):
        raise ValueError("Namibia original native terminal is unsettled")
    for family, bindings in {
        "native_files": {
            "report.json": "native-report.json",
            "source-guards.json": "source-guards.json",
            "source-support.json": "source-support.json",
            "overlap-folds.json": "overlap-folds.json",
            "prediction-ledger.json": "prediction-ledger.json",
            "scores.json": "scores.json",
        },
        "comparison_files": {
            "independent-numerical-review.json": "independent-numerical-review.json"
        },
    }.items():
        for original, retained in bindings.items():
            if terminal[family][original]["sha256"] != SOURCE_SHA256[retained]:
                raise ValueError("Namibia native output binding differs")
    if terminal["log_sha256"] != SOURCE_SHA256["native.log"]:
        raise ValueError("Namibia original log binding differs")
    plan = values["study-plan.json"]
    if plan["candidate"] != terminal["candidate"]:
        raise ValueError("Namibia original candidate differs")
    for name, sha in plan["controls_sha256"].items():
        retained = (
            name
            if name in ("protocol.json", "scientific-controls-inventory.json")
            else "original-" + name
        )
        if SOURCE_SHA256[retained] != sha:
            raise ValueError("Namibia original control binding differs")
    protocol = values["protocol.json"]
    model = values["native-report.json"]
    source = values["source-support.json"]
    if (
        protocol["taxa"] != AXES
        or protocol["methods"] != METHODS
        or protocol["radii_m"] != RADII
        or protocol["expected_groups"] != GROUPS
    ):
        raise ValueError("Namibia protocol axes or group support differs")
    for flag, expected in {
        "target_data_already_exposed": True,
        "untouched_confirmation": False,
        "field_vegetation_accuracy": False,
        "PPE_or_ERV_estimation": False,
        "radius_selection_allowed": False,
        "positive_observed_source_cells_required": True,
        "source_year_or_BP_conversion": False,
    }.items():
        if protocol[flag] is not expected:
            raise ValueError("Namibia source or scientific claim differs: " + flag)
    if not (
        _count(protocol["sphere_radius_m"], 6371000)
        and _count(protocol["nominal_source_envelope_radius_m"], 1500)
        and _count(protocol["group_intersection_threshold_m"], 3000)
    ):
        raise ValueError("Namibia nominal geometry convention differs")
    for name in ("PANGAEA.931033.tab", "PANGAEA.931035.tab"):
        if (
            protocol["source_hashes"][name] != SOURCE_SHA256[name]
            or source["source_hashes"][name] != SOURCE_SHA256[name]
            or model["source_hashes"][name] != SOURCE_SHA256[name]
        ):
            raise ValueError("Namibia original count/area identity differs")
    if (
        model["status"]
        != "new_training_only_development_consumer_completed_pending_independent_numerical_review"
        or model["no_radius_selection"] is not True
        or model["PPE_ERV_field_vegetation_Nordic_or_untouched_claim"] is not False
        or model["protocol_sha256"] != SOURCE_SHA256["protocol.json"]
    ):
        raise ValueError("Namibia original pending status or claim scope differs")
    population = {
        "methods": 3,
        "nominal_overlap_groups": 9,
        "paired_method_contrasts": 300,
        "predicted_fraction_cells": 2250,
        "prediction_vectors": 450,
        "radius_labels": 15,
        "scores": 450,
        "sites": 10,
        "summaries": 45,
        "taxa": 5,
        "unique_five_label_grain_total": 6894,
    }
    if set(model["population"]) != set(population) or any(
        not _count(model["population"][k], n) for k, n in population.items()
    ):
        raise ValueError("Namibia original population differs")
    for name, sha in model["producer_sources"].items():
        if sha != SOURCE_SHA256["original-" + name]:
            raise ValueError("Namibia numerical producer authority differs")
    if len(values["source-guards.json"]) != 17:
        raise ValueError("Namibia actual source guard population differs")
    if (
        source["taxa"] != AXES
        or set(source["counts"]) != set(SITES)
        or set(source["areas_m2"]) != set(SITES)
    ):
        raise ValueError("Namibia original source panel differs")
    for counts in source["counts"].values():
        if len(counts) != 5 or any(type(n) is not int or n <= 0 for n in counts):
            raise ValueError("Namibia positive observed source counts differ")
    if sum(sum(v) for v in source["counts"].values()) != 6894:
        raise ValueError("Namibia unique five-label grain denominator differs")
    for areas in source["areas_m2"].values():
        if set(areas) != {str(r) for r in RADII} or any(
            len(v) != 5
            or any(
                type(a) not in (int, float) or not math.isfinite(a) or a <= 0 for a in v
            )
            for v in areas.values()
        ):
            raise ValueError("Namibia complete positive map ring source differs")
    folds = values["overlap-folds.json"]
    if (
        folds["groups"] != GROUPS
        or not _count(folds["folds"], 9)
        or not _count(folds["heldout_sites"], 10)
        or len(folds["pairs"]) != 45
        or [r["sites"] for r in folds["pairs"] if r["nominal_envelopes_intersect"]]
        != [["Namibia_T4", "Namibia_T5"]]
    ):
        raise ValueError("Namibia nominal overlap grouping differs")
    predictions = values["prediction-ledger.json"]
    scores = values["scores.json"]
    if (
        predictions["groups"] != GROUPS
        or predictions["taxa"] != AXES
        or predictions["methods"] != METHODS
        or predictions["source_already_exposed"] is not True
        or predictions["protocol_sha256"] != SOURCE_SHA256["protocol.json"]
        or scores["prediction_ledger_sha256"] != SOURCE_SHA256["prediction-ledger.json"]
    ):
        raise ValueError("Namibia saved prediction ledger authority differs")
    expected_keys = {(s, r, m) for s in SITES for r in RADII for m in METHODS}
    if (
        len(predictions["predictions"]) != 450
        or len(scores["scores"]) != 450
        or _row_keys(predictions["predictions"]) != expected_keys
        or _row_keys(scores["scores"]) != expected_keys
    ):
        raise ValueError("Namibia paired prediction/score population differs")
    for row in predictions["predictions"]:
        heldout = next(g for g in GROUPS if row["site"] in g)
        if row["heldout_group"] != heldout or row["training_groups"] != [
            g for g in GROUPS if g != heldout
        ]:
            raise ValueError("Namibia held-out whole-group exclusion differs")
        vector = row["predicted_five_taxon_fractions"]
        if (
            len(vector) != 5
            or any(
                type(v) not in (int, float) or not math.isfinite(v) or v <= 0
                for v in vector
            )
            or abs(sum(vector) - 1) > 1e-12
        ):
            raise ValueError("Namibia positive five-taxon prediction simplex differs")
    for row in scores["scores"]:
        target = row["observed_deposited_calculated_area_fractions"]
        if (
            len(target) != 5
            or any(
                type(v) not in (int, float) or not math.isfinite(v) or v <= 0
                for v in target
            )
            or abs(sum(target) - 1) > 1e-12
            or type(row["squared_Hellinger"]) not in (int, float)
            or not 0 <= row["squared_Hellinger"] <= 1
        ):
            raise ValueError("Namibia saved target/loss scope differs")
    summaries = scores["summaries"]
    if (
        len(summaries) != 45
        or {(r["radius_label_m"], r["method"]) for r in summaries}
        != {(r, m) for r in RADII for m in METHODS}
        or any(
            not _count(r["site_denominator"], 10)
            or not _count(r["overlap_group_denominator"], 9)
            for r in summaries
        )
    ):
        raise ValueError("Namibia complete means and denominator scope differs")
    contrasts = scores["all300_paired_contrasts"]
    if len(contrasts) != 300 or {
        (r["site"], r["radius_label_m"], r["comparator"]) for r in contrasts
    } != {(s, r, m) for s in SITES for r in RADII for m in METHODS[1:]}:
        raise ValueError("Namibia complete paired contrast support differs")
    negative = [r for r in contrasts if r["empirical_poorer"] is True]
    if (
        len(negative) != 110
        or negative != model["negative_contrasts_retained"]
        or [
            sum(
                r["empirical_poorer"] is True for r in contrasts if r["comparator"] == m
            )
            for m in METHODS[1:]
        ]
        != [20, 90]
    ):
        raise ValueError("Namibia poorer source outcomes were changed or removed")
    oracle = values["independent-numerical-review.json"]
    if (
        oracle["status"] != "source_bound_numerical_agreement"
        or not _count(oracle["total_numeric_fields_compared"], 7290)
        or not _count(oracle["distinct_prediction_fraction_cells"], 2250)
        or not _count(oracle["source_position_pair_count"], 45)
        or oracle["prediction_ledger_sha256"] != SOURCE_SHA256["prediction-ledger.json"]
        or oracle["scores_sha256"] != SOURCE_SHA256["scores.json"]
        or oracle["controls_sha256"]["protocol.json"] != SOURCE_SHA256["protocol.json"]
        or oracle["controls_sha256"]["independent.py"]
        != SOURCE_SHA256["original-independent.py"]
        or oracle["same_interpreter_different_numerical_implementation"] is not True
        or oracle["no_independent_field_model_PPE_ERV_or_untouched_admission"]
        is not True
        or not 0 <= float(oracle["maximum_abs_numerical_gap"]) <= 1e-12
        or oracle["unchanged_abs_tolerance"] != "1e-12"
    ):
        raise ValueError("Namibia distinct actual numerical qualification differs")
    qualification = values["original-account-saved-result-qualification.json"]
    if (
        qualification["terminal_sha256"] != SOURCE_SHA256["native-terminal.json"]
        or qualification["plan_sha256"] != SOURCE_SHA256["study-plan.json"]
        or qualification["native_pending_report_preserved"] is not True
    ):
        raise ValueError("Namibia saved-result source account differs")
    account = values["source-account-inventory.json"]
    for name, pin in account["members"].items():
        if pin["sha256"] != SOURCE_SHA256["original-account-" + name]:
            raise ValueError("Namibia original seven-member reader account differs")
    reviewer = values["independent-account-review.json"]
    if (
        reviewer["decision"]
        != "accepted_for_scoped_retained_source_account_with_minor_precision_note"
        or reviewer["account_inventory_sha256"]
        != SOURCE_SHA256["source-account-inventory.json"]
        or reviewer["native_terminal_sha256"] != SOURCE_SHA256["native-terminal.json"]
        or reviewer["actual_independent_numerical_review_sha256"]
        != SOURCE_SHA256["independent-numerical-review.json"]
        or not _count(
            reviewer["actual_unfamiliar_reader_exercises_completed_by_this_review"], 0
        )
        or not _count(
            reviewer["qualified_external_review_decisions_received_by_this_review"], 0
        )
    ):
        raise ValueError("Namibia independent agent source review scope differs")


def load_inputs(repository: Path, source_root: Path) -> dict[str, Any]:
    descriptor = safe_source_file(
        repository, DESCRIPTOR.as_posix(), "Namibia source descriptor"
    )
    capture = safe_source_file(
        repository, CAPTURE.as_posix(), "Namibia retained capture"
    )
    if (
        hashlib.sha256(descriptor.read_bytes()).hexdigest() != DESCRIPTOR_SHA256
        or hashlib.sha256(capture.read_bytes()).hexdigest() != CAPTURE_SHA256
    ):
        raise ValueError("Namibia descriptor or capture identity changed")
    control = read_json(capture.read_bytes())
    if (
        control["source_id"] != SOURCE_ID
        or control["source_files_sha256"] != SOURCE_SHA256
        or control["original_native_pending_status_preserved"] is not True
        or control["numerical_reexecution_by_retained_writer"] is not False
        or control["private_raw_rows_promoted"] is not False
        or control["actual_unfamiliar_or_qualified_external_review_admitted"]
        is not False
        or control["field_vegetation_PPE_ERV_or_historical_reproduction_admitted"]
        is not False
    ):
        raise ValueError(
            "Namibia retained capture membership or scientific scope differs"
        )
    qualified = validated_author_snapshot(repository, source_root, DESCRIPTOR)
    if {p.name for p in qualified.directory.iterdir()} != set(SOURCE_SHA256) | {
        "manifest.json"
    }:
        raise ValueError("Namibia owned source family contains unexpected members")
    values: dict[str, Any] = {}
    for name, expected in SOURCE_SHA256.items():
        body = safe_source_file(
            qualified.directory, name, "Namibia exact retained source"
        ).read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError("Namibia retained source byte identity changed")
        if name.endswith(".json"):
            values[name] = read_json(body)
    try:
        validate(values)
    except (KeyError, TypeError, StopIteration) as error:
        raise ValueError("Namibia retained source schema is incomplete") from error
    return values
