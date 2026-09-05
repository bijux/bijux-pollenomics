"""Construct fieldwork candidates from the governed Sweden lake registry."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.core import haversine_km
from ..metrics import _weighted_average
from ..models import (
    LakeEvidenceCandidate,
    LakeEvidenceSourceAnchor,
    _PointEvidence,
    _SvarLakeRecord,
)
from ..temporal import (
    _human_context_overlap_ratio,
    _time_aware_ratio,
    _validated_interval,
)
from .matching import _is_direct_lake_pollen_match
from .naming import _clean_lake_name_display, _resolve_basin_posture
from .pollen import _LakeCandidateDraft
from .sampling import _classify_sampling_lake, _lake_sampling_fit
from .uncertainty import _build_ambiguity_note, _build_lake_label

__all__ = []


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
