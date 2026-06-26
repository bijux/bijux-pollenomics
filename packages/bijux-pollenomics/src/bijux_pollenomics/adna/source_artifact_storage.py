from __future__ import annotations

import gzip
import json
from pathlib import Path

__all__ = [
    "migrate_html_source_artifact",
    "migrate_html_source_artifacts",
    "read_source_artifact_text",
    "resolve_source_artifact_path",
    "source_artifact_exists",
    "write_source_artifact_bytes",
]


def resolve_source_artifact_path(path: Path) -> Path:
    """Resolve one logical source-artifact path to its stored repository path."""
    logical_path = Path(path)
    if logical_path.is_file():
        return logical_path
    compressed_path = logical_path.with_name(f"{logical_path.name}.gz")
    if compressed_path.is_file():
        return compressed_path
    return logical_path


def source_artifact_exists(path: Path) -> bool:
    """Return whether one logical source-artifact path is present on disk."""
    return resolve_source_artifact_path(path).is_file()


def read_source_artifact_text(
    path: Path,
    *,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> str:
    """Read one logical source-artifact text payload, inflating gzip when needed."""
    stored_path = resolve_source_artifact_path(path)
    if not stored_path.is_file():
        raise FileNotFoundError(stored_path)
    if stored_path.suffix == ".gz":
        with gzip.open(
            stored_path,
            mode="rt",
            encoding=encoding,
            errors=errors,
        ) as handle:
            return handle.read()
    return stored_path.read_text(encoding=encoding, errors=errors)


def write_source_artifact_bytes(
    path: Path,
    payload: bytes,
    *,
    compress_html: bool = True,
) -> Path:
    """Write one source-artifact payload using compressed storage for logical HTML."""
    logical_path = Path(path)
    logical_path.parent.mkdir(parents=True, exist_ok=True)
    if compress_html and logical_path.suffix == ".html":
        stored_path = logical_path.with_name(f"{logical_path.name}.gz")
        if logical_path.exists():
            logical_path.unlink()
        with gzip.open(stored_path, mode="wb") as handle:
            handle.write(payload)
        return stored_path
    compressed_path = logical_path.with_name(f"{logical_path.name}.gz")
    if compressed_path.exists():
        compressed_path.unlink()
    logical_path.write_bytes(payload)
    return logical_path


def migrate_html_source_artifact(path: Path, *, output_root: Path) -> Path:
    """Migrate one logical HTML artifact to compressed storage and refresh metadata."""
    logical_path = Path(path)
    if logical_path.suffix != ".html":
        raise ValueError(f"Expected .html artifact, received {logical_path}")
    output_root = Path(output_root)
    metadata_path = logical_path.with_suffix(logical_path.suffix + ".metadata.json")
    payload = _read_logical_artifact_bytes(logical_path)
    stored_path = write_source_artifact_bytes(logical_path, payload, compress_html=True)
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if isinstance(metadata, dict):
            metadata["byte_size"] = len(payload)
            metadata["storage_byte_size"] = stored_path.stat().st_size
            metadata["storage_path"] = str(stored_path.relative_to(output_root))
            metadata["content_encoding"] = (
                "gzip" if stored_path.suffix == ".gz" else None
            )
            metadata_path.write_text(
                json.dumps(metadata, indent=2),
                encoding="utf-8",
            )
    return stored_path


def migrate_html_source_artifacts(
    output_root: Path,
    *,
    logical_paths: tuple[Path, ...] | None = None,
) -> tuple[Path, ...]:
    """Migrate governed HTML source captures under one repository data root."""
    output_root = Path(output_root)
    candidates = logical_paths or tuple(
        sorted(
            (
                *output_root.glob(
                    "adna/governance/source_library/papers/*/article.html"
                ),
                *output_root.glob(
                    "adna/governance/source_library/projects/*/archive_metadata.html"
                ),
            )
        )
    )
    return tuple(
        migrate_html_source_artifact(path, output_root=output_root)
        for path in candidates
    )


def _read_logical_artifact_bytes(path: Path) -> bytes:
    stored_path = resolve_source_artifact_path(path)
    if not stored_path.is_file():
        raise FileNotFoundError(stored_path)
    if stored_path.suffix == ".gz":
        with gzip.open(stored_path, mode="rb") as handle:
            return handle.read()
    return stored_path.read_bytes()
