"""Qualify an actual returned country bundle through its separate saved-product observer."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from call_evidence import ORIGINAL_PLAN_SHA, qualify_original
from contracts import require, strict_equal
from runtime_evidence import validate_observation

OWNER = "countries/sweden/land-use-replay/semantic-receipt"
REPORT = "docs/report/countries/sweden/land-use-replay/receipt.json"
READER = "docs/report/countries/sweden/land-use-replay/README.md"
CAPTURE = "data/source-custody/country-reports/sweden/capture.json"
OLD_REPORT_SHA = "f6fcc69f04872d7ef65ed3ac19f2168e2f4b27b2ed2e073730f66de905b253a0"
SAVED_SOURCE_SHA = "c182abf3987c140b7a4e5ae006f63f8c62c69b3a4d81e6898b43717f26788c79"
CATEGORIES = (
    "source_membership",
    "normalized_identity_or_value",
    "policy_or_weighting",
    "admission_or_exclusion",
    "scientific_result",
    "presentation",
)
REF_NAMES = (
    "country-plan",
    "country-inner",
    "country-outer",
    "country-progress",
    "country-clock",
    "country-callable",
    "country-products",
    "country-receipt",
    "owned-source-ledger",
    "runtime-plan",
    "runtime-common",
    "runtime-outer",
    "runtime-review",
    "saved-plan",
    "saved-inner",
    "saved-outer",
    "saved-review",
    "saved-products",
    "saved-history",
    "country-controller-manifest",
    "country-controller-review",
    "source-declaration",
    "saved-controller-manifest",
    "saved-controller-review",
    "pre-country-history",
)


def protected(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {row["path"]: row for row in rows}
    require(len(result) == len(rows), "Duplicate original input identity")
    return result


def qualify_saved(
    documents: dict[str, Any],
    identities: dict[str, dict[str, Any]],
    original_references: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Observe metadata only; this never calls a country producer or reconstructs raw data."""
    require(
        set(documents) == set(identities) == set(REF_NAMES),
        "Complete exact execution reference set required",
    )
    original = documents["country-plan"]
    plan = documents["saved-plan"]
    inner = documents["saved-inner"]
    outer = documents["saved-outer"]
    report = documents["saved-review"]
    clock = documents["country-clock"]
    returned = qualify_original(
        original,
        documents["country-inner"],
        documents["country-outer"],
        clock,
        documents["country-callable"],
        documents["country-progress"],
        original_references,
        documents["runtime-plan"],
    )
    require(
        identities["country-plan"] == original_references["plan.json"]
        and identities["country-inner"]
        == original_references["sweden-country-semantic-terminal.json"]
        and identities["country-outer"]
        == original_references["sweden-country-semantic-launch-terminal.json"]
        and identities["country-progress"] == original_references["stage-progress.json"]
        and identities["country-clock"]
        == original_references["country-clock-observation.json"]
        and identities["country-callable"]
        == original_references["country-callable-identity.json"]
        and identities["country-products"]
        == original_references["output-products.json"]
        and identities["country-receipt"]
        == original_references["producer/receipt.json"],
        "Original metadata/receipt roles replaced",
    )
    original_inputs = protected(original["input_pins"])
    saved_inputs = protected(plan["input_pins"])
    require(
        all(saved_inputs.get(path) == row for path, row in original_inputs.items())
        and saved_inputs.get(identities["country-plan"]["path"])
        == identities["country-plan"],
        "Saved observer lost original complete input roles",
    )
    require(
        identities["runtime-plan"] == original["qualified_source_runtime"]["plan"]
        and strict_equal(
            plan["qualified_source_runtime"], original["qualified_source_runtime"]
        )
        and original_inputs.get(identities["runtime-plan"]["path"])
        == identities["runtime-plan"],
        "Complete original qualified runtime authority differs",
    )
    for name, role in (
        ("runtime-common", "common"),
        ("runtime-outer", "outer"),
        ("runtime-review", "independent_review"),
    ):
        require(
            identities[name] == original["qualified_source_runtime"][role]
            and original_inputs.get(identities[name]["path"]) == identities[name],
            "Qualified runtime proof reference differs",
        )
    validate_observation(
        documents["runtime-plan"],
        documents["runtime-common"],
        documents["runtime-outer"],
        documents["runtime-review"],
        identities["runtime-plan"]["sha256"],
    )
    owner = original["source_declaration"]["original_owner"]
    require(
        owner["owner_id"] == OWNER
        and owner["role"] == "unresolved"
        and owner["paths"] == [REPORT]
        and strict_equal(
            original["source_declaration"], documents["source-declaration"]
        )
        and strict_equal(plan["source_declaration"], documents["source-declaration"]),
        "Full original owner/source criterion differs",
    )
    require(
        plan["original_registered_plan_sha256"] == ORIGINAL_PLAN_SHA
        and plan["original_country_execution_candidate"] == original["candidate"]
        and plan["original_owned_source_candidate"]
        == original["original_owned_source_candidate"]
        and plan["original_saved_country_output"] == original["output"]
        and plan["owned_repository"] == original["owned_repository"],
        "Country, owned-source and saved-observer epochs conflated",
    )
    ledger = documents["owned-source-ledger"]
    require(
        original["source_ledger"]
        == plan["source_ledger"]
        == identities["owned-source-ledger"]
        and ledger["canonical_identity"]["candidate"]
        == original["original_owned_source_candidate"],
        "Original full owned source/resource ledger replaced",
    )
    for prefix, inputs, expected_sha in (
        (
            "country",
            original_inputs,
            "32700b3d6977d648f338a1fab3265af426b702224967d21ff753c9ba5c8eec98",
        ),
        ("saved", saved_inputs, SAVED_SOURCE_SHA),
    ):
        manifest = documents[prefix + "-controller-manifest"]
        approval = documents[prefix + "-controller-review"]
        manifest_pin = identities[prefix + "-controller-manifest"]
        approval_pin = identities[prefix + "-controller-review"]
        require(
            manifest_pin["sha256"] == expected_sha
            and manifest["source_only"] is True
            and approval["approved"] is True
            and approval["source_manifest_sha256"] == expected_sha
            and inputs.get(manifest_pin["path"]) == manifest_pin
            and inputs.get(approval_pin["path"]) == approval_pin
            and all(inputs.get(row["path"]) == row for row in manifest["files"]),
            "Exact executed controller/independent approval missing from native inputs",
        )
    expected_resources = {
        "overall_timeout_seconds": 600,
        "outer_timeout_seconds": 660,
        "declared_memory_bytes": 8 * 1024**3,
        "declared_storage_bytes": 1024**3,
    }
    require(
        strict_equal(plan["resources"], expected_resources),
        "Saved observer resource contract differs",
    )
    for value in (inner, outer, report):
        require(
            type(value["actual_exit"]) is int
            and value["actual_exit"] == 0
            and value["candidate"] == plan["candidate"],
            "Saved observation must be collected actual zero",
        )
    plan_sha = identities["saved-plan"]["sha256"]
    require(
        inner["plan_sha256"]
        == outer["plan_sha256"]
        == report["registered_plan_sha256"]
        == plan_sha
        and inner["products_manifest"] == identities["saved-products"]
        and outer["inner_terminal"] == identities["saved-inner"]
        and outer["registered_plan_unchanged"] is True
        and outer["child_timed_out"] is False
        and type(outer["child_native_exit"]) is int
        and outer["child_native_exit"] == 0,
        "Collected saved-observer registered-plan/product joins differ",
    )
    require(
        inner["exception"] is None
        and inner["after_custody_error"] is None
        and inner["completed_whole_wall_bound_pass"] is True
        and outer["completed_outer_wall_bound_pass"] is True
        and all(
            value[key] is True
            for value in (inner, outer)
            for key in ("memory_bound_pass", "inclusive_storage_bound_pass")
        ),
        "Collected saved whole custody or resource refusal",
    )
    expected_stage = {
        "id": "independent-saved-country-semantic-clock-observer",
        "action": "observer",
        "timeout_seconds": 360,
        "argv": [
            plan["qualified_source_runtime"]["lexical_python"],
            "-I",
            "-B",
            str(
                Path(identities["saved-controller-manifest"]["path"]).parent
                / "entry.py"
            ),
            "observer",
            "--plan",
            identities["saved-plan"]["path"],
        ],
    }
    require(
        strict_equal(plan["stages"], [expected_stage]) and len(inner["stages"]) == 1,
        "Only exact one saved observer may execute",
    )
    actual_stage = inner["stages"][0]
    require(
        strict_equal({key: actual_stage[key] for key in expected_stage}, expected_stage)
        and type(actual_stage["actual_exit"]) is int
        and actual_stage["actual_exit"] == 0
        and actual_stage["timed_out"] is False,
        "Actual saved observer stage differs",
    )
    require(
        type(report["original_controller_actual_exit"]) is int
        and report["original_controller_actual_exit"] == 1
        and type(report["original_whole_actual_exit"]) is int
        and report["original_whole_actual_exit"] == 1
        and report["country_call_returned_normally"] is True
        and type(report["actual_country_call_return_events"]) is int
        and report["actual_country_call_return_events"] == 1
        and report["full_captured_return_object_recovered"] is False
        and report["original_read_or_import_origin_ledger_recovered"] is False
        and report["independent_expected_projection_is_not_captured_return"] is True
        and type(report["independent_country_producer_calls"]) is int
        and report["independent_country_producer_calls"] == 0
        and report["full_source_resource_input_closure_bound"] is True
        and report["original_owner_verification"] == owner["verification"]
        and report[
            "historical_generated_ownership_or_vegetation_rights_human_LRA_admitted"
        ]
        is False,
        "Original failed history, missing telemetry or scientific scope inflated",
    )
    require(
        report["original_country_execution_candidate"] == original["candidate"]
        and report["original_owned_source_candidate"]
        == original["original_owned_source_candidate"]
        and report["original_registered_plan_sha256"] == ORIGINAL_PLAN_SHA
        and report["country_callable_identity"] == identities["country-callable"]
        and report["country_clock_observation"] == identities["country-clock"]
        and strict_equal(report["native_UTC_clock"], returned["native_UTC_clock"])
        and strict_equal(
            report["exact_absent_default_import_attempt"],
            returned["exact_absent_default_import_attempt"],
        ),
        "Saved native clock, callable and source observation joins differ",
    )
    require(
        plan["retained_failed_controller_history"]
        == report["retained_call_authority"]
        == identities["saved-history"]
        and documents["saved-history"]["country_call_returned_normally"] is True
        and saved_inputs.get(identities["saved-history"]["path"])
        == identities["saved-history"],
        "Complete failed controller/call authority differs",
    )
    saved_catalog = protected(documents["saved-products"]["files"])
    require(
        saved_catalog.get(identities["saved-review"]["path"])
        == identities["saved-review"]
        and saved_catalog.get(identities["saved-history"]["path"])
        == identities["saved-history"]
        and saved_catalog.get(identities["saved-plan"]["path"])
        == identities["saved-plan"],
        "Collected saved output catalogue lost a required exact role",
    )
    receipt = documents["country-receipt"]
    semantic = report["semantic_receipt"]
    require(
        set(receipt["semantic_changes"])
        == set(receipt["change_counts"])
        == set(CATEGORIES)
        and strict_equal(
            receipt["semantic_changes"], semantic["independently_reconstructed_changes"]
        ),
        "All six native semantic categories must be independently reconstructed",
    )
    for name in CATEGORIES:
        require(
            type(receipt["semantic_changes"][name]) is list
            and type(receipt["change_counts"][name]) is int
            and receipt["change_counts"][name]
            == len(receipt["semantic_changes"][name]),
            "Typed native semantic denominator differs",
        )
    require(
        receipt["status"] in {"changed", "identical"}
        and type(semantic["tracked_byte_checker_actual_exit"]) is int
        and semantic["tracked_byte_checker_actual_exit"] in {0, 2},
        "Separate exact byte check status differs",
    )
    native_catalog = protected(documents["country-products"]["files"])
    actual_products = report["actual_products"]
    product_root = Path(original["output"]) / "producer/candidate"
    declared = {
        row["relative_path"]
        for row in documents["source-declaration"]["published_roles"]
    }
    names = []
    for row in actual_products:
        path = Path(row["path"])
        require(
            path.is_relative_to(product_root)
            and native_catalog.get(row["path"]) == row,
            "Saved product escaped original native catalogue",
        )
        names.append(path.relative_to(product_root).as_posix())
    require(
        len(names) == len(set(names))
        and declared <= set(names)
        and all(name in declared or name.startswith("_map_assets/") for name in names),
        "Complete original country bundle and resource membership differs",
    )
    return {
        "schema_version": "sweden-saved-country-current-publication-witness.v1",
        "original_owner_row": deepcopy(owner),
        "current_receipt_sha256": identities["country-receipt"]["sha256"],
        "historical_receipt_sha256": OLD_REPORT_SHA,
        "country_execution_candidate": original["candidate"],
        "owned_source_candidate": original["original_owned_source_candidate"],
        "saved_observation_candidate": plan["candidate"],
        "saved_registered_plan_sha256": plan_sha,
        "country_call_returned_normally": True,
        "actual_country_call_return_events": 1,
        "original_controller_actual_exit": 1,
        "original_whole_actual_exit": 1,
        "saved_observer_actual_exit": 0,
        "saved_whole_actual_exit": 0,
        "missing_full_return_read_or_import_telemetry_recovered": False,
        "human_typed_record_channel": "Independent expected reconstruction from frozen ANNO, not captured in-memory return",
        "human_actual_product_channels": [
            "default sample CSV",
            "default sample GeoJSON",
            "all21 locality CSV columns",
            "summary and bundle counts/day",
        ],
        "native_UTC_clock": deepcopy(returned["native_UTC_clock"]),
        "native_semantic_status": receipt["status"],
        "native_semantic_change_counts": deepcopy(receipt["change_counts"]),
        "native_semantic_changes": deepcopy(receipt["semantic_changes"]),
        "ordered_typed_synthesis_differences": deepcopy(
            semantic["complete_ordered_typed_synthesis_differences"]
        ),
        "tracked_byte_checker_actual_exit": semantic[
            "tracked_byte_checker_actual_exit"
        ],
        "source_authority_unavailability": deepcopy(
            report["source_authority_unavailability"]
        ),
        "human_source_joins": deepcopy(report["human_source_joins"]),
        "animal_source_joins": deepcopy(report["animal_source_joins"]),
        "synthesis_source_joins": deepcopy(report["synthesis_source_joins"]),
        "vegetation_rights_human_biology_or_LRA_acceptance": False,
    }
