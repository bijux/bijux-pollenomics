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
from bijux_pollenomics_dev.lra_validation.reference_replay import CERTIFICATE_SHA256

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
    parse_owner_manifest,
    producer_input_identity,
    require_independent_owner_inputs,
    require_inventory_matches_tree,
)
from .execution import ASSEMBLY_SCHEMA, OWNED_ASSEMBLY_SCHEMA
from .original_r_reference import validated_original_r_reference
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
    schema = manifest.get("schema_version")
    if schema == OWNED_ASSEMBLY_SCHEMA:
        expected |= {"owner_paths", "owner_manifest_sha256"}
    if set(manifest) != expected or schema not in {
        ASSEMBLY_SCHEMA,
        OWNED_ASSEMBLY_SCHEMA,
    }:
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
    if schema == OWNED_ASSEMBLY_SCHEMA:
        owner_paths = require_mapping(manifest["owner_paths"], "assembly owner_paths")
        owner_digests = require_mapping(
            manifest["owner_manifest_sha256"], "assembly owner_manifest_sha256"
        )
        if not owner_paths or set(owner_paths) != set(owner_digests):
            raise ReportRebuildError("assembly owner manifest coverage is not exact")
        seen = set(claimed_paths)
        for owner_id, paths in owner_paths.items():
            require_string(owner_id, "assembly owner identity")
            require_string(owner_digests[owner_id], "assembly owner digest")
            for owner_path in require_string_sequence(
                paths, f"assembly owner paths {owner_id}"
            ):
                if owner_path in seen:
                    raise ReportRebuildError("assembly owner path ownership overlaps")
                seen.add(owner_path)
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


def _load_owner_outputs(
    *,
    artifacts_root: Path | None,
    repo_root: Path,
    lane: str,
    binding: RebuildBinding,
    policy: JsonObject,
    publisher_ids: set[str],
) -> dict[str, tuple[JsonObject, tuple[InventoryEntry, ...], Path]]:
    """Load every independent owner artifact for one lane."""
    if artifacts_root is None:
        return {}
    if (
        not artifacts_root.is_dir()
        or artifacts_root.is_symlink()
        or not artifacts_root.resolve().is_relative_to(repo_root / "artifacts")
    ):
        raise ReportRebuildError("owner artifacts must be below repository artifacts")
    owners: dict[str, tuple[JsonObject, tuple[InventoryEntry, ...], Path]] = {}
    for owner_root in sorted(artifacts_root.iterdir()):
        if owner_root.is_symlink() or not owner_root.is_dir():
            raise ReportRebuildError(f"invalid owner artifact directory: {owner_root}")
        path = owner_root / "manifest.json"
        if path.is_symlink() or not path.is_file():
            raise ReportRebuildError(f"owner manifest is missing: {owner_root}")
        manifest = parse_owner_manifest(path)
        if manifest["lane"] != lane:
            raise ReportRebuildError(f"owner manifest names the wrong lane: {path}")
        owner_id = cast(str, manifest["owner_id"])
        if owner_root.name != owner_id:
            raise ReportRebuildError(
                f"owner directory differs from identity: {owner_id}"
            )
        if owner_id in publisher_ids or owner_id in owners:
            raise ReportRebuildError(f"owner identity overlaps: {owner_id}")
        require_exact_binding(
            binding_from_manifest(manifest, "owner manifest"), binding, owner_id
        )
        inventory = parse_inventory(manifest["inventory"], "owner inventory")
        require_inventory_matches_tree(
            root=path.parent / "output",
            expected=inventory,
            policy=policy,
            label=owner_id,
        )
        _require_current_owner_inputs(manifest, repo_root, owner_id, policy)
        owners[owner_id] = (manifest, inventory, path)
    return owners


def _require_current_owner_inputs(
    manifest: JsonObject, repo_root: Path, owner_id: str, policy: JsonObject
) -> None:
    """Reject a producer receipt whose named source files changed or vanished."""
    inputs = require_mapping(manifest["producer_inputs"], "owner producer_inputs")
    paths = {
        label: Path(
            require_string(
                require_mapping(value, f"owner producer input {label}")["path"],
                f"owner producer input {label} path",
            )
        )
        for label, value in inputs.items()
    }
    require_independent_owner_inputs(
        paths,
        tuple(cast(dict[str, str], manifest["source_paths"]).values()),
        repo_root,
        cast(str, policy["tracked_report_root"]),
    )
    if producer_input_identity(paths, repo_root) != inputs:
        raise ReportRebuildError(f"owner producer inputs changed: {owner_id}")


def _merge_owned_inventories(
    publisher: tuple[InventoryEntry, ...],
    owners: dict[str, tuple[JsonObject, tuple[InventoryEntry, ...], Path]],
) -> tuple[InventoryEntry, ...]:
    """Require one owner for every file in a lane's combined inventory."""
    combined = {entry.path: entry for entry in publisher}
    for identity, (_, inventory, _) in owners.items():
        for entry in inventory:
            if entry.path in combined:
                raise ReportRebuildError(
                    f"owner output overlaps publisher or another owner: "
                    f"{identity}: {entry.path}"
                )
            combined[entry.path] = entry
    return tuple(combined[path] for path in sorted(combined))


