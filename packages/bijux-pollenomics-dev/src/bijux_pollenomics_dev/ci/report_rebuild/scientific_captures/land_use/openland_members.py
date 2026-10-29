"""Retain source-bound OpenLand member evidence without claiming acquisition or reuse rights."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import ReportOwnershipError, _regular_confined_file

CAPTURE: Any = "data/surface-reference/openland-member-source-capture/capture.json"
CAPTURE_SHA256: Any = "43d2ddca92c24ea37204c4f584ec5382db2af9c968fdbf0e8bdc64f69da57106"
CAPTURE_BYTES: Any = 509119
MEMBER_COUNT: Any = 2209
MEMBERS_SHA256: Any = "658d4236f0f35d9db12278b2fb3e209eda083f907d5b1859d3325c004f6aba07"
ORIGINAL_CANDIDATE: Any = "5c120dcb67d31b50d9da6d7bf5efb41dcb0ddf87"
OWNER: Any = "source-relations/openland-intake/report-products"
PUBLICATIONS: Any = [
    "docs/report/source-relations/openland-intake/doi-lineage.json",
    "docs/report/source-relations/openland-intake/members.csv",
    "docs/report/source-relations/openland-intake/report.json",
    "docs/report/source-relations/openland-intake/upstream-tree.json",
]
INPUT_SCOPE_COUNTS: Any = {
    "runtime_identity_only": 59886,
    "private_archive_or_intake_identity_only": 3,
    "retained_original_execution_source": 2181,
    "retained_historical_publication_input": 4,
    "bytecode_identity_only": 4356,
}
PUBLICATION_ROLES: Any = {
    "members.csv": "maintained_native_produced",
    "report.json": "maintained_native_produced",
    "upstream-tree.json": "retained_declared_input_copy_not_new_acquisition",
    "doi-lineage.json": "retained_declared_input_copy_not_new_acquisition",
}
EXPECTED_SCOPE: Any = {
    "new_native_retention_execution_claimed": False,
    "private_archive_intakes_or_dependency_runtime_redistributed": False,
    "two_declared_metadata_input_copies_are_new_HTTP_or_original_acquisition": False,
    "public_member_rights_map_export_or_independent_vegetation_admitted": False,
    "PANGAEA_row_overlap_interpolation_LRA_or_human_acceptance": False,
    "CSV_scientific_values_or_rights_changed": False,
    "whole_current_source_tree_equated_with_original_capture": False,
    "bytecode_payloads_published_or_equated_with_source_or_fresh_compilation": False,
}


def _require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError("OpenLand member source custody: " + reason)


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
        return _regular_confined_file(root, name, "OpenLand member source custody")
    except (ReportOwnershipError, OSError) as error:
        raise ReportRebuildError(
            "OpenLand member missing, linked or unconfined"
        ) from error


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
        raise ReportRebuildError("OpenLand JSON is invalid") from error


def _same(left: object, right: object) -> bool:
    _exact(left, right)
    return True


def validate_report_correspondence(
    previous: dict[str, Any], current: dict[str, Any], bridge: dict[str, Any]
) -> None:
    """Allow the sole reviewed source-attribution digest, preserving all scientific fields."""
    path = bridge["path"]
    _exact(
        path,
        "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/open_land/authority.py",
    )
    _exact(previous["inputs"][path], bridge["recorded"]["sha256"])
    _exact(current["inputs"][path], bridge["current"]["sha256"])
    expected = {
        **previous,
        "inputs": {**previous["inputs"], path: bridge["current"]["sha256"]},
    }
    _exact(current, expected)
    for key, value in [
        ("schema_version", "openland-member-intake.v1"),
        ("public_member_admissions", 0),
        ("independent_vegetation_benchmarks", 0),
        ("modeled_source_member_count", 25),
        ("exact_pinned_upstream_members", 26),
        ("member_content_sha256_count", 27),
        ("status", "source_identified_private_review_only"),
    ]:
        _exact(current[key], value)
    for key in (
        "mixed_archive_redistribution_authorized",
        "public_map_or_export_authorized",
    ):
        _exact(current["rights"][key], False)
    for key in ("raw_archive_copied",):
        _exact(current["source_archive"][key], False)
    _exact(
        current["source_archive"]["sha256"],
        "7ed602f3b480a995cd2e1ff6dc445e994442100b1f626a953185849305e2434b",
    )
    _exact(current["source_archive"]["member_count"], 51)


def validate_source_pair(
    old: bytes, current: bytes, producer: bytes, bridge: dict[str, Any]
) -> None:
    for raw, expected in ((old, bridge["recorded"]), (current, bridge["current"])):
        _exact(
            {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)},
            {key: expected[key] for key in ("sha256", "bytes")},
        )
    trees = [ast.parse(raw) for raw in (old, current)]
    values = []
    for tree in trees:
        matches = [
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "SOURCE_ATTRIBUTION"
                for target in node.targets
            )
        ]
        _exact(len(matches), 1)
        values.append(ast.literal_eval(matches[0].value))
        tree.body.remove(matches[0])
    _exact(
        values,
        [
            "Behnaz Pirzamanbein; Pirzamanbein et al. (2022), doi:10.3389/fevo.2022.795794",
            "Behnaz Pirzamanbein (upstream data creator); Githumbi et al. (2022), doi:10.3389/fevo.2022.795794",
        ],
    )
    _exact(
        ast.dump(trees[0], include_attributes=False),
        ast.dump(trees[1], include_attributes=False),
    )
    _require(
        not any(
            isinstance(node, ast.ImportFrom)
            and any(alias.name == "SOURCE_ATTRIBUTION" for alias in node.names)
            for node in ast.walk(ast.parse(producer))
        ),
        "Attribution binding became a numerical input",
    )


def validate_native_records(
    plan: dict[str, Any],
    common: dict[str, Any],
    inner: dict[str, Any],
    outer: dict[str, Any],
    review: dict[str, Any],
    execution: dict[str, Any],
) -> None:
    """Keep native0, CSV checker0 and original report checker2 as separate literal facts."""
    checksum = "e060b579fdc3d30106b7b96df7a909e6e01ba9535e66192dadec1a4867da1f1d"
    for record in (plan, common, inner, review, execution):
        _exact(record["candidate"], ORIGINAL_CANDIDATE)
    _exact(outer["source_candidate"], ORIGINAL_CANDIDATE)
    for record in (common, inner, outer):
        _exact(record["actual_exit"], 0)
        _exact(record["plan_sha256"], checksum)
    for record in (review, execution):
        _exact(record["actual_exit"] if record is review else record["source_exit"], 0)
        _exact(record["plan"]["sha256"], checksum)
    _exact(common["canonical_before"], plan["canonical_identity"])
    _exact(common["canonical_after"], plan["canonical_identity"])
    _exact(common["before_pin_mismatches"], [])
    _exact(common["after_pin_mismatches"], [])
    _exact(common["absent_input_paths_unchanged"], True)
    _exact(len(plan["input_pins"]), 66430)
    _exact(len({row["path"] for row in plan["input_pins"]}), 66430)
    _exact(
        [row["id"] for row in plan["stages"]],
        [
            "maintained-openland-member-source",
            "independent-openland-member-copychain-observer",
        ],
    )
    _exact(len(common["stages"]), 2)
    _exact(inner["native_stages"], common["stages"])
    for expected, actual in zip(plan["stages"], common["stages"], strict=True):
        for key in ("id", "argv", "timeout_seconds", "must_succeed"):
            _exact(actual[key], expected[key])
        _exact(actual["actual_exit"], 0)
        _exact(actual["timed_out"], False)
    _exact(inner["common_actual_exit"], 0)
    _exact(inner["timed_out"], False)
    _exact(inner["source_custody_error"], None)
    _exact(inner["scientific_acceptance_claimed"], False)
    _exact(
        [row["checker_actual_exit"] for row in inner["tracked_byte_comparisons"]],
        [0, 2],
    )
    _exact(inner["tracked_checker_changes_are_native_failure"], False)
    _exact(inner["produced_output_names"], ["members.csv", "report.json"])
    _exact(inner["retained_input_names"], ["upstream-tree.json", "doi-lineage.json"])
    _exact(outer["delegate_actual_exit"], 0)
    _exact(outer["timed_out"], False)
    _exact(outer["before_runtime_error"], None)
    _exact(outer["after_runtime_error"], None)
    _exact(outer["resource_bounds_met"], True)
    _exact(outer["qualified_source_runtime"], plan["qualified_source_runtime"])
    _exact(plan["qualified_source_runtime"]["selected_distributions"], 147)
    _exact(plan["qualified_source_runtime"]["original_bootstrap_whole_actual_exit"], 1)
    _exact(plan["qualified_source_runtime"]["production_stage_actual_exits"], [0, 0, 0])
    _exact(plan["qualified_source_runtime"]["new_observer_actual_exit"], 0)
    _exact(review["independent_source_join_science_and_allowed_metadata_exit"], 0)
    _exact(review["tracked_members_CSV_byte_checker_exit"], 0)
    _exact(review["tracked_report_byte_checker_exit"], 2)
    _exact(review["archive_entries"], 51)
    _exact(review["exact_upstream_blobs"], 26)
    _exact(review["local_GeoPackage_or_editor_payload_reads"], 0)
    _exact(review["public_member_admissions"], 0)
    _exact(review["independent_vegetation_benchmarks"], 0)
    _exact(review["new_HTTP_or_historical_tree_DOI_acquisition_claimed"], False)
    _exact(execution["source"], plan["maintained_source"])
    _exact(execution["source_exit"], 0)
    _exact(execution["metadata_exit"], 0)
    _exact(execution["metadata_error"], None)
    _exact(execution["counters"]["LRA_implementation_function_calls"], 0)
    _exact(
        sorted(execution["counters"]["member_content_reads"]),
        review["member_payload_reads"],
    )
    _exact(len(execution["counters"]["member_content_reads"]), 27)
    _exact(
        execution["retained_input_copy_chain"], review["retained_declared_input_copies"]
    )
    _exact(
        plan["source_attribution_bridge"],
        inner["allowed_source_attribution_metadata_bridge"],
    )
    _exact(plan["source_attribution_bridge"], review["source_attribution_bridge"])
    _exact(plan["owner_row"]["owner_id"], OWNER)
    _exact(plan["owner_row"]["role"], "unresolved")
    _exact(plan["owner_row"]["paths"], PUBLICATIONS)


def validated_openland_member_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit two source-produced files and two declared input copies, without acquisition claims."""
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    if not selected and not (repository / CAPTURE).exists():
        return (), {}
    _exact(len(selected), 1)
    owner = selected[0]
    for key, value in [
        ("role", "retained_source"),
        ("paths", PUBLICATIONS),
        ("producer_paths", []),
        ("producer_inputs", []),
    ]:
        _exact(owner[key], value)
    for other in owners:
        if other is not owner:
            other_paths = other.get("paths")
            _require(
                isinstance(other_paths, list)
                and not set(PUBLICATIONS).intersection(other_paths),
                "Other owner overlaps exact four outputs/input copies",
            )
    capture = _file(repository, CAPTURE)
    _exact(
        {
            "sha256": hashlib.sha256(capture.read_bytes()).hexdigest(),
            "bytes": capture.stat().st_size,
        },
        {"sha256": CAPTURE_SHA256, "bytes": CAPTURE_BYTES},
    )
    packet = _json(capture)
    for key, value in [
        ("schema_version", "openland-member-source-capture.v1"),
        ("owner_id", OWNER),
        ("original_execution_candidate", ORIGINAL_CANDIDATE),
        ("original_native_stage_exits", [0, 0]),
        ("original_whole_actual_exit", 0),
        ("original_tracked_CSV_checker_exit", 0),
        ("original_tracked_report_checker_exit", 2),
        ("independent_science_and_exact_source_attribution_bridge_exit", 0),
        ("original_input_count", 66430),
        ("member_count", MEMBER_COUNT),
        ("original_input_scope_counts", INPUT_SCOPE_COUNTS),
        ("publication_roles", PUBLICATION_ROLES),
        ("scope", EXPECTED_SCOPE),
    ]:
        _exact(packet[key], value)
    members = _object(packet["members"])
    _exact(len(members), MEMBER_COUNT)
    _exact(
        hashlib.sha256(
            json.dumps(members, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        MEMBERS_SHA256,
    )
    physical = set()
    for path in capture.parent.rglob("*"):
        _require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "Capsule contains alias/special entry",
        )
        if path.is_file():
            physical.add(path.relative_to(capture.parent).as_posix())
    _exact(physical, set(members) | {"capture.json"})
    prefix = capture.parent.relative_to(repository).as_posix()
    for name, expected in members.items():
        _require(
            type(name) is str
            and Path(name).suffix != ".pyc"
            and "__pycache__" not in Path(name).parts,
            "Bytecode payload cannot be published",
        )
        path = _file(repository, prefix + "/" + name)
        _exact(
            {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            },
            expected,
        )

    def record(name: str) -> dict[str, Any]:
        return _json(_file(repository, prefix + "/" + name))

    plan, common, inner, outer, review, execution = [
        record("execution/" + name)
        for name in (
            "plan.json",
            "terminal.json",
            "openland-member-terminal.json",
            "runtime-custody-terminal.json",
            "independent-source-review.json",
            "source-execution.json",
        )
    ]
    validate_native_records(plan, common, inner, outer, review, execution)
    for stage in common["stages"]:
        for stream in ("stdout", "stderr"):
            _exact(
                members["execution/" + Path(stage[stream]).name]["sha256"],
                stage[stream + "_sha256"],
            )
    original_runtime = record("runtime-authority/plan.json")
    runtime_names = {row["path"] for row in original_runtime["input_pins"]}
    for label, name in [
        ("plan", "plan.json"),
        ("outer", "runtime-observation-terminal.json"),
        ("common", "terminal.json"),
        ("independent_review", "independent-runtime-review.json"),
    ]:
        row = plan["qualified_source_runtime"][label]
        _exact(
            members["runtime-authority/" + name],
            {k: row[k] for k in ("sha256", "bytes")},
        )
        runtime_names.add(row["path"])
    _exact(
        original_runtime["candidate"],
        plan["qualified_source_runtime"]["observed_runtime_candidate"],
    )
    private_names = {
        plan["source_input_records"][name]["path"]
        for name in ("archive", "failed_intake", "received_intake")
    }
    catalog = json.loads(
        _file(repository, prefix + "/original-input-custody.json").read_bytes()
    )
    _exact(len(catalog), 66430)
    counts: dict[str, int] = {}
    pinned = {row["path"]: row for row in plan["input_pins"]}
    for index, (row, original) in enumerate(
        zip(catalog, plan["input_pins"], strict=True)
    ):
        _exact(set(row), {"index", "scope", "member"})
        _exact(row["index"], index)
        scope = row["scope"]
        counts[scope] = counts.get(scope, 0) + 1
        path = Path(original["path"])
        if scope == "runtime_identity_only":
            _require(
                original["path"] in runtime_names,
                "Omitted runtime pin is not original runtime authority",
            )
            _exact(row["member"], None)
        elif scope == "private_archive_or_intake_identity_only":
            _require(
                original["path"] in private_names,
                "Undeclared private identity omission",
            )
            _exact(row["member"], None)
        elif scope == "bytecode_identity_only":
            _require(
                path.is_relative_to(Path(plan["repository"]) / "packages")
                and (path.suffix == ".pyc" or "__pycache__" in path.parts),
                "Nonbytecode source omitted",
            )
            _exact(row["member"], None)
        else:
            _require(
                scope
                in {
                    "retained_original_execution_source",
                    "retained_historical_publication_input",
                },
                "Unknown original pin role",
            )
            _require(
                path.is_relative_to(Path(plan["repository"])),
                "Retained public source must be repository-confined",
            )
            _exact(
                members[row["member"]],
                {key: original[key] for key in ("sha256", "bytes")},
            )
    _exact(counts, INPUT_SCOPE_COUNTS)
    for origin in execution["first_party_origins"]:
        _exact(
            pinned[origin["path"]],
            {key: origin[key] for key in ("path", "sha256", "bytes")},
        )
    bridge = plan["source_attribution_bridge"]
    old_authority = _file(
        repository, prefix + "/historical-source/open-land-authority.py"
    ).read_bytes()
    authority = _file(
        repository, prefix + "/source-code/" + bridge["path"]
    ).read_bytes()
    producer_name = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/openland_intake.py"
    producer_bytes = _file(
        repository, prefix + "/source-code/" + producer_name
    ).read_bytes()
    validate_source_pair(old_authority, authority, producer_bytes, bridge)
    validate_report_correspondence(
        record("historical-publications/report.json"),
        record("publication/report.json"),
        bridge,
    )
    for name in (
        producer_name,
        bridge["path"],
        "data/landclim/raw/landclim_sources.json",
    ):
        current = _file(repository, name)
        _exact(
            {
                "sha256": hashlib.sha256(current.read_bytes()).hexdigest(),
                "bytes": current.stat().st_size,
            },
            members["source-code/" + name],
        )
    entries = []
    for name in PUBLICATIONS:
        public, retained = (
            _file(repository, name),
            _file(repository, prefix + "/publication/" + Path(name).name),
        )
        _exact(public.read_bytes(), retained.read_bytes())
        entry = tracked_by_path.get(name)
        _require(entry is not None, "Tracked public output/input-copy required")
        assert entry is not None
        expected = members["publication/" + Path(name).name]
        for actual, value in [
            (entry.path, name.removeprefix("docs/report/")),
            (entry.kind, "file"),
            (entry.sha256, expected["sha256"]),
            (entry.size, expected["bytes"]),
        ]:
            _exact(actual, value)
        entries.append(entry)
    return tuple(entries), {
        "owner_id": OWNER,
        "capture_sha256": CAPTURE_SHA256,
        "original_execution_candidate": ORIGINAL_CANDIDATE,
        "original_native_stages": [0, 0],
        "original_CSV_checker_exit": 0,
        "original_report_checker_exit": 2,
        "independent_source_attribution_bridge_exit": 0,
        "publication_roles": dict(PUBLICATION_ROLES),
        "bytecode_identity_only": 4356,
        "paths": [entry.path for entry in entries],
        "scope": dict(EXPECTED_SCOPE),
    }
