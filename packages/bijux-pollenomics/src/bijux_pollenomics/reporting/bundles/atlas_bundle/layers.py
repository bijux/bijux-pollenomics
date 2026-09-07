"""Atlas layer preparation, projection, and static-asset publication."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...modeled_context.publication_projection import project_modeled_context_layers


_ANIMAL_CHRONOLOGY_CONTEXT = {
    "semantic_role": "animal_source_chronology_context",
    "group": "animal-chronology-context",
    "contribution_role": "display_only",
    "default_enabled": False,
    "applies_time_filter": True,
    "candidate_ranking_eligible": False,
    "scientific_classification_eligible": False,
    "scientific_selection_enabled": False,
    "propagation_status": "refused",
    "propagation_reason_code": "display_only_source_chronology",
    "edge_count": 0,
}


def is_animal_chronology_context(layer: dict[str, object]) -> bool:
    """Identify the display-only animal layer or refuse contradictory posture."""
    if (
        layer.get("semantic_role") != "animal_source_chronology_context"
        and layer.get("group") != "animal-chronology-context"
    ):
        return False
    if any(
        layer.get(field) != expected
        for field, expected in _ANIMAL_CHRONOLOGY_CONTEXT.items()
    ):
        raise ValueError("animal source chronology context posture differs")
    return True


def prepare_layers(
    staging_output_dir: Path,
    *,
    report: Any,
    version: str,
    all_samples: Any,
    context_root: Path | None,
    geography_scope: Any,
    build_atlas_bundle_paths_fn: Any,
    build_context_layers_fn: Any,
    build_samples_geojson_fn: Any,
    atlas_detail_records: Any,
    atlas_scientific_signals: Any,
    atlas_edge_records: Any,
    atlas_sequence_records: Any,
    surface: Any,
) -> tuple[Any, ...]:
    bundle_paths = build_atlas_bundle_paths_fn(
        output_dir=staging_output_dir, slug=report.slug, version=version
    )
    map_geojson = build_samples_geojson_fn(all_samples)
    bundle_paths.samples_geojson_path.write_text(
        surface.json.dumps(map_geojson, indent=2), encoding="utf-8"
    )
    point_layers, polygon_layers, extra_artifacts = build_context_layers_fn(
        samples=all_samples,
        version=version,
        output_dir=staging_output_dir,
        published_output_dir=report.output_dir,
        context_root=context_root,
        geography_scope=geography_scope,
    )
    animal_localities = ()
    animal_coordinate_review = surface.AnimalCoordinateVisibilityReview(
        direct_coordinate_feature_count=0,
        named_site_geocoded_feature_count=0,
        weaker_geography_feature_count=0,
    )
    animal_chronology_context = None
    if context_root is not None:
        animal_bundle = surface.build_tracked_animal_atlas_bundle(
            data_root=context_root,
            output_dir=staging_output_dir,
            atlas_slug=report.slug,
            geography_scope=geography_scope,
        )
        point_layers.extend(animal_bundle.point_layers)
        extra_artifacts.extend(animal_bundle.extra_artifacts)
        animal_chronology_context = surface.build_animal_sample_chronology_context(
            data_root=context_root,
            geography_scope=geography_scope,
        )
        point_layers.extend(animal_chronology_context.point_layers)
        animal_localities = animal_bundle.localities
        animal_coordinate_review = surface.AnimalCoordinateVisibilityReview(
            direct_coordinate_feature_count=animal_bundle.coordinate_review.direct_coordinate_feature_count,
            named_site_geocoded_feature_count=animal_bundle.coordinate_review.named_site_geocoded_feature_count,
            weaker_geography_feature_count=animal_bundle.coordinate_review.weaker_geography_feature_count,
        )
    point_layers.extend(
        surface.build_sweden_lake_atlas_layers(
            version=version,
            staging_output_dir=staging_output_dir,
            published_output_dir=report.output_dir,
        )
    )
    detail_projection_reconciliation = None
    if context_root is not None and atlas_detail_records is None:
        detail_projection = surface.build_map_evidence_projection(
            context_root, point_layers
        )
        atlas_detail_records = detail_projection.detail_records
        detail_projection_reconciliation = detail_projection.reconciliation
        point_layers.extend(detail_projection.point_layers)
    surface._attach_traceability_surfaces(point_layers, bundle_paths)
    static_assets = surface.write_static_atlas_assets(
        staging_output_dir,
        slug=report.slug,
        version=version,
        point_layers=point_layers,
        polygon_layers=project_modeled_context_layers(polygon_layers),
        detail_records=atlas_detail_records,
        scientific_signals=atlas_scientific_signals,
        edge_records=atlas_edge_records,
        sequence_records=atlas_sequence_records,
    )
    if static_assets.manifest_path != bundle_paths.map_static_assets_manifest_path:
        raise ValueError("static atlas manifest path does not match bundle ownership")
    extra_artifacts.append(
        ("Static atlas bootstrap manifest", static_assets.manifest_path.name)
    )
    extra_artifacts.extend(
        ("Static atlas data chunk", path.name) for path in static_assets.asset_paths
    )
    return (
        bundle_paths,
        point_layers,
        polygon_layers,
        extra_artifacts,
        animal_localities,
        animal_coordinate_review,
        animal_chronology_context,
        detail_projection_reconciliation,
        static_assets,
    )
