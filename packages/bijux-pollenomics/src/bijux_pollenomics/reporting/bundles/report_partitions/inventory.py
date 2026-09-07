"""Fail-closed file inventory and partition-tree assembly."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import shutil

from .artifacts import scientific_artifact_inventory
from .models import PublishedReportPartitionPlan


def relative_file_inventory(root: Path) -> tuple[str, ...]:
    """Return the sorted POSIX file inventory below one partition root."""
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"Report partition root is missing: {root}")
    _reject_symlinks(root, label="Report partition")
    return tuple(
        path.relative_to(root).as_posix()
        for path in sorted(path for path in root.rglob("*") if path.is_file())
    )


def assemble_fragment_files(
    output_root: Path,
    *,
    plan: PublishedReportPartitionPlan,
    partition_roots: Mapping[str, Path],
) -> None:
    """Copy one exact non-overlapping inventory from every planned fragment."""
    expected_ids = set(plan.partition_ids)
    actual_ids = set(partition_roots)
    if actual_ids != expected_ids:
        missing = sorted(expected_ids - actual_ids)
        extra = sorted(actual_ids - expected_ids)
        raise ValueError(
            f"Report partition inventory differs from plan: missing={missing}, extra={extra}"
        )

    owners: dict[str, str] = {}
    inventories: dict[str, tuple[str, ...]] = {}
    for partition in plan.partitions:
        root = Path(partition_roots[partition.identity])
        inventory = relative_file_inventory(root)
        if not inventory:
            raise ValueError(f"Report partition is empty: {partition.identity}")
        _validate_partition_paths(partition.identity, inventory, plan=plan)
        inventories[partition.identity] = inventory
        for relative_path in inventory:
            previous_owner = owners.get(relative_path)
            if previous_owner is not None:
                raise ValueError(
                    "Report partition output overlaps: "
                    f"{relative_path} ({previous_owner}, {partition.identity})"
                )
            owners[relative_path] = partition.identity

    output_root = Path(output_root)
    for partition in plan.partitions:
        source_root = Path(partition_roots[partition.identity])
        for relative_path in inventories[partition.identity]:
            source = source_root / relative_path
            destination = output_root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)


def _validate_partition_paths(
    partition_id: str,
    relative_paths: tuple[str, ...],
    *,
    plan: PublishedReportPartitionPlan,
) -> None:
    partition = next(item for item in plan.partitions if item.identity == partition_id)
    if partition.kind == "foundation":
        expected = {
            *scientific_artifact_inventory().values(),
            "animal_output_audit.json",
            "animal_output_audit.md",
        }
        if set(relative_paths) != expected:
            missing = sorted(expected - set(relative_paths))
            extra = sorted(set(relative_paths) - expected)
            raise ValueError(
                "Foundation partition inventory differs from contract: "
                f"missing={missing}, extra={extra}"
            )
        return

    scope_lookup = {scope.key: scope for scope in plan.geography.all_scopes()}
    prefixes = tuple(
        Path(*scope_lookup[key].output_dir_parts).as_posix() + "/"
        for key in partition.scope_keys
    )
    missing_prefixes = [
        prefix
        for prefix in prefixes
        if not any(path.startswith(prefix) for path in relative_paths)
    ]
    unexpected = [
        path
        for path in relative_paths
        if not any(path.startswith(prefix) for prefix in prefixes)
    ]
    if missing_prefixes or unexpected:
        raise ValueError(
            f"Report partition paths differ from plan: {partition_id}; "
            f"missing_scopes={missing_prefixes}, unexpected={unexpected}"
        )


def copy_scope_inputs(
    output_root: Path,
    *,
    scope_input_root: Path,
    plan: PublishedReportPartitionPlan,
) -> None:
    """Copy every planned scope directory into a foundation work tree."""
    output_root = Path(output_root)
    scope_input_root = Path(scope_input_root)
    for scope in plan.geography.all_scopes():
        relative_dir = Path(*scope.output_dir_parts)
        source = scope_input_root / relative_dir
        if source.is_symlink() or not source.is_dir():
            raise ValueError(f"Foundation scope input is missing: {relative_dir}")
        _reject_symlinks(source, label="Foundation scope input")
        shutil.copytree(source, output_root / relative_dir)


def remove_scope_inputs(
    output_root: Path, *, plan: PublishedReportPartitionPlan
) -> None:
    """Remove dependency-only scope trees from a foundation fragment."""
    top_level_dirs = {
        scope.output_dir_parts[0] for scope in plan.geography.all_scopes()
    }
    for name in sorted(top_level_dirs):
        path = Path(output_root) / name
        if path.is_dir():
            shutil.rmtree(path)


def _reject_symlinks(root: Path, *, label: str) -> None:
    symlinks = sorted(path for path in root.rglob("*") if path.is_symlink())
    if symlinks:
        relative_path = symlinks[0].relative_to(root).as_posix()
        raise ValueError(f"{label} contains a symbolic link: {relative_path}")
