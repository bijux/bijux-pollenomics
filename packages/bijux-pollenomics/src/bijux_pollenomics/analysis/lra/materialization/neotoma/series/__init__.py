"""Bounded Neotoma candidate-series projection."""

from bijux_pollenomics.collection.sources.neotoma.relational.variables import (
    source_element_status,
)

from .projection import (
    MAX_OBSERVATIONS,
    MAX_SAMPLES,
    NeotomaCandidateSeries,
    build_neotoma_candidate_series,
)

__all__ = [
    "MAX_OBSERVATIONS",
    "MAX_SAMPLES",
    "NeotomaCandidateSeries",
    "build_neotoma_candidate_series",
    "source_element_status",
]
