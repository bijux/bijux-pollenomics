"""Authenticate exact private captures and their original source populations."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
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


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value = {}
    for key, child in pairs:
        if key in value:
            raise ValueError("duplicate correspondence source key")
        value[key] = child
    return value


def _constant(value: str) -> None:
    raise ValueError("nonfinite correspondence JSON constant: " + value)


def read_json(body: bytes) -> Any:
    """Decode retained JSON while rejecting duplicate keys and nonfinite values."""
    value = json.loads(body, object_pairs_hook=_pairs, parse_constant=_constant)

    def finite(child: object) -> None:
        if isinstance(child, float) and not math.isfinite(child):
            raise ValueError("nonfinite correspondence JSON number")
        if isinstance(child, dict):
            for descendant in child.values():
                finite(descendant)
        if isinstance(child, list):
            for descendant in child:
                finite(descendant)

    finite(value)
    return value


def validate(values: dict[str, Any]) -> None:
    """Validate capture semantics without rerunning the original numeric study."""
    receipt = values["native-terminal.json"]
    if (
        type(receipt["native_exit_code"]) is not int
        or receipt["native_exit_code"] != 0
        or receipt["status"] not in {"PASS", "PASS_PENDING_SOURCE_CAPTURE_ADMISSION"}
        or not receipt["custody_after_checked"]
        or not receipt["custody_after_unchanged"]
        or receipt["custody_errors"]
        or receipt["owned_survivors"]
        or receipt["resource_failure"] is not None
        or receipt["plan_sha256"] != SOURCE_SHA256["diagnostic-plan.json"]
    ):
        raise ValueError("correspondence native receipt is not admitted")
    bindings = {
        "source-closure-account.json": "source-account.json",
        "literal-bridge-diagnostics.json": "correspondence-diagnostics.json",
        "candidate-source-rows.json": "candidate-source-rows.json",
        "bridge-attempt-population.json": "bridge-attempt-population.json",
        "refused-source-population.json": "refused-source-population.json",
        "source-guards.json": "source-guards.json",
    }
    if set(receipt["comparison_files"]) != set(bindings):
        raise ValueError("correspondence original output population differs")
    for original, saved in bindings.items():
        if receipt["comparison_files"][original]["sha256"] != SOURCE_SHA256[saved]:
            raise ValueError("correspondence output capture authority differs")
    plan = values["diagnostic-plan.json"]
    if (
        plan["candidate"] != receipt["candidate"]
        or plan["controls_sha256"]["inspect_closure.py"]
        != SOURCE_SHA256["original-diagnostic-producer.py"]
    ):
        raise ValueError("correspondence producer authority differs")
    guards = values["source-guards.json"]
    if len(guards) != 6 or any(
        row["result"] not in {"expected_refusal", "expected_numeric_scope"}
        for row in guards
    ):
        raise ValueError("correspondence source controls are unsettled")
    account = values["source-account.json"]
    candidates = values["candidate-source-rows.json"]
    refused = values["refused-source-population.json"]
    attempts = values["bridge-attempt-population.json"]
    diagnostics = values["correspondence-diagnostics.json"]
    eligible = {row["native_sample_id"] for row in candidates}
    excluded = {row["native_sample_id"] for row in refused}
    if any(
        type(row["native_sample_id"]) is not int
        for row in candidates + refused + attempts + diagnostics
    ):
        raise ValueError("correspondence native IDs must be literal integers")
    if (
        len(candidates) != 430
        or len(eligible) != 430
        or len(refused) != len(excluded)
        or len(refused) != 950
        or eligible & excluded
        or len(eligible | excluded) != 1380
        or account["native_joined_records"] != 1380
        or account["eligible_saved_integer_source_records"] != 430
        or account["source_refusals"] != 950
        or account["curated_samples"] != 5765
        or account["curated_taxon_labels"] != 242
        or len(diagnostics) != 551
        or len(attempts) != 860
    ):
        raise ValueError("correspondence source population differs")
    hypotheses = {"literal_numeric_id", "native_id_plus_20000_unverified"}
    if {(row["native_sample_id"], row["id_bridge_hypothesis"]) for row in attempts} != {
        (sample, hypothesis) for sample in eligible for hypothesis in hypotheses
    }:
        raise ValueError("correspondence attempted population differs")
    outcomes = Counter(row["result"] for row in attempts)
    if dict(outcomes) != {
        "numeric_id_found_coordinate_equal": 214,
        "numeric_id_found_coordinate_mismatch": 337,
        "refused_curated_numeric_id_absent": 309,
    } or account["bridge_attempt_outcomes"] != dict(outcomes):
        raise ValueError("correspondence outcome denominators differ")
    for row in diagnostics:
        if (
            row["bridge_authenticated"] is not False
            or row["denominator_authenticated"] is not False
            or row["closure_pass_claim"] is not False
            or row["entity_encoding_authenticated"] is not False
            or row["zero_imputation_performed"] is not False
            or row["taxon_rule"] != "literal_labels_only_no_aliases_or_amalgamation"
            or row["denominator_hypothesis"]
            != "sum_of_all_reported_native_labels_including_unclassified_labels"
        ):
            raise ValueError("correspondence scope was upgraded")
        if type(row["curated_sample_id"]) is not int or row["curated_sample_id"] <= 0:
            raise ValueError("correspondence curated ID is not a native integer")
        gap = row["max_abs_shared_percentage_point_difference"]
        if gap is not None and (not Decimal(gap).is_finite() or Decimal(gap) < 0):
            raise ValueError("correspondence gap is not finite nonnegative")
        if row["literal_common_label_count"] != len(
            row["native_shared_integer_counts"]
        ):
            raise ValueError("correspondence shared axis population differs")
        for coordinates in (row["native_coordinates"], row["curated_coordinates"]):
            for key, bound in (("latitude", 90), ("longitude", 180)):
                number = Decimal(coordinates[key])
                if not number.is_finite() or not -bound <= number <= bound:
                    raise ValueError("correspondence coordinates are invalid")
    matching = [row for row in diagnostics if row["coordinate_numeric_agreement"]]
    shared = [
        row for row in matching if row["literal_shared_values_within_display_quantum"]
    ]
    full = [
        row for row in matching if row["entire_literal_vector_within_display_quantum"]
    ]
    if (
        len(matching) != 214
        or any(row["id_bridge_hypothesis"] != "literal_numeric_id" for row in matching)
        or len(shared) != 112
        or {row["native_sample_id"] for row in full} != {53, 3862}
        or len(full) != 2
        or any(row["entire_literal_vector_exact_rational_equal"] for row in full)
        or not {row["native_sample_id"] for row in full}
        <= {row["native_sample_id"] for row in shared}
    ):
        raise ValueError("correspondence conditional support differs")
    if any(
        account[key] != expected
        for key, expected in (
            ("coordinate_equal_literal_shared_value_correspondences", 112),
            ("coordinate_equal_entire_literal_vector_correspondences", 2),
            ("coordinate_equal_exact_rational_entire_vector_correspondences", 0),
            ("authenticated_native_curated_bridges", 0),
            ("authenticated_denominator_or_amalgamation_closures", 0),
        )
    ):
        raise ValueError("correspondence numerical account scope differs")
    review = values["independent-source-review.json"]
    if (
        review["source_bindings"]["terminal"] != SOURCE_SHA256["native-terminal.json"]
        or review["source_bindings"]["actual_diagnostics"]
        != SOURCE_SHA256["correspondence-diagnostics.json"]
        or review["source_bindings"]["full_vector_source_capsule"]
        != SOURCE_SHA256["full-vector-source-account.json"]
        or review["acceptance"]["historical_crosswalk_or_general_mapping_admitted"]
        is not False
        or review["acceptance"]["conditional_numerical_correspondences_accepted"]
        is not True
        or review["acceptance"]["rights_or_externalqualified_review_admitted"]
        is not False
    ):
        raise ValueError("correspondence independent review scope differs")
    full_sources = values["full-vector-source-account.json"]
    if len(full_sources) != 2 or {row["native_sample_id"] for row in full_sources} != {
        53,
        3862,
    }:
        raise ValueError("correspondence full-vector source population differs")
    full_by_id = {row["native_sample_id"]: row for row in full}
    for row in full_sources:
        diagnostic = full_by_id[row["native_sample_id"]]
        if row["diagnostic"] != diagnostic:
            raise ValueError("correspondence full-vector source association differs")
        original_labels = {
            item["taxon_clean"] for item in row["original_native_pollen_rows"]
        }
        if (
            original_labels != set(diagnostic["native_shared_integer_counts"])
            or len(original_labels) != diagnostic["literal_common_label_count"]
        ):
            raise ValueError("correspondence full-vector source axis differs")
    original = values["original-input-identities.json"]
    for receipt_name, input_name, product_name in (
        (
            "original-native-join-terminal.json",
            "native-sample-joins.json",
            "native-sample-joins.json",
        ),
        (
            "original-curated-acquisition-terminal.json",
            "curated-percentages.csv",
            "Modern_pollen_perc_emb_smpds.csv",
        ),
    ):
        native = values[receipt_name]
        if (
            native["native_exit_code"] != 0
            or not native["custody_after_unchanged"]
            or native["owned_survivors"]
            or native["resource_failure"] is not None
        ):
            raise ValueError("correspondence original source custody differs")
        if (
            native["product_files"][product_name]["sha256"]
            != original[input_name]["sha256"]
        ):
            raise ValueError("correspondence original input identity differs")
    access = values["supplement-access-account.json"]
    access_receipt = values["supplement-access-terminal.json"]
    if (
        access["http_status"] != 403
        or access["request_count"] != 1
        or access["redirects_followed"] != 0
        or access["source_document_admitted"] is not False
        or not access["received_body_complete"]
        or access_receipt["native_exit_code"] != 1
        or not access_receipt["custody_after_unchanged"]
        or access_receipt["owned_survivors"]
        or access_receipt["native_files"]["acquisition-account.json"]["sha256"]
        != SOURCE_SHA256["supplement-access-account.json"]
        or access_receipt["native_files"]["publisher-response.bin"]["sha256"]
        != access["retained_body_sha256"]
    ):
        raise ValueError("correspondence supplement refusal authority differs")
    if values["raw-relations-summary.json"]["all_recorded_taxa"] != 1184:
        raise ValueError("correspondence raw taxonomy scope differs")


def load_inputs(repository: Path, source_root: Path) -> dict[str, Any]:
    """Use the maintained author-snapshot qualifier with independently pinned specs."""
    descriptor = safe_source_file(
        repository, DESCRIPTOR.as_posix(), "correspondence descriptor"
    )
    capture = safe_source_file(repository, CAPTURE.as_posix(), "correspondence capture")
    if (
        hashlib.sha256(descriptor.read_bytes()).hexdigest() != DESCRIPTOR_SHA256
        or hashlib.sha256(capture.read_bytes()).hexdigest() != CAPTURE_SHA256
    ):
        raise ValueError("correspondence descriptor or capture changed")
    control = read_json(capture.read_bytes())
    if (
        control["source_id"] != SOURCE_ID
        or control["source_files_sha256"] != SOURCE_SHA256
        or control["private_raw_rows_promoted"] is not False
    ):
        raise ValueError("correspondence capture membership or privacy differs")
    qualified = validated_author_snapshot(repository, source_root, DESCRIPTOR)
    values = {}
    for name, expected in SOURCE_SHA256.items():
        body = safe_source_file(
            qualified.directory, name, "correspondence private source"
        ).read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError("correspondence captured source differs")
        if name.endswith(".json"):
            values[name] = read_json(body)
    validate(values)
    return values
