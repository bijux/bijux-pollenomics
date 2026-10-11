"""Evidence parsing and file-coverage checks for report rebuild partitions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
from pathlib import Path
import shutil
import stat
from typing import cast

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry, inventory_reports

from .contracts import (
    JsonObject,
    RebuildBinding,
    ReportRebuildError,
    load_json,
    parse_binding,
    require_mapping,
    require_relative_path,
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
        path = require_relative_path(entry["path"], f"{label}[{index}].path")
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


def producer_input_identity(inputs: Mapping[str, Path], repo_root: Path) -> JsonObject:
    """Bind each declared producer input to its path and current file bytes."""
    if not inputs:
        raise ReportRebuildError("owner producer inputs must be nonempty")
    identity: JsonObject = {}
    for label, supplied_path in sorted(inputs.items()):
        require_string(label, "owner producer input label")
        path = (
            supplied_path if supplied_path.is_absolute() else repo_root / supplied_path
        )
        try:
            if path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode):
                raise ReportRebuildError(
                    f"owner producer input is not regular: {label}"
                )
            digest = hashlib.sha256()
            size = 0
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
                    size += len(block)
        except OSError as error:
            raise ReportRebuildError(
                f"cannot read owner producer input: {label}"
            ) from error
        resolved = path.resolve()
        identity[label] = {
            "path": (
                resolved.relative_to(repo_root).as_posix()
                if resolved.is_relative_to(repo_root)
                else str(resolved)
            ),
            "sha256": digest.hexdigest(),
            "size": size,
        }
    return identity


def require_independent_owner_inputs(
    inputs: Mapping[str, Path],
    report_paths: Sequence[str],
    repo_root: Path,
    tracked_report_root: str,
) -> None:
    """A generated-output receipt cannot use its tracked result as an input."""
    targets = {
        (
            repo_root
            / tracked_report_root
            / require_relative_path(path, "owner report path")
        ).resolve()
        for path in report_paths
    }
    for label, supplied_path in inputs.items():
        source = (
            supplied_path if supplied_path.is_absolute() else repo_root / supplied_path
        )
        if source.resolve() in targets:
            raise ReportRebuildError(
                f"owner producer input is its claimed tracked output: {label}"
            )


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


def parse_owner_manifest(path: Path) -> JsonObject:
    """Load an exact manifest for one independent report producer."""
    record = load_json(path, "owner manifest")
    if (
        set(record)
        != {
            "binding",
            "inventory",
            "lane",
            "owner_id",
            "producer_command",
            "producer_argv",
            "producer_output_root",
            "producer_inputs",
            "schema_version",
            "source_paths",
        }
        or record.get("schema_version") != "partitioned-report-owner.v1"
    ):
        raise ReportRebuildError("owner manifest fields or schema are invalid")
    parse_binding(record["binding"], "owner manifest binding")
    require_string(record["lane"], "owner manifest lane")
    require_string(record["owner_id"], "owner manifest owner_id")
    for field in ("producer_command", "producer_argv"):
        command = record[field]
        if (
            not isinstance(command, list)
            or not command
            or any(
                not isinstance(argument, str) or not argument for argument in command
            )
        ):
            raise ReportRebuildError(f"owner {field} must be nonempty argv")
    output_root = Path(
        require_string(record["producer_output_root"], "owner producer_output_root")
    )
    if not output_root.is_absolute() or output_root.name != "producer-output":
        raise ReportRebuildError("owner producer_output_root is invalid")
    template = cast(list[str], record["producer_command"])
    argv = cast(list[str], record["producer_argv"])
    if not any("{output_root}" in argument for argument in template) or argv != [
        argument.replace("{output_root}", str(output_root)) for argument in template
    ]:
        raise ReportRebuildError("owner producer argv does not match its command")
    inputs = require_mapping(record["producer_inputs"], "owner producer_inputs")
    if not inputs:
        raise ReportRebuildError("owner producer_inputs must be nonempty")
    for label, raw_identity in inputs.items():
        require_string(label, "owner producer input label")
        identity = require_mapping(raw_identity, f"owner producer input {label}")
        if set(identity) != {"path", "sha256", "size"}:
            raise ReportRebuildError(
                f"owner producer input fields are invalid: {label}"
            )
        input_path = require_string(
            identity["path"], f"owner producer input {label} path"
        )
        if not Path(input_path).is_absolute():
            require_relative_path(input_path, f"owner producer input {label} path")
        digest = require_string(
            identity["sha256"], f"owner producer input {label} digest"
        )
        if len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ReportRebuildError(f"owner producer input digest is invalid: {label}")
        if type(identity["size"]) is not int or identity["size"] < 0:
            raise ReportRebuildError(f"owner producer input size is invalid: {label}")
    sources = require_mapping(record["source_paths"], "owner source_paths")
    if not sources:
        raise ReportRebuildError("owner source_paths must be nonempty")
    report_paths: list[str] = []
    for source, target in sources.items():
        require_relative_path(source, "owner source path")
        report_paths.append(require_relative_path(target, "owner report path"))
    inventory = parse_inventory(record["inventory"], "owner inventory")
    if sorted(report_paths) != sorted(entry.path for entry in inventory):
        raise ReportRebuildError("owner paths do not match its inventory")
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
