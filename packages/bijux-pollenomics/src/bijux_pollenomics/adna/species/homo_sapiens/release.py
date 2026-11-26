"""Discovery and identity validation for governed AADR releases."""

from __future__ import annotations

import json
import os
import stat
from hashlib import sha256
from pathlib import Path

from bijux_pollenomics.adna.workflow.runtime import AdnaSourceBundle
from bijux_pollenomics.core.filesystem.anchors import DirectoryAnchor

from .release_manifest import (
    validate_release_manifest_identity as validate_release_manifest_identity,
)

ReleaseCacheKey = tuple[
    str,
    str,
    str,
    str,
    str,
    tuple[tuple[str, str], ...],
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


def _read_annotation(path: Path) -> bytes:
    """Capture a regular annotation while retaining supported hard links."""
    if not all(hasattr(os, flag) for flag in ("O_NOFOLLOW", "O_NONBLOCK")):
        raise ValueError("Safe AADR source reads are unsupported")
    with DirectoryAnchor(path.parent) as anchor:
        before = os.stat(path.name, dir_fd=anchor.fd, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("AADR annotation is not a regular file")
        fd = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=anchor.fd
        )
        try:

            def stamp(node: os.stat_result) -> tuple[int, ...]:
                return (
                    node.st_dev,
                    node.st_ino,
                    node.st_mode,
                    node.st_nlink,
                    node.st_size,
                    node.st_mtime_ns,
                    node.st_ctime_ns,
                )

            if stamp(os.fstat(fd)) != stamp(before):
                raise ValueError("AADR annotation changed while opening")
            chunks = []
            remaining = before.st_size
            while remaining:
                block = os.read(fd, min(remaining, 1024 * 1024))
                if not block:
                    raise ValueError("AADR annotation changed while reading")
                chunks.append(block)
                remaining -= len(block)
            if stamp(os.fstat(fd)) != stamp(before) or stamp(
                os.stat(path.name, dir_fd=anchor.fd, follow_symlinks=False)
            ) != stamp(before):
                raise ValueError("AADR annotation changed while reading")
            anchor.check()
            return b"".join(chunks)
        finally:
            os.close(fd)


def capture_release_inputs(bundle: AdnaSourceBundle) -> tuple[tuple[str, bytes], ...]:
    """Capture ordered bodies from resolved paths, with each read size-bound."""
    paths = discover_homo_sapiens_anno_files(Path(bundle.tracked_root))
    captured = []
    for path in paths:
        resolved = path.resolve(strict=True)
        raw = _read_annotation(resolved)
        captured.append((str(path), raw))
    return tuple(captured)


def release_cache_key(
    bundle: AdnaSourceBundle, captured: tuple[tuple[str, bytes], ...] | None = None
) -> ReleaseCacheKey:
    """Identify the exact captured bodies and all parsing-relevant bundle fields."""
    if captured is None:
        captured = capture_release_inputs(bundle)
    file_rows = tuple((path, sha256(raw).hexdigest()) for path, raw in captured)
    return (
        bundle.source_release,
        bundle.source_family,
        bundle.record_modality,
        bundle.review_strength,
        bundle.provenance_quality,
        file_rows,
    )
