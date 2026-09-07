"""Evidence parsing and file-coverage checks for report rebuild partitions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
import shutil

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry, inventory_reports

from .contracts import (
    JsonObject,
    RebuildBinding,
    ReportRebuildError,
    load_json,
    parse_binding,
    require_mapping,
    require_string,
    require_string_sequence,
)


def parse_inventory(value: object, label: str) -> tuple[InventoryEntry, ...]:
    """Parse and validate an ordered report inventory."""
    if not isinstance(value, list):
        raise ReportRebuildError(f"{label} must be a list")
    entries: list[InventoryEntry] = []
    for index, raw_entry in enumerate(value):
        entry = require_mapping(raw_entry, f"{label}[{index}]")
        if set(entry) != {"canonical_sha256", "kind", "path", "sha256", "size"}:
            raise ReportRebuildError(f"{label}[{index}] fields are not exact")
        path = require_string(entry["path"], f"{label}[{index}].path")
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise ReportRebuildError(f"{label}[{index}].path is unsafe")
        if entry["kind"] != "file":
            raise ReportRebuildError(f"{label}[{index}] is not a regular file")
        if type(entry["size"]) is not int or int(entry["size"]) < 0:
            raise ReportRebuildError(f"{label}[{index}].size is invalid")
        entries.append(
            InventoryEntry(
                path=path,
                kind="file",
                size=int(entry["size"]),
                sha256=require_string(entry["sha256"], f"{label}[{index}].sha256"),
                canonical_sha256=require_string(
                    entry["canonical_sha256"],
                    f"{label}[{index}].canonical_sha256",
                ),
            )
        )
    paths = [entry.path for entry in entries]
    if len(paths) != len(set(paths)):
        raise ReportRebuildError(f"{label} paths must be unique")
    return tuple(entries)


def inventory_json(entries: Sequence[InventoryEntry]) -> list[JsonObject]:
    """Serialize an inventory for a manifest."""
    return [entry.as_json() for entry in entries]


def discover_manifests(root: Path, schema_version: str) -> tuple[Path, ...]:
    """Require every downloaded manifest to use the expected fragment schema."""
    paths: list[Path] = []
    for path in sorted(root.rglob("manifest.json")):
        record = load_json(path, "partition manifest candidate")
        if record.get("schema_version") != schema_version:
            raise ReportRebuildError(
                f"unexpected manifest schema in partition artifact root: {path}"
            )
        paths.append(path)
    return tuple(paths)


def parse_partition_manifest(path: Path) -> JsonObject:
    """Load one exact partition manifest and validate its inventory."""
    record = load_json(path, "partition manifest")
    expected = {
        "binding",
        "inventory",
        "lane",
        "partition_id",
        "relative_paths",
        "schema_version",
    }
    if set(record) != expected or record.get("schema_version") != (
        "partitioned-report-fragment.v1"
    ):
        raise ReportRebuildError("partition manifest fields or schema are invalid")
    parse_binding(record["binding"], "partition manifest binding")
    require_string(record["lane"], "partition manifest lane")
    require_string(record["partition_id"], "partition manifest partition_id")
    paths = require_string_sequence(
        record["relative_paths"], "partition manifest relative_paths"
    )
    inventory = parse_inventory(record["inventory"], "partition manifest inventory")
    if paths != tuple(entry.path for entry in inventory):
        raise ReportRebuildError("partition relative_paths do not match its inventory")
    return record


def require_inventory_matches_tree(
    *, root: Path, expected: Sequence[InventoryEntry], policy: JsonObject, label: str
) -> tuple[InventoryEntry, ...]:
    """Require a downloaded output tree to match its manifest byte-for-byte."""
    observed = inventory_reports(root, policy)
    if tuple(expected) != observed:
        raise ReportRebuildError(f"{label} output tree does not match its manifest")
    return observed


def merge_fragment_trees(
    fragments: Mapping[str, tuple[Path, Sequence[InventoryEntry]]], destination: Path
) -> dict[str, str]:
    """Copy disjoint fragment trees and return path ownership."""
    if destination.exists() or destination.is_symlink():
        raise ReportRebuildError(
            f"fragment merge destination already exists: {destination}"
        )
    destination.mkdir(parents=True)
    owners: dict[str, str] = {}
    for partition_id in sorted(fragments):
        root, inventory = fragments[partition_id]
        for entry in inventory:
            prior = owners.setdefault(entry.path, partition_id)
            if prior != partition_id:
                raise ReportRebuildError(
                    f"partition output overlap for {entry.path}: {prior}, {partition_id}"
                )
            source = root / entry.path
            target = destination / entry.path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    return owners


def binding_from_manifest(record: Mapping[str, object], label: str) -> RebuildBinding:
    """Parse the binding member of a manifest."""
    return parse_binding(record.get("binding"), f"{label} binding")
