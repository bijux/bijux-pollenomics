"""AADR source-row loading with checkout-independent evidence identity."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path, PurePosixPath

from bijux_pollenomics.adna.species.homo_sapiens.materialization.models import (
    AadrSourceTable,
)
from bijux_pollenomics.adna.species.homo_sapiens.materialization.source_rows import (
    load_aadr_source_table as _load_aadr_source_table,
)


def validate_aadr_logical_source_path(value: str) -> str:
    """Return a canonical repository-relative POSIX source identity path."""
    candidate = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or candidate.is_absolute()
        or value != candidate.as_posix()
        or any(part in {"", ".", ".."} for part in candidate.parts)
    ):
        raise ValueError(f"AADR logical source path is not canonical: {value!r}")
    return value


def load_aadr_source_table(
    path: Path,
    *,
    source_release: str,
    dataset_name: str,
    logical_source_path: str,
    expected_sha256: str | None = None,
) -> AadrSourceTable:
    """Load an AADR table while separating access path from evidence identity."""
    logical_path = validate_aadr_logical_source_path(logical_source_path)
    table = _load_aadr_source_table(
        path,
        source_release=source_release,
        dataset_name=dataset_name,
        expected_sha256=expected_sha256,
    )
    logical_source = replace(table.source, source_path=logical_path)
    return replace(
        table,
        source=logical_source,
        rows=tuple(replace(row, source=logical_source) for row in table.rows),
    )


__all__ = ["load_aadr_source_table", "validate_aadr_logical_source_path"]
