"""Scientific aDNA value objects and locality semantics."""

from __future__ import annotations

from dataclasses import dataclass as dataclass

from ....core.temporal_semantics import (
    build_temporal_semantics as build_temporal_semantics,
)
from .chronology import AdnaChronology, AdnaCoordinate
from .evidence import AdnaCoordinateProvenanceRecord, AdnaSiteEvidenceRecord
from .identity import AdnaLocalityIdentity, AdnaSampleIdentity
from .localities import AdnaLocalitySummary
from .samples import AdnaSampleRecord
from .vocabularies import (
    ADNA_CHRONOLOGY_EVIDENCE_CLASSES,
    ADNA_CHRONOLOGY_PRECISION_POSTURES,
    ADNA_COORDINATE_CONFIDENCE,
    ADNA_COORDINATE_PROVENANCE_CLASSES,
    ADNA_DATING_BASES,
    ADNA_MAPPING_POSTURES,
)

__all__ = [
    "ADNA_CHRONOLOGY_EVIDENCE_CLASSES",
    "ADNA_CHRONOLOGY_PRECISION_POSTURES",
    "ADNA_COORDINATE_CONFIDENCE",
    "ADNA_COORDINATE_PROVENANCE_CLASSES",
    "ADNA_DATING_BASES",
    "ADNA_MAPPING_POSTURES",
    "AdnaChronology",
    "AdnaCoordinate",
    "AdnaCoordinateProvenanceRecord",
    "AdnaLocalityIdentity",
    "AdnaLocalitySummary",
    "AdnaSampleIdentity",
    "AdnaSampleRecord",
    "AdnaSiteEvidenceRecord",
]


def _preserve_pickle_module(*model_types: type[object]) -> None:
    for model_type in model_types:
        model_type.__module__ = __name__


_preserve_pickle_module(
    AdnaChronology,
    AdnaCoordinate,
    AdnaCoordinateProvenanceRecord,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
    AdnaSampleIdentity,
    AdnaSampleRecord,
    AdnaSiteEvidenceRecord,
)
