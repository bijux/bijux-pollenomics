"""Lossless accountability models for AADR source rows."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Literal

CoordinateStatus = Literal[
    "admitted",
    "missing",
    "partial",
    "invalid_numeric",
    "non_finite",
    "out_of_range",
]
DateMethodFamily = Literal[
    "direct",
    "contextual",
    "modern",
    "known_historical",
    "modeled_relational",
    "unclassified",
]
ChronologyEvaluationStatus = Literal["not_evaluated"]
TaxonScopeStatus = Literal["not_asserted_by_source"]

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


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
class AadrDateMethodEvidence:
    """Raw dating-method token and its syntax-only family classification."""

    raw_value: str
    normalized_value: str
    family: DateMethodFamily


@dataclass(frozen=True, slots=True)
class AadrChronologyEvidence:
    """Uninterpreted chronology fields awaiting a separate scientific policy."""

    date_method: AadrDateMethodEvidence
    date_mean_bp_raw: str
    date_stddev_bp_raw: str
    full_date_raw: str
    evaluation_status: ChronologyEvaluationStatus = "not_evaluated"


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
