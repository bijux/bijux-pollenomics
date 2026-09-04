from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile

__all__ = [
    "SourceArtifactContentDriftError",
    "migrate_html_source_artifact",
    "migrate_html_source_artifacts",
    "read_source_artifact_bytes",
    "read_source_artifact_text",
    "resolve_source_artifact_path",
    "source_artifact_exists",
    "write_source_artifact_bytes",
]


class SourceArtifactContentDriftError(ValueError):
    """Refuse replacement when a logical source capture changes content."""

    def __init__(
        self,
        *,
        logical_path: Path,
        stored_path: Path,
        existing_payload: bytes,
        candidate_payload: bytes,
    ) -> None:
        self.logical_path = logical_path
        self.stored_path = stored_path
        self.existing_sha256 = hashlib.sha256(existing_payload).hexdigest()
        self.candidate_sha256 = hashlib.sha256(candidate_payload).hexdigest()
        self.existing_byte_size = len(existing_payload)
        self.candidate_byte_size = len(candidate_payload)
        super().__init__(
            "Source artifact content drift refused for "
            f"{logical_path}: {self.existing_sha256} != {self.candidate_sha256}"
        )


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
    return read_source_artifact_bytes(path).decode(encoding=encoding, errors=errors)


def read_source_artifact_bytes(path: Path) -> bytes:
    """Read exact logical bytes independent of the repository storage encoding."""
    stored_path = resolve_source_artifact_path(path)
    if not stored_path.is_file():
        raise FileNotFoundError(stored_path)
    if stored_path.suffix == ".gz":
        with gzip.open(stored_path, mode="rb") as handle:
            return handle.read()
    return stored_path.read_bytes()


def write_source_artifact_bytes(
    path: Path,
    payload: bytes,
    *,
    compress_html: bool = True,
) -> Path:
    """Immutably store logical source bytes, compressing HTML deterministically."""
    logical_path = Path(path)
    logical_path.parent.mkdir(parents=True, exist_ok=True)
    compressed_path = logical_path.with_name(f"{logical_path.name}.gz")
    existing_paths = tuple(
        candidate
        for candidate in (logical_path, compressed_path)
        if candidate.is_file()
    )
    existing_payloads = {
        candidate: _read_stored_artifact_bytes(candidate)
        for candidate in existing_paths
    }
    if existing_payloads:
        first_path, first_payload = next(iter(existing_payloads.items()))
        if any(content != first_payload for content in existing_payloads.values()):
            raise ValueError(
                f"Conflicting plain and gzip source artifacts for {logical_path}"
            )
        if first_payload != payload:
            raise SourceArtifactContentDriftError(
                logical_path=logical_path,
                stored_path=first_path,
                existing_payload=first_payload,
                candidate_payload=payload,
            )

    use_gzip = compress_html and logical_path.suffix == ".html"
    stored_path = compressed_path if use_gzip else logical_path
    legacy_path = logical_path if use_gzip else compressed_path
    if stored_path.is_file():
        if legacy_path.is_file():
            legacy_path.unlink()
        return stored_path

    stored_payload = _deterministic_gzip_bytes(payload) if use_gzip else payload
    _install_without_replacement(stored_path, stored_payload)
    if legacy_path.is_file():
        legacy_path.unlink()
    return stored_path


def migrate_html_source_artifact(path: Path, *, output_root: Path) -> Path:
    """Migrate one logical HTML artifact to compressed storage and refresh metadata."""
    logical_path = Path(path)
    if logical_path.suffix != ".html":
        raise ValueError(f"Expected .html artifact, received {logical_path}")
    output_root = Path(output_root)
    metadata_path = logical_path.with_suffix(logical_path.suffix + ".metadata.json")
    payload = _read_logical_artifact_bytes(logical_path)
    compressed_path = logical_path.with_name(f"{logical_path.name}.gz")
    if compressed_path.is_file():
        compressed_payload = _read_stored_artifact_bytes(compressed_path)
        if compressed_payload != payload:
            raise SourceArtifactContentDriftError(
                logical_path=logical_path,
                stored_path=compressed_path,
                existing_payload=compressed_payload,
                candidate_payload=payload,
            )
        canonical_storage = _deterministic_gzip_bytes(payload)
        if compressed_path.read_bytes() != canonical_storage:
            _atomic_replace_bytes(compressed_path, canonical_storage)
        stored_path = compressed_path
        if logical_path.is_file():
            logical_path.unlink()
    else:
        stored_path = write_source_artifact_bytes(
            logical_path, payload, compress_html=True
        )
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
    return read_source_artifact_bytes(path)


def _read_stored_artifact_bytes(path: Path) -> bytes:
    if path.suffix == ".gz":
        with gzip.open(path, mode="rb") as handle:
            return handle.read()
    return path.read_bytes()


def _deterministic_gzip_bytes(payload: bytes) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0) as handle:
        handle.write(payload)
    return buffer.getvalue()


def _install_without_replacement(path: Path, payload: bytes) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError:
            existing = _read_stored_artifact_bytes(path)
            candidate = gzip.decompress(payload) if path.suffix == ".gz" else payload
            if existing != candidate:
                raise SourceArtifactContentDriftError(
                    logical_path=(
                        path.with_name(path.name.removesuffix(".gz"))
                        if path.suffix == ".gz"
                        else path
                    ),
                    stored_path=path,
                    existing_payload=existing,
                    candidate_payload=candidate,
                ) from None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _atomic_replace_bytes(path: Path, payload: bytes) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
