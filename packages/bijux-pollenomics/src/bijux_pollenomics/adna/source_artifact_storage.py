from __future__ import annotations

import gzip
from pathlib import Path

__all__ = [
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
