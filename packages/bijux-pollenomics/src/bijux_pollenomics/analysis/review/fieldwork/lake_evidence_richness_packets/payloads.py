from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceRichnessReport,
)

from .candidate_features import (
    _build_candidate_features,
)


def build_lake_evidence_richness_payload(
    report: LakeEvidenceRichnessReport,
) -> dict[str, object]:
    """Build the machine-readable lake evidence richness payload."""
    return report.as_dict()


def build_lake_evidence_richness_geojson(
    report: LakeEvidenceRichnessReport,
) -> dict[str, object]:
    """Build one GeoJSON feature collection for all Sweden lake candidates."""
    return {
        "type": "FeatureCollection",
        "features": [
            feature
            for assessment in report.assessments
            for feature in _build_candidate_features(assessment)
        ],
    }


def write_lake_evidence_richness_json(
    path: Path,
    report: LakeEvidenceRichnessReport,
) -> None:
    """Write one JSON payload describing Sweden lake evidence richness."""
    path.write_text(
        json.dumps(build_lake_evidence_richness_payload(report), indent=2),
        encoding="utf-8",
    )


def write_lake_evidence_richness_geojson(
    path: Path,
    report: LakeEvidenceRichnessReport,
) -> None:
    """Write one GeoJSON feature collection for Sweden lake candidates."""
    path.write_text(
        json.dumps(build_lake_evidence_richness_geojson(report), indent=2),
        encoding="utf-8",
    )
