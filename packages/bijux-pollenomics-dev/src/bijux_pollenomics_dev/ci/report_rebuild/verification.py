"""Final two-build and tracked-tree verification for report partitions."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from bijux_pollenomics_dev.ci.rebuild_reports import (
    InventoryEntry,
    compare_inventories,
    inventory_inputs,
    inventory_reports,
    repository_identity,
    write_rebuild_evidence,
)

from .contracts import (
    JsonObject,
    RebuildBinding,
    ReportRebuildError,
    load_json,
    parse_binding,
    require_exact_binding,
    require_mapping,
    require_string,
    require_string_sequence,
    sha256_bytes,
)
from .evidence import (
    binding_from_manifest,
    inventory_json,
    parse_inventory,
    require_inventory_matches_tree,
)
from .execution import ASSEMBLY_SCHEMA
from .planning import parse_plan, require_current_binding


def _parse_assembly_manifest(path: Path) -> JsonObject:
    manifest = load_json(path, "assembly manifest")
    expected = {
        "assembly_id",
        "assembly_paths",
        "binding",
        "fragment_manifest_sha256",
        "fragment_paths",
        "inventory",
        "lane",
        "partition_ids",
        "schema_version",
    }
    if set(manifest) != expected or manifest.get("schema_version") != ASSEMBLY_SCHEMA:
        raise ReportRebuildError("assembly manifest fields or schema are invalid")
    parse_binding(manifest["binding"], "assembly manifest binding")
    require_string(manifest["assembly_id"], "assembly manifest assembly_id")
    partition_ids = require_string_sequence(
        manifest["partition_ids"], "assembly manifest partition_ids"
    )
    assembly_paths = require_string_sequence(
        manifest["assembly_paths"], "assembly manifest assembly_paths"
    )
    fragments = require_mapping(
        manifest["fragment_paths"], "assembly manifest fragment_paths"
    )
    digests = require_mapping(
        manifest["fragment_manifest_sha256"],
        "assembly manifest fragment_manifest_sha256",
    )
    if set(fragments) != set(partition_ids) or set(digests) != set(partition_ids):
        raise ReportRebuildError("assembly fragment manifest coverage is not exact")
    claimed_paths: list[str] = list(assembly_paths)
    for partition_id in partition_ids:
        claimed_paths.extend(
            require_string_sequence(
                fragments[partition_id], f"assembly fragment paths {partition_id}"
            )
        )
        require_string(
            digests[partition_id], f"assembly fragment digest {partition_id}"
        )
    inventory = parse_inventory(manifest["inventory"], "assembly inventory")
    if sorted(claimed_paths) != sorted(entry.path for entry in inventory):
        raise ReportRebuildError(
            "assembly path ownership is overlapping or does not cover its inventory"
        )
    return manifest


def _load_complete_lane(
    *,
    lane: str,
    manifest_path: Path,
    expected_assembly_id: str,
    expected_partition_ids: tuple[str, ...],
    binding: RebuildBinding,
    policy: JsonObject,
) -> tuple[JsonObject, tuple[InventoryEntry, ...]]:
    manifest = _parse_assembly_manifest(manifest_path)
    if manifest["lane"] != lane:
        raise ReportRebuildError(f"{lane} assembly names the wrong lane")
    if manifest["assembly_id"] != expected_assembly_id:
        raise ReportRebuildError(f"{lane} assembly names the wrong reducer")
    partition_ids = require_string_sequence(
        manifest["partition_ids"], "assembly partition_ids"
    )
    if partition_ids != expected_partition_ids:
        raise ReportRebuildError(f"{lane} assembly partition coverage changed")
    require_exact_binding(
        binding_from_manifest(manifest, f"{lane} assembly"),
        binding,
        lane,
    )
    inventory = parse_inventory(manifest["inventory"], f"{lane} inventory")
    require_inventory_matches_tree(
        root=manifest_path.parent / "output",
        expected=inventory,
        policy=policy,
        label=lane,
    )
    return manifest, inventory


def verify_partitioned_rebuild(
    *,
    repo_root: Path,
    policy_path: Path,
    plan_path: Path,
    reference_manifest_path: Path,
    replay_manifest_path: Path,
    evidence_root: Path,
) -> JsonObject:
    """Verify two complete partitioned builds and the tracked report tree."""
    if evidence_root.exists() or evidence_root.is_symlink():
        raise ReportRebuildError(f"final evidence root already exists: {evidence_root}")
    repo_root = repo_root.resolve()
    plan = parse_plan(plan_path)
    policy, binding, inputs_before = require_current_binding(
        repo_root=repo_root, policy_path=policy_path, plan=plan
    )
    partition_ids = require_string_sequence(plan["partition_ids"], "partition_ids")
    assembly_id = require_string(plan["assembly_id"], "assembly_id")
    reference_manifest, reference = _load_complete_lane(
        lane="reference",
        manifest_path=reference_manifest_path,
        expected_assembly_id=assembly_id,
        expected_partition_ids=partition_ids,
        binding=binding,
        policy=policy,
    )
    replay_manifest, replay = _load_complete_lane(
        lane="replay",
        manifest_path=replay_manifest_path,
        expected_assembly_id=assembly_id,
        expected_partition_ids=partition_ids,
        binding=binding,
        policy=policy,
    )
    for field in ("assembly_paths", "fragment_paths"):
        if reference_manifest[field] != replay_manifest[field]:
            raise ReportRebuildError(
                f"reference and replay assembly ownership differ: {field}"
            )
    tracked = inventory_reports(
        repo_root / cast(str, policy["tracked_report_root"]), policy
    )
    differences: list[JsonObject] = [
        {"comparison": "reference_vs_replay", **row}
        for row in compare_inventories(reference, replay, canonical=False)
    ]
    differences.extend(
        {"comparison": "tracked_vs_reference", **row}
        for row in compare_inventories(tracked, reference, canonical=True)
    )
    if inputs_before != inventory_inputs(repo_root, policy):
        differences.append(
            {"comparison": "inputs", "path": "*", "kind": "changed_during_build"}
        )
    repository_after = repository_identity(
        repo_root, required=cast(bool, policy["require_clean_repository"])
    )
    if binding.repository != repository_after:
        differences.append(
            {
                "comparison": "repository",
                "path": "*",
                "kind": "changed_during_build",
            }
        )
    report: JsonObject = {
        "schema_version": "reproducible-report-build-evidence.v2",
        "status": "PASS" if not differences else "FAIL",
        "policy_path": policy_path.resolve().relative_to(repo_root).as_posix(),
        "policy_sha256": binding.policy_sha256,
        "repository": binding.repository,
        "inputs": inventory_json(inputs_before),
        "partition_plan": plan,
        "assemblies": {
            "reference": {
                "manifest_sha256": sha256_bytes(reference_manifest_path.read_bytes()),
                "assembly_paths": reference_manifest["assembly_paths"],
                "fragment_paths": reference_manifest["fragment_paths"],
                "fragment_manifest_sha256": reference_manifest[
                    "fragment_manifest_sha256"
                ],
            },
            "replay": {
                "manifest_sha256": sha256_bytes(replay_manifest_path.read_bytes()),
                "assembly_paths": replay_manifest["assembly_paths"],
                "fragment_paths": replay_manifest["fragment_paths"],
                "fragment_manifest_sha256": replay_manifest["fragment_manifest_sha256"],
            },
        },
        "inventories": {
            "tracked": inventory_json(tracked),
            "reference": inventory_json(reference),
            "replay": inventory_json(replay),
        },
        "differences": differences,
    }
    evidence_root.mkdir(parents=True)
    write_rebuild_evidence(evidence_root, report)
    return report
