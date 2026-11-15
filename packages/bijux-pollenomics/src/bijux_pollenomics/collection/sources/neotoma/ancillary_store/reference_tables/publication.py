"""Retain literal public reference captures in a closed self-contained archive."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
    publish_new_output_tree,
)

from ...capture.receipts import _read, _safe_root
from ...capture.reference_tables import replay_neotoma_reference_tables
from ...capture.reference_tables.models import METADATA_SCOPE
from ...resource_catalogue.archive.files import _digest, encoded_json
from .metadata import (
    MAX_BYTES,
    MAX_FILES,
    SCHEMA,
    read_neotoma_reference_archive_inventory,
    source_index,
)


def load_neotoma_reference_archive(
    directory: Path, *, expected_manifest_sha256: str
) -> dict[str, Any]:
    """Authenticate every original entity and replay its source assessments."""
    inventory = read_neotoma_reference_archive_inventory(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    replay_neotoma_reference_tables(
        _safe_root(directory) / "capture",
        expected_manifest_sha256=inventory.manifest["capture_manifest_sha256"],
    )
    return inventory.manifest


def write_neotoma_reference_archive(
    directory: Path, *, capture_directory: Path, expected_capture_manifest_sha256: str
) -> dict[str, Any]:
    """Copy a replayed source capture; do not recapture or relabel refused prefixes."""
    final, source = _safe_root(directory), _safe_root(capture_directory)
    if final.exists():
        raise FileExistsError(f"Reference archive already exists: {final}")
    if not _digest(expected_capture_manifest_sha256):
        raise ValueError("An independent reference capture anchor is required")
    replay_neotoma_reference_tables(
        source, expected_manifest_sha256=expected_capture_manifest_sha256
    )
    buffers = {}
    for path in sorted(source.iterdir()):
        if not path.is_file() or path.is_symlink():
            raise ValueError("Reference capture contains an unsafe namespace member")
        buffers["capture/" + path.name] = _read(path, MAX_BYTES)
    files = {
        name: {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
        for name, raw in buffers.items()
    }
    files["index.json"] = {"bytes": 0, "sha256": "0" * 64}
    buffers["index.json"] = encoded_json(
        source_index(source, expected_capture_manifest_sha256, files)
    )
    files["index.json"] = {
        "bytes": len(buffers["index.json"]),
        "sha256": sha256(buffers["index.json"]).hexdigest(),
    }
    manifest = {
        "schema_version": SCHEMA,
        "capture_manifest_sha256": expected_capture_manifest_sha256,
        "files": files,
        "source_bytes": sum(len(raw) for raw in buffers.values()),
        "scientific_admission": "not_asserted",
        "metadata_scope": METADATA_SCOPE,
        "table_population_complete": False,
        "historical_snapshot_replaced": False,
    }
    raw = encoded_json(manifest)
    digest = sha256(raw).hexdigest()
    staging = build_staging_output_dir(final)
    with OwnedTreeWriter(staging, max_bytes=MAX_BYTES, max_files=MAX_FILES) as writer:
        for name, body in buffers.items():
            writer.write_bytes(name, body)
        writer.write_bytes("manifest.json", raw)
    load_neotoma_reference_archive(staging, expected_manifest_sha256=digest)
    for path in source.iterdir():
        name = "capture/" + path.name
        if name not in buffers or _read(path, MAX_BYTES) != buffers[name]:
            raise ValueError("Reference source changed during publication")
    if {"capture/" + p.name for p in source.iterdir()} != set(buffers) - {"index.json"}:
        raise ValueError("Reference source namespace changed during publication")
    publish_new_output_tree(final_output_root=final, staging_output_root=staging)
    load_neotoma_reference_archive(final, expected_manifest_sha256=digest)
    return manifest
