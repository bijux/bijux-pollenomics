from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

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
    record_count: int
    numeric_interval_record_count: int
    detail_metrics: dict[str, int]
    caveats: tuple[str, ...]


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
        "schema_version": "source-spatiotemporal-posture-registry.v1",
        "row_count": len(rows),
        "rows": [asdict(row) for row in rows],
    }


def _build_landclim_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    payload = _load_json(
        output_root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson"
    )
    features = _geojson_features(payload)
    numeric_interval_count = sum(
        1 for feature in features if _feature_has_numeric_interval(feature)
    )
    return SourceSpatiotemporalPostureRecord(
        source_key="landclim",
        display_name="LandClim pollen context",
        governing_surface_path="data/landclim/normalized/nordic_pollen_site_sequences.geojson",
        review_surface_paths=(
            "data/landclim/normalized/landclim_summary.json",
            "data/source_family_evidence_stage_matrix.json",
        ),
        spatial_representation="site-sequence point inventory",
        temporal_support_posture="numeric_site_sequence_intervals",
        temporal_support_note=(
            "Checked-in LandClim sequence points carry numeric BP windows in the "
            "normalized repository layer."
        ),
        temporal_scope="site-sequence context",
        distance_scoring_posture="supporting_pollen_context",
        distance_scoring_note=(
            "Use LandClim to strengthen pollen context around lakes; do not treat it "
            "as direct human or archaeological evidence."
        ),
        record_count=len(features),
        numeric_interval_record_count=numeric_interval_count,
        detail_metrics={
            "site_sequence_record_count": len(features),
            "numeric_interval_record_count": numeric_interval_count,
        },
        caveats=(
            "The registry reflects normalized site-sequence intervals rather than a separate chronology packet inventory.",
        ),
    )


def _build_neotoma_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    review_payload = _load_json(output_root / "neotoma" / "review" / "temporal_review.json")
    normalized_payload = _load_json(
        output_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson"
    )
    coverage_summary = _dict(review_payload.get("coverage_summary"))
    feature_count = len(_geojson_features(normalized_payload))
    bp_age_range_count = _int(
        coverage_summary.get("site_count_with_bp_age_ranges", 0)
    )
    chronology_count = _int(coverage_summary.get("site_count_with_chronologies", 0))
    chronology_capture_posture = str(
        coverage_summary.get("chronology_capture_posture", "")
    ).strip() or "unresolved"
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
    review_payload = _load_json(output_root / "sead" / "review" / "temporal_review.json")
    normalized_payload = _load_json(
        output_root / "sead" / "normalized" / "nordic_environmental_sites.geojson"
    )
    inventory_summary = _dict(review_payload.get("inventory_summary"))
    feature_count = len(_geojson_features(normalized_payload))
    temporal_capture_posture = str(
        inventory_summary.get("temporal_capture_posture", "")
    ).strip() or "unresolved"
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
        spatial_representation="site point inventory",
        temporal_support_posture=temporal_capture_posture,
        temporal_support_note=(
            "Checked-in SEAD points are useful archaeology context, but the repository must not read them as uniformly time-resolved evidence."
        ),
        temporal_scope="archaeology-context inventory",
        distance_scoring_posture="contextual_archaeology_only",
        distance_scoring_note=(
            "Use SEAD to measure archaeology context around lakes; do not treat it as same-period support unless numeric intervals are explicitly present."
        ),
        record_count=feature_count,
        numeric_interval_record_count=_int(
            inventory_summary.get("numeric_interval_row_count", 0)
        ),
        detail_metrics={
            "site_inventory_only_row_count": _int(
                inventory_summary.get("site_inventory_only_row_count", 0)
            ),
            "dating_range_row_count": _int(
                inventory_summary.get("dating_range_row_count", 0)
            ),
            "relative_period_row_count": _int(
                inventory_summary.get("relative_period_row_count", 0)
            ),
        },
        caveats=tuple(caveats),
    )


def _build_raa_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    payload = _load_json(output_root / "raa" / "normalized" / "sweden_archaeology_layer.json")
    counts = _dict(payload.get("counts"))
    all_published_sites = _int(counts.get("all_published_sites", 0))
    return SourceSpatiotemporalPostureRecord(
        source_key="raa",
        display_name="RAA archaeology context",
        governing_surface_path="data/raa/normalized/sweden_archaeology_layer.json",
        review_surface_paths=("data/source_family_evidence_stage_matrix.json",),
        spatial_representation="coarse archaeology density surface",
        temporal_support_posture="spatial_density_without_time",
        temporal_support_note=(
            "Checked-in RAA outputs summarize Swedish archaeology density and site counts without repository-owned time windows."
        ),
        temporal_scope="sweden archaeology density context",
        distance_scoring_posture="coarse_archaeology_context_only",
        distance_scoring_note=(
            "Use RAA to compare Swedish archaeology richness around lakes, not to infer exact site-by-site time alignment."
        ),
        record_count=all_published_sites,
        numeric_interval_record_count=0,
        detail_metrics={
            "all_published_sites": all_published_sites,
            "fornlamning_count": _int(counts.get("fornlamning", 0)),
        },
        caveats=(
            "The normalized repository surface is density-oriented rather than a direct local-distance inventory of every upstream site row.",
        ),
    )


def _build_svar_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    payload = _load_json(output_root / "svar" / "normalized" / "sweden_lake_registry.geojson")
    feature_count = len(_geojson_features(payload))
    return SourceSpatiotemporalPostureRecord(
        source_key="svar",
        display_name="SMHI SVAR lake registry",
        governing_surface_path="data/svar/normalized/sweden_lake_registry.geojson",
        review_surface_paths=(
            "data/svar/normalized/svar_summary.json",
            "data/source_family_evidence_stage_matrix.json",
        ),
        spatial_representation="candidate lake registry",
        temporal_support_posture="no_time_dimension",
        temporal_support_note=(
            "SVAR contributes the lake anchors themselves rather than dated evidence around those lakes."
        ),
        temporal_scope="lake-anchor registry",
        distance_scoring_posture="candidate_lake_anchor",
        distance_scoring_note=(
            "Use SVAR as the authoritative Sweden lake candidate surface before nearby evidence is counted."
        ),
        record_count=feature_count,
        numeric_interval_record_count=0,
        detail_metrics={"lake_count": feature_count},
        caveats=(
            "SVAR governs lake identity and location, not chronology or surrounding evidence completeness.",
        ),
    )


def _build_boundaries_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    payload = _load_json(
        output_root / "boundaries" / "normalized" / "nordic_country_boundaries.geojson"
    )
    feature_count = len(_geojson_features(payload))
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
        record_count=feature_count,
        numeric_interval_record_count=0,
        detail_metrics={"polygon_count": feature_count},
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
