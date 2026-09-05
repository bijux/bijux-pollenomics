"""Construct lake candidates from pollen-source evidence."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import TypedDict

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from ..metrics import _weighted_average
from ..models import (
    LakeEvidenceCandidate,
    LakeEvidenceSourceAnchor,
    _LakeSourcePoint,
)
from ..temporal import _time_aware_ratio
from .matching import (
    _build_lake_components,
    _choose_canonical_lake_name,
    _choose_representative_source_point,
    _coordinate_resolution_method,
    _max_pair_distance,
)
from .naming import (
    _build_lake_token,
    _clean_lake_name_display,
    _lake_name_key,
    _resolve_basin_posture,
)
from .uncertainty import (
    _base_ambiguity_flags,
    _build_ambiguity_note,
    _build_lake_label,
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
