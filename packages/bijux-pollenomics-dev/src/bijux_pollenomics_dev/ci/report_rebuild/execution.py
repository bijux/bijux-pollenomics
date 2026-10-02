"""Fresh partition execution and complete-lane assembly."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry, inventory_reports
from bijux_pollenomics_dev.lra_validation.reference_replay import CERTIFICATE_SHA256

from .contracts import (
    JsonObject,
    RebuildBinding,
    ReportRebuildError,
    atomic_write_json,
    require_exact_binding,
    require_mapping,
    require_relative_path,
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
    producer_input_identity,
    require_independent_owner_inputs,
    require_inventory_matches_tree,
)
from .maintained_sources import validated_maintained_report_sources
from .original_r_reference import validated_original_r_reference
from .owner_process import run_owner_command
from .planning import (
    current_binding,
    parse_plan,
    require_current_binding,
    require_owner_plan_binding,
)
from .runtime_process import run_runtime_command

FRAGMENT_SCHEMA = "partitioned-report-fragment.v1"
ASSEMBLY_SCHEMA = "partitioned-report-assembly.v1"
OWNED_ASSEMBLY_SCHEMA = "partitioned-report-assembly.v2"
SOURCE_ASSEMBLY_SCHEMA = "partitioned-report-assembly.v3"
_LANES = frozenset({"reference", "replay"})
OWNER_SCHEMA = "partitioned-report-owner.v1"


def _require_merged_source_inputs(
    root: Path,
    expected: tuple[InventoryEntry, ...],
    policy: JsonObject,
    label: str,
) -> None:
    """Compare merged source trees by path independent of directory walk order."""
    observed = inventory_reports(root, policy)
    if tuple(sorted(observed, key=lambda entry: entry.path)) != expected:
        raise ReportRebuildError(f"{label} tree differs from its source inventories")


def build_owner_output(
    *,
    repo_root: Path,
    policy_path: Path,
    plan_path: Path,
    lane: str,
    owner_id: str,
    producer_command: tuple[str, ...],
    producer_inputs: Mapping[str, Path],
    source_paths: dict[str, str],
    evidence_root: Path,
    timeout_seconds: float = 1800,
) -> JsonObject:
    """Run one producer into a new artifact tree and bind its exact owned files."""
    if lane not in _LANES:
        raise ReportRebuildError(f"unsupported rebuild lane: {lane}")
    repo_root = repo_root.resolve()
    plan = parse_plan(plan_path)
    policy, binding = require_owner_plan_binding(
        repo_root=repo_root, policy_path=policy_path, plan=plan
    )
    identity = require_relative_path(owner_id, "owner_id")
    if identity in {
        *require_string_sequence(plan["partition_ids"], "partition_ids"),
        require_string(plan["assembly_id"], "assembly_id"),
    }:
        raise ReportRebuildError("owner identity overlaps a publisher partition")
    if not source_paths:
        raise ReportRebuildError("owner source_paths must be nonempty")
    paths = {
        require_relative_path(source, "owner source path"): require_relative_path(
            target, "owner report path"
        )
        for source, target in source_paths.items()
    }
    if len(set(paths.values())) != len(paths):
        raise ReportRebuildError("owner report paths overlap")
    if not producer_command or not any(
        "{output_root}" in arg for arg in producer_command
    ):
        raise ReportRebuildError("producer command must name {output_root}")
    require_independent_owner_inputs(
        producer_inputs,
        tuple(paths.values()),
        repo_root,
        cast(str, policy["tracked_report_root"]),
    )
    inputs_before = producer_input_identity(producer_inputs, repo_root)
    if not evidence_root.resolve().is_relative_to(repo_root / "artifacts"):
        raise ReportRebuildError("owner evidence must be below repository artifacts")
    if evidence_root.exists() or evidence_root.is_symlink():
        raise ReportRebuildError(f"owner evidence root already exists: {evidence_root}")
    evidence_root.mkdir(parents=True)
    producer_root = evidence_root / "producer-output"
    producer_root.mkdir()
    command = tuple(
        arg.replace("{output_root}", str(producer_root.resolve()))
        for arg in producer_command
    )
    run_owner_command(
        command=command,
        repo_root=repo_root,
        evidence_root=evidence_root,
        owner_id=identity,
        lane=lane,
        binding=binding.as_json(),
        producer_inputs=inputs_before,
        timeout_seconds=timeout_seconds,
    )
    generated = inventory_reports(producer_root, policy)
    if {entry.path for entry in generated} != set(paths):
        raise ReportRebuildError("owner producer output coverage is not exact")
    output_root = evidence_root / "output"
    output_root.mkdir()
    for source, target in sorted(paths.items()):
        destination = output_root / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        (producer_root / source).rename(destination)
    inventory = inventory_reports(output_root, policy)
    if producer_input_identity(producer_inputs, repo_root) != inputs_before:
        raise ReportRebuildError("owner producer input bytes changed during execution")
    _, binding_after = require_owner_plan_binding(
        repo_root=repo_root, policy_path=policy_path, plan=plan
    )
    require_exact_binding(binding_after, binding, f"{identity} post-producer")
    manifest: JsonObject = {
        "schema_version": OWNER_SCHEMA,
        "binding": binding.as_json(),
        "lane": lane,
        "owner_id": identity,
        "producer_command": list(producer_command),
        "producer_argv": list(command),
        "producer_output_root": str(producer_root.resolve()),
        "producer_inputs": inputs_before,
        "source_paths": paths,
        "inventory": inventory_json(inventory),
    }
    atomic_write_json(evidence_root / "manifest.json", manifest)
    return manifest


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
    owner_artifacts_root: Path | None = None,
    owner_ids: tuple[str, ...] = (),
    source_root: Path | None = None,
    retain_maintained_report_sources: bool = False,
    retain_original_r_reference: bool = False,
) -> JsonObject:
    """Assemble one complete report tree from exactly one copy of every partition."""
    if lane not in _LANES:
        raise ReportRebuildError(f"unsupported rebuild lane: {lane}")
    if evidence_root.exists() or evidence_root.is_symlink():
        raise ReportRebuildError(
            f"assembly evidence root already exists: {evidence_root}"
        )
    if bool(owner_ids) != (owner_artifacts_root is not None):
        raise ReportRebuildError(
            "owner identities and artifact root are required together"
        )
    if len(owner_ids) != len(set(owner_ids)):
        raise ReportRebuildError("owner identities must be unique")
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
    owner_outputs: dict[str, tuple[JsonObject, tuple[InventoryEntry, ...], Path]] = {}
    if owner_artifacts_root is not None:
        from .verification import _load_owner_outputs

        owner_outputs = _load_owner_outputs(
            artifacts_root=owner_artifacts_root,
            repo_root=repo_root,
            lane=lane,
            binding=binding,
            policy=policy,
            publisher_ids={
                *partition_ids,
                require_string(plan["assembly_id"], "assembly_id"),
            },
            source_root=source_root,
        )
        if set(owner_outputs) != set(owner_ids):
            raise ReportRebuildError("assembly owner coverage is not exact")
        fragment_input_paths = {
            entry.path
            for _, inventory, _, _ in fragments.values()
            for entry in inventory
        }
        owner_paths = [
            entry.path
            for _, inventory, _ in owner_outputs.values()
            for entry in inventory
        ]
        if len(owner_paths) != len(
            set(owner_paths)
        ) or fragment_input_paths.intersection(owner_paths):
            raise ReportRebuildError("assembly owner output overlaps another input")
    maintained, maintained_evidence = (
        validated_maintained_report_sources(
            repo_root,
            inventory_reports(
                repo_root / cast(str, policy["tracked_report_root"]), policy
            ),
            expected_repository=binding.repository,
        )
        if retain_maintained_report_sources
        else ((), {})
    )
    retained_r = (
        validated_original_r_reference(repo_root, policy)
        if retain_original_r_reference
        else ()
    )
    source_inputs: JsonObject = {
        **(
            {"maintained_report_sources": maintained_evidence}
            if retain_maintained_report_sources
            else {}
        ),
        **(
            {
                "original_r_reference": {
                    "certificate_sha256": CERTIFICATE_SHA256,
                    "inventory": inventory_json(retained_r),
                }
            }
            if retain_original_r_reference
            else {}
        ),
    }
    source_paths = [entry.path for entry in (*maintained, *retained_r)]
    if len(source_paths) != len(set(source_paths)):
        raise ReportRebuildError("checked-in source categories overlap")
    fragment_input_paths = {
        entry.path for _, inventory, _, _ in fragments.values() for entry in inventory
    }
    if fragment_input_paths.intersection(source_paths):
        raise ReportRebuildError("checked-in source overlaps publisher fragment")
    evidence_root.mkdir(parents=True)
    owner_input_root: Path | None = None
    inputs = {
        identity: (path.parent / "output", inventory)
        for identity, (_, inventory, path) in owner_outputs.items()
    }
    if maintained:
        inputs["@maintained-report-sources"] = (
            repo_root / cast(str, policy["tracked_report_root"]),
            maintained,
        )
    if retained_r:
        inputs["@original-r-reference"] = (
            repo_root / cast(str, policy["tracked_report_root"]),
            retained_r,
        )
    if inputs:
        owner_input_root = evidence_root / "owner-input"
        merge_fragment_trees(inputs, owner_input_root)
        expected_inputs = tuple(
            sorted(
                (entry for _, inventory in inputs.values() for entry in inventory),
                key=lambda entry: entry.path,
            )
        )
        _require_merged_source_inputs(
            owner_input_root, expected_inputs, policy, "assembly source inputs"
        )
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
            "owner_input_root": (
                None if owner_input_root is None else str(owner_input_root.resolve())
            ),
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
    if owner_input_root is not None:
        _require_merged_source_inputs(
            owner_input_root, expected_inputs, policy, "post-reducer source inputs"
        )
    complete = inventory_reports(output_root, policy)
    complete_by_path = {entry.path: entry for entry in complete}
    injected_paths = {
        entry.path for _, inventory in inputs.values() for entry in inventory
    }
    if set(complete_by_path) & injected_paths:
        raise ReportRebuildError("assembly retained injected source inputs")
    if retain_maintained_report_sources:
        maintained_after, evidence_after = validated_maintained_report_sources(
            repo_root,
            inventory_reports(
                repo_root / cast(str, policy["tracked_report_root"]), policy
            ),
            expected_repository=binding.repository,
        )
        if maintained_after != maintained or evidence_after != maintained_evidence:
            raise ReportRebuildError("maintained sources changed during assembly")
    if (
        retain_original_r_reference
        and validated_original_r_reference(repo_root, policy) != retained_r
    ):
        raise ReportRebuildError("retained R source changed during assembly")
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
        "schema_version": (
            SOURCE_ASSEMBLY_SCHEMA
            if source_inputs
            else OWNED_ASSEMBLY_SCHEMA
            if owner_outputs
            else ASSEMBLY_SCHEMA
        ),
        "assembly_id": require_string(plan["assembly_id"], "assembly_id"),
        "assembly_paths": assembly_paths,
        "binding": binding.as_json(),
        "fragment_manifest_sha256": fragment_digests,
        "fragment_paths": fragment_paths,
        "inventory": inventory_json(complete),
        "lane": lane,
        "partition_ids": list(partition_ids),
    }
    if owner_outputs or source_inputs:
        manifest["owner_paths"] = {
            identity: [entry.path for entry in inventory]
            for identity, (_, inventory, _) in sorted(owner_outputs.items())
        }
        manifest["owner_manifest_sha256"] = {
            identity: sha256_bytes(path.read_bytes())
            for identity, (_, _, path) in sorted(owner_outputs.items())
        }
    if source_inputs:
        manifest["source_inputs"] = source_inputs
    atomic_write_json(evidence_root / "manifest.json", manifest)
    return manifest
