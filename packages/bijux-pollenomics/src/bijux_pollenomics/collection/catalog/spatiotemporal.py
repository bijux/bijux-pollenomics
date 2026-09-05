from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from ..sources.boundaries.collection import (
    BOUNDARY_CODES,
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
)
from ..sources.boundaries import load_country_boundaries
from ..sources.raa import assess_raa_density_authority

__all__ = [
    "SourceSpatiotemporalPostureRecord",
    "build_source_spatiotemporal_posture_payload",
]


@dataclass(frozen=True)
class SourceSpatiotemporalPostureRecord:
    source_key: str
    display_name: str
    governing_surface_path: str
    review_surface_paths: tuple[str, ...]
    spatial_representation: str
    temporal_support_posture: str
    temporal_support_note: str
    temporal_scope: str
    distance_scoring_posture: str
    distance_scoring_note: str
    availability_status: str
    refusal_reasons: tuple[str, ...]
    record_count: int | None
    numeric_interval_record_count: int
    detail_metrics: dict[str, int | None]
    caveats: tuple[str, ...]
    capability_contract_path: str = "data/source_family_contracts.json"
    capability_materialization_audit_path: str = (
        "data/source_family_evidence_stage_matrix.json"
    )
    capability_and_materialization_are_independent: bool = True


def build_source_spatiotemporal_posture_payload(
    output_root: Path,
) -> dict[str, object]:
    """Build one reader-facing registry of source spatiotemporal posture."""
    output_root = Path(output_root)
    rows = (
        _build_landclim_row(output_root),
        _build_neotoma_row(output_root),
        _build_sead_row(output_root),
        _build_raa_row(output_root),
        _build_svar_row(output_root),
        _build_boundaries_row(output_root),
    )
    return {
        "schema_version": "source-spatiotemporal-posture-registry.v2",
        "row_count": len(rows),
        "rows": [asdict(row) for row in rows],
    }


def _build_landclim_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    payload = _load_json(
        output_root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson"
    )
    features = _geojson_features(payload)
    temporal_grid_features = _geojson_features(
        _load_json(
            output_root
            / "landclim"
            / "normalized"
            / "nordic_reveals_temporal_grid_cells.geojson"
        )
    )
    grid_features = _geojson_features(
        _load_json(
            output_root
            / "landclim"
            / "normalized"
            / "nordic_reveals_grid_cells.geojson"
        )
    )
    numeric_interval_count = sum(
        1 for feature in features if _feature_has_numeric_interval(feature)
    )
    return SourceSpatiotemporalPostureRecord(
        source_key="landclim",
        display_name="LandClim pollen context",
        governing_surface_path="data/landclim/normalized/nordic_pollen_site_sequences.geojson",
        review_surface_paths=(
            "data/landclim/review/spatiotemporal_review.json",
            "data/landclim/normalized/landclim_summary.json",
            "data/landclim/normalized/landclim_bibliography.json",
            "data/source_family_evidence_stage_matrix.json",
        ),
        spatial_representation="site-sequence points plus time-window model polygons",
        temporal_support_posture="numeric_site_and_reveals_window_intervals",
        temporal_support_note=(
            "LandClim sequence points carry explicit temporal posture and REVEALS "
            "model cells are published as separate, filterable time-window records."
        ),
        temporal_scope="site-sequence coverage and modeled vegetation windows",
        distance_scoring_posture="supporting_pollen_context",
        distance_scoring_note=(
            "Use LandClim to strengthen pollen context around lakes; do not treat it "
            "as direct human or archaeological evidence."
        ),
        availability_status="available",
        refusal_reasons=(),
        record_count=len(features),
        numeric_interval_record_count=numeric_interval_count,
        detail_metrics={
            "site_sequence_record_count": len(features),
            "numeric_interval_record_count": numeric_interval_count,
            "grid_cell_count": len(grid_features),
            "temporal_grid_feature_count": len(temporal_grid_features),
        },
        caveats=(
            "REVEALS windows are modeled vegetation estimates, not sample-owned chronologies.",
        ),
    )


def _build_neotoma_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    review_payload = _load_json(
        output_root / "neotoma" / "review" / "temporal_review.json"
    )
    normalized_payload = _load_json(
        output_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson"
    )
    coverage_summary = _dict(review_payload.get("coverage_summary"))
    feature_count = len(_geojson_features(normalized_payload))
    bp_age_range_count = _int(coverage_summary.get("site_count_with_bp_age_ranges", 0))
    chronology_count = _int(coverage_summary.get("site_count_with_chronologies", 0))
    chronology_capture_posture = (
        str(coverage_summary.get("chronology_capture_posture", "")).strip()
        or "unresolved"
    )
    caveats = []
    if chronology_capture_posture == "bp_site_spans_without_chronology_rows":
        caveats.append(
            "Numeric BP site spans are available, but the checked-in raw capture does not currently include chronology rows for the same Sweden-facing site family."
        )
    if _int(coverage_summary.get("site_count_with_no_age_ranges", 0)) > 0:
        caveats.append(
            "Some checked-in Neotoma sites remain spatial context only because they do not carry publishable BP age ranges."
        )
    return SourceSpatiotemporalPostureRecord(
        source_key="neotoma",
        display_name="Neotoma pollen context",
        governing_surface_path="data/neotoma/normalized/nordic_pollen_sites.geojson",
        review_surface_paths=("data/neotoma/review/temporal_review.json",),
        spatial_representation="site point inventory",
        temporal_support_posture=chronology_capture_posture,
        temporal_support_note=(
            "Checked-in Neotoma points can carry numeric BP site spans, but chronology support remains uneven and must be read from the review packet."
        ),
        temporal_scope="site-span pollen context",
        distance_scoring_posture="supporting_pollen_context",
        distance_scoring_note=(
            "Use Neotoma to compare pollen context around lakes; only promote it into chronology-aware support when a numeric interval is actually present."
        ),
        availability_status="available_with_limitations",
        refusal_reasons=(),
        record_count=feature_count,
        numeric_interval_record_count=bp_age_range_count,
        detail_metrics={
            "site_count_with_bp_age_ranges": bp_age_range_count,
            "site_count_with_chronology_rows": chronology_count,
            "site_count_without_bp_age_ranges": _int(
                coverage_summary.get("site_count_without_bp_age_ranges", 0)
            ),
        },
        caveats=tuple(caveats),
    )


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


