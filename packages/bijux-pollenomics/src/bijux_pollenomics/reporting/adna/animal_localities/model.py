"""Public animal atlas bundle result and locality compatibility loader."""

from __future__ import annotations

from dataclasses import dataclass
from ....adna import AdnaLocalitySummary
from ..atlas_evidence_rows import (
    AnimalAtlasCoordinateReview,
    AnimalAtlasEvidenceRow,
)


@dataclass(frozen=True)
class AnimalAtlasBundle:
    point_layers: tuple[dict[str, object], ...]
    evidence_rows: tuple[AnimalAtlasEvidenceRow, ...]
    localities: tuple[AdnaLocalitySummary, ...]
    coordinate_review: AnimalAtlasCoordinateReview
    extra_artifacts: tuple[tuple[str, str], ...]
