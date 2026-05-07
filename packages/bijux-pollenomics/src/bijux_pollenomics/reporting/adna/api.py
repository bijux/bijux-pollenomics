from __future__ import annotations

from ...adna import AdnaLocalitySummary, AdnaSampleRecord, summarize_sample_localities
from ..models import SchemaError
from .animal_localities import (
    AnimalAtlasBundle,
    build_tracked_animal_atlas_bundle,
    load_tracked_animal_localities,
)
from .atlas_evidence_rows import (
    AnimalAtlasCoordinateReview,
    AnimalAtlasEvidenceRow,
    build_tracked_animal_atlas_coordinate_review,
    build_tracked_animal_atlas_evidence_rows,
    load_tracked_animal_mappable_localities,
)
from .country_outputs import (
    CountryAnimalOutputBundle,
    build_country_animal_output_bundle,
)
from .homo_sapiens import (
    discover_anno_files,
    iter_samples_from_anno,
    load_country_samples,
)

__all__ = [
    "SchemaError",
    "AnimalAtlasBundle",
    "AnimalAtlasCoordinateReview",
    "AnimalAtlasEvidenceRow",
    "CountryAnimalOutputBundle",
    "build_tracked_animal_atlas_bundle",
    "build_tracked_animal_atlas_coordinate_review",
    "build_tracked_animal_atlas_evidence_rows",
    "build_country_animal_output_bundle",
    "discover_anno_files",
    "iter_samples_from_anno",
    "load_country_samples",
    "load_tracked_animal_mappable_localities",
    "load_tracked_animal_localities",
    "summarize_localities",
]


def summarize_localities(
    samples: list[AdnaSampleRecord],
) -> list[AdnaLocalitySummary]:
    """Summarize governed Homo sapiens report samples by locality."""
    return summarize_sample_localities(samples)