def verify_partitioned_rebuild(
    *,
    repo_root: Path,
    policy_path: Path,
    plan_path: Path,
    reference_manifest_path: Path,
    replay_manifest_path: Path,
    evidence_root: Path,
    reference_owners_root: Path | None = None,
    replay_owners_root: Path | None = None,
    owner_ids: tuple[str, ...] = (),
    retain_original_r_reference: bool = False,
) -> JsonObject:
    """Verify two complete partitioned builds and the tracked report tree."""
    if evidence_root.exists() or evidence_root.is_symlink():
        raise ReportRebuildError(f"final evidence root already exists: {evidence_root}")
    if (reference_owners_root is None) != (replay_owners_root is None):
        raise ReportRebuildError("both owner artifact lanes are required together")
    if bool(owner_ids) != (reference_owners_root is not None):
        raise ReportRebuildError(
            "owner identities and both artifact roots are required together"
        )
    if len(owner_ids) != len(set(owner_ids)) or any(
        not identity for identity in owner_ids
    ):
        raise ReportRebuildError("owner identities must be nonempty and unique")
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
    publisher_ids = {*partition_ids, assembly_id}
    reference_owners = _load_owner_outputs(
        artifacts_root=reference_owners_root,
        repo_root=repo_root,
        lane="reference",
        binding=binding,
        policy=policy,
        publisher_ids=publisher_ids,
    )
    replay_owners = _load_owner_outputs(
        artifacts_root=replay_owners_root,
        repo_root=repo_root,
        lane="replay",
        binding=binding,
        policy=policy,
        publisher_ids=publisher_ids,
    )
    for lane, owners in (("reference", reference_owners), ("replay", replay_owners)):
        if set(owners) != set(owner_ids):
            raise ReportRebuildError(f"{lane} owner coverage is not exact")
    for lane, assembly, owners in (
        ("reference", reference_manifest, reference_owners),
        ("replay", replay_manifest, replay_owners),
    ):
        if owners:
            if assembly["schema_version"] != OWNED_ASSEMBLY_SCHEMA:
                raise ReportRebuildError(
                    f"{lane} assembly did not consume owner inputs"
                )
            claimed_paths = require_mapping(
                assembly["owner_paths"], "assembly owner_paths"
            )
            claimed_digests = require_mapping(
                assembly["owner_manifest_sha256"], "assembly owner_manifest_sha256"
            )
            if claimed_paths != {
                identity: [entry.path for entry in inventory]
                for identity, (_, inventory, _) in sorted(owners.items())
            } or claimed_digests != {
                identity: sha256_bytes(path.read_bytes())
                for identity, (_, _, path) in sorted(owners.items())
            }:
                raise ReportRebuildError(f"{lane} assembly owner inputs changed")
        elif assembly["schema_version"] != ASSEMBLY_SCHEMA:
            raise ReportRebuildError(f"{lane} assembly claims unexpected owner inputs")
    for identity in reference_owners:
        for field in ("source_paths", "producer_command", "producer_inputs"):
            if (
                reference_owners[identity][0][field]
                != replay_owners[identity][0][field]
            ):
                raise ReportRebuildError(f"owner {field} changed: {identity}")
    complete_reference = _merge_owned_inventories(reference, reference_owners)
    complete_replay = _merge_owned_inventories(replay, replay_owners)
    retained_reference = (
        validated_original_r_reference(repo_root, policy)
        if retain_original_r_reference
        else ()
    )
    generated_paths = {entry.path for entry in complete_reference}
    generated_paths.update(entry.path for entry in complete_replay)
    if generated_paths.intersection(entry.path for entry in retained_reference):
        raise ReportRebuildError("retained R reference overlaps generated output")
    complete_reference = tuple(
        sorted((*complete_reference, *retained_reference), key=lambda entry: entry.path)
    )
    complete_replay = tuple(
        sorted((*complete_replay, *retained_reference), key=lambda entry: entry.path)
    )
    tracked = inventory_reports(
        repo_root / cast(str, policy["tracked_report_root"]), policy
    )
    differences: list[JsonObject] = [
        {"comparison": "reference_vs_replay", **row}
        for row in compare_inventories(
            complete_reference, complete_replay, canonical=False
        )
    ]
    differences.extend(
        {"comparison": "tracked_vs_reference", **row}
        for row in compare_inventories(tracked, complete_reference, canonical=True)
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
    for owners in (reference_owners, replay_owners):
        for identity, (manifest, _, _) in owners.items():
            _require_current_owner_inputs(manifest, repo_root, identity, policy)
    report: JsonObject = {
        "schema_version": "reproducible-report-build-evidence.v3",
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
        "owners": {
            lane: {
                identity: {
                    "manifest_sha256": sha256_bytes(path.read_bytes()),
                    "paths": [entry.path for entry in inventory],
                    "producer_argv": manifest["producer_argv"],
                    "producer_inputs": manifest["producer_inputs"],
                }
                for identity, (manifest, inventory, path) in sorted(owners.items())
            }
            for lane, owners in (
                ("reference", reference_owners),
                ("replay", replay_owners),
            )
        },
        "retained_sources": (
            {
                "original_r_reference": {
                    "certificate_sha256": CERTIFICATE_SHA256,
                    "paths": [entry.path for entry in retained_reference],
                }
            }
            if retain_original_r_reference
            else {}
        ),
        "inventories": {
            "tracked": inventory_json(tracked),
            "reference": inventory_json(complete_reference),
            "replay": inventory_json(complete_replay),
        },
        "differences": differences,
    }
    evidence_root.mkdir(parents=True)
    write_rebuild_evidence(evidence_root, report)
    return report
