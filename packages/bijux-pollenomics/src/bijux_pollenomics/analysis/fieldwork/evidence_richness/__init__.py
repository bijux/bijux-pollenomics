"""Evidence-richness modeling for Sweden lake fieldwork decisions."""

from .models import (
    DEFAULT_LAKE_EVIDENCE_RADII_KM,
    LakeEvidenceBandScore,
    LakeEvidenceCandidate,
    LakeEvidenceRichnessAssessment,
    LakeEvidenceRichnessReport,
    LakeEvidenceSourceAnchor,
)
from .service import build_sweden_lake_evidence_richness_report
from .temporal import _intervals_overlap as _intervals_overlap

__all__ = [
    "DEFAULT_LAKE_EVIDENCE_RADII_KM",
    "LakeEvidenceBandScore",
    "LakeEvidenceCandidate",
    "LakeEvidenceRichnessAssessment",
    "LakeEvidenceRichnessReport",
    "LakeEvidenceSourceAnchor",
    "build_sweden_lake_evidence_richness_report",
]
