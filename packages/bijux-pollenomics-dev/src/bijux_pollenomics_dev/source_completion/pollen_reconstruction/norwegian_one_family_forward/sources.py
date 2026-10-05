"""Authenticate retained source custody and later scoped numerical qualification."""

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


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate Norwegian source JSON key")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError("nonfinite Norwegian source JSON constant: " + value)


def read_json(body: bytes) -> Any:
    result = json.loads(body, object_pairs_hook=_pairs, parse_constant=_constant)

    def finite(value: Any) -> None:
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("nonfinite Norwegian source JSON number")
        if isinstance(value, dict):
            for child in value.values():
                finite(child)
        if isinstance(value, list):
            for child in value:
                finite(child)

    finite(result)
    return result


def validate(values: dict[str, Any]) -> None:
    """Refuse source or scope drift without repeating physical model execution."""
    receipt = values["native-terminal.json"]
    if (
        type(receipt["native_exit_code"]) is not int
        or receipt["native_exit_code"] != 0
        or receipt["status"] != "PASS_PENDING_SOURCE_CAPTURE_ADMISSION"
        or receipt["custody_after_checked"] is not True
        or receipt["custody_after_unchanged"] is not True
        or receipt["custody_errors"]
        or receipt["owned_survivors"]
        or receipt["resource_failure"] is not None
        or receipt["plan_sha256"] != SOURCE_SHA256["study-plan.json"]
    ):
        raise ValueError("Norwegian original terminal is unsettled")
    for group, bindings in {
        "native_files": {
            "report.json": "model-report.json",
            "prediction-ledger.json": "prediction-ledger.json",
            "outcome-ledger.json": "outcome-ledger.json",
            "score-ledger.json": "score-ledger.json",
            "local-native-source-support.json": "private-native-source-support.json",
            "new-physical-tuples.json": "new-physical-tuples.json",
            "algebra-controls.json": "algebra-controls.json",
        },
        "comparison_files": {
            "source-guards.json": "source-guards.json",
            "independent-scalar-review.json": "independent-scalar-review.json",
            "independent-252m-physical-review.json": "independent-physical-review.json",
            "consumer-result.json": "consumer-result.json",
            "stages.json": "stages.json",
        },
    }.items():
        for original, captured in bindings.items():
            if receipt[group][original]["sha256"] != SOURCE_SHA256[captured]:
                raise ValueError("Norwegian original output authority differs")
    plan = values["study-plan.json"]
    if plan["candidate"] != receipt["candidate"]:
        raise ValueError("Norwegian original candidate differs")
    for name in (
        "source_support.py",
        "workbook.py",
        "predict.py",
        "independent.py",
        "lens.py",
        "collect.py",
        "runner.py",
    ):
        if plan["controls_sha256"][name] != SOURCE_SHA256["original-" + name]:
            raise ValueError("Norwegian original producer controls differ")
    if plan["controls_sha256"]["protocol.json"] != SOURCE_SHA256["protocol.json"]:
        raise ValueError("Norwegian protocol authority differs")
    protocol = values["protocol.json"]
    model = values["model-report.json"]
    if (
        protocol["context_mask"] != [1486, 1436]
        or protocol["distance_radius_m"] != 100000
        or protocol["training_dataset_ids"] != [4286, 4372]
        or protocol["target_dataset_id"] != 20034
        or protocol["grouping"]["independent_training_family_count"] != 1
        or protocol["grouping"]["primary_training_family"] != [1096]
        or protocol["grouping"]["target_primary_family"] != [9495]
        or protocol["grouping"]["statistical_independence_established"] is not False
        or [
            (r["dataset_id"], r["chronology_id"], r["radius_m"])
            for r in protocol["cores"]
        ]
        != [(4286, 30602, 252), (4372, 25351, 98), (20034, 11601, 160)]
        or [(r["name"], r["native_taxon_id"]) for r in protocol["panel"]]
        != [("Betula", 29), ("Poaceae", 417)]
        or model["protocol_sha256"] != SOURCE_SHA256["protocol.json"]
        or model["source_projection_sha256"] != SOURCE_SHA256["source-projection.json"]
        or model["new252physical_and_independent_scalar_qualification_pending"]
        is not True
        or model["empirical_accuracy_or_untouched_claim"] is not False
        or model["training_dependency_families"] != 1
        or model["same_context_all_methods"] != [1486, 1436]
    ):
        raise ValueError("Norwegian original scientific scope differs")
    populations = {
        "4286": {"accepted": 55, "refused": 1},
        "4372": {"accepted": 30, "refused": 2},
        "20034": {"accepted": 72, "refused": 0},
    }
    if model["core_sample_populations"] != populations:
        raise ValueError("Norwegian source population differs")
    predictions, outcomes, scores = (
        values[n]
        for n in ("prediction-ledger.json", "outcome-ledger.json", "score-ledger.json")
    )
    training = protocol["expected_training_windows"]
    paired = protocol["expected_paired_windows"]
    methods = protocol["methods"]
    if methods != [
        "physical_inverse_forward",
        "count_pooled_pollen",
        "equal_source_pollen_mean",
    ]:
        raise ValueError("Norwegian comparison method axes differ")
    if (
        len(training) != 20
        or len(paired) != 18
        or [r["window_index"] for r in predictions] != training
        or [r["window_index"] for r in outcomes] != training
        or len(scores) != 60
        or len({(r["window_index"], r["method"]) for r in scores}) != 60
        or {(r["window_index"], r["method"]) for r in scores}
        != {(i, m) for i in training for m in methods}
        or model["physical_prediction_windows"] != 20
        or model["paired_scoring_windows"] != 18
        or model["all_method_vectors"] != 60
        or model["scored_method_rows"] != 54
        or model["missing_target_method_rows"] != 6
        or model["prediction_ledger_written_before_current_scoring"] is not True
        or model["prediction_ledger_frozen_sha256"]
        != SOURCE_SHA256["prediction-ledger.json"]
    ):
        raise ValueError("Norwegian prediction/scoring population or freeze differs")
    outcome_by_window = {r["window_index"]: r for r in outcomes}
    for row in predictions:
        if row["forward_predictive_uncertainty_emitted"] is not False or set(
            row["predictions"]
        ) != set(methods):
            raise ValueError("Norwegian prediction scope or axes differ")
        for vector in row["predictions"].values():
            if (
                len(vector) != 2
                or any(
                    type(v) not in (int, float) or not math.isfinite(v) or v < 0
                    for v in vector
                )
                or abs(sum(vector) - 1) > 1e-12
            ):
                raise ValueError("Norwegian panel prediction simplex differs")
    for row in scores:
        index = row["window_index"]
        if row["prediction_ledger_sha256"] != SOURCE_SHA256["prediction-ledger.json"]:
            raise ValueError("Norwegian score uses another prediction ledger")
        if index in paired:
            counts = outcome_by_window[index]["target_counts"]
            if (
                any(type(n) is not int or n < 0 for n in counts)
                or row["status"] != "scored"
                or row["target_panel_N"] != sum(counts)
            ):
                raise ValueError("Norwegian score denominator differs")
        elif (
            row["status"] != "no_scored_outcome"
            or row["target_panel_N"] is not None
            or outcome_by_window[index]["target_counts"] is not None
        ):
            raise ValueError("Norwegian absent target outcome was invented")
    if sum(sum(outcome_by_window[i]["target_counts"]) for i in paired) != 17935:
        raise ValueError("Norwegian unique target count denominator differs")
    if len(model["paired_contrasts"]) != 36 or {
        (r["window_index"], r["baseline"]) for r in model["paired_contrasts"]
    } != {(i, m) for i in paired for m in methods[1:]}:
        raise ValueError("Norwegian negative contrast population differs")
    if [r["method"] for r in model["summaries"]] != methods or any(
        r["paired_windows"] != 18 or r["target_panel_N"] != 17935
        for r in model["summaries"]
    ):
        raise ValueError("Norwegian summary denominators differ")
    scalar = values["independent-scalar-review.json"]
    if (
        scalar["status"] != "PASS_SCOPED_CONDITIONAL_SCALAR_MATH"
        or scalar["Decimal_precision"] != 50
        or scalar["actual_scalar_cell_comparisons"] != 632
    ):
        raise ValueError("Norwegian independent scalar population differs")
    for key, name in (
        ("source_model_report_sha256", "model-report.json"),
        ("source_predictions_sha256", "prediction-ledger.json"),
        ("source_scores_sha256", "score-ledger.json"),
        ("source_protocol_sha256", "protocol.json"),
    ):
        if scalar[key] != SOURCE_SHA256[name]:
            raise ValueError("Norwegian scalar source authority differs")
    physical = values["independent-physical-review.json"]
    tuples = values["new-physical-tuples.json"]
    if (
        physical["status"] != "PASS_SCOPED_NEW252_PHYSICAL_TUPLES"
        or physical["actual_new_tuples"] != 2
        or physical["actual_window_taxon_uses"] != 40
        or physical["source_tuple_ledger_sha256"]
        != SOURCE_SHA256["new-physical-tuples.json"]
        or len(physical["results"]) != 2
    ):
        raise ValueError("Norwegian own physical qualification differs")
    for result, parameters in zip(physical["results"], tuples, strict=True):
        if (
            result["parameters"] != parameters
            or parameters["receiver_radius_m"] != 252
            or parameters["inner_radius_m"] != 252
            or parameters["uses"] != training
            or result["absolute_difference"]
            > 2e-8 + 2e-8 * abs(result["independent_factor"])
        ):
            raise ValueError("Norwegian new physical tuple uses or agreement differ")
    guards = values["source-guards.json"]
    stages = values["stages.json"]
    consumer = values["consumer-result.json"]
    if (
        guards["actual_controls"] != 15
        or len(guards["checks"]) != 15
        or len(stages) != 3
        or any(
            type(s["native_exit_code"]) is not int or s["native_exit_code"] != 0
            for s in stages
        )
        or consumer["stages"] != stages
        or consumer["two_independent_training_groups_claim"] is not False
        or consumer["untouched_or_vegetation_accuracy_claim"] is not False
    ):
        raise ValueError("Norwegian source/control stages are unsettled")
    for radius in (98, 160):
        for row in model["responses"][str(radius)]:
            if (
                row["review_sha256"]
                != SOURCE_SHA256[f"prior-{radius}m-physical-review.json"]
                or row["terminal_sha256"]
                != SOURCE_SHA256[f"prior-{radius}m-physical-terminal.json"]
            ):
                raise ValueError("Norwegian previous geometry reuse authority differs")

    review = values["independent-output-review.json"]
    if (
        review["accepted_for_scoped_retention"] is not True
        or review["terminal_sha256"] != SOURCE_SHA256["native-terminal.json"]
        or review["plan_sha256"] != SOURCE_SHA256["study-plan.json"]
        or review["native_model_qualification_pending_flag_preserved"] is not True
        or review["actual_method_vectors"] != 60
        or review["unique_paired_target_panel_N"] != 17935
        or review["summaries"] != model["summaries"]
    ):
        raise ValueError("Norwegian independent retained-output review differs")
    for key, original in (
        ("native/report.json", "model-report.json"),
        ("native/prediction-ledger.json", "prediction-ledger.json"),
        ("comparison/independent-scalar-review.json", "independent-scalar-review.json"),
        (
            "comparison/independent-252m-physical-review.json",
            "independent-physical-review.json",
        ),
    ):
        if review["authenticated_outputs"][key]["sha256"] != SOURCE_SHA256[original]:
            raise ValueError("Norwegian independent review source binding differs")


