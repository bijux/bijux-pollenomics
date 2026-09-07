"""Immutable contracts for source-native animal sample chronology."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

JsonObject: TypeAlias = dict[str, object]


@dataclass(frozen=True)
class InputArtifactIdentity:
    """Content identity for one governed input artifact."""

    logical_path: str
    byte_count: int
    sha256: str

    def as_dict(self) -> JsonObject:
        return {
            "logical_path": self.logical_path,
            "byte_count": self.byte_count,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class AnimalChronologyInputIdentity:
    """Path-and-byte-bound identity for the complete governed input set."""

    combined_sha256: str
    family_sha256: tuple[tuple[str, str], ...]
    artifacts: tuple[InputArtifactIdentity, ...]

    def as_dict(self) -> JsonObject:
        return {
            "identity_algorithm": "sha256-length-framed-logical-path-and-bytes.v1",
            "combined_sha256": self.combined_sha256,
            "family_sha256": dict(self.family_sha256),
            "artifact_count": len(self.artifacts),
            "artifacts": [artifact.as_dict() for artifact in self.artifacts],
        }


@dataclass(frozen=True)
class AnimalSampleChronologyNode:
    """One sample whose source chronology and coordinates are displayable."""

    feature_id: str
    project_accession: str
    repo_stable_sample_id: str
    preferred_sample_label: str
    project_species_latin_name: str
    project_species_common_name: str
    source_native_identity_kind: str | None
    source_native_tax_id: str | None
    source_native_scientific_name: str | None
    locality_text: str
    site_name: str
    country_name: str | None
    broader_geography: str | None
    latitude: float
    longitude: float
    latitude_text: str
    longitude_text: str
    coordinate_basis: str
    coordinate_confidence: str
    chronology_text: str
    chronology_strength: str
    chronology_evidence_class: str
    chronology_precision_posture: str
    chronology_normalization_status: str
    younger_bp: int
    older_bp: int
    mean_bp: int
    dating_basis: str
    sample_lineage_path: str
    sample_lineage_locator: str
    sample_lineage_excerpt: str
    chronology_provenance_path: str
    chronology_provenance_kind: str
    chronology_provenance_locator: str
    chronology_provenance_text: str
    location_evidence_artifact_path: str
    location_evidence_artifact_kind: str
    location_evidence_locator: str
    location_evidence_text: str
    source_url: str

    @property
    def source_native_taxonomy_status(self) -> str:
        return (
            "available"
            if self.source_native_identity_kind and self.source_native_scientific_name
            else "unavailable"
        )


@dataclass(frozen=True)
class AnimalSampleChronologyRefusal:
    """Exclusive terminal disposition for one non-admitted master identity."""

    project_accession: str
    repo_stable_sample_id: str
    reason_code: str

    def as_dict(self) -> JsonObject:
        return {
            "project_accession": self.project_accession,
            "repo_stable_sample_id": self.repo_stable_sample_id,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class AnimalSampleChronologyCorpus:
    """Globally validated source corpus before geography projection."""

    nodes: tuple[AnimalSampleChronologyNode, ...]
    refusals: tuple[AnimalSampleChronologyRefusal, ...]
    input_identity: AnimalChronologyInputIdentity
    source_counts: tuple[tuple[str, int], ...]
    refusal_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class AnimalSampleChronologyContextProjection:
    """Map-ready display projection and its complete accountability."""

    point_layers: tuple[JsonObject, ...]
    accountability: JsonObject
    refusals: tuple[AnimalSampleChronologyRefusal, ...]
    input_identity: AnimalChronologyInputIdentity


__all__ = [
    "AnimalChronologyInputIdentity",
    "AnimalSampleChronologyContextProjection",
    "AnimalSampleChronologyCorpus",
    "AnimalSampleChronologyNode",
    "AnimalSampleChronologyRefusal",
    "InputArtifactIdentity",
    "JsonObject",
]
