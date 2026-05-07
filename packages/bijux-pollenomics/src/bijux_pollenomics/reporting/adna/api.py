from __future__ import annotations

from ...adna import AdnaLocalitySummary, AdnaSampleRecord, summarize_sample_localities
from ..models import SchemaError
from .animal_localities import (
    AnimalAtlasBundle,
    build_tracked_animal_atlas_bundle,
    load_tracked_animal_localities,
)
from .homo_sapiens import (
    discover_anno_files,
    iter_samples_from_anno,
    load_country_samples,
)

__all__ = [
    "SchemaError",
    "AnimalAtlasBundle",
    "build_tracked_animal_atlas_bundle",
    "discover_anno_files",
    "iter_samples_from_anno",
    "load_country_samples",
    "load_tracked_animal_localities",
    "summarize_localities",
]


def summarize_localities(
    samples: list[AdnaSampleRecord],
) -> list[AdnaLocalitySummary]:
    """Summarize governed Homo sapiens report samples by locality."""
    return summarize_sample_localities(samples)
