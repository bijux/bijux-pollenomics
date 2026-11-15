"""Publish a portable literal unit source capture beside its original roster."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import stat
from typing import Any

from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
    publish_new_output_tree,
)

from ...capture.receipts import _read, _safe_root
from ...capture.resources.models import DEFAULT_RESOURCE_LIMITS, NeotomaResourceLimits
from ...capture.unit_resources.replay import replay_neotoma_unit_resources
from ...resource_catalogue.archive.files import encoded_json
from .metadata import (
    _SCOPE,
    MAX_BYTES,
    MAX_FILES,
    MAX_METADATA,
    SCHEMA,
    UnitMetadataInventory,
    pinned,
    read_neotoma_unit_metadata_inventory,
    source_index,
    source_metadata,
)
from .reading import guard_all_bodies
from .scope import prepare_scopes


def load_neotoma_unit_metadata_archive(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    context_directory: Path,
    expected_context_sha256: str,
    native_archive_directory: Path,
    expected_native_archive_sha256: str,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> dict[str, Any]:
    """Explicitly replay every original unit entity only after fresh all-body role guards."""
    inventory = read_neotoma_unit_metadata_inventory(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        context_directory=context_directory,
        expected_context_sha256=expected_context_sha256,
        native_archive_directory=native_archive_directory,
        expected_native_archive_sha256=expected_native_archive_sha256,
        limits=limits,
    )
    guard_all_bodies(inventory, limits)
    replay_neotoma_unit_resources(
        inventory.root / "capture",
        expected_manifest_sha256=inventory.manifest["capture_manifest_sha256"],
        roster_path=inventory.root
        / f"rosters/{inventory.manifest['original_roster_sha256']}.json",
        metadata_captures=inventory.scopes.original_metadata,
        limits=limits,
    )
    return inventory.manifest


def write_neotoma_unit_metadata_archive(
    directory: Path,
    *,
    capture_directory: Path,
    expected_capture_manifest_sha256: str,
    original_roster_path: Path,
    context_directory: Path,
    expected_context_sha256: str,
    native_archive_directory: Path,
    expected_native_archive_sha256: str,
) -> dict[str, Any]:
    """Retain original bytes once; neither raw unit metadata nor unit tokens become science."""
    final, capture, original = (
        _safe_root(directory),
        _safe_root(capture_directory),
        _safe_root(original_roster_path),
    )
    if final.exists():
        raise FileExistsError(f"Unit metadata archive already exists: {final}")
    source = source_metadata(capture, expected_capture_manifest_sha256)
    node = original.lstat()
    if (
        not stat.S_ISREG(node.st_mode)
        or node.st_nlink != 1
        or node.st_size > MAX_METADATA
    ):
        raise ValueError("Unit original roster is not a bounded ordinary file")
    if (
        source.document["response_bytes"]
        + sum(len(raw) for raw in source.buffers.values())
        + node.st_size
        > MAX_BYTES
    ):
        raise ValueError("Unit archive source exceeds finite byte budget")
    raw = _read(original, MAX_METADATA)
    original_pin = source.plan.roster_sha256
    if sha256(raw).hexdigest() != original_pin:
        raise ValueError("Unit original roster differs from original source plan")
    scopes = prepare_scopes(
        source.plan,
        source.control,
        original,
        source.limits,
        context_directory=context_directory,
        expected_context_sha256=expected_context_sha256,
        native_archive_directory=native_archive_directory,
        expected_native_archive_sha256=expected_native_archive_sha256,
    )
    buffers = {
        **source.buffers,
        f"rosters/{original_pin}.json": raw,
        "index.json": encoded_json(source_index(source, scopes)),
    }
    files = {
        **source.files,
        **{
            name: {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
            for name, raw in buffers.items()
        },
    }
    manifest = {
        "schema_version": SCHEMA,
        "capture_manifest_sha256": expected_capture_manifest_sha256,
        "original_roster_sha256": original_pin,
        "context_manifest_sha256": expected_context_sha256,
        "native_archive_manifest_sha256": expected_native_archive_sha256,
        "current_roster_sha256": scopes.current_roster_sha256,
        "current_scope_basis_sha256": scopes.current_basis_sha256,
        "files": files,
        "source_bytes": sum(member["bytes"] for member in files.values()),
        "scientific_admission": "not_asserted",
        "native_body_copies": 0,
        "historical_snapshot_replaced": False,
        "metadata_scope": _SCOPE,
        "related_resource_graph_complete": False,
    }
    content = encoded_json(manifest)
    if (
        len(content) > MAX_METADATA
        or len(buffers["index.json"]) > MAX_METADATA
        or len(files) + 1 > MAX_FILES
        or manifest["source_bytes"] + len(content) > MAX_BYTES
    ):
        raise ValueError("Unit archive exceeds finite publication budget")
    inventory = UnitMetadataInventory(
        final, manifest, source_index(source, scopes), source, scopes
    )
    guard_all_bodies(inventory, DEFAULT_RESOURCE_LIMITS)
    digest = sha256(content).hexdigest()
    options: dict[str, Any] = {
        "expected_manifest_sha256": digest,
        "context_directory": context_directory,
        "expected_context_sha256": expected_context_sha256,
        "native_archive_directory": native_archive_directory,
        "expected_native_archive_sha256": expected_native_archive_sha256,
    }
    staging = build_staging_output_dir(final)
    with OwnedTreeWriter(staging, max_bytes=MAX_BYTES, max_files=MAX_FILES) as writer:
        for name, member in files.items():
            body = (
                buffers[name]
                if name in buffers
                else pinned(
                    capture / name.removeprefix("capture/"),
                    member,
                    32 * 1024 * 1024 + 1,
                )
            )
            writer.write_bytes(name, body)
        writer.write_bytes("manifest.json", content)
    load_neotoma_unit_metadata_archive(staging, **options)
    if {path.name for path in capture.iterdir()} != {
        name.removeprefix("capture/") for name in source.files
    }:
        raise ValueError("Original unit capture namespace changed during publication")
    for name, member in source.files.items():
        pinned(capture / name.removeprefix("capture/"), member, 32 * 1024 * 1024 + 1)
    if _read(original, MAX_METADATA) != raw:
        raise ValueError("Original unit roster changed during publication")
    publish_new_output_tree(final_output_root=final, staging_output_root=staging)
    load_neotoma_unit_metadata_archive(final, **options)
    return manifest
