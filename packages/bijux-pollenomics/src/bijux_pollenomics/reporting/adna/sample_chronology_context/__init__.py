"""Source-native animal sample chronology reporting API."""

from __future__ import annotations

from pathlib import Path

from ...geography import GeographicScope
from .contracts import (
    AnimalChronologyInputIdentity,
    AnimalSampleChronologyContextProjection,
    AnimalSampleChronologyNode,
    AnimalSampleChronologyRefusal,
)
from .projection import project_animal_sample_chronology_context
from .repository import load_animal_sample_chronology_corpus

__all__ = [
    "AnimalChronologyInputIdentity",
    "AnimalSampleChronologyContextProjection",
    "AnimalSampleChronologyNode",
    "AnimalSampleChronologyRefusal",
    "animal_sample_chronology_context_available",
    "build_animal_sample_chronology_context",
]


def animal_sample_chronology_context_available(data_root: Path) -> bool:
    """Return whether the governed chronology corpus is declared in this data root."""
    registry_path = (
        Path(data_root)
        / "adna"
        / "governance"
        / "source_library"
        / "project_registry.json"
    )
    return registry_path.exists() or registry_path.is_symlink()


def build_animal_sample_chronology_context(
    data_root: Path,
    *,
    geography_scope: GeographicScope | None = None,
) -> AnimalSampleChronologyContextProjection:
    """Build a display-only projection from exact governed sample joins."""
    corpus = load_animal_sample_chronology_corpus(Path(data_root))
    return project_animal_sample_chronology_context(
        corpus,
        geography_scope=geography_scope,
    )
