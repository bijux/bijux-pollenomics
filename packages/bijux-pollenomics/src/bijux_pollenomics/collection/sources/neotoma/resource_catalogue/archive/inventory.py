"""Authenticate archive metadata and internal resolvers without numerical bodies."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from ...capture.receipts import _object, _read, _safe_root
from ...capture.resources import NeotomaRetainedSource
from ..publication import load_neotoma_resource_catalogue
from ..source_projection import _same
from .files import (
    MAX_BYTES,
    MAX_FILES,
    MAX_MANIFEST_BYTES,
    validate_manifest,
    validate_namespace,
)
from .inputs import preflight_archive_inputs


@dataclass(frozen=True)
class ArchiveInventory:
    """Pinned metadata and internal paths; unselected source buffers stay unread."""

    root: Path
    manifest: dict[str, Any]
    manifest_bytes: int
    capture_sources: dict[str, Path]
    retained_sources: dict[str, NeotomaRetainedSource]
    original_relational_root: Path | None


def read_archive_inventory(
    directory: Path, *, expected_manifest_sha256: str
) -> ArchiveInventory:
    """Bind exact physical inventory, catalogue and source-declared member hashes."""
    root = _safe_root(directory)
    raw = _read(root / "manifest.json", MAX_MANIFEST_BYTES)
    if sha256(raw).hexdigest() != expected_manifest_sha256:
        raise ValueError("Neotoma source archive manifest identity differs")
    manifest = _object(raw)
    validate_manifest(manifest)
    validate_namespace(root, {"manifest.json", *manifest["files"]})
    for relative, member in manifest["files"].items():
        if (root / relative).stat(follow_symlinks=False).st_size != member["bytes"]:
            raise ValueError(
                "Neotoma source archive member identity differs: input is not a bounded regular file"
            )
    catalogue = load_neotoma_resource_catalogue(
        root / "catalogue",
        expected_manifest_sha256=manifest["catalogue_manifest_sha256"],
    )
    captures = {
        digest: root / "captures" / digest
        for digest in catalogue["capture_descriptors"]
    }
    retained = {
        key: NeotomaRetainedSource(
            root / value["body"],
            root / value["provenance"],
            value["provenance_sha256"],
            value["body_sha256"],
        )
        for key, value in manifest["retained_sources"].items()
    }
    original = (
        root / "captures/original-metadata" if "original_metadata" in manifest else None
    )
    expected = preflight_archive_inputs(
        root / "catalogue",
        expected_catalogue_manifest_sha256=manifest["catalogue_manifest_sha256"],
        capture_sources=captures,
        retained_sources=retained,
        original_relational_root=original,
        max_bytes=MAX_BYTES,
        max_files=MAX_FILES,
        max_manifest_bytes=MAX_MANIFEST_BYTES,
    )
    if not _same(manifest, expected.manifest):
        raise ValueError("Neotoma source archive member identity or population differs")
    for relative, (path, maximum) in expected.paths.items():
        if (
            relative.startswith(("catalogue/", "captures/original-metadata/"))
            or path.suffix == ".body"
        ):
            continue
        member = manifest["files"][relative]
        content = _read(path, min(maximum, member["bytes"]))
        if (
            len(content) != member["bytes"]
            or sha256(content).hexdigest() != member["sha256"]
        ):
            raise ValueError("Neotoma source archive metadata identity differs")
    member = manifest["files"]["downloads/index.json"]
    index = _read(root / "downloads/index.json", min(member["bytes"], 16 * 1024 * 1024))
    if len(index) != member["bytes"] or sha256(index).hexdigest() != member["sha256"]:
        raise ValueError("Neotoma source archive download identity differs")
    if not _same(_object(index), _object(expected.index)):
        raise ValueError("Neotoma source archive download partition differs")
    return ArchiveInventory(root, manifest, len(raw), captures, retained, original)
