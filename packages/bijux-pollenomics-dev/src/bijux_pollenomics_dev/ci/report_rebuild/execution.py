"""Fresh partition execution and complete-lane assembly."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry, inventory_reports

from .contracts import (
    JsonObject,
    RebuildBinding,
    ReportRebuildError,
    atomic_write_json,
    require_exact_binding,
    require_mapping,
    require_string,
    require_string_sequence,
    sha256_bytes,
)
from .evidence import (
    binding_from_manifest,
    discover_manifests,
    inventory_json,
    merge_fragment_trees,
    parse_inventory,
    parse_partition_manifest,
    require_inventory_matches_tree,
)
from .planning import current_binding, parse_plan, require_current_binding
from .runtime_process import run_runtime_command

FRAGMENT_SCHEMA = "partitioned-report-fragment.v1"
ASSEMBLY_SCHEMA = "partitioned-report-assembly.v1"
_LANES = frozenset({"reference", "replay"})


def load_fragments(
    *,
    artifacts_root: Path,
    expected_ids: tuple[str, ...],
    lane: str,
    binding: RebuildBinding,
    policy: JsonObject,
) -> dict[str, tuple[Path, tuple[InventoryEntry, ...], JsonObject, Path]]:
    """Load one exact, content-bound set of partition artifacts."""
    fragments: dict[str, tuple[Path, tuple[InventoryEntry, ...], JsonObject, Path]] = {}
    for manifest_path in discover_manifests(artifacts_root, FRAGMENT_SCHEMA):
        manifest = parse_partition_manifest(manifest_path)
        if manifest["lane"] != lane:
            raise ReportRebuildError(
                f"partition manifest names the wrong lane: {manifest_path}"
            )
        partition_id = cast(str, manifest["partition_id"])
        if partition_id in fragments:
            raise ReportRebuildError(f"duplicate partition manifest: {partition_id}")
        require_exact_binding(
            binding_from_manifest(manifest, "partition manifest"),
            binding,
            partition_id,
        )
        inventory = parse_inventory(manifest["inventory"], "partition inventory")
        output_root = manifest_path.parent / "output"
        require_inventory_matches_tree(
            root=output_root,
            expected=inventory,
            policy=policy,
            label=partition_id,
        )
        fragments[partition_id] = (output_root, inventory, manifest, manifest_path)
    if set(fragments) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(fragments))
        extra = sorted(set(fragments) - set(expected_ids))
        raise ReportRebuildError(
            f"partition manifest coverage is not exact; missing={missing}, extra={extra}"
        )
    return fragments


def build_partition(
    *,
    repo_root: Path,
    policy_path: Path,
    plan_path: Path,
    lane: str,
    partition_id: str,
    evidence_root: Path,
    scope_artifacts_root: Path | None = None,
) -> JsonObject:
    """Build one fresh partition and emit content-bound fragment evidence."""
    if lane not in _LANES:
        raise ReportRebuildError(f"unsupported rebuild lane: {lane}")
    repo_root = repo_root.resolve()
    plan = parse_plan(plan_path)
    policy, binding, _ = require_current_binding(
        repo_root=repo_root, policy_path=policy_path, plan=plan
    )
    partition_ids = require_string_sequence(plan["partition_ids"], "partition_ids")
    if partition_id not in partition_ids:
        raise ReportRebuildError(f"partition is not in the bound plan: {partition_id}")
    parameters = require_mapping(plan["parameters"], "plan parameters")
    if evidence_root.exists() or evidence_root.is_symlink():
        raise ReportRebuildError(
            f"partition evidence root already exists: {evidence_root}"
        )
    evidence_root.mkdir(parents=True)
    scope_input_root: Path | None = None
    if partition_id == "foundation":
        if scope_artifacts_root is None:
            raise ReportRebuildError("foundation requires scope partition artifacts")
        scope_ids = require_string_sequence(
            plan["scope_partition_ids"], "scope_partition_ids"
        )
        fragments = load_fragments(
            artifacts_root=scope_artifacts_root,
            expected_ids=scope_ids,
            lane=lane,
            binding=binding,
            policy=policy,
        )
        scope_input_root = evidence_root / "scope-input"
        merge_fragment_trees(
            {identity: (row[0], row[1]) for identity, row in fragments.items()},
            scope_input_root,
        )
    elif scope_artifacts_root is not None:
        raise ReportRebuildError("scope artifacts are only valid for foundation")
    output_root = evidence_root / "output"
    countries = require_string_sequence(parameters["countries"], "plan countries")
    result = run_runtime_command(
        {
            "schema_version": "published-report-partition-command.v1",
            "operation": "generate",
            "partition_id": partition_id,
            "version_dir": str(
                repo_root / "data/aadr" / cast(str, parameters["version"])
            ),
            "countries": list(countries),
            "output_root": str(output_root.resolve()),
            "published_output_root": cast(str, parameters["published_output_root"]),
            "title": cast(str, parameters["title"]),
            "slug": cast(str, parameters["slug"]),
            "context_root": str((repo_root / "data").resolve()),
            "scope_input_root": (
                None if scope_input_root is None else str(scope_input_root.resolve())
            ),
            "country_group_size": cast(int, parameters["country_group_size"]),
        }
    )
    if set(result) != {"partition_id", "relative_paths"}:
        raise ReportRebuildError("runtime partition result fields are not exact")
    if require_string(result["partition_id"], "runtime partition_id") != partition_id:
        raise ReportRebuildError("runtime partition result identity does not match")
    inventory = inventory_reports(output_root, policy)
    paths = tuple(entry.path for entry in inventory)
    result_paths = require_string_sequence(
        result["relative_paths"], "runtime relative_paths"
    )
    if (
        not paths
        or len(result_paths) != len(set(result_paths))
        or set(result_paths) != set(paths)
    ):
        raise ReportRebuildError(
            "runtime partition result does not match the materialized output inventory"
        )
    binding_after, _ = current_binding(repo_root, policy_path, policy)
    require_exact_binding(binding_after, binding, f"{partition_id} post-build")
    manifest: JsonObject = {
        "schema_version": FRAGMENT_SCHEMA,
        "binding": binding.as_json(),
        "lane": lane,
        "partition_id": partition_id,
        "relative_paths": list(paths),
        "inventory": inventory_json(inventory),
    }
    atomic_write_json(evidence_root / "manifest.json", manifest)
    return manifest


def assemble_partition_lane(
    *,
    repo_root: Path,
    policy_path: Path,
    plan_path: Path,
    lane: str,
    partition_artifacts_root: Path,
    evidence_root: Path,
) -> JsonObject:
    """Assemble one complete report tree from exactly one copy of every partition."""
    if lane not in _LANES:
        raise ReportRebuildError(f"unsupported rebuild lane: {lane}")
    if evidence_root.exists() or evidence_root.is_symlink():
        raise ReportRebuildError(
            f"assembly evidence root already exists: {evidence_root}"
        )
    repo_root = repo_root.resolve()
    plan = parse_plan(plan_path)
    policy, binding, _ = require_current_binding(
        repo_root=repo_root, policy_path=policy_path, plan=plan
    )
    partition_ids = require_string_sequence(plan["partition_ids"], "partition_ids")
    fragments = load_fragments(
        artifacts_root=partition_artifacts_root,
        expected_ids=partition_ids,
        lane=lane,
        binding=binding,
        policy=policy,
    )
    evidence_root.mkdir(parents=True)
    output_root = evidence_root / "output"
    parameters = require_mapping(plan["parameters"], "plan parameters")
    result = run_runtime_command(
        {
            "schema_version": "published-report-partition-command.v1",
            "operation": "assemble",
            "version_dir": str(
                repo_root / "data/aadr" / cast(str, parameters["version"])
            ),
            "countries": list(
                require_string_sequence(parameters["countries"], "plan countries")
            ),
            "output_root": str(output_root.resolve()),
            "partition_roots": {
                identity: str(row[0].resolve()) for identity, row in fragments.items()
            },
            "published_output_root": cast(str, parameters["published_output_root"]),
            "title": cast(str, parameters["title"]),
            "slug": cast(str, parameters["slug"]),
            "context_root": str((repo_root / "data").resolve()),
            "country_group_size": cast(int, parameters["country_group_size"]),
        }
    )
    if set(result) != {"output_root"}:
        raise ReportRebuildError("runtime assembly result fields are not exact")
    if Path(require_string(result["output_root"], "runtime output_root")) != (
        output_root.resolve()
    ):
        raise ReportRebuildError("runtime assembly result output root does not match")
    complete = inventory_reports(output_root, policy)
    complete_by_path = {entry.path: entry for entry in complete}
    owners: dict[str, str] = {}
    fragment_paths: dict[str, object] = {}
    fragment_digests: dict[str, object] = {}
    for partition_id in partition_ids:
        _, inventory, _, manifest_path = fragments[partition_id]
        fragment_paths[partition_id] = [entry.path for entry in inventory]
        fragment_digests[partition_id] = sha256_bytes(manifest_path.read_bytes())
        for entry in inventory:
            prior = owners.setdefault(entry.path, partition_id)
            if prior != partition_id:
                raise ReportRebuildError(
                    f"partition output overlap for {entry.path}: {prior}, {partition_id}"
                )
            if complete_by_path.get(entry.path) != entry:
                raise ReportRebuildError(
                    f"assembled output changed or omitted {partition_id} path: {entry.path}"
                )
    assembly_paths = sorted(set(complete_by_path) - set(owners))
    if not assembly_paths:
        raise ReportRebuildError(
            "assembly did not materialize any reducer-owned outputs"
        )
    binding_after, _ = current_binding(repo_root, policy_path, policy)
    require_exact_binding(binding_after, binding, f"{lane} post-assembly")
    manifest: JsonObject = {
        "schema_version": ASSEMBLY_SCHEMA,
        "assembly_id": require_string(plan["assembly_id"], "assembly_id"),
        "assembly_paths": assembly_paths,
        "binding": binding.as_json(),
        "fragment_manifest_sha256": fragment_digests,
        "fragment_paths": fragment_paths,
        "inventory": inventory_json(complete),
        "lane": lane,
        "partition_ids": list(partition_ids),
    }
    atomic_write_json(evidence_root / "manifest.json", manifest)
    return manifest
