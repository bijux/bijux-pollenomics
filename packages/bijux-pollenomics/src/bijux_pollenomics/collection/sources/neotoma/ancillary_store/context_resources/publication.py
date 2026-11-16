"""Literal context archive publication and explicitly full owned-body validation."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import (
    OwnedTreeWriter,
    validate_regular_namespace,
)
from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
    publish_new_output_tree,
)

from ...capture.context_resources.models import DEFAULT_CONTEXT_LIMITS
from ...capture.context_resources.protocol import validate_plan
from ...capture.receipts import _safe_root
from ...capture.resources.models import NeotomaResourceLimits
from ...resource_catalogue.archive.files import encoded_json
from .metadata import (
    MAX_BYTES,
    MAX_FILES,
    MAX_METADATA,
    SCHEMA,
    NeotomaContextResourceInventory,
    pinned,
    read_neotoma_context_resource_inventory,
    source_index,
    source_metadata,
)
from .reading import guard_all_bodies, qualify_profile, read_entry
from .scope import NeotomaContextArchiveBindings, prepare_scopes


def load_neotoma_context_resource_archive(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    original: NeotomaContextArchiveBindings,
    current: NeotomaContextArchiveBindings,
    limits: NeotomaResourceLimits = DEFAULT_CONTEXT_LIMITS,
) -> dict[str, Any]:
    """Replay every owned entity explicitly, without promoting source-profile refusals."""
    inventory = read_neotoma_context_resource_inventory(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        original=original,
        current=current,
        limits=limits,
    )
    guard_all_bodies(inventory, limits)
    profiles = []
    for entry in inventory.source.document["resources"]:
        profile = {
            "site_id": entry["site_id"],
            "resource_kind": entry["resource_kind"],
            "qualification_status": "not_qualified_source_result",
        }
        if entry["attempts"] and "body_file" in entry["attempts"][0]:
            result = read_entry(inventory, entry, limits)
            if (
                entry["terminal_status"]
                == "received_complete_unqualified_context_resource"
            ):
                try:
                    _, qualified = qualify_profile(inventory, entry, result["body"])
                except ValueError as error:
                    profile.update(
                        qualification_status="refused_foreign_native_parent"
                        if "foreign native parent" in str(error)
                        else "refused_native_profile",
                        reason=str(error),
                    )
                else:
                    profile.update(qualified)
        profiles.append(profile)
    return {
        "manifest": inventory.manifest,
        "native_profiles": profiles,
        "native_profile_partitions": dict(
            Counter(row["qualification_status"] for row in profiles)
        ),
        "source_capture_history_replayed": True,
        "body_hashes_verified": True,
        "native_profile_refusals_preserved": True,
        "scientific_admission": "not_asserted",
    }


def write_neotoma_context_resource_archive(
    directory: Path,
    *,
    capture_directory: Path,
    expected_capture_manifest_sha256: str,
    original: NeotomaContextArchiveBindings,
    current: NeotomaContextArchiveBindings,
    limits: NeotomaResourceLimits = DEFAULT_CONTEXT_LIMITS,
) -> dict[str, Any]:
    """Copy the closed source once; shared original/current foundations remain referenced."""
    final, capture = _safe_root(directory), _safe_root(capture_directory)
    if final.exists():
        raise FileExistsError(f"Context archive already exists: {final}")
    source = source_metadata(capture, expected_capture_manifest_sha256)
    validate_plan(source.plan, limits)
    scopes = prepare_scopes(
        source.plan, source.proof, original=original, current=current
    )
    buffers = {**source.buffers, "index.json": encoded_json(source_index(source))}
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
        "original_context_manifest_sha256": source.plan.context_manifest_sha256,
        "original_native_archive_manifest_sha256": source.plan.native_archive_manifest_sha256,
        "files": files,
        "source_bytes": sum(member["bytes"] for member in files.values()),
        "native_body_copies": 0,
        "scientific_admission": "not_asserted",
        "historical_snapshot_replaced": False,
        "related_resource_graph_complete": False,
    }
    raw = encoded_json(manifest)
    if (
        len(raw) > MAX_METADATA
        or any(len(value) > MAX_METADATA for value in buffers.values())
        or len(files) + 1 > MAX_FILES
        or manifest["source_bytes"] + len(raw) > MAX_BYTES
    ):
        raise ValueError("Context archive exceeds finite publication budget")
    guard_all_bodies(
        NeotomaContextResourceInventory(
            final, manifest, source_index(source), source, scopes
        ),
        limits,
    )
    options: dict[str, Any] = {
        "expected_manifest_sha256": sha256(raw).hexdigest(),
        "original": original,
        "current": current,
        "limits": limits,
    }
    staging = build_staging_output_dir(final)
    with OwnedTreeWriter(staging, max_bytes=MAX_BYTES, max_files=MAX_FILES) as writer:
        for name, member in files.items():
            body = (
                buffers[name]
                if name in buffers
                else pinned(
                    capture / name.removeprefix("capture/"), member, 32 * 1024 * 1024
                )
            )
            writer.write_bytes(name, body)
        writer.write_bytes("manifest.json", raw)
        load_neotoma_context_resource_archive(staging, **options)
        validate_regular_namespace(
            capture,
            {name.removeprefix("capture/") for name in source.files},
            max_files=MAX_FILES,
            max_bytes=MAX_BYTES,
        )
        writer.validate_attachment()
        owned = staging.stat(follow_symlinks=False)
        publish_new_output_tree(final_output_root=final, staging_output_root=staging)
        published = final.stat(follow_symlinks=False)
        if (owned.st_dev, owned.st_ino) != (published.st_dev, published.st_ino):
            raise ValueError("Published context archive is not the owned staging inode")
        load_neotoma_context_resource_archive(final, **options)
    return manifest
