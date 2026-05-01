from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib

__all__ = ["SourceHashes", "build_source_hashes"]


@dataclass(frozen=True)
class SourceHashes:
    source: str
    snapshot_sha256: str
    normalized_sha256: str


def _hash_files(paths: list[Path], *, root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _collect_files(root: Path) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    return [path for path in root.rglob("*") if path.is_file()]


def build_source_hashes(
    *, source_output_roots: dict[str, str], selected_sources: tuple[str, ...]
) -> dict[str, SourceHashes]:
    """Build deterministic source and normalized layer hashes per source."""
    hashes: dict[str, SourceHashes] = {}
    for source in selected_sources:
        source_root = Path(source_output_roots[source])
        snapshot_files = _collect_files(source_root)
        normalized_files = _collect_files(source_root / "normalized")
        hashes[source] = SourceHashes(
            source=source,
            snapshot_sha256=_hash_files(snapshot_files, root=source_root),
            normalized_sha256=_hash_files(
                normalized_files, root=source_root / "normalized"
            )
            if normalized_files
            else hashlib.sha256(b"").hexdigest(),
        )
    return hashes
