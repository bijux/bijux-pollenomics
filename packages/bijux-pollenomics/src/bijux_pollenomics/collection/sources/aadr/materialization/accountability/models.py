"""Typed source-accountability contracts for AADR review preparation."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

from bijux_pollenomics.adna.species.homo_sapiens.materialization.reconciliation import (
    AadrSourceRowLink,
)

from ..source_rows import validate_aadr_logical_source_path

PoliticalEntityEvidenceStatus = Literal[
    "reported",
    "value_missing",
    "token_missing",
    "column_unavailable",
]
PoliticalEntityReconciliationStatus = Literal["exact", "complementary", "conflict"]
PoliticalEntityDisposition = Literal[
    "DK",
    "FI",
    "NO",
    "SE",
    "other",
    "missing",
    "conflict",
]

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class AadrReleaseManifestIdentity:
    """Stable identity of the release receipt that declared the input panels."""

    logical_path: str
    source_release: str
    sha256: str
    byte_count: int

    def __post_init__(self) -> None:
        validate_aadr_logical_source_path(self.logical_path)
        if not self.source_release:
            raise ValueError("AADR release-manifest release must be non-empty")
        if not _SHA256_RE.fullmatch(self.sha256):
            raise ValueError("AADR release-manifest digest must be lowercase SHA-256")
        if (
            isinstance(self.byte_count, bool)
            or not isinstance(self.byte_count, int)
            or self.byte_count < 0
        ):
            raise ValueError(
                "AADR release-manifest byte count must be a nonnegative integer"
            )


@dataclass(frozen=True, slots=True)
class AadrPoliticalEntityEvidence:
    """One source-native Political Entity token without country inference."""

    raw_value: str | None
    trimmed_value: str | None
    status: PoliticalEntityEvidenceStatus


@dataclass(frozen=True, slots=True)
class AadrPoliticalEntityEvidenceGroup:
    """One exact Political Entity token and every source row reporting it."""

    evidence: AadrPoliticalEntityEvidence
    source_rows: tuple[AadrSourceRowLink, ...]


@dataclass(frozen=True, slots=True)
class AadrPoliticalEntityReconciliation:
    """All Political Entity evidence for one reconciled Genetic ID."""

    genetic_id: str
    evidence_groups: tuple[AadrPoliticalEntityEvidenceGroup, ...]
    reconciliation_status: PoliticalEntityReconciliationStatus
    disposition: PoliticalEntityDisposition


__all__ = [
    "AadrPoliticalEntityEvidence",
    "AadrPoliticalEntityEvidenceGroup",
    "AadrPoliticalEntityReconciliation",
    "AadrReleaseManifestIdentity",
    "PoliticalEntityDisposition",
    "PoliticalEntityEvidenceStatus",
    "PoliticalEntityReconciliationStatus",
]