def _build_svar_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    registry_path = output_root / "svar" / "normalized" / "sweden_lake_registry.geojson"
    payload = _load_json(registry_path)
    feature_count = len(_geojson_features(payload))
    authority_available = registry_path.is_file()
    return SourceSpatiotemporalPostureRecord(
        source_key="svar",
        display_name="SMHI SVAR lake registry",
        governing_surface_path="data/svar/normalized/sweden_lake_registry.geojson",
        review_surface_paths=(
            "data/svar/normalized/svar_summary.json",
            "data/source_family_evidence_stage_matrix.json",
        ),
        spatial_representation="candidate lake registry",
        temporal_support_posture=(
            "no_time_dimension" if authority_available else "refused_missing_authority"
        ),
        temporal_support_note=(
            "SVAR contributes the lake anchors themselves rather than dated evidence around those lakes."
        ),
        temporal_scope="lake-anchor registry",
        distance_scoring_posture=(
            "candidate_lake_anchor"
            if authority_available
            else "refused_missing_authority"
        ),
        distance_scoring_note=(
            "Use SVAR as the authoritative Sweden lake candidate surface only when "
            "the governing normalized registry is present."
        ),
        availability_status="available" if authority_available else "refused",
        refusal_reasons=(
            () if authority_available else ("missing_governing_normalized_registry",)
        ),
        record_count=feature_count if authority_available else None,
        numeric_interval_record_count=0,
        detail_metrics={
            "lake_count": feature_count if authority_available else None,
        },
        caveats=(
            (
                "SVAR governs lake identity and location, not chronology or "
                "surrounding evidence completeness. Derived review subsets are "
                "excluded when the governing registry is absent."
            ),
        ),
    )


def _build_boundaries_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    payload = _load_json(
        output_root / "boundaries" / "normalized" / "nordic_country_boundaries.geojson"
    )
    feature_count = len(_geojson_features(payload))
    try:
        boundary_authority = load_country_boundaries(
            output_root=output_root / "boundaries",
            boundary_codes=BOUNDARY_CODES,
            natural_earth_version=NATURAL_EARTH_VERSION,
            natural_earth_admin0_url=NATURAL_EARTH_ADMIN0_URL,
            natural_earth_terms_url=NATURAL_EARTH_TERMS_URL,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        boundary_authority = None
    authority_available = boundary_authority is not None and feature_count == 4
    return SourceSpatiotemporalPostureRecord(
        source_key="boundaries",
        display_name="Boundary framing",
        governing_surface_path="data/boundaries/normalized/nordic_country_boundaries.geojson",
        review_surface_paths=("data/source_family_evidence_stage_matrix.json",),
        spatial_representation="country framing polygons",
        temporal_support_posture="no_time_dimension",
        temporal_support_note=(
            "Boundary layers frame geography only and do not contribute time-resolved evidence."
        ),
        temporal_scope="geographic framing only",
        distance_scoring_posture="framing_only",
        distance_scoring_note=(
            "Use boundary geometry to constrain reporting scope, not to increase lake evidence scores."
        ),
        availability_status=("review_required" if authority_available else "refused"),
        refusal_reasons=(
            ("qualified_boundary_inclusion_review_missing",)
            if authority_available
            else ("missing_or_invalid_boundary_authority",)
        ),
        record_count=feature_count if authority_available else None,
        numeric_interval_record_count=0,
        detail_metrics={
            "polygon_count": feature_count if authority_available else None,
        },
        caveats=(
            "Boundary framing should never be misread as biological, archaeological, or chronological evidence.",
        ),
    )


def _load_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _geojson_features(payload: dict[str, object]) -> list[dict[str, object]]:
    features = payload.get("features")
    if not isinstance(features, list):
        return []
    return [feature for feature in features if isinstance(feature, dict)]


def _feature_has_numeric_interval(feature: dict[str, object]) -> bool:
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        return False
    start = properties.get("time_start_bp")
    end = properties.get("time_end_bp")
    return isinstance(start, (int, float)) or isinstance(end, (int, float))


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip()
    if not text:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0
