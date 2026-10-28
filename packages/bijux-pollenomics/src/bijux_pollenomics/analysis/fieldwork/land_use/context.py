"""Summarize spatial and temporal context for declared fieldwork targets."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from bijux_pollenomics.adna.domain.locality import locality_sample_intervals

from .models import _Target as Target


def overlapping_geojson_context(
    *,
    target: Target,
    features: Iterable[Mapping[str, Any]],
    time_start_bp: int,
    time_end_bp: int,
    within_radius: Callable[..., bool],
    intervals_overlap: Callable[..., bool],
) -> dict[str, int]:
    """Count dated point features and locality references near the target."""
    records = []
    localities = set()
    for feature in features:
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        coordinates = geometry.get("coordinates", [])
        if geometry.get("type") != "Point" or len(coordinates) < 2:
            continue
        if not within_radius(
            target, latitude=float(coordinates[1]), longitude=float(coordinates[0])
        ):
            continue
        if not intervals_overlap(
            time_start_bp,
            time_end_bp,
            properties.get("time_start_bp"),
            properties.get("time_end_bp"),
        ):
            continue
        records.append(feature)
        localities.add(str(properties.get("source_url", "")))
    return {"record_count": len(records), "locality_count": len(localities)}


def overlapping_human_context(
    *,
    target: Target,
    localities: Iterable[Any],
    time_start_bp: int,
    time_end_bp: int,
    within_radius: Callable[..., bool],
    intervals_overlap: Callable[..., bool],
) -> dict[str, int]:
    """Count localities and samples with overlapping owned intervals."""
    matched_localities = 0
    matched_samples = 0
    for locality in localities:
        coordinates = locality.coordinates
        if not within_radius(
            target, latitude=coordinates.latitude, longitude=coordinates.longitude
        ):
            continue
        sample_ids = {
            sample_id
            for sample_id, interval in locality_sample_intervals(locality)
            if intervals_overlap(
                time_start_bp, time_end_bp, interval.younger_bp, interval.older_bp
            )
        }
        if sample_ids:
            matched_localities += 1
            matched_samples += len(sample_ids)
    return {"locality_count": matched_localities, "sample_count": matched_samples}


def overlapping_animal_context(
    *,
    target: Target,
    localities: Iterable[Mapping[str, Any]],
    time_start_bp: int,
    time_end_bp: int,
    within_radius: Callable[..., bool],
    intervals_overlap: Callable[..., bool],
    number: Callable[[Any], float],
) -> dict[str, int]:
    """Count animal localities and sample totals within the declared bounds."""
    matched = []
    for locality in localities:
        chronology = locality.get("chronology", {})
        if not within_radius(
            target,
            latitude=number(locality.get("latitude")),
            longitude=number(locality.get("longitude")),
        ):
            continue
        if intervals_overlap(
            time_start_bp,
            time_end_bp,
            chronology.get("time_start_bp"),
            chronology.get("time_end_bp"),
        ):
            matched.append(locality)
    return {
        "locality_count": len(matched),
        "sample_count": sum(
            int(locality.get("sample_count", 0)) for locality in matched
        ),
    }