def load_inputs(repository: Path, source_root: Path) -> dict[str, Any]:
    descriptor = safe_source_file(
        repository, DESCRIPTOR.as_posix(), "Norwegian descriptor"
    )
    capture = safe_source_file(repository, CAPTURE.as_posix(), "Norwegian capture")
    if (
        hashlib.sha256(descriptor.read_bytes()).hexdigest() != DESCRIPTOR_SHA256
        or hashlib.sha256(capture.read_bytes()).hexdigest() != CAPTURE_SHA256
    ):
        raise ValueError("Norwegian descriptor or capture changed")
    control = read_json(capture.read_bytes())
    if (
        control["source_id"] != SOURCE_ID
        or control["source_files_sha256"] != SOURCE_SHA256
        or control["private_raw_rows_promoted"] is not False
        or control["original_model_pending_flag_preserved"] is not True
        or control["numerical_reexecution_by_retained_writer"] is not False
        or control["rights_or_external_review_admitted"] is not False
    ):
        raise ValueError("Norwegian capture membership or scope differs")
    qualified = validated_author_snapshot(repository, source_root, DESCRIPTOR)
    values: dict[str, Any] = {}
    for name, expected in SOURCE_SHA256.items():
        body = safe_source_file(
            qualified.directory, name, "Norwegian private source"
        ).read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError("Norwegian retained source changed")
        if name.endswith(".json"):
            values[name] = read_json(body)
    validate(values)
    return values
