"""Complete source-family point loading for boundary review."""

from __future__ import annotations

from pathlib import Path

from ..models import JsonObject, PointEvidence
from .animal_adna import _load_animal_adna_points as _load_animal_adna_points
from .landclim import _load_landclim_points as _load_landclim_points
from .neotoma import _load_neotoma_points as _load_neotoma_points
from .sead import _load_sead_points as _load_sead_points


def _load_governed_points(
    root: Path,
) -> tuple[dict[str, list[PointEvidence]], dict[str, list[JsonObject]]]:
    loaders = (
        _load_neotoma_points,
        _load_landclim_points,
        _load_sead_points,
        _load_animal_adna_points,
    )
    points_by_source: dict[str, list[PointEvidence]] = {}
    artifacts_by_source: dict[str, list[JsonObject]] = {}
    for loader in loaders:
        source, points, artifacts = loader(root)
        if source in points_by_source:
            raise ValueError(f"Duplicate point source family: {source}")
        if not points:
            raise ValueError(f"Governed point source is empty: {source}")
        identifiers = [point.source_record_id for point in points]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(f"Duplicate point record identifiers: {source}")
        points_by_source[source] = points
        artifacts_by_source[source] = artifacts
    return points_by_source, artifacts_by_source
