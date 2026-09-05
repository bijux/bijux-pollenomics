"""Lake identity resolution and candidate construction."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
import re
from typing import TypedDict
import unicodedata

from bijux_pollenomics.core import (
    haversine_km,
)
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from .models import (
    LakeEvidenceCandidate,
    LakeEvidenceSourceAnchor,
    _COORDINATE_SPREAD_FLAG_KM,
    _ENGINEERED_WATER_TERMS,
    _GENERIC_LAKE_TOKENS,
    _LAKE_MATCH_DISTANCE_KM,
    _LAKE_NAME_TERMS,
    _LakeSourcePoint,
    _POSITION_NOTE_PATTERNS,
    _PointEvidence,
    _SvarLakeRecord,
    _WETLAND_TERMS,
)
from .metrics import (
    _weighted_average,
)
from .temporal import (
    _human_context_overlap_ratio,
    _time_aware_ratio,
    _validated_interval,
)

__all__ = []


class _LakeCandidateDraft(TypedDict):
    lake_name: str
    name_key: str
    lake_token: str
    latitude: float
    longitude: float
    basin_posture: str
    direct_pollen_source_count: int
    direct_pollen_record_count: int
    time_aware_direct_pollen_records: int
    pollen_sources: tuple[str, ...]
    supporting_pollen_names: tuple[str, ...]
    supporting_source_records: tuple[str, ...]
    supporting_source_points: tuple[LakeEvidenceSourceAnchor, ...]
    representative_source_record: str
    representative_source_layer_key: str
    representative_source_name: str
    representative_source_url: str
    coordinate_resolution_method: str
    coordinate_spread_km: float
    ambiguity_flags: list[str]
    position_notes: tuple[str, ...]
    direct_pollen_signal: float


class _SvarLakeCandidateDraft(_LakeCandidateDraft):
    lake_registry_id: str
    lake_registry_uuid: str
    lake_water_identity: str
    lake_name_status: str
    lake_area_km2: float | None
    lake_sampling_posture: str
    lake_sampling_fit: float
    lake_sampling_notes: tuple[str, ...]
    lake_sampling_readiness_posture: str
    lake_sampling_missing_inputs: tuple[str, ...]


def _derive_lake_candidates(
    pollen_points: Iterable[ContextPointRecord],
    *,
    neotoma_position_notes: dict[str, str],
) -> tuple[LakeEvidenceCandidate, ...]:
    lake_points: list[_LakeSourcePoint] = []
    for point in pollen_points:
        basin_posture = _resolve_basin_posture(point.name, point.description)
        if basin_posture != "lake_basin":
            continue
        name_key = _lake_name_key(point.name)
        if not name_key:
            continue
        position_note = (
            neotoma_position_notes.get(point.record_id)
            if point.layer_key == "neotoma-pollen"
            else None
        )
        lake_points.append(
            _LakeSourcePoint(
                point=point,
                name_key=name_key,
                cleaned_name=_clean_lake_name_display(point.name),
                source_record=f"{point.layer_key}:{point.record_id}",
                position_note=position_note,
            )
        )

    components = _build_lake_components(lake_points)
    provisional_candidates: list[_LakeCandidateDraft] = []
    for component in components:
        points = tuple(component)
        canonical_name = _choose_canonical_lake_name(points)
        representative_source_point = _choose_representative_source_point(points)
        representative_latitude = round(representative_source_point.point.latitude, 6)
        representative_longitude = round(representative_source_point.point.longitude, 6)
        pollen_sources = tuple(
            sorted({source_point.point.layer_key for source_point in points})
        )
        supporting_names = tuple(
            sorted({source_point.cleaned_name for source_point in points})
        )
        supporting_source_records = tuple(
            sorted({source_point.source_record for source_point in points})
        )
        supporting_source_points = tuple(
            sorted(
                (
                    LakeEvidenceSourceAnchor(
                        source_record=source_point.source_record,
                        source_name=source_point.cleaned_name,
                        source_layer_key=source_point.point.layer_key,
                        latitude=source_point.point.latitude,
                        longitude=source_point.point.longitude,
                        source_url=source_point.point.source_url,
                        time_start_bp=source_point.point.time_start_bp,
                        time_end_bp=source_point.point.time_end_bp,
                        time_mean_bp=source_point.point.time_mean_bp,
                        time_label=source_point.point.time_label,
                        temporal_semantics=source_point.point.temporal_semantics,
                    )
                    for source_point in points
                ),
                key=lambda source_point: (
                    source_point.source_name,
                    source_point.source_layer_key,
                    source_point.source_record,
                ),
            )
        )
        coordinate_spread_km = round(_max_pair_distance(points), 4)
        ambiguity_flags = list(_base_ambiguity_flags(points, coordinate_spread_km))
        position_notes = tuple(
            sorted(
                {
                    source_point.position_note
                    for source_point in points
                    if source_point.position_note
                }
            )
        )
        direct_pollen_signal = round(
            _weighted_average(
                (
                    min(1.0, len(pollen_sources) / 2.0),
                    0.35,
                ),
                (
                    min(1.0, len(points) / 4.0),
                    0.25,
                ),
                (
                    _time_aware_ratio(
                        tuple(source_point.point for source_point in points)
                    ),
                    0.2,
                ),
                (
                    1.0,
                    0.2,
                ),
            ),
            4,
        )
        provisional_candidates.append(
            {
                "lake_name": canonical_name,
                "name_key": _lake_name_key(canonical_name),
                "lake_token": _build_lake_token(
                    canonical_name,
                    latitude=representative_latitude,
                    longitude=representative_longitude,
                ),
                "latitude": representative_latitude,
                "longitude": representative_longitude,
                "basin_posture": "lake_basin",
                "direct_pollen_source_count": len(pollen_sources),
                "direct_pollen_record_count": len(points),
                "time_aware_direct_pollen_records": sum(
                    1
                    for source_point in points
                    if source_point.point.time_start_bp is not None
                    and source_point.point.time_end_bp is not None
                ),
                "pollen_sources": pollen_sources,
                "supporting_pollen_names": supporting_names,
                "supporting_source_records": supporting_source_records,
                "supporting_source_points": supporting_source_points,
                "representative_source_record": representative_source_point.source_record,
                "representative_source_layer_key": representative_source_point.point.layer_key,
                "representative_source_name": representative_source_point.cleaned_name,
                "representative_source_url": representative_source_point.point.source_url,
                "coordinate_resolution_method": _coordinate_resolution_method(points),
                "coordinate_spread_km": coordinate_spread_km,
                "ambiguity_flags": ambiguity_flags,
                "position_notes": position_notes,
                "direct_pollen_signal": direct_pollen_signal,
            }
        )

    duplicate_name_counts = Counter(
        candidate["name_key"]
        for candidate in provisional_candidates
        if candidate["name_key"]
    )
    candidates: list[LakeEvidenceCandidate] = []
    for candidate in provisional_candidates:
        ambiguity_flags = list(candidate["ambiguity_flags"])
        duplicate_name_count = duplicate_name_counts[candidate["name_key"]]
        if duplicate_name_count > 1 and "duplicate_sweden_name" not in ambiguity_flags:
            ambiguity_flags.append("duplicate_sweden_name")
        ambiguity_flags = sorted(set(ambiguity_flags))
        lake_name = str(candidate["lake_name"])
        latitude = float(candidate["latitude"])
        longitude = float(candidate["longitude"])
        candidates.append(
            LakeEvidenceCandidate(
                lake_name=lake_name,
                lake_label=_build_lake_label(
                    lake_name,
                    latitude=latitude,
                    longitude=longitude,
                    duplicate_name_count=duplicate_name_count,
                    ambiguity_flags=tuple(ambiguity_flags),
                ),
                lake_token=str(candidate["lake_token"]),
                name_key=str(candidate["name_key"]),
                latitude=latitude,
                longitude=longitude,
                basin_posture=str(candidate["basin_posture"]),
                direct_pollen_source_count=int(candidate["direct_pollen_source_count"]),
                direct_pollen_record_count=int(candidate["direct_pollen_record_count"]),
                time_aware_direct_pollen_records=int(
                    candidate["time_aware_direct_pollen_records"]
                ),
                pollen_sources=candidate["pollen_sources"],
                supporting_pollen_names=candidate["supporting_pollen_names"],
                supporting_source_records=candidate["supporting_source_records"],
                supporting_source_points=candidate["supporting_source_points"],
                representative_source_record=str(
                    candidate["representative_source_record"]
                ),
                representative_source_layer_key=str(
                    candidate["representative_source_layer_key"]
                ),
                representative_source_name=str(candidate["representative_source_name"]),
                representative_source_url=str(candidate["representative_source_url"]),
                coordinate_resolution_method=str(
                    candidate["coordinate_resolution_method"]
                ),
                duplicate_name_count=duplicate_name_count,
                coordinate_spread_km=float(candidate["coordinate_spread_km"]),
                ambiguity_flags=tuple(ambiguity_flags),
                ambiguity_note=_build_ambiguity_note(
                    duplicate_name_count=duplicate_name_count,
                    coordinate_spread_km=float(candidate["coordinate_spread_km"]),
                    ambiguity_flags=tuple(ambiguity_flags),
                    position_notes=candidate["position_notes"],
                ),
                direct_pollen_signal=float(candidate["direct_pollen_signal"]),
            )
        )
    return tuple(sorted(candidates, key=lambda candidate: candidate.lake_label))


def _derive_svar_lake_candidates(
    svar_lakes: Sequence[_SvarLakeRecord],
    *,
    pollen_points: Sequence[ContextPointRecord],
    neotoma_position_notes: dict[str, str],
    human_points: Sequence[_PointEvidence],
) -> tuple[LakeEvidenceCandidate, ...]:
    del neotoma_position_notes
    lake_basin_pollen_points = tuple(
        point
        for point in pollen_points
        if _resolve_basin_posture(point.name, point.description) == "lake_basin"
    )
    provisional_candidates: list[_SvarLakeCandidateDraft] = []
    for lake in svar_lakes:
        if lake.lake_name_status in {"fallback_waterwebb_label", "unnamed"}:
            continue
        lake_sampling_posture, lake_sampling_notes = _classify_sampling_lake(
            lake.lake_name,
            lake_area_km2=lake.lake_area_km2,
        )
        if lake_sampling_posture in {
            "engineered_waterbody_excluded",
            "wetland_context_excluded",
        }:
            continue
        nearest_human_distance = min(
            (
                haversine_km(
                    latitude_a=lake.latitude,
                    longitude_a=lake.longitude,
                    latitude_b=point.latitude,
                    longitude_b=point.longitude,
                )
                for point in human_points
            ),
            default=None,
        )
        if nearest_human_distance is None or nearest_human_distance > 50:
            continue
        direct_pollen_points = tuple(
            point
            for point in lake_basin_pollen_points
            if _is_direct_lake_pollen_match(lake, point)
        )
        pollen_sources = tuple(
            sorted({point.layer_key for point in direct_pollen_points})
        )
        supporting_pollen_names = tuple(
            sorted(
                {_clean_lake_name_display(point.name) for point in direct_pollen_points}
            )
        )
        supporting_source_records = tuple(
            sorted(
                {
                    f"svar-lakes:{lake.lake_registry_id or lake.lake_registry_uuid or lake.lake_token}",
                    *(
                        f"{point.layer_key}:{point.record_id}"
                        for point in direct_pollen_points
                    ),
                }
            )
        )
        supporting_source_points = (
            LakeEvidenceSourceAnchor(
                source_record=(
                    f"svar-lakes:{lake.lake_registry_id or lake.lake_registry_uuid or lake.lake_token}"
                ),
                source_name=lake.lake_name,
                source_layer_key="svar-lakes",
                latitude=lake.latitude,
                longitude=lake.longitude,
                source_url=lake.source_url,
            ),
            *sorted(
                (
                    LakeEvidenceSourceAnchor(
                        source_record=f"{point.layer_key}:{point.record_id}",
                        source_name=_clean_lake_name_display(point.name),
                        source_layer_key=point.layer_key,
                        latitude=point.latitude,
                        longitude=point.longitude,
                        source_url=point.source_url,
                        time_start_bp=point.time_start_bp,
                        time_end_bp=point.time_end_bp,
                        time_mean_bp=point.time_mean_bp,
                        time_label=point.time_label,
                        temporal_semantics=point.temporal_semantics,
                    )
                    for point in direct_pollen_points
                ),
                key=lambda source_point: (
                    source_point.source_name,
                    source_point.source_layer_key,
                    source_point.source_record,
                ),
            ),
        )
        ambiguity_flags: list[str] = []
        if lake.lake_name_status and lake.lake_name_status not in {
            "official_register_name",
            "water_surface_name",
        }:
            ambiguity_flags.append("non_official_registry_name")
        lake_sampling_fit = _lake_sampling_fit(
            lake_area_km2=lake.lake_area_km2,
            lake_sampling_posture=lake_sampling_posture,
        )
        nearby_human_points = tuple(
            point
            for point in human_points
            if haversine_km(
                latitude_a=lake.latitude,
                longitude_a=lake.longitude,
                latitude_b=point.latitude,
                longitude_b=point.longitude,
            )
            <= 50
        )
        direct_pollen_signal = round(
            _weighted_average(
                (min(1.0, len(pollen_sources) / 2.0), 0.3),
                (min(1.0, len(direct_pollen_points) / 4.0), 0.25),
                (_time_aware_ratio(direct_pollen_points), 0.15),
                (
                    _human_context_overlap_ratio(
                        direct_pollen_points,
                        nearby_human_points,
                    ),
                    0.2,
                ),
                (1.0 if direct_pollen_points else 0.0, 0.1),
            ),
            4,
        )
        provisional_candidates.append(
            {
                "lake_name": lake.lake_name,
                "name_key": lake.name_key,
                "lake_token": (
                    f"sweden_lake_registry:{lake.lake_registry_id}"
                    if lake.lake_registry_id
                    else lake.lake_token
                ),
                "latitude": lake.latitude,
                "longitude": lake.longitude,
                "basin_posture": "lake_basin",
                "direct_pollen_source_count": len(pollen_sources),
                "direct_pollen_record_count": len(direct_pollen_points),
                "time_aware_direct_pollen_records": sum(
                    1
                    for point in direct_pollen_points
                    if _validated_interval(point.time_start_bp, point.time_end_bp)
                    is not None
                ),
                "pollen_sources": pollen_sources,
                "supporting_pollen_names": supporting_pollen_names,
                "supporting_source_records": supporting_source_records,
                "supporting_source_points": supporting_source_points,
                "representative_source_record": (
                    f"svar-lakes:{lake.lake_registry_id or lake.lake_registry_uuid or lake.lake_token}"
                ),
                "representative_source_layer_key": "svar-lakes",
                "representative_source_name": lake.lake_name,
                "representative_source_url": lake.source_url,
                "coordinate_resolution_method": "svar_polygon_representative_point",
                "coordinate_spread_km": 0.0,
                "ambiguity_flags": ambiguity_flags,
                "position_notes": (),
                "direct_pollen_signal": direct_pollen_signal,
                "lake_registry_id": lake.lake_registry_id,
                "lake_registry_uuid": lake.lake_registry_uuid,
                "lake_water_identity": lake.lake_water_identity,
                "lake_name_status": lake.lake_name_status,
                "lake_area_km2": lake.lake_area_km2,
                "lake_sampling_posture": lake_sampling_posture,
                "lake_sampling_fit": lake_sampling_fit,
                "lake_sampling_notes": lake_sampling_notes,
                "lake_sampling_readiness_posture": lake.lake_sampling_readiness_posture,
                "lake_sampling_missing_inputs": lake.lake_sampling_missing_inputs,
            }
        )

    duplicate_name_counts = Counter(
        candidate["name_key"]
        for candidate in provisional_candidates
        if candidate["name_key"]
    )
    candidates: list[LakeEvidenceCandidate] = []
    for candidate in provisional_candidates:
        ambiguity_flags = list(candidate["ambiguity_flags"])
        duplicate_name_count = duplicate_name_counts[str(candidate["name_key"])]
        if duplicate_name_count > 1 and "duplicate_sweden_name" not in ambiguity_flags:
            ambiguity_flags.append("duplicate_sweden_name")
        ambiguity_flags = sorted(set(ambiguity_flags))
        lake_name = str(candidate["lake_name"])
        latitude = float(candidate["latitude"])
        longitude = float(candidate["longitude"])
        candidates.append(
            LakeEvidenceCandidate(
                lake_name=lake_name,
                lake_label=_build_lake_label(
                    lake_name,
                    latitude=latitude,
                    longitude=longitude,
                    duplicate_name_count=duplicate_name_count,
                    ambiguity_flags=tuple(ambiguity_flags),
                ),
                lake_token=str(candidate["lake_token"]),
                name_key=str(candidate["name_key"]),
                latitude=latitude,
                longitude=longitude,
                basin_posture=str(candidate["basin_posture"]),
                direct_pollen_source_count=int(candidate["direct_pollen_source_count"]),
                direct_pollen_record_count=int(candidate["direct_pollen_record_count"]),
                time_aware_direct_pollen_records=int(
                    candidate["time_aware_direct_pollen_records"]
                ),
                pollen_sources=candidate["pollen_sources"],
                supporting_pollen_names=candidate["supporting_pollen_names"],
                supporting_source_records=candidate["supporting_source_records"],
                supporting_source_points=candidate["supporting_source_points"],
                representative_source_record=str(
                    candidate["representative_source_record"]
                ),
                representative_source_layer_key=str(
                    candidate["representative_source_layer_key"]
                ),
                representative_source_name=str(candidate["representative_source_name"]),
                representative_source_url=str(candidate["representative_source_url"]),
                coordinate_resolution_method=str(
                    candidate["coordinate_resolution_method"]
                ),
                duplicate_name_count=duplicate_name_count,
                coordinate_spread_km=float(candidate["coordinate_spread_km"]),
                ambiguity_flags=tuple(ambiguity_flags),
                ambiguity_note=_build_ambiguity_note(
                    duplicate_name_count=duplicate_name_count,
                    coordinate_spread_km=float(candidate["coordinate_spread_km"]),
                    ambiguity_flags=tuple(ambiguity_flags),
                    position_notes=candidate["position_notes"],
                    lake_name_status=str(candidate["lake_name_status"]),
                ),
                direct_pollen_signal=float(candidate["direct_pollen_signal"]),
                lake_registry_id=str(candidate["lake_registry_id"]),
                lake_registry_uuid=str(candidate["lake_registry_uuid"]),
                lake_water_identity=str(candidate["lake_water_identity"]),
                lake_name_status=str(candidate["lake_name_status"]),
                lake_area_km2=float(candidate["lake_area_km2"])
                if isinstance(candidate["lake_area_km2"], (int, float))
                else None,
                lake_sampling_posture=str(candidate["lake_sampling_posture"]),
                lake_sampling_fit=float(candidate["lake_sampling_fit"]),
                lake_sampling_notes=candidate["lake_sampling_notes"],
                lake_sampling_readiness_posture=str(
                    candidate["lake_sampling_readiness_posture"]
                ),
                lake_sampling_missing_inputs=candidate["lake_sampling_missing_inputs"],
            )
        )
    return tuple(sorted(candidates, key=lambda candidate: candidate.lake_label))


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


def _base_ambiguity_flags(
    points: Sequence[_LakeSourcePoint], coordinate_spread_km: float
) -> tuple[str, ...]:
    flags: set[str] = set()
    if len({source_point.cleaned_name for source_point in points}) > 1:
        flags.add("source_name_variants")
    if coordinate_spread_km >= _COORDINATE_SPREAD_FLAG_KM:
        flags.add("source_coordinate_spread")
    if any(source_point.position_note for source_point in points):
        flags.add("source_position_note")
    return tuple(sorted(flags))


def _build_lake_label(
    lake_name: str,
    *,
    latitude: float,
    longitude: float,
    duplicate_name_count: int,
    ambiguity_flags: tuple[str, ...],
) -> str:
    if duplicate_name_count > 1 or ambiguity_flags:
        return f"{lake_name} ({latitude:.6f}, {longitude:.6f})"
    return lake_name


def _build_ambiguity_note(
    *,
    duplicate_name_count: int,
    coordinate_spread_km: float,
    ambiguity_flags: tuple[str, ...],
    position_notes: tuple[str, ...],
    lake_name_status: str = "",
) -> str:
    parts: list[str] = []
    if "duplicate_sweden_name" in ambiguity_flags:
        parts.append(
            f"{duplicate_name_count} Sweden candidates share this cleaned lake name."
        )
    if "source_coordinate_spread" in ambiguity_flags:
        parts.append(
            f"Source coordinates span {coordinate_spread_km:.2f} km inside this candidate."
        )
    if "source_name_variants" in ambiguity_flags:
        parts.append(
            "Source records use more than one lake name form for this candidate."
        )
    if "non_official_registry_name" in ambiguity_flags and lake_name_status:
        parts.append(
            "Lake naming falls back to a non-register registry label "
            f"({lake_name_status})."
        )
    if "source_position_note" in ambiguity_flags and position_notes:
        parts.append(position_notes[0])
    return " ".join(parts)


def _classify_sampling_lake(
    lake_name: str,
    *,
    lake_area_km2: float | None,
) -> tuple[str, tuple[str, ...]]:
    normalized_name = _normalize_text(lake_name)
    has_lake_term = any(term in normalized_name for term in _LAKE_NAME_TERMS)
    has_wetland_term = any(term in normalized_name for term in _WETLAND_TERMS)
    has_engineered_term = any(
        term in normalized_name for term in _ENGINEERED_WATER_TERMS
    )
    notes: list[str] = []
    if has_wetland_term and not has_lake_term:
        notes.append("registry name points to a wetland-style basin rather than a lake")
        return ("wetland_context_excluded", tuple(notes))
    if has_engineered_term and not has_lake_term:
        notes.append(
            "registry name points to an engineered water body rather than a natural lake"
        )
        return ("engineered_waterbody_excluded", tuple(notes))
    if lake_area_km2 is not None and lake_area_km2 < 0.05:
        notes.append(
            "very small mapped water surface; treat as a micro-basin until field validation confirms suitability"
        )
        return ("small_lake_review", tuple(notes))
    if lake_area_km2 is not None and lake_area_km2 < 0.15:
        notes.append(
            "small mapped water surface; prefer checking basin depth and access before field planning"
        )
        return ("compact_lake_candidate", tuple(notes))
    return ("sampling_lake_candidate", tuple(notes))


def _lake_sampling_fit(
    *,
    lake_area_km2: float | None,
    lake_sampling_posture: str,
) -> float:
    if lake_sampling_posture in {
        "engineered_waterbody_excluded",
        "wetland_context_excluded",
    }:
        return 0.0
    if lake_area_km2 is None:
        area_score = 0.7
    elif lake_area_km2 < 0.03:
        area_score = 0.15
    elif lake_area_km2 < 0.05:
        area_score = 0.3
    elif lake_area_km2 < 0.15:
        area_score = 0.55
    elif lake_area_km2 < 0.5:
        area_score = 0.78
    elif lake_area_km2 < 20:
        area_score = 1.0
    else:
        area_score = 0.9
    posture_score = {
        "small_lake_review": 0.45,
        "compact_lake_candidate": 0.75,
        "sampling_lake_candidate": 1.0,
    }.get(lake_sampling_posture, 0.6)
    return round(_weighted_average((area_score, 0.6), (posture_score, 0.4)), 4)


def _resolve_basin_posture(name: str, description: str) -> str:
    normalized_name = _normalize_text(name)
    normalized_description = _normalize_text(description)
    if any(
        term in normalized_name or term in normalized_description
        for term in _LAKE_NAME_TERMS
    ):
        return "lake_basin"
    if any(
        term in normalized_name or term in normalized_description
        for term in _WETLAND_TERMS
    ):
        return "wetland_basin"
    return "ambiguous_basin"


def _build_lake_token(name: str, *, latitude: float, longitude: float) -> str:
    return (
        f"sweden_lake:{_lake_name_key(name)}:{round(latitude, 6)}:{round(longitude, 6)}"
    )


def _lake_name_key(value: str) -> str:
    tokens = _tokenize_lake_name(value)
    while tokens and (tokens[0] in _GENERIC_LAKE_TOKENS or len(tokens[0]) == 1):
        tokens = tokens[1:]
    return "".join(tokens)


def _tokenize_lake_name(value: str) -> list[str]:
    normalized = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    return [token for token in re.findall(r"[a-z0-9]+", normalized.casefold()) if token]


def _clean_lake_name_display(value: str) -> str:
    cleaned = re.sub(r"^\s*lake\s+", "", value, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\s*[A-Za-zÅÄÖåäö]\.\s+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -")
    return cleaned or value.strip()


def _lake_name_source_priority(layer_key: str) -> int:
    priorities = {
        "landclim-sites": 3,
        "neotoma-pollen": 2,
    }
    return priorities.get(layer_key, 0)


def _name_has_non_ascii(value: str) -> int:
    return 1 if any(ord(character) > 127 for character in value) else 0


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


def _normalize_text(value: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    return re.sub(r"[^a-z0-9]+", "", normalized.casefold())


def _normalize_note_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\r", " ").replace("\n", " ")).strip()


def _note_signals_position_uncertainty(note: str) -> bool:
    return any(pattern.search(note) for pattern in _POSITION_NOTE_PATTERNS)


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
