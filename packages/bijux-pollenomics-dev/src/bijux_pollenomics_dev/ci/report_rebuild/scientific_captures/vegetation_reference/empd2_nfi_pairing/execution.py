"""Validate the genuine outcome-blind source execution and scientific refusal records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ....contracts import ReportRebuildError

CAPTURE = "data/validation/empd2-nfi-pairing-source-capture/capture.json"
CAPTURE_SHA256 = "00212dc7d9438617081a51c68fd3755df1234c5c27ec59ac1d40bf31eff61bb5"
OWNER = "validation/empd2-nfi-pairing/report-products"
REPORT_ROOT = "docs/report/validation/empd2-nfi-pairing"
ORIGINAL_CANDIDATE = "97be88f37a117a518c8c4639ccca98927e13cb24"
MEMBER_COUNT = 2286
SCOPE_COUNTS = {
    "runtime_identity_only": 59856,
    "private_input_identity_only": 4,
    "existing_public_metadata_identity_only": 34,
    "declared_execution_control": 92,
    "public_first_party_source_resource": 2159,
    "first_party_bytecode_identity_only": 4356,
}
RECEIPTS = {
    "plan.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-empd2-nfi-observed-refusal-replay/plan.json",
        "sha256": "0b5a59b1096f8416386a525cd7171dc31a696d9ae9cd15956fe1e855af578629",
        "bytes": 19344531,
    },
    "terminal.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-empd2-nfi-observed-refusal-replay/terminal.json",
        "sha256": "1ba385f8f26376e4f9c7c20c1a8a0c318df3d3a1d9c9084b1256fa8ac133385e",
        "bytes": 8758,
    },
    "pairing-terminal.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-empd2-nfi-observed-refusal-replay/pairing-terminal.json",
        "sha256": "6629e66ca5d4cc69aad331fb23f0b22336e01b8c40c625675a1483dabbd024cb",
        "bytes": 5359,
    },
    "runtime-custody-terminal.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-empd2-nfi-observed-refusal-replay/runtime-custody-terminal.json",
        "sha256": "de834135c766b4c2392b0788982e3eb76b077c2303c47dc2dbd2e786445da4c3",
        "bytes": 2598,
    },
    "source-execution.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-empd2-nfi-observed-refusal-replay/source-execution.json",
        "sha256": "836ad1646a5753a9a2f2965e02fed16eae7a7759dbccf459e0827b1f6d7ec75b",
        "bytes": 416438,
    },
    "independent-pairing-review.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-empd2-nfi-observed-refusal-replay/independent-pairing-review.json",
        "sha256": "f92fce9995e9a7c4006eac1f1f5a8c69060b73e78aa23ae7b377503f661b6114",
        "bytes": 4463,
    },
}
PRODUCTS = {
    "pairs.csv": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-empd2-nfi-observed-refusal-replay/producer/pairs.csv",
        "sha256": "dead80111026ca2f0ceb8bd31c36ae3461bdbb1d89f367656d43445f65d94c40",
        "bytes": 15177,
    },
    "report.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-empd2-nfi-observed-refusal-replay/producer/report.json",
        "sha256": "cc90bccae9c54808dfea71cb4c07bb1bd12273e10eefbe889981369e34f66642",
        "bytes": 3000,
    },
}
TIMEOUT_RECEIPTS = {
    "plan.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-outcome-blind-empd2-nfi-pairing/plan.json",
        "sha256": "ce4e09d4525fe2f1a4e18d5c47404db148b036cf924176c7a2cac24215db3fd1",
        "bytes": 19334323,
    },
    "terminal.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-outcome-blind-empd2-nfi-pairing/terminal.json",
        "sha256": "51f45e6af06c4b20db4754a7fe6ce03e93f39faa8a8a769eaa15ea09479ae5a8",
        "bytes": 5671,
    },
    "pairing-terminal.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-outcome-blind-empd2-nfi-pairing/pairing-terminal.json",
        "sha256": "6b3fdd716386e33c61476c50840c308d46f50dfebb0038bd2706a02d8f8726af",
        "bytes": 3623,
    },
    "runtime-custody-terminal.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-outcome-blind-empd2-nfi-pairing/runtime-custody-terminal.json",
        "sha256": "a9a1d710e17a1be1790f183e39df664fa3cfef148d138fd86393acf5487ea345",
        "bytes": 2600,
    },
}


def _require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError(reason)


def _object(value: object) -> dict[str, Any]:
    _require(type(value) is dict, "EMPD2/NFI object required")
    assert isinstance(value, dict)
    return value


def _exact(left: Any, right: Any) -> None:
    _require(type(left) is type(right), "EMPD2/NFI value type differs")
    if isinstance(left, dict):
        _require(left.keys() == right.keys(), "EMPD2/NFI object membership differs")
        for key in left:
            _exact(left[key], right[key])
    elif isinstance(left, list):
        _require(len(left) == len(right), "EMPD2/NFI list membership differs")
        for a, b in zip(left, right, strict=True):
            _exact(a, b)
    else:
        _require(left == right, "EMPD2/NFI value differs")


def _read_json(path: Path) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            _require(key not in result, "EMPD2/NFI duplicate JSON key")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=pairs)
        json.dumps(value, allow_nan=False)
        return value
    except (OSError, ValueError) as error:
        raise ReportRebuildError("EMPD2/NFI invalid retained JSON") from error


def _json(path: Path) -> dict[str, Any]:
    return _object(_read_json(path))


def _pin(path: Path) -> dict[str, Any]:
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }


def _native_records(
    plan: dict[str, Any],
    common: dict[str, Any],
    pairing: dict[str, Any],
    runtime: dict[str, Any],
    execution: dict[str, Any],
    review: dict[str, Any],
) -> None:
    _require(
        all(
            row.get("candidate") == ORIGINAL_CANDIDATE
            for row in (plan, common, pairing, execution, review)
        )
        and runtime.get("source_candidate") == ORIGINAL_CANDIDATE,
        "EMPD2/NFI native source candidate differs",
    )
    plan_sha = RECEIPTS["plan.json"]["sha256"]
    _require(
        all(row.get("plan_sha256") == plan_sha for row in (common, pairing, runtime)),
        "EMPD2/NFI native plan differs",
    )
    for value in (
        common.get("actual_exit"),
        pairing.get("actual_exit"),
        pairing.get("common_actual_exit"),
        runtime.get("actual_exit"),
        runtime.get("delegate_actual_exit"),
        execution.get("source_exit"),
        execution.get("metadata_exit"),
        review.get("actual_exit"),
    ):
        _exact(value, 0)
    _require(
        common.get("canonical_before")
        == common.get("canonical_after")
        == plan.get("canonical_identity")
        and common.get("before_pin_mismatches")
        == common.get("after_pin_mismatches")
        == []
        and common.get("absent_input_paths_unchanged") is True,
        "EMPD2/NFI original input/candidate custody differs",
    )
    _require(
        _object(pairing.get("common_terminal")).get("sha256")
        == RECEIPTS["terminal.json"]["sha256"]
        and pairing.get("timed_out") is False
        and pairing.get("source_custody_error") is None
        and pairing.get("scientific_acceptance_claimed") is False,
        "EMPD2/NFI common/source/resource refusal differs",
    )
    _require(
        runtime.get("timed_out") is False
        and runtime.get("before_runtime_error") is None
        and runtime.get("after_runtime_error") is None
        and runtime.get("resource_bounds_met") is True,
        "EMPD2/NFI dependency runtime custody differs",
    )
    _exact(
        runtime.get("qualified_source_runtime"), plan.get("qualified_source_runtime")
    )
    intended = plan.get("stages")
    actual = common.get("stages")
    _require(
        type(intended) is list
        and type(actual) is list
        and len(intended) == len(actual) == 2,
        "EMPD2/NFI two native stages required",
    )
    assert isinstance(intended, list) and isinstance(actual, list)
    for wanted, observed in zip(intended, actual, strict=True):
        _require(
            all(observed.get(key) == value for key, value in wanted.items())
            and observed.get("timed_out") is False,
            "EMPD2/NFI native argv/timeout differs",
        )
        _exact(observed.get("actual_exit"), 0)
    _exact(pairing.get("native_stages"), actual)
    _exact(review.get("actual_producer_stage"), actual[0])
    _require(
        execution.get("metadata_error") is None, "EMPD2/NFI source telemetry failed"
    )
    _exact(
        execution.get("counters"),
        {
            "selected_NFI_cells": 263358,
            "selected_NFI_rows": 43893,
            "outcome_cell_decode_attempts": 0,
            "LRA_implementation_function_calls": 0,
        },
    )
    _require(
        all(
            _object(row.get("plan")).get("sha256") == plan_sha
            for row in (execution, review)
        ),
        "EMPD2/NFI execution/observer plan join differs",
    )
    _exact(execution.get("source"), plan.get("maintained_source"))
    _exact(
        execution.get("executed_source_argv"),
        [
            plan["maintained_source"]["path"],
            "--repository",
            plan["repository"],
            "--private-source-store",
            plan["private_source_store"],
            "--output",
            str(Path(plan["output"]) / "producer"),
        ],
    )
    _require(
        _object(review.get("source_execution")).get("sha256")
        == RECEIPTS["source-execution.json"]["sha256"],
        "EMPD2/NFI source-execution hash join differs",
    )
    _exact(
        review.get("current_private_source_identities"),
        plan.get("source_input_records"),
    )
    for field, value in {
        "all_native_NFI_metadata_rows": 43892,
        "distinct_native_NFI_tract_plot_pairs": 6018,
        "native_pollen_records_rejoined": 16,
        "complete_source_rows": 16,
        "all_source_fields_checked": 26,
        "public_fields_checked": 19,
        "private_location_fields_excluded": 8,
        "admitted_pairs": 0,
        "refusals": 16,
        "tree_outcome_cells_selected": 0,
        "retained_all_pairs_within1km_claim": 53,
        "geodesic_retained_agreement_tolerance_m": 1e-5,
        "full132_by43892_spatial_sweep_recomputed": False,
        "scientific_acceptance_claimed": False,
        "current_refusals_are_not_vegetation_validation": True,
        "no_fresh_source_rights_or_human_review_claimed": True,
    }.items():
        _exact(review.get(field), value)
    _exact(
        review.get("workbook_access"),
        {
            "selected_columns": [
                "Year",
                "TractID",
                "PlotID",
                "Inventory_Date",
                "Easting",
                "Northing",
            ],
            "selected_cells": 263358,
            "source_rows": 43892,
            "outcome_columns_decoded": 0,
            "zip_members_semantically_selected": [
                "xl/sharedStrings.xml",
                "xl/worksheets/sheet2.xml",
            ],
            "physical_XML_and_shared_string_bytes_read": True,
            "raw_outcome_bytes_unread_claimed": False,
        },
    )
    proj = _object(execution.get("PROJ"))
    _require(
        proj.get("network_enabled") is False
        and proj.get("OS_network_firewall_or_complete_mapped_image_census_claimed")
        is False
        and proj.get("same_input_R_or_LRA_estimator_called") is False,
        "EMPD2/NFI PROJ/estimator scope differs",
    )
    _require(
        proj.get("data_directory") == plan.get("PROJ_data_directory")
        and proj.get("private_user_directory") == plan.get("PROJ_user_directory"),
        "EMPD2/NFI PROJ resource context differs",
    )
    pins = {row["path"]: row for row in plan["input_pins"]}
    _exact(pins.get(_object(proj.get("proj_db")).get("path")), proj.get("proj_db"))
    for origin in proj["module_origins"]:
        _exact(
            pins.get(origin["path"]),
            {key: origin[key] for key in ("path", "sha256", "bytes")},
        )
    for item in pairing["tracked_byte_comparisons"]:
        _exact(item.get("checker_actual_exit"), 0)
        name = Path(item["path"]).name
        _require(name in PRODUCTS, "EMPD2/NFI unknown tracked product")
        _exact(item.get("generated"), PRODUCTS[name])
        _exact(
            item.get("tracked"),
            {
                **PRODUCTS[name],
                "path": str(Path(plan["repository"]) / REPORT_ROOT / name),
            },
        )
    _require(
        len(pairing["tracked_byte_comparisons"]) == 2,
        "EMPD2/NFI two public byte comparisons required",
    )


def _public_refusals(rows: list[dict[str, str]], report: dict[str, Any]) -> None:
    _exact(len(rows), 16)
    for row in rows:
        _exact(
            list(row),
            [
                "candidate_id",
                "nfi_row_identity_sha256",
                "empd2_sample",
                "empd2_source_sha256",
                "empd2_source_agebp",
                "empd2_source_age_code",
                "empd2_collection_time_status",
                "empd2_longitude_wgs84",
                "empd2_latitude_wgs84",
                "nfi_source_sha256",
                "distance_m_wgs84",
                "coordinate_comparability",
                "time_comparability",
                "measurement_comparability",
                "footprint_comparability",
                "source_identity_status",
                "missing_or_unreviewed_fields",
                "current_benchmark_decision",
                "scientific_admission",
            ],
        )
        _require(
            row["scientific_admission"] == "false"
            and row["current_benchmark_decision"] == "refused_missing_pair_evidence"
            and row["measurement_comparability"]
            == "nfi_tree_outcomes_sealed_and_pollen_target_unmapped",
            "EMPD2/NFI public refusal expanded",
        )
    _exact(report["denominators"]["measured_pairs_admitted"], 0)
    _exact(report["denominators"]["current_benchmark_refusals"], 16)
    _require(
        report["status"] == "zero_measured_pairs_refused_for_current_benchmark"
        and report["decision"]["scientific_acceptance"] == "not_evaluated"
        and report["decision"]["review_state"] == "awaiting_qualified_source_review",
        "EMPD2/NFI scientific/human scope expanded",
    )
    for field in (
        "benchmark_policy_frozen",
        "evaluation_performed",
        "local_plot_validation_supported",
        "observed_tree_vegetation_measurement_pair_admitted",
        "regional_reconstruction_validation_supported",
    ):
        _require(
            report["decision"][field] is False, "EMPD2/NFI measured evaluation admitted"
        )
    for field in (
        "nfi_outcomes_opened",
        "nfi_row_level_location_published",
        "raw_sources_copied",
    ):
        _require(
            report["source_provenance"][field] is False,
            "EMPD2/NFI private source scope expanded",
        )
