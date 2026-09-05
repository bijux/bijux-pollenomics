"""Locality evidence context supplied to candidate ranking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ....reporting.models import LocalitySummary


@dataclass(frozen=True)
class CandidateSiteContext:
    """One rankable locality anchor plus direct and contextual evidence around it."""

    locality: LocalitySummary
    direct_evidence: tuple[LocalitySummary, ...] = field(default_factory=tuple)
    nearby_context_points: int = 0
    nearby_context_layer_count: int = 0
    time_aware_context_points: int = 0
    temporal_overlap_points: int = 0
    nearest_context_distance_km: float | None = None

    def __post_init__(self) -> None:
        if not self.direct_evidence:
            object.__setattr__(self, "direct_evidence", (self.locality,))

    @property
    def direct_sample_count(self) -> int:
        return sum(locality.sample_count for locality in self.direct_evidence)

    @property
    def distinct_species_count(self) -> int:
        return len({locality.species_latin_name for locality in self.direct_evidence})

    @property
    def record_modalities(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    modality
                    for locality in self.direct_evidence
                    for modality in locality.record_modalities
                }
            )
        )

    @property
    def review_strengths(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    strength
                    for locality in self.direct_evidence
                    for strength in locality.review_strengths
                }
            )
        )

    @property
    def provenance_qualities(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    quality
                    for locality in self.direct_evidence
                    for quality in locality.provenance_qualities
                }
            )
        )
