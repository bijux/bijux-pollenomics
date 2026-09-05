"""SEAD and RAÄ spatiotemporal posture evidence."""

from __future__ import annotations

from pathlib import Path

from ...sources.raa import assess_raa_density_authority
from .model import SourceSpatiotemporalPostureRecord
from .records import _dict, _geojson_features, _int, _load_json

__all__ = []


def _build_sead_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    review_payload = _load_json(
        output_root / "sead" / "review" / "temporal_review.json"
    )
    normalized_payload = _load_json(
        output_root / "sead" / "normalized" / "nordic_environmental_sites.geojson"
    )
    temporal_payload = _load_json(
        output_root / "sead" / "normalized" / "nordic_temporal_evidence.geojson"
    )
    inventory_summary = _dict(review_payload.get("inventory_summary"))
    feature_count = len(_geojson_features(normalized_payload))
    temporal_features = _geojson_features(temporal_payload)
    temporal_feature_count = len(temporal_features)
    represented_chronology_record_count = sum(
        _int(_dict(feature.get("properties")).get("record_count", 0))
        for feature in temporal_features
    )
    temporal_capture_posture = (
        str(inventory_summary.get("temporal_capture_posture", "")).strip()
        or "unresolved"
    )
    caveats = []
    if temporal_capture_posture == "site_inventory_only":
        caveats.append(
            "The checked-in SEAD state is a site inventory and contextual point layer, not a repository-wide chronology-support layer."
        )
    if _int(inventory_summary.get("relative_period_row_count", 0)) == 0:
        caveats.append(
            "The current Sweden-facing SEAD capture does not yet preserve linked relative-period or dating-range tables in checked-in raw form."
        )
    return SourceSpatiotemporalPostureRecord(
        source_key="sead",
        display_name="SEAD archaeology context",
        governing_surface_path="data/sead/normalized/nordic_environmental_sites.geojson",
        review_surface_paths=(
            "data/sead/review/temporal_review.json",
            "data/sead/review/evidence_legibility_review.json",
            "data/sead/review/access_model.json",
        ),
        spatial_representation="site inventory plus record-level chronology points",
        temporal_support_posture=temporal_capture_posture,
        temporal_support_note=(
            "SEAD chronology is published as interval-preserving temporal features; upstream-undated sites remain available only in the separate spatial inventory."
        ),
        temporal_scope="linked archaeology chronology",
        distance_scoring_posture="contextual_archaeology_only",
        distance_scoring_note=(
            "Use SEAD to measure archaeology context around lakes; do not treat it as same-period support unless numeric intervals are explicitly present."
        ),
        availability_status="available_with_limitations",
        refusal_reasons=(),
        record_count=feature_count,
        numeric_interval_record_count=temporal_feature_count,
        detail_metrics={
            "unresolved_site_count": _int(
                inventory_summary.get("unresolved_site_count", 0)
            ),
            "captured_chronology_record_count": _int(
                inventory_summary.get("chronology_record_count", 0)
            ),
            "mapped_temporal_feature_count": temporal_feature_count,
            "mapped_chronology_record_count": represented_chronology_record_count,
        },
        caveats=tuple(caveats),
    )


def _build_raa_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    payload = _load_json(
        output_root / "raa" / "normalized" / "sweden_archaeology_layer.json"
    )
    counts = _dict(payload.get("counts"))
    authority = assess_raa_density_authority(output_root)
    all_published_sites = (
        _int(counts.get("all_published_sites", 0)) if authority.admitted else None
    )
    return SourceSpatiotemporalPostureRecord(
        source_key="raa",
        display_name="RAÄ archaeology context",
        governing_surface_path="data/raa/normalized/sweden_archaeology_layer.json",
        review_surface_paths=("data/source_family_evidence_stage_matrix.json",),
        spatial_representation="coarse archaeology density surface",
        temporal_support_posture=(
            "spatial_density_without_time"
            if authority.admitted
            else "refused_missing_authority"
        ),
        temporal_support_note=(
            "RAÄ density has no repository-owned time windows and is admitted only "
            "when raw inventory, summary, normalized counts, and qualified review "
            "reconcile."
        ),
        temporal_scope="sweden archaeology density context",
        distance_scoring_posture=(
            "coarse_archaeology_context_only"
            if authority.admitted
            else "refused_missing_authority"
        ),
        distance_scoring_note=(
            "Use RAÄ only after authority admission and only as coarse context, "
            "never as exact site-by-site time alignment."
        ),
        availability_status="available" if authority.admitted else "refused",
        refusal_reasons=authority.reason_codes,
        record_count=all_published_sites,
        numeric_interval_record_count=0,
        detail_metrics={
            "all_published_sites": all_published_sites,
            "fornlamning_count": (
                _int(counts.get("fornlamning", 0)) if authority.admitted else None
            ),
        },
        caveats=(
            (
                "The normalized density surface is excluded until its source inventory, "
                "counts, and qualified review reconcile."
            ),
        ),
    )
