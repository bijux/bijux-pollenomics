"""Retain exact normalized lake sources while preserving the governing refusal."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import ReportOwnershipError, _regular_confined_file
from ...retained_source import validate_capsule

CAPTURE: Any = "data/surface-reference/svar-normalized-source-capture/capture.json"
CAPTURE_SHA256: Any = "5c071b9ac12cf04b5d3d1c256fc85cf75b546392faa923afec2d68815b2e461e"
OWNER: Any = "source-relations/svar/normalized-export/report-products"
REPORT: Any = "docs/report/source-relations/svar/normalized-export/report.json"
ORIGINAL_CANDIDATE: Any = "ada0128d4b96a0c0655e7b8c24ba81329f34a2cb"
EXPECTED_MEMBERS: Any = {
    "execution/plan.json": {
        "sha256": "2990df0def41de045883192fc08390cde4f2da38208b97b8c70076b01feb0acd",
        "bytes": 1435457,
    },
    "execution/terminal.json": {
        "sha256": "0c4509afdc2aca9ebd8a65e726a3def7202358199d88fee12652ac0c1d04e8ec",
        "bytes": 7390,
    },
    "execution/svar-replay-terminal.json": {
        "sha256": "fb80fe6c14ae833e313c7046268df1ec821970e7a434706750787ec299bfdc4f",
        "bytes": 1592,
    },
    "execution/independent-source-review.json": {
        "sha256": "a9d12d46b9d754feef73c79bc71bdf9282819571f861a88ff1bd5752c6bbef17",
        "bytes": 89010,
    },
    "execution/source-runtime-observation.json": {
        "sha256": "a1c925570c313c28b6335e12152e0bcaf82e4f60391ddb4e6acef4fa1d897348",
        "bytes": 93863,
    },
    "execution/stage-progress.json": {
        "sha256": "554e931e61dfefe05c564e181738c4be0378154e243660a6f1ea57b008977e58",
        "bytes": 2316,
    },
    "execution/maintained-svar-normalized-source.stdout": {
        "sha256": "9309f8f54826ba206c27d3eb753a77264eb6f8f715c3432a14da67a37d02a30e",
        "bytes": 589,
    },
    "execution/maintained-svar-normalized-source.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/independent-svar-source-refusal-observer.stdout": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/independent-svar-source-refusal-observer.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "publication/report.json": {
        "sha256": "ab082b7899ce947b7bef8c0f8c58fc030aed79b54ee14edf50c81bf5e18f9baf",
        "bytes": 2047,
    },
    "source-code/artifacts/science/svar-source-final-census/check_contracts.py": {
        "sha256": "d4672fa8eabd49a25c3709d4a181988d14f1eac5e5a2ed2bafd48a3fb1118f71",
        "bytes": 4695,
    },
    "source-code/artifacts/science/svar-source-final-census/common_runner.py": {
        "sha256": "9062395231bd7a4ec19bfe41df1587281c06e143b146119fe445a6eb0ce7ce8a",
        "bytes": 6924,
    },
    "source-code/artifacts/science/svar-source-final-census/contracts.py": {
        "sha256": "d1993f6910c8dbbb19f9581998ed1658b6272f05ce389d1254e7abbd75425b82",
        "bytes": 5135,
    },
    "source-code/artifacts/science/svar-source-final-census/declared-inputs.json": {
        "sha256": "22c279e3935d8ebc77d38140e83ba6e089e189f00c795d31d03821cb9d254f34",
        "bytes": 2267,
    },
    "source-code/artifacts/science/svar-source-final-census/execute_source.py": {
        "sha256": "39d29b0796af42118b5adb8601eece582eb6368febd220001dff2cb141189166",
        "bytes": 3027,
    },
    "source-code/artifacts/science/svar-source-final-census/independent-source-review.json": {
        "sha256": "28473882eebe39972b3536e9a4ffa7d9c89d63e9176bc6e788d5975046a989e9",
        "bytes": 2255,
    },
    "source-code/artifacts/science/svar-source-final-census/observe.py": {
        "sha256": "d3645d7a5e12b9efef8b801eaebfe8b7e1b96d8844ff4b0fc2476a52d4a0e3c8",
        "bytes": 5094,
    },
    "source-code/artifacts/science/svar-source-final-census/preflight/final-style.log": {
        "sha256": "63cf07208296b7d4c933dad0e9dfa9e3e201bec2a151898fdf6991e5ff245988",
        "bytes": 67,
    },
    "source-code/artifacts/science/svar-source-final-census/preflight/guards.log": {
        "sha256": "dc7e9d1f824ca5c6481617fb4ef9c3123f3c24ef7628fdb622ca3ae983bfee3f",
        "bytes": 103,
    },
    "source-code/artifacts/science/svar-source-final-census/preflight/strict.log": {
        "sha256": "050c52a2b0c61e8b681ef5c485e0bc03340b8d55148e0acef27d744c8be42033",
        "bytes": 43,
    },
    "source-code/artifacts/science/svar-source-final-census/prepare.py": {
        "sha256": "435bfb5e8be5784e3319d4c51abd8815bab9368814f7341fa401127814134c14",
        "bytes": 6867,
    },
    "source-code/artifacts/science/svar-source-final-census/prepared-source-manifest.json": {
        "sha256": "c3fb17c77a15c3d2b082f2d75a79897f35e4be86b67f3a406c621a08465d1402",
        "bytes": 4020,
    },
    "source-code/artifacts/science/svar-source-final-census/protocol.json": {
        "sha256": "135beab7b22dc68a769c6a48253ad16cfb5c8f41fbd6fa57417016f510f3650e",
        "bytes": 2956,
    },
    "source-code/artifacts/science/svar-source-final-census/run.py": {
        "sha256": "b87356b8abcb1d2d88ae32f8a3d58fea072e5963d895949fc3a172a02d45e9c5",
        "bytes": 7115,
    },
    "source-code/artifacts/science/svar-source-final-census/runtime.py": {
        "sha256": "403f378400b8236aecc001406aa2e7837eef20b0b3202c13e661ebe3e4d0de98",
        "bytes": 17236,
    },
    "source-code/artifacts/science/svar-source-final-census/source-correction.diff": {
        "sha256": "8e8470e1725e81eefd21559e8e424621631db6377fed598b5597d9af4433ff38",
        "bytes": 9825,
    },
    "source-code/artifacts/science/svar-source-final-census/source-qualification.json": {
        "sha256": "c1f5ef63dd0ebfe1948d24136c39bd8da369b266cfa479f799514a07bd5b4ba7",
        "bytes": 5446,
    },
    "source-code/configs/ci/report-ownership.json": {
        "sha256": "400e96c0ae50769f75f4007d3ca0f151cf5119e4cdc30af58d769589cf5c88e3",
        "bytes": 9617332,
    },
    "source-code/docs/report/source-relations/svar/normalized-export/verify.py": {
        "sha256": "74b0ae6c32e187020f5d37753ebda29b9d8b88b75dbfeeedd203dc763d34b7d3",
        "bytes": 4517,
    },
}
INPUT_SCOPE_COUNTS: Any = {
    "runtime_identity_only": 3481,
    "private_source_identity_only": 3,
    "retained_execution_source": 19,
    "existing_public_relation_reference": 3,
    "retained_produced_product": 1,
}
EXPECTED_SCOPE: Any = {
    "new_native_retention_execution_claimed": False,
    "raw_private_sources_redistributed": False,
    "original_WFS_export_link_recovered": False,
    "new_GeoJSON_feature_census": False,
    "source_population_reconciled": False,
    "ranking_admitted": False,
    "new_rights_or_qualified_review": False,
    "runtime_payloads_redistributed": False,
}


def _require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError("SVAR normalized source custody: " + reason)


def _exact(left: object, right: object) -> None:
    _require(type(left) is type(right), "metadata type differs")
    if isinstance(left, dict) and isinstance(right, dict):
        _require(left.keys() == right.keys(), "metadata fields differ")
        for key in left:
            _exact(left[key], right[key])
    elif isinstance(left, list) and isinstance(right, list):
        _require(len(left) == len(right), "metadata list membership differs")
        for a, b in zip(left, right, strict=True):
            _exact(a, b)
    else:
        _require(left == right, "metadata value differs")


def _object(value: object) -> dict[str, Any]:
    _require(
        isinstance(value, dict) and all(isinstance(k, str) for k in value),
        "JSON object required",
    )
    assert isinstance(value, dict)
    return value


def _file(root: Path, name: str) -> Path:
    try:
        return _regular_confined_file(root, name, "SVAR normalized source custody")
    except (ReportOwnershipError, OSError) as error:
        raise ReportRebuildError("SVAR member missing, linked or unconfined") from error


def _json(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in items:
            _require(key not in value, "duplicate JSON key")
            value[key] = item
        return value

    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=pairs)
        json.dumps(value, allow_nan=False)
        return _object(value)
    except (OSError, ValueError) as error:
        raise ReportRebuildError("SVAR JSON is invalid") from error


def validate_report(report: dict[str, Any]) -> None:
    """Metadata counts and source hashes never confer governing registry authority."""
    for key, value in {
        "schema_version": "svar-normalized-export-custody.v1",
        "export_generated_on": "2026-09-08",
        "export_lake_count_claim": 40565,
        "review_source_lake_count_claim": 40523,
        "review_subset_feature_count": 99,
        "current_ranked_candidate_count": 0,
        "source_population_reconciled": False,
        "raw_wfs_capture_bound_to_export": False,
        "qualified_review_accepted": False,
        "ranking_admitted": False,
    }.items():
        _exact(report[key], value)
    _exact(len(report["inputs"]), 6)
    _exact(
        report["export_lake_count_claim"] - report["review_source_lake_count_claim"], 42
    )


def validate_native_records(
    plan: dict[str, Any],
    common: dict[str, Any],
    outer: dict[str, Any],
    review: dict[str, Any],
    runtime: dict[str, Any],
) -> None:
    """Bind completed original source processes separately from authored retention."""
    digest = EXPECTED_MEMBERS["execution/plan.json"]["sha256"]
    for row in (plan, common, outer, review, runtime):
        _exact(row["candidate"], ORIGINAL_CANDIDATE)
    for row in (common, outer):
        _exact(row["plan_sha256"], digest)
        _exact(row["actual_exit"], 0)
    for row in (review, runtime):
        _exact(row["plan"]["sha256"], digest)
    _exact(common["canonical_before"], plan["canonical_identity"])
    _exact(common["canonical_after"], plan["canonical_identity"])
    _exact(common["before_pin_mismatches"], [])
    _exact(common["after_pin_mismatches"], [])
    _exact(common["absent_input_paths_unchanged"], True)
    _exact(len(plan["input_pins"]), 3507)
    _exact(len({row["path"] for row in plan["input_pins"]}), 3507)
    _exact(plan["declared_owner"]["owner_id"], OWNER)
    _exact(plan["declared_owner"]["role"], "unresolved")
    _exact(
        plan["maintained_source"]["sha256"],
        EXPECTED_MEMBERS[
            "source-code/docs/report/source-relations/svar/normalized-export/verify.py"
        ]["sha256"],
    )
    _exact(
        [row["id"] for row in plan["stages"]],
        [
            "maintained-svar-normalized-source",
            "independent-svar-source-refusal-observer",
        ],
    )
    _exact(len(common["stages"]), 2)
    for wanted, actual in zip(plan["stages"], common["stages"], strict=True):
        for key in ("id", "argv"):
            _exact(actual[key], wanted[key])
        _exact(actual["actual_exit"], 0)
        _exact(actual["timed_out"], False)
    _exact(outer["common_actual_exit"], 0)
    _exact(outer["actual_native_stage_exits"], [0, 0])
    _exact(outer["tracked_byte_checker_exit"], 0)
    _exact(outer["outer_timed_out"], False)
    for key in (
        "memory_bound_pass",
        "storage_bound_pass",
        "framework_membership_unchanged",
        "absent_paths_unchanged",
        "completed_whole_wall_bound_pass",
    ):
        _exact(outer[key], True)
    _exact(
        outer["common_terminal"]["sha256"],
        EXPECTED_MEMBERS["execution/terminal.json"]["sha256"],
    )
    _exact(
        outer["independent_review"]["sha256"],
        EXPECTED_MEMBERS["execution/independent-source-review.json"]["sha256"],
    )
    for key, value in [
        ("actual_exit", 0),
        ("tracked_byte_checker_exit", 0),
        ("complete_typed_report_and_bytes_exact", True),
        ("independently_authenticated_input_members", 6),
        ("source_population_difference", 42),
        ("source_lake_count_is_metadata_claim_not_new_GeoJSON_feature_census", True),
        ("ranking_admitted", False),
    ]:
        _exact(review[key], value)
    _exact(
        review["generated"]["sha256"],
        EXPECTED_MEMBERS["publication/report.json"]["sha256"],
    )
    _exact(review["canonical"], plan["historical_report"])
    _exact(
        review["source_runtime"]["sha256"],
        EXPECTED_MEMBERS["execution/source-runtime-observation.json"]["sha256"],
    )
    _exact(runtime["source"], plan["maintained_source"])
    _exact(runtime["executed_source_argv"], plan["maintained_source_argv"])
    _exact(runtime["interpreter_flags"], ["-I", "-S", "-B"])
    _exact(runtime["source_exit"], 0)
    _exact(runtime["metadata_exit"], 0)
    _exact(runtime["metadata_error"], None)
    _require(
        type(runtime["before"]["pid"]) is int and runtime["before"]["pid"] > 0,
        "Actual source PID required",
    )
    _exact(runtime["before"]["pid"], runtime["after"]["pid"])
    _exact(plan["runtime_profile"]["profile"], "isolated-base-standard-library")
    _exact(plan["runtime_profile"]["site_initialization_disabled"], True)
    _exact(plan["runtime_profile"]["scientific_installed_runtime"], False)
    pins = {row["path"] for row in plan["input_pins"]}
    for snapshot in [
        runtime["before"],
        runtime["after"],
        review["observer_before"],
        review["observer_after"],
    ]:
        for origin in snapshot["namespace"]:
            _require(
                origin["file"] is None or origin["file"] in pins,
                "Unpinned actual Python origin",
            )
        for image in snapshot["native_images"]:
            _require(
                image in pins
                or image.startswith(
                    (
                        "/usr/lib/",
                        "/System/Library/",
                        "/System/Volumes/Preboot/Cryptexes/OS/usr/lib/",
                        "/System/Volumes/Preboot/Cryptexes/OS/System/Library/",
                    )
                ),
                "Unpinned actual native image",
            )


DETACHED_SOURCE_MEMBERS = frozenset(
    [
        "source-code/artifacts/science/svar-source-final-census/check_contracts.py",
        "source-code/artifacts/science/svar-source-final-census/common_runner.py",
        "source-code/artifacts/science/svar-source-final-census/contracts.py",
        "source-code/artifacts/science/svar-source-final-census/execute_source.py",
        "source-code/artifacts/science/svar-source-final-census/observe.py",
        "source-code/artifacts/science/svar-source-final-census/prepare.py",
        "source-code/artifacts/science/svar-source-final-census/run.py",
        "source-code/artifacts/science/svar-source-final-census/runtime.py",
        "source-code/artifacts/science/svar-source-final-census/source-correction.diff",
        "source-code/configs/ci/report-ownership.json",
        "source-code/docs/report/source-relations/svar/normalized-export/verify.py",
    ]
)


def _validate_source_members(repository: Path, prefix: str) -> None:
    """Validate original identities once and detach only exact maintained source."""
    detached = validate_capsule(repository, prefix, EXPECTED_MEMBERS)
    _exact(sorted(detached), sorted(DETACHED_SOURCE_MEMBERS))


def validated_svar_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit one reproduced source/refusal receipt without restoring a lake ranking."""
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    if not selected and not (repository / CAPTURE).exists():
        return (), {}
    _require(len(selected) == 1, "One exact source owner required")
    owner = selected[0]
    for key, value in [
        ("role", "retained_source"),
        ("paths", [REPORT]),
        ("producer_paths", []),
        ("producer_inputs", []),
    ]:
        _exact(owner[key], value)
    path = _file(repository, CAPTURE)
    _exact(hashlib.sha256(path.read_bytes()).hexdigest(), CAPTURE_SHA256)
    packet = _json(path)
    for key, value in [
        ("schema_version", "svar-normalized-source-capture.v1"),
        ("owner_id", OWNER),
        ("publication_paths", [REPORT]),
        ("original_execution_candidate", ORIGINAL_CANDIDATE),
        ("original_native_stage_exits", [0, 0]),
        ("original_tracked_byte_checker_exit", 0),
        ("original_input_count", 3507),
        ("member_count", 30),
        ("members", EXPECTED_MEMBERS),
        ("input_scope_counts", INPUT_SCOPE_COUNTS),
        ("scope", EXPECTED_SCOPE),
    ]:
        _exact(packet[key], value)
    prefix = path.parent.relative_to(repository).as_posix()
    _validate_source_members(repository, prefix)
    records = [
        _json(_file(repository, prefix + "/execution/" + name))
        for name in [
            "plan.json",
            "terminal.json",
            "svar-replay-terminal.json",
            "independent-source-review.json",
            "source-runtime-observation.json",
        ]
    ]
    plan, common, outer, review, runtime = records
    validate_native_records(plan, common, outer, review, runtime)
    _exact(
        [row["original"] for row in packet["original_input_custody"]],
        plan["input_pins"],
    )
    scopes: dict[str, int] = {}
    for row in packet["original_input_custody"]:
        scopes[row["scope"]] = scopes.get(row["scope"], 0) + 1
        if row["member"] is not None:
            _exact(
                EXPECTED_MEMBERS[row["member"]],
                {key: row["original"][key] for key in ("sha256", "bytes")},
            )
        elif row["scope"] == "existing_public_relation_reference":
            relative = (
                Path(row["original"]["path"])
                .relative_to(Path(plan["repository"]))
                .as_posix()
            )
            member = _file(repository, relative)
            _exact(
                {
                    "sha256": hashlib.sha256(member.read_bytes()).hexdigest(),
                    "bytes": member.stat().st_size,
                },
                {key: row["original"][key] for key in ("sha256", "bytes")},
            )
        else:
            _require(
                row["scope"]
                in {"runtime_identity_only", "private_source_identity_only"},
                "Undeclared source omission",
            )
            if row["scope"] == "runtime_identity_only":
                _require(
                    not Path(row["original"]["path"]).is_relative_to(
                        Path(plan["repository"])
                    ),
                    "First-party source cannot be omitted as runtime",
                )
    _exact(scopes, INPUT_SCOPE_COUNTS)
    publication = _file(repository, REPORT)
    retained = _file(repository, prefix + "/publication/report.json")
    _exact(publication.read_bytes(), retained.read_bytes())
    wanted = EXPECTED_MEMBERS["publication/report.json"]
    _exact(hashlib.sha256(publication.read_bytes()).hexdigest(), wanted["sha256"])
    validate_report(_json(publication))
    entry = tracked_by_path.get(REPORT)
    _require(entry is not None, "Tracked source receipt required")
    assert entry is not None
    for observed_field, expected_field in [
        (entry.path, REPORT.removeprefix("docs/report/")),
        (entry.kind, "file"),
        (entry.sha256, wanted["sha256"]),
        (entry.size, wanted["bytes"]),
    ]:
        _exact(observed_field, expected_field)
    return (entry,), {
        "owner_id": OWNER,
        "capture_sha256": CAPTURE_SHA256,
        "original_execution_candidate": ORIGINAL_CANDIDATE,
        "original_native_stages": [0, 0],
        "tracked_byte_checker_exit": 0,
        "paths": [entry.path],
        "scope": dict(EXPECTED_SCOPE),
    }
