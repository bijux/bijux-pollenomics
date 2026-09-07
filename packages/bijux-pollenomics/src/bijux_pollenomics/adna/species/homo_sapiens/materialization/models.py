"""Lossless accountability models for AADR source rows."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Literal

from .chronology import AadrChronologyEvidence

CoordinateStatus = Literal[
    "admitted",
    "missing",
    "partial",
    "invalid_numeric",
    "non_finite",
    "out_of_range",
]
TaxonScopeStatus = Literal["not_asserted_by_source"]

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


def build_aadr_source_file_key(
    *,
    source_path: str,
    source_release: str,
    dataset_name: str,
    source_sha256: str,
) -> str:
    """Return a deterministic identity key for one physical AADR input."""
    identity = json.dumps(
        [source_sha256, source_release, dataset_name, source_path],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()
    return f"source-file:{sha256(identity).hexdigest()}"


@dataclass(frozen=True, slots=True)
class AadrSourceFile:
    """Immutable identity and provenance for one physical AADR source file."""

    source_path: str
    source_release: str
    dataset_name: str
    source_sha256: str
    source_byte_count: int

    def __post_init__(self) -> None:
        if not self.source_path:
            raise ValueError("AADR source path must be non-empty")
        if not self.source_release:
            raise ValueError("AADR source release must be non-empty")
        if not self.dataset_name:
            raise ValueError("AADR dataset name must be non-empty")
        if not _SHA256_RE.fullmatch(self.source_sha256):
            raise ValueError("AADR source digest must be lowercase SHA-256")
        if self.source_byte_count < 0:
            raise ValueError("AADR source byte count cannot be negative")

    @property
    def key(self) -> str:
        """Return the stable physical-source identity key."""
        return build_aadr_source_file_key(
            source_path=self.source_path,
            source_release=self.source_release,
            dataset_name=self.dataset_name,
            source_sha256=self.source_sha256,
        )


@dataclass(frozen=True, slots=True)
class AadrCoordinateEvidence:
    """Raw coordinate tokens and their non-inferential parsing result."""

    latitude_raw: str
    longitude_raw: str
    latitude: float | None
    longitude: float | None
    status: CoordinateStatus

    @property
    def admitted(self) -> bool:
        """Return whether both source-native coordinates are usable as a point."""
        return self.status == "admitted"


@dataclass(frozen=True, slots=True)
class AadrSourceRow:
    """One accountability row retained regardless of identity or data quality."""

    source: AadrSourceFile
    source_record_number: int
    source_line_start: int
    source_line_end: int
    column_names: tuple[str, ...]
    raw_tokens: tuple[str, ...]
    genetic_id_raw: str
    coordinates: AadrCoordinateEvidence
    chronology: AadrChronologyEvidence
    taxon_scope_status: TaxonScopeStatus = field(
        default="not_asserted_by_source", init=False
    )

    def __post_init__(self) -> None:
        if self.source_record_number < 1:
            raise ValueError("AADR source record number must be positive")
        if self.source_line_start < 2:
            raise ValueError("AADR source rows must follow the header line")
        if self.source_line_end < self.source_line_start:
            raise ValueError("AADR source line range is reversed")

    def raw_value(self, column_name: str) -> str:
        """Return an exact source token without stripping or null coercion."""
        matches = tuple(
            index for index, name in enumerate(self.column_names) if name == column_name
        )
        if len(matches) > 1:
            raise ValueError(f"AADR column name is ambiguous: {column_name}")
        if not matches or matches[0] >= len(self.raw_tokens):
            return ""
        return self.raw_tokens[matches[0]]

    @property
    def unmatched_raw_tokens(self) -> tuple[str, ...]:
        """Return source tokens beyond the declared header without discarding them."""
        return self.raw_tokens[len(self.column_names) :]


@dataclass(frozen=True, slots=True)
class AadrSourceTable:
    """One immutable AADR file plus every parsed physical source row."""

    source: AadrSourceFile
    column_names: tuple[str, ...]
    rows: tuple[AadrSourceRow, ...]
