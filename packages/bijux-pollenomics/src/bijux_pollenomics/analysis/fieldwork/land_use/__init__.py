from __future__ import annotations

import json
from pathlib import Path

from ....core import haversine_km
from ....core.temporal_semantics import (
    InvalidBpIntervalError,
    canonical_bp_interval,
    closed_bp_intervals_overlap,
)
from .context import (
    overlapping_animal_context,
    overlapping_geojson_context,
    overlapping_human_context,
)
from .inputs import load_features, target_landclim_features
from .interpretation import cross_proxy_posture, number
from .models import (
    CONTEXT_RADIUS_KM,
    GOVERNED_NAMED_TARGETS,
    HOJEA_REPORT_URL,
    LANDCLIM_DATASET_ID,
)
from .models import (
    _Target as _Target,
)
from .outputs import render_markdown, write_csv, write_json
from .spatial import polygon_contains, within_radius
from .synthesis import build_synthesis
from .targets import synthesis_targets, target_row
from .temporal import intervals_overlap

__all__ = [
    "build_sweden_land_use_synthesis",
    "render_sweden_land_use_synthesis_markdown",
    "write_sweden_land_use_synthesis_csv",
    "write_sweden_land_use_synthesis_json",
]

_LANDCLIM_DATASET_ID = LANDCLIM_DATASET_ID
_CONTEXT_RADIUS_KM = CONTEXT_RADIUS_KM
_HOJEA_REPORT_URL = HOJEA_REPORT_URL
_GOVERNED_NAMED_TARGETS = GOVERNED_NAMED_TARGETS
_Target.__module__ = __name__


def build_sweden_land_use_synthesis(  # type: ignore[no-untyped-def]
    *,
    context_root: Path,
    lake_report,
    human_localities,
    animal_localities,
) -> dict[str, object]:
    """Join modeled land cover with time-compatible governed context near targets."""
    return build_synthesis(
        context_root=Path(context_root),
        lake_report=lake_report,
        human_localities=human_localities,
        animal_localities=animal_localities,
        load_features=_load_features,
        synthesis_targets=_synthesis_targets,
        target_landclim_features=_target_landclim_features,
        target_row=_target_row,
        overlapping_geojson_context=_overlapping_geojson_context,
        overlapping_human_context=_overlapping_human_context,
        overlapping_animal_context=_overlapping_animal_context,
        number=_number,
        cross_proxy_posture=_cross_proxy_posture,
        dataset_id=_LANDCLIM_DATASET_ID,
        context_radius_km=_CONTEXT_RADIUS_KM,
    )


def write_sweden_land_use_synthesis_json(
    path: Path, payload: dict[str, object]
) -> None:
    write_json(path, payload, json_module=json)


def write_sweden_land_use_synthesis_csv(path: Path, payload: dict[str, object]) -> None:
    write_csv(path, payload)


def render_sweden_land_use_synthesis_markdown(payload: dict[str, object]) -> str:
    return render_markdown(payload)


def _synthesis_targets(lake_report) -> tuple[_Target, ...]:  # type: ignore[no-untyped-def]
    return synthesis_targets(
        lake_report,
        governed_named_targets=_GOVERNED_NAMED_TARGETS,
        target_type=_Target,
    )


def _target_row(  # type: ignore[no-untyped-def]
    target: _Target,
    *,
    lake_candidates,
    landclim_features: list[dict[str, object]],
) -> dict[str, object]:
    return target_row(
        target,
        lake_candidates=lake_candidates,
        landclim_features=landclim_features,
        distance_km=haversine_km,
        context_report_url=_HOJEA_REPORT_URL,
    )


def _load_features(path: Path) -> list[dict[str, object]]:
    return load_features(path, json_module=json)


def _target_landclim_features(
    target: _Target, features: list[dict[str, object]]
) -> list[dict[str, object]]:
    return target_landclim_features(
        target,
        features,
        dataset_id=_LANDCLIM_DATASET_ID,
        contains=_polygon_contains,
    )


def _polygon_contains(geometry, *, longitude: float, latitude: float) -> bool:  # type: ignore[no-untyped-def]
    return polygon_contains(geometry, longitude=longitude, latitude=latitude)


def _overlapping_geojson_context(  # type: ignore[no-untyped-def]
    *, target: _Target, features, time_start_bp: int, time_end_bp: int
) -> dict[str, int]:
    return overlapping_geojson_context(
        target=target,
        features=features,
        time_start_bp=time_start_bp,
        time_end_bp=time_end_bp,
        within_radius=_within_radius,
        intervals_overlap=_intervals_overlap,
    )


def _overlapping_human_context(  # type: ignore[no-untyped-def]
    *, target: _Target, localities, time_start_bp: int, time_end_bp: int
) -> dict[str, int]:
    return overlapping_human_context(
        target=target,
        localities=localities,
        time_start_bp=time_start_bp,
        time_end_bp=time_end_bp,
        within_radius=_within_radius,
        intervals_overlap=_intervals_overlap,
    )


def _overlapping_animal_context(  # type: ignore[no-untyped-def]
    *, target: _Target, localities, time_start_bp: int, time_end_bp: int
) -> dict[str, int]:
    return overlapping_animal_context(
        target=target,
        localities=localities,
        time_start_bp=time_start_bp,
        time_end_bp=time_end_bp,
        within_radius=_within_radius,
        intervals_overlap=_intervals_overlap,
        number=_number,
    )


def _within_radius(target: _Target, *, latitude: float, longitude: float) -> bool:
    return within_radius(
        target,
        latitude=latitude,
        longitude=longitude,
        distance_km=haversine_km,
        context_radius_km=_CONTEXT_RADIUS_KM,
    )


def _intervals_overlap(
    start_a: float | int | None,
    end_a: float | int | None,
    start_b: float | int | None,
    end_b: float | int | None,
) -> bool:
    return intervals_overlap(
        start_a,
        end_a,
        start_b,
        end_b,
        canonical_interval=canonical_bp_interval,
        invalid_interval_error=InvalidBpIntervalError,
        closed_intervals_overlap=closed_bp_intervals_overlap,
    )


def _cross_proxy_posture(
    *, sead_count: int, human_count: int, animal_count: int
) -> str:
    return cross_proxy_posture(
        sead_count=sead_count,
        human_count=human_count,
        animal_count=animal_count,
    )


def _number(value) -> float:  # type: ignore[no-untyped-def]
    return number(value)
