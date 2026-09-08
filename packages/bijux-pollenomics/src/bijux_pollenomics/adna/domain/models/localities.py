"""Species-aware locality summaries derived from aDNA samples."""

from __future__ import annotations

from dataclasses import dataclass

from .chronology import AdnaChronology, AdnaCoordinate
from .identity import AdnaLocalityIdentity


@dataclass(frozen=True)
class AdnaLocalitySummary:
    """Species-aware locality summary derived from normalized ancient-DNA samples."""

    identity: AdnaLocalityIdentity
    species_latin_name: str
    species_common_name: str
    source_family: str
    source_releases: tuple[str, ...]
    record_modalities: tuple[str, ...]
    review_strengths: tuple[str, ...]
    provenance_qualities: tuple[str, ...]
    locality: str | None
    coordinates: AdnaCoordinate
    sample_count: int
    sample_ids: tuple[str, ...]
    datasets: tuple[str, ...]
    chronology: AdnaChronology
    sample_namespace: str
    project_accessions: tuple[str, ...] = ()
    original_location_text: str = ""
    nordic_inclusion: bool = False
    nordic_inclusion_reason: str = ""
    interpretation_note: str = ""

    @property
    def latitude(self) -> float | None:
        return self.coordinates.latitude

    @property
    def longitude(self) -> float | None:
        return self.coordinates.longitude

    @property
    def latitude_text(self) -> str:
        return self.coordinates.latitude_text

    @property
    def longitude_text(self) -> str:
        return self.coordinates.longitude_text

    @property
    def coordinate_confidence(self) -> str:
        return self.coordinates.confidence

    @property
    def locality_namespace(self) -> str:
        return self.identity.namespace

    @property
    def locality_token(self) -> str:
        return self.identity.stable_token

    @property
    def time_start_bp(self) -> int | None:
        return self.chronology.time_start_bp

    @property
    def time_end_bp(self) -> int | None:
        return self.chronology.time_end_bp

    @property
    def time_mean_bp(self) -> int | None:
        return self.chronology.time_mean_bp

    @property
    def time_label(self) -> str:
        return self.chronology.original_text

    @property
    def dating_basis(self) -> str:
        return self.chronology.dating_basis

    def as_dict(self) -> dict[str, object]:
        return {
            "identity": self.identity.as_dict(),
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "source_family": self.source_family,
            "source_releases": list(self.source_releases),
            "record_modalities": list(self.record_modalities),
            "review_strengths": list(self.review_strengths),
            "provenance_qualities": list(self.provenance_qualities),
            "locality": self.locality,
            "coordinates": self.coordinates.as_dict(),
            "sample_count": self.sample_count,
            "sample_ids": list(self.sample_ids),
            "datasets": list(self.datasets),
            "chronology": self.chronology.as_dict(),
            "sample_namespace": self.sample_namespace,
            "project_accessions": list(self.project_accessions),
            "original_location_text": self.original_location_text,
            "nordic_inclusion": self.nordic_inclusion,
            "nordic_inclusion_reason": self.nordic_inclusion_reason,
            "interpretation_note": self.interpretation_note,
        }
