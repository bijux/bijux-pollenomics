"""Validate a closed regular archive and replay its exact native source witnesses."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from ...capture.receipts import _read
from ..publication import load_neotoma_resource_catalogue
from .files import MAX_BYTES
from .inventory import read_archive_inventory
from .original_metadata import resolve_original_metadata


def load_neotoma_source_archive(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    original_relational_root: Path | None = None,
) -> dict[str, Any]:
    """Reconcile the complete portable publication and replay every source capsule."""
    inventory = read_archive_inventory(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    root, manifest = inventory.root, inventory.manifest
    total = inventory.manifest_bytes
    source_bytes = 0
    for relative, member in manifest["files"].items():
        bound = min(member["bytes"], 32 * 1024 * 1024 + 1, MAX_BYTES - total)
        body = _read(root / relative, bound)
        total += len(body)
        source_bytes += len(body)
        if len(body) != member["bytes"] or sha256(body).hexdigest() != member["sha256"]:
            raise ValueError("Neotoma source archive member identity differs")
        if total > MAX_BYTES:
            raise ValueError("Neotoma source archive exceeds its finite byte budget")
    if manifest["source_bytes"] != source_bytes:
        raise ValueError("Neotoma source archive source byte population differs")
    if "original_metadata" in manifest:
        original_relational_root, _ = resolve_original_metadata(
            root, manifest["original_metadata"], original_relational_root
        )
    load_neotoma_resource_catalogue(
        root / "catalogue",
        expected_manifest_sha256=manifest["catalogue_manifest_sha256"],
        capture_sources=inventory.capture_sources,
        retained_sources=inventory.retained_sources,
        original_relational_root=original_relational_root,
        require_source_bodies=True,
    )
    return manifest
