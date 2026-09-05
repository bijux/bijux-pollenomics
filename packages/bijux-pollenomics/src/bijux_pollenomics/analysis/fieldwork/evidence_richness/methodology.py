"""Evidence-richness methodology and coverage reporting."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from pathlib import Path

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from .models import (
    _COORDINATE_SPREAD_FLAG_KM,
    _LAKE_MATCH_DISTANCE_KM,
    _AGGREGATE_RADIUS_WEIGHTS,
    _SVAR_AGGREGATE_RADIUS_WEIGHTS,
    LakeEvidenceCandidate,
    LakeEvidenceRichnessReport,
)
from .inputs import (
    _load_review_payload,
)
from .temporal import (
    _context_point_has_numeric_interval,
    _validated_interval,
)

__all__ = []


def _build_empty_report(
    radii_km: tuple[int, ...],
    *,
    candidate_source: str = "pollen_candidate_points",
    source_temporal_coverage: dict[str, object] | None = None,
    raa_authority: dict[str, object] | None = None,
) -> LakeEvidenceRichnessReport:
    return LakeEvidenceRichnessReport(
        schema_version="sweden-lake-evidence-richness.v2",
        country="Sweden",
        radii_km=radii_km,
        methodology=_build_methodology(
            radii_km,
            candidate_source=candidate_source,
            source_temporal_coverage=source_temporal_coverage,
            raa_authority=raa_authority,
        ),
        candidate_count=0,
        assessments=(),
    )


def _build_methodology(
    radii_km: tuple[int, ...],
    *,
    candidate_source: str = "pollen_candidate_points",
    source_temporal_coverage: dict[str, object] | None = None,
    candidates: Sequence[LakeEvidenceCandidate] = (),
    raa_authority: dict[str, object] | None = None,
) -> dict[str, object]:
    if candidate_source == "svar_registry_authority_unavailable":
        payload: dict[str, object] = {
            "candidate_derivation": (
                "No SVAR lake candidates were admitted because the derived review "
                "subset exists without its governing normalized registry."
            ),
            "candidate_source": candidate_source,
            "availability_status": "blocked",
            "refusal_reason": "governing_svar_registry_missing",
            "governing_surface": ("data/svar/normalized/sweden_lake_registry.geojson"),
            "derived_subset_admitted": False,
            "distance_bands": list(radii_km),
            "temporal_navigation": _temporal_navigation_summary(candidates),
        }
        if source_temporal_coverage:
            payload["source_temporal_coverage"] = source_temporal_coverage
        if raa_authority is not None:
            payload["raa_density_authority"] = raa_authority
        return payload
    if candidate_source == "svar_lake_registry":
        payload = {
            "candidate_derivation": (
                "Candidates come from the Sweden lake registry published through "
                "SMHI SVAR. Each candidate uses a representative point derived "
                "from the official lake polygon instead of a pollen-point centroid. "
                "Only lakes with at least one human aDNA locality within 50 km "
                "remain in the ranked set. Registry names that clearly describe "
                "engineered water bodies or wetlands instead of sampling lakes are "
                "kept out of the shortlist."
            ),
            "distance_bands": list(radii_km),
            "aggregate_radius_weights": {
                str(radius): _SVAR_AGGREGATE_RADIUS_WEIGHTS.get(radius, 0.0)
                for radius in radii_km
            },
            "score_components": {
                "human_adna_signal": 0.59,
                "direct_pollen_signal": 0.14,
                "nearby_pollen_signal": 0.07,
                "lake_sampling_fit": 0.07,
                "archaeology_signal": 0.07,
                "domesticated_animal_signal": 0.04,
                "evidence_diversity_signal": 0.02,
            },
            "ranking_decision_rule": (
                "Aggregate and band ranks sort first by human aDNA locality and "
                "sample coverage, then by direct pollen support, then by broader "
                "pollen and archaeology context, with sampling fit and blended score "
                "used as later tie-breakers."
            ),
            "temporal_alignment_rule": (
                "Neotoma pollen and SEAD archaeology remain lake-anchored context "
                "layers, but their stronger chronology contribution comes only from "
                "records with numeric BP intervals that overlap nearby human locality "
                "windows."
            ),
            "identity_diagnostics": {
                "coordinate_spread_flag_km": _COORDINATE_SPREAD_FLAG_KM,
                "name_match_distance_km": _LAKE_MATCH_DISTANCE_KM,
                "coordinate_resolution_methods": [
                    "svar_polygon_representative_point",
                ],
                "ambiguity_flags": [
                    "duplicate_sweden_name",
                    "non_official_registry_name",
                ],
            },
            "pollen_note": (
                "Direct pollen signal reflects lake-basin pollen records placed on "
                "or very near the official lake. Nearby pollen signal then adds "
                "broader pollen context within the active distance band, with extra "
                "credit when those pollen records carry comparable chronology that "
                "overlaps nearby human localities."
            ),
            "sampling_note": (
                "Lake suitability remains separate from evidence density. Very small "
                "basins stay visible but score lower, while registry names that "
                "clearly point to wetlands, pits, ponds, or engineered water bodies "
                "do not enter the ranked shortlist."
            ),
            "archaeology_note": (
                "SEAD contributes site-level point counts and gains stronger weight "
                "when those site spans are numerically comparable and overlap nearby "
                "human locality windows. RAÄ contributes coarse density cells, so the "
                "archaeology term still measures surrounding evidence richness rather "
                "than exact site-to-lake proximity."
            ),
            "animal_note": (
                "Domesticated animal aDNA remains a secondary contextual signal. "
                "Human aDNA is the decisive ranking term, direct pollen is the "
                "next tie-break, and archaeology resolves ties among similarly "
                "sampled lakes."
            ),
        }
        if source_temporal_coverage:
            payload["source_temporal_coverage"] = source_temporal_coverage
        if raa_authority is not None:
            payload["raa_density_authority"] = raa_authority
        payload["temporal_navigation"] = _temporal_navigation_summary(candidates)
        return payload
    payload = {
        "candidate_derivation": (
            "Candidates come from Sweden-scoped Neotoma and LandClim pollen "
            "points whose names or site descriptions identify lake-like basins. "
            "Points merge only when their cleaned lake names match and their "
            "coordinates stay within 2 km, so nearby but differently named lakes "
            "remain distinct. Each candidate keeps one source-backed "
            "representative coordinate chosen from the supporting points instead "
            "of a synthetic arithmetic centroid. Duplicate names, coordinate "
            "spread, and source position notes remain explicit as ambiguity "
            "diagnostics."
        ),
        "distance_bands": list(radii_km),
        "aggregate_radius_weights": {
            str(radius): _AGGREGATE_RADIUS_WEIGHTS.get(radius, 0.0)
            for radius in radii_km
        },
        "score_components": {
            "direct_pollen_signal": 0.2,
            "nearby_pollen_signal": 0.1,
            "archaeology_signal": 0.25,
            "human_adna_signal": 0.2,
            "domesticated_animal_signal": 0.15,
            "evidence_diversity_signal": 0.1,
        },
        "identity_diagnostics": {
            "coordinate_spread_flag_km": _COORDINATE_SPREAD_FLAG_KM,
            "name_match_distance_km": _LAKE_MATCH_DISTANCE_KM,
            "coordinate_resolution_methods": [
                "shared_source_coordinate",
                "source_coordinate_medoid",
            ],
            "ambiguity_flags": [
                "duplicate_sweden_name",
                "source_coordinate_spread",
                "source_name_variants",
                "source_position_note",
            ],
        },
        "archaeology_note": (
            "SEAD contributes site-level point counts. RAÄ contributes coarse "
            "1-degree density cells, so the RAÄ term captures archaeology "
            "richness around the lake rather than precise site-by-site distance."
        ),
        "animal_note": (
            "Domesticated animal aDNA remains sparse in the current Sweden bundle. "
            "The ranking keeps that sparsity visible instead of inflating it."
        ),
    }
    if source_temporal_coverage:
        payload["source_temporal_coverage"] = source_temporal_coverage
    if raa_authority is not None:
        payload["raa_density_authority"] = raa_authority
    payload["temporal_navigation"] = _temporal_navigation_summary(candidates)
    return payload


def _temporal_navigation_summary(
    candidates: Sequence[LakeEvidenceCandidate],
) -> dict[str, object]:
    source_layer_counts = Counter(
        point.source_layer_key
        for candidate in candidates
        for point in candidate.temporal_context_points
    )
    window_counts = Counter(
        str((point.temporal_semantics or {}).get("temporal_window_key", "unresolved"))
        for candidate in candidates
        for point in candidate.temporal_context_points
    )
    return {
        "candidate_count": len(candidates),
        "candidate_with_numeric_context_count": sum(
            1 for candidate in candidates if candidate.temporal_context_points
        ),
        "candidate_with_direct_numeric_pollen_count": sum(
            1
            for candidate in candidates
            if any(
                _validated_interval(point.time_start_bp, point.time_end_bp) is not None
                for point in candidate.supporting_source_points
            )
        ),
        "context_summary_count": sum(
            len(candidate.temporal_context_points) for candidate in candidates
        ),
        "context_source_layer_counts": dict(sorted(source_layer_counts.items())),
        "context_window_counts": dict(sorted(window_counts.items())),
        "context_radius_km": 50,
        "interpretation_rule": (
            "Temporal context summaries support time navigation for the ranked lake "
            "set. They remain explicitly separate from direct lake pollen chronology."
        ),
    }


def _build_context_temporal_coverage_summary(
    pollen_points: Sequence[ContextPointRecord],
    *,
    context_root: Path,
    sead_points: Sequence[ContextPointRecord],
) -> dict[str, object]:
    posture_lookup = _load_source_spatiotemporal_posture_lookup(
        context_root / "source_spatiotemporal_posture_registry.json"
    )
    neotoma_summary = _temporal_coverage_summary(
        point
        for point in pollen_points
        if point.layer_key == "neotoma-pollen" or point.source == "Neotoma"
    )
    landclim_summary = _temporal_coverage_summary(
        point
        for point in pollen_points
        if point.layer_key == "landclim-sites" or point.source == "LandClim"
    )
    sead_summary = _temporal_coverage_summary(sead_points)
    _merge_source_temporal_review(
        neotoma_summary,
        _load_review_payload(
            context_root / "neotoma" / "review" / "temporal_review.json"
        ),
        source_family="neotoma",
    )
    _merge_source_temporal_review(
        sead_summary,
        _load_review_payload(context_root / "sead" / "review" / "temporal_review.json"),
        source_family="sead",
    )
    _merge_source_spatiotemporal_posture(
        neotoma_summary, posture_lookup.get("neotoma"), source_family="neotoma"
    )
    _merge_source_spatiotemporal_posture(
        landclim_summary, posture_lookup.get("landclim"), source_family="landclim"
    )
    _merge_source_spatiotemporal_posture(
        sead_summary, posture_lookup.get("sead"), source_family="sead"
    )
    if not landclim_summary.get("capture_posture"):
        landclim_summary["capture_posture"] = "spatial_inventory_only"
    return {
        "neotoma_pollen": neotoma_summary,
        "landclim_pollen": landclim_summary,
        "sead_archaeology": sead_summary,
    }


def _temporal_coverage_summary(
    points: Iterable[ContextPointRecord],
) -> dict[str, object]:
    materialized_points = tuple(points)
    total_records = len(materialized_points)
    numeric_interval_records = sum(
        1 for point in materialized_points if _context_point_has_numeric_interval(point)
    )
    return {
        "record_count": total_records,
        "numeric_interval_record_count": numeric_interval_records,
        "numeric_interval_share": round(numeric_interval_records / total_records, 4)
        if total_records
        else 0.0,
    }


def _merge_source_temporal_review(
    summary: dict[str, object],
    payload: dict[str, object],
    *,
    source_family: str,
) -> None:
    if source_family == "neotoma":
        coverage_summary = payload.get("coverage_summary", {})
        if not isinstance(coverage_summary, dict):
            return
        capture_posture = str(
            coverage_summary.get("chronology_capture_posture", "")
        ).strip()
        if capture_posture:
            summary["capture_posture"] = capture_posture
        summary["bp_age_range_record_count"] = int(
            coverage_summary.get("site_count_with_bp_age_ranges", 0) or 0
        )
        summary["chronology_row_record_count"] = int(
            coverage_summary.get("site_count_with_chronologies", 0) or 0
        )
        return
    if source_family == "sead":
        inventory_summary = payload.get("inventory_summary", {})
        if not isinstance(inventory_summary, dict):
            return
        capture_posture = str(
            inventory_summary.get("temporal_capture_posture", "")
        ).strip()
        if capture_posture:
            summary["capture_posture"] = capture_posture
        summary["site_inventory_only_record_count"] = int(
            inventory_summary.get("site_inventory_only_row_count", 0) or 0
        )


def _load_source_spatiotemporal_posture_lookup(
    path: Path,
) -> dict[str, dict[str, object]]:
    payload = _load_review_payload(path)
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return {}
    lookup: dict[str, dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_key = str(row.get("source_key", "")).strip()
        if source_key:
            lookup[source_key] = row
    return lookup


def _merge_source_spatiotemporal_posture(
    summary: dict[str, object],
    payload: dict[str, object] | None,
    *,
    source_family: str,
) -> None:
    if not isinstance(payload, dict):
        return
    for field in (
        "spatial_representation",
        "temporal_support_posture",
        "temporal_support_note",
        "temporal_scope",
        "distance_scoring_posture",
        "distance_scoring_note",
    ):
        value = str(payload.get(field, "")).strip()
        if value:
            summary[field] = value
    detail_metrics = payload.get("detail_metrics")
    if isinstance(detail_metrics, dict):
        summary["detail_metrics"] = detail_metrics
    caveats = payload.get("caveats")
    if isinstance(caveats, list) and caveats:
        summary["caveats"] = [
            str(item).strip() for item in caveats if str(item).strip()
        ]
    if source_family == "landclim" and "capture_posture" not in summary:
        summary["capture_posture"] = "numeric_site_sequence_intervals"
