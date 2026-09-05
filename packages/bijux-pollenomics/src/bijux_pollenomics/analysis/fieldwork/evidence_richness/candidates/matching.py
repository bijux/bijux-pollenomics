"""Resolve source records into stable lake identities and coordinates."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.core import haversine_km
from ..models import (
    _LAKE_MATCH_DISTANCE_KM,
    _LakeSourcePoint,
    _SvarLakeRecord,
)
from .naming import (
    _lake_name_key,
    _lake_name_source_priority,
    _name_has_non_ascii,
)

__all__ = []


def _build_lake_components(
    lake_points: Sequence[_LakeSourcePoint],
) -> tuple[tuple[_LakeSourcePoint, ...], ...]:
    components: list[tuple[_LakeSourcePoint, ...]] = []
    visited: set[int] = set()
    adjacency = {
        index: {
            other_index
            for other_index in range(len(lake_points))
            if other_index != index
            and _lake_points_match(lake_points[index], lake_points[other_index])
        }
        for index in range(len(lake_points))
    }
    for index in range(len(lake_points)):
        if index in visited:
            continue
        stack = [index]
        component_indexes: list[int] = []
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            component_indexes.append(current)
            stack.extend(adjacency[current] - visited)
        components.append(
            tuple(
                sorted(
                    (lake_points[item] for item in component_indexes),
                    key=lambda source_point: (
                        source_point.cleaned_name,
                        source_point.point.layer_key,
                        source_point.point.record_id,
                    ),
                )
            )
        )
    return tuple(components)


def _lake_points_match(left: _LakeSourcePoint, right: _LakeSourcePoint) -> bool:
    if left.name_key != right.name_key:
        return False
    return (
        haversine_km(
            latitude_a=left.point.latitude,
            longitude_a=left.point.longitude,
            latitude_b=right.point.latitude,
            longitude_b=right.point.longitude,
        )
        <= _LAKE_MATCH_DISTANCE_KM
    )


def _choose_canonical_lake_name(points: Sequence[_LakeSourcePoint]) -> str:
    cleaned_counts = Counter(source_point.cleaned_name for source_point in points)
    best = max(
        points,
        key=lambda source_point: (
            _name_has_non_ascii(source_point.cleaned_name),
            cleaned_counts[source_point.cleaned_name],
            _lake_name_source_priority(source_point.point.layer_key),
            len(source_point.cleaned_name),
            source_point.cleaned_name,
        ),
    )
    return best.cleaned_name


def _choose_representative_source_point(
    points: Sequence[_LakeSourcePoint],
) -> _LakeSourcePoint:
    coordinate_counts = Counter(
        (
            round(source_point.point.latitude, 6),
            round(source_point.point.longitude, 6),
        )
        for source_point in points
    )
    return min(
        points,
        key=lambda source_point: (
            -coordinate_counts[
                (
                    round(source_point.point.latitude, 6),
                    round(source_point.point.longitude, 6),
                )
            ],
            _total_distance_to_component(source_point, points),
            -_lake_name_source_priority(source_point.point.layer_key),
            -_name_has_non_ascii(source_point.cleaned_name),
            source_point.cleaned_name,
            source_point.source_record,
        ),
    )


def _total_distance_to_component(
    anchor: _LakeSourcePoint,
    points: Sequence[_LakeSourcePoint],
) -> float:
    return round(
        sum(
            haversine_km(
                latitude_a=anchor.point.latitude,
                longitude_a=anchor.point.longitude,
                latitude_b=other.point.latitude,
                longitude_b=other.point.longitude,
            )
            for other in points
        ),
        6,
    )


def _coordinate_resolution_method(points: Sequence[_LakeSourcePoint]) -> str:
    unique_coordinates = {
        (
            round(source_point.point.latitude, 6),
            round(source_point.point.longitude, 6),
        )
        for source_point in points
    }
    if len(unique_coordinates) == 1:
        return "shared_source_coordinate"
    return "source_coordinate_medoid"


def _max_pair_distance(points: Sequence[_LakeSourcePoint]) -> float:
    maximum = 0.0
    for left_index, left in enumerate(points):
        for right in points[left_index + 1 :]:
            maximum = max(
                maximum,
                haversine_km(
                    latitude_a=left.point.latitude,
                    longitude_a=left.point.longitude,
                    latitude_b=right.point.latitude,
                    longitude_b=right.point.longitude,
                ),
            )
    return maximum


def _is_direct_lake_pollen_match(
    lake: _SvarLakeRecord,
    point: ContextPointRecord,
) -> bool:
    distance_km = haversine_km(
        latitude_a=lake.latitude,
        longitude_a=lake.longitude,
        latitude_b=point.latitude,
        longitude_b=point.longitude,
    )
    point_name_key = _lake_name_key(point.name)
    if point_name_key and point_name_key == lake.name_key and distance_km <= 10:
        return True
    return distance_km <= _LAKE_MATCH_DISTANCE_KM
