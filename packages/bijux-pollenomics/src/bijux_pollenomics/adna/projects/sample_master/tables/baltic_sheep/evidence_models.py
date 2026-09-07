"""Immutable official-evidence records for the Baltic ancient sheep."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BalticSheepArchiveEvidence:
    """One ENA sample identity, coordinate pair, and material statement."""

    accession: str
    sample_label: str
    site_name: str
    latitude_text: str
    longitude_text: str
    material_claim: str
    description: str
    source_path: str
    source_locator: str
    description_source_locator: str


@dataclass(frozen=True)
class BalticSheepChronologyEvidence:
    """One article Table 1 chronology with explicit interval semantics."""

    sample_label: str
    site_name: str
    region_name: str
    source_text: str
    chronology_text: str
    younger_bp: int | None
    older_bp: int | None
    dating_basis: str
    evidence_class: str
    precision_posture: str
    contextual: bool
    source_path: str
    source_locator: str
    source_excerpt: str


@dataclass(frozen=True)
class BalticSheepMaterialEvidenceConflict:
    """Typed preservation of conflicting archive and supplement anatomy claims."""

    accession: str
    sample_label: str
    status: str
    archive_claim: str
    supplement_claim: str
    archive_source_path: str
    archive_source_locator: str
    supplement_source_path: str
    supplement_source_locator: str

    def as_dict(self) -> dict[str, str]:
        """Return the unresolved two-source claim without collapsing either side."""
        return {
            "accession": self.accession,
            "sample_label": self.sample_label,
            "status": self.status,
            "archive_claim": self.archive_claim,
            "supplement_claim": self.supplement_claim,
            "archive_source_path": self.archive_source_path,
            "archive_source_locator": self.archive_source_locator,
            "supplement_source_path": self.supplement_source_path,
            "supplement_source_locator": self.supplement_source_locator,
        }

    @property
    def note(self) -> str:
        """Render both claims without selecting or rewriting either source."""
        return (
            "material_evidence_conflict: ENA states "
            f"{self.archive_claim!r}; the paper supplement states "
            f"{self.supplement_claim!r}; neither claim supersedes the other."
        )


@dataclass(frozen=True)
class BalticSheepOfficialSampleEvidence:
    """One exact identity join across ENA sample XML and article Table 1."""

    archive: BalticSheepArchiveEvidence
    chronology: BalticSheepChronologyEvidence
    region_name: str
    country_name: str
    jurisdiction_basis: str
    jurisdiction_registry_id: str
    jurisdiction_registry_version: str
    jurisdiction_registry_path: str
    jurisdiction_registry_locator: str


@dataclass(frozen=True)
class BalticSheepEvidenceDenominator:
    """Evidence denominators proving a complete one-to-one five-sample join."""

    expected_sample_count: int
    ena_sample_count: int
    article_sample_count: int
    joined_sample_count: int


@dataclass(frozen=True)
class BalticSheepOfficialEvidenceBundle:
    """Validated official evidence plus its explicit completeness denominator."""

    samples: tuple[BalticSheepOfficialSampleEvidence, ...]
    denominator: BalticSheepEvidenceDenominator

    def by_accession(self) -> dict[str, BalticSheepOfficialSampleEvidence]:
        """Index samples by their exact ENA biological-sample accession."""
        return {row.archive.accession: row for row in self.samples}
