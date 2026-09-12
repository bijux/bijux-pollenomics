"""Outputs checksums for the LRA engine."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics_lra.provenance.identity import sha256_file


def _write_checksum_manifest(directory: Path) -> Path:
    files = sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.name != "checksums.json"
    )
    manifest = {
        str(path.relative_to(directory)): {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in files
    }
    destination = directory / "checksums.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return destination
