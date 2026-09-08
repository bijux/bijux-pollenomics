"""Discovery and identity validation for governed AADR releases."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.adna.workflow.runtime import AdnaSourceBundle

from .release_manifest import (
    validate_release_manifest_identity as validate_release_manifest_identity,
)

ReleaseCacheKey = tuple[
    str,
    str,
    str,
    str,
    str,
    tuple[tuple[str, int, int], ...],
]


def discover_homo_sapiens_anno_files(release_dir: Path) -> list[Path]:
    """Find all governed AADR anno files inside the Homo sapiens runtime surface."""
    files = sorted(path for path in release_dir.glob("*/*.anno") if path.is_file())
    if not files:
        raise FileNotFoundError(f"No .anno files found under {release_dir}")
    return files


def release_dataset_names(
    release_manifest_path: Path, release_dir: Path
) -> tuple[str, ...]:
    """Return validated dataset names declared by one AADR release."""
    if not release_manifest_path.exists():
        return tuple(
            sorted(
                path.name
                for path in release_dir.iterdir()
                if path.is_dir() and any(path.glob("*.anno"))
            )
        )
    payload = json.loads(release_manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("AADR release manifest must be a JSON object")
    validate_release_manifest_identity(payload, release_dir)
    anno_files = payload.get("anno_files", [])
    if not isinstance(anno_files, list):
        return ()
    names = {
        str(row.get("dataset_name", "")).strip()
        for row in anno_files
        if isinstance(row, dict) and str(row.get("dataset_name", "")).strip()
    }
    return tuple(sorted(names))


def release_cache_key(bundle: AdnaSourceBundle) -> ReleaseCacheKey:
    """Fingerprint the release inputs that invalidate normalized row caches."""
    release_dir = Path(bundle.tracked_root)
    file_rows = tuple(
        (str(path), path.stat().st_mtime_ns, path.stat().st_size)
        for path in discover_homo_sapiens_anno_files(release_dir)
    )
    return (
        bundle.source_release,
        bundle.source_family,
        bundle.record_modality,
        bundle.review_strength,
        bundle.provenance_quality,
        file_rows,
    )
