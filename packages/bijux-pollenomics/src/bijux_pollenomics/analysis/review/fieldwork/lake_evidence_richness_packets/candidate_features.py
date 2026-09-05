from __future__ import annotations

import json

from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceCandidate,
    LakeEvidenceRichnessAssessment,
    LakeEvidenceSourceAnchor,
)

from .presentation import (
    _candidate_description,
    _candidate_media_links,
    _render_ambiguity_cell,
)
from ..lake_fieldwork_priority import band_score as _band_score


def _build_candidate_features(
    assessment: LakeEvidenceRichnessAssessment,
) -> list[dict[str, object]]:
    candidate = assessment.candidate
    temporal_sources = _candidate_temporal_sources(candidate)
    sources = temporal_sources or (None,)
    return [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [candidate.longitude, candidate.latitude],
            },
            "properties": {
                "source": "bijux-pollenomics",
                "layer_key": "lake-evidence-candidates",
                "layer_label": "Sweden lake evidence candidates",
                "category": "Lake evidence candidate",
                "country": "Sweden",
                "record_id": _temporal_record_id(candidate, source_point),
                "name": candidate.lake_label,
                "geometry_type": "Point",
                "subtitle": "Sweden lake evidence candidate",
                "description": candidate.ambiguity_note
                or _candidate_description(candidate),
                "source_url": candidate.representative_source_url,
                "record_count": 1,
                "media_links": _candidate_media_links(candidate),
                "popup_rows": [
                    *_candidate_popup_rows(assessment),
                    *_temporal_popup_rows(source_point),
                ],
                **_temporal_properties(source_point),
            },
        }
        for source_point in sources
    ]


def _candidate_popup_rows(
    assessment: LakeEvidenceRichnessAssessment,
) -> list[dict[str, str]]:
    candidate = assessment.candidate
    return [
        {"label": "Aggregate rank", "value": str(assessment.aggregate_rank)},
        {"label": "Aggregate score", "value": f"{assessment.aggregate_score:.4f}"},
        {
            "label": "Coordinates",
            "value": f"{candidate.latitude:.6f}, {candidate.longitude:.6f}",
        },
        {
            "label": "Coordinate method",
            "value": candidate.coordinate_resolution_method,
        },
        {
            "label": "Representative source",
            "value": (
                f"{candidate.representative_source_record} "
                f"({candidate.representative_source_name})"
            ),
        },
        {
            "label": "Lake registry id",
            "value": candidate.lake_registry_id or "Not available",
        },
        {
            "label": "Lake name status",
            "value": candidate.lake_name_status or "Not available",
        },
        {
            "label": "Lake area",
            "value": (
                f"{candidate.lake_area_km2:.3f} km²"
                if candidate.lake_area_km2 is not None
                else "Not available"
            ),
        },
        {
            "label": "Sampling posture",
            "value": candidate.lake_sampling_posture or "Not available",
        },
        {
            "label": "Sampling fit",
            "value": f"{candidate.lake_sampling_fit:.4f}",
        },
        {
            "label": "Sampling readiness",
            "value": candidate.lake_sampling_readiness_posture,
        },
        {
            "label": "Sampling evidence still required",
            "value": ", ".join(candidate.lake_sampling_missing_inputs)
            or "Not recorded",
        },
        {
            "label": "Pollen sources",
            "value": ", ".join(candidate.pollen_sources) or "None",
        },
        {
            "label": "Direct pollen with numeric chronology",
            "value": str(candidate.time_aware_direct_pollen_records),
        },
        {
            "label": "20 km pollen with numeric chronology",
            "value": str(_band_score(assessment, 20).time_aware_pollen_site_count),
        },
        {
            "label": "20 km pollen overlapping nearby human chronology",
            "value": str(_band_score(assessment, 20).human_overlap_pollen_site_count),
        },
        {
            "label": "20 km SEAD with numeric chronology",
            "value": str(_band_score(assessment, 20).time_aware_sead_site_count),
        },
        {
            "label": "20 km SEAD overlapping nearby human chronology",
            "value": str(_band_score(assessment, 20).human_overlap_sead_site_count),
        },
        {
            "label": "Duplicate Sweden names",
            "value": str(candidate.duplicate_name_count),
        },
        {
            "label": "Coordinate spread",
            "value": f"{candidate.coordinate_spread_km:.2f} km",
        },
        {
            "label": "Identity diagnostics",
            "value": _render_ambiguity_cell(candidate.ambiguity_flags),
        },
        {
            "label": "Identity note",
            "value": candidate.ambiguity_note or "No explicit identity warning.",
        },
    ]


def _candidate_temporal_sources(
    candidate: LakeEvidenceCandidate,
) -> tuple[LakeEvidenceSourceAnchor, ...]:
    if candidate.temporal_context_points:
        return candidate.temporal_context_points
    return _candidate_direct_temporal_sources(candidate)


def _candidate_direct_temporal_sources(
    candidate: LakeEvidenceCandidate,
) -> tuple[LakeEvidenceSourceAnchor, ...]:
    return tuple(
        source_point
        for source_point in candidate.supporting_source_points
        if source_point.time_start_bp is not None
        and source_point.time_end_bp is not None
    )


def _render_temporal_evidence_json(candidate: LakeEvidenceCandidate) -> str:
    return json.dumps(
        [
            source_point.as_dict()
            for source_point in _candidate_direct_temporal_sources(candidate)
        ],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _render_context_evidence_json(candidate: LakeEvidenceCandidate) -> str:
    return json.dumps(
        [source_point.as_dict() for source_point in candidate.temporal_context_points],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _temporal_record_id(
    candidate: LakeEvidenceCandidate,
    source_point: LakeEvidenceSourceAnchor | None,
) -> str:
    if source_point is None:
        return candidate.lake_token
    return f"{candidate.lake_token}:{source_point.source_record}"


def _temporal_properties(
    source_point: LakeEvidenceSourceAnchor | None,
) -> dict[str, object]:
    if source_point is None:
        return {
            "time_start_bp": None,
            "time_end_bp": None,
            "time_mean_bp": None,
            "time_label": "Chronology unresolved",
            "temporal_semantics": {
                "comparability_posture": "unresolved",
                "comparison_note": (
                    "The lake identity remains visible, but no numeric direct or "
                    "nearby contextual interval supports time filtering."
                ),
            },
        }
    return {
        "time_start_bp": source_point.time_start_bp,
        "time_end_bp": source_point.time_end_bp,
        "time_mean_bp": source_point.time_mean_bp,
        "time_label": source_point.time_label,
        "temporal_semantics": source_point.temporal_semantics or {},
    }


def _temporal_popup_rows(
    source_point: LakeEvidenceSourceAnchor | None,
) -> list[dict[str, str]]:
    if source_point is None:
        return [{"label": "Temporal support", "value": "No numeric temporal context"}]
    interval_label = source_point.time_label or (
        f"{source_point.time_start_bp}–{source_point.time_end_bp} BP"
    )
    return [
        {
            "label": "Temporal support",
            "value": (
                f"{interval_label} ({source_point.evidence_role.replace('_', ' ')})"
            ),
        },
        {"label": "Temporal source", "value": source_point.source_record},
        {
            "label": "Context records",
            "value": str(source_point.record_count),
        },
        {
            "label": "Context radius",
            "value": (
                f"{source_point.context_radius_km} km"
                if source_point.context_radius_km is not None
                else "Direct lake evidence"
            ),
        },
    ]
