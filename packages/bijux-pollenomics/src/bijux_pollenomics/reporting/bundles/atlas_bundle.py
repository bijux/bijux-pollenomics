from __future__ import annotations

from collections.abc import Callable, Iterable
import json
from pathlib import Path

from ...analysis import (
    build_ranking_engine_manifest,
    build_ranking_sensitivity_report,
    rank_localities,
    render_candidate_site_markdown,
    render_candidate_site_sensitivity_markdown,
    write_candidate_site_sensitivity_json,
    write_candidate_sites_csv,
    write_candidate_sites_json,
)
from ...core.geojson import JsonObject
from ...data_downloader.models import ContextPointRecord
from ...evidence import (
    AnimalCoordinateVisibilityReview,
    build_atlas_evidence_surface,
    build_scientific_review_surface,
    render_atlas_evidence_surface_markdown,
    render_scientific_review_surface_markdown,
    write_atlas_evidence_surface_json,
    write_scientific_review_surface_json,
)
from ..geography import GeographicScope
from ..map_publication import (
    build_map_point_traceability,
    build_map_publication_contract,
    render_map_point_traceability_markdown,
    render_map_publication_contract_markdown,
    resolve_map_scope_policy,
)
from ..aadr import summarize_localities
from ..adna import build_tracked_animal_atlas_bundle
from ..models import MultiCountryMapReport, SampleRecord
from .paths import AtlasBundlePaths
from .summary_builders.atlas import build_multi_country_bundle_manifest

__all__ = ["publish_multi_country_map_bundle"]


def publish_multi_country_map_bundle(
    staging_output_dir: Path,
    *,
    report: MultiCountryMapReport,
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    country_sample_counts: dict[str, int],
    all_samples: tuple[SampleRecord, ...],
    context_root: Path | None,
    geography_scope: GeographicScope | None,
    asset_base_path: str,
    build_atlas_bundle_paths_fn: Callable[..., AtlasBundlePaths],
    build_context_layers_fn: Callable[
        ...,
        tuple[list[dict[str, object]], list[dict[str, object]], list[tuple[str, str]]],
    ],
    build_multi_country_map_summary_fn: Callable[..., dict[str, object]],
    build_samples_geojson_fn: Callable[[Iterable[SampleRecord]], JsonObject],
    copy_map_assets_fn: Callable[[Path], Path],
    render_multi_country_map_html_fn: Callable[..., str],
    render_multi_country_map_markdown_fn: Callable[..., str],
    write_summary_json_fn: Callable[[Path, dict[str, object]], None],
) -> None:
    """Write the full atlas bundle into one staging directory."""
    bundle_paths = build_atlas_bundle_paths_fn(
        output_dir=staging_output_dir, slug=report.slug, version=version
    )
    map_geojson = build_samples_geojson_fn(all_samples)
    bundle_paths.samples_geojson_path.write_text(
        json.dumps(map_geojson, indent=2), encoding="utf-8"
    )
    point_layers, polygon_layers, extra_artifacts = build_context_layers_fn(
        samples=all_samples,
        version=version,
        output_dir=staging_output_dir,
        context_root=context_root,
        geography_scope=geography_scope,
    )
    animal_localities = ()
    animal_coordinate_review = AnimalCoordinateVisibilityReview(
        direct_coordinate_feature_count=0,
        named_site_geocoded_feature_count=0,
        weaker_geography_feature_count=0,
    )
    if context_root is not None:
        animal_bundle = build_tracked_animal_atlas_bundle(
            data_root=context_root,
            output_dir=staging_output_dir,
            atlas_slug=report.slug,
            geography_scope=geography_scope,
        )
        point_layers.extend(animal_bundle.point_layers)
        extra_artifacts.extend(animal_bundle.extra_artifacts)
        animal_localities = animal_bundle.localities
        animal_coordinate_review = AnimalCoordinateVisibilityReview(
            direct_coordinate_feature_count=animal_bundle.coordinate_review.direct_coordinate_feature_count,
            named_site_geocoded_feature_count=animal_bundle.coordinate_review.named_site_geocoded_feature_count,
            weaker_geography_feature_count=animal_bundle.coordinate_review.weaker_geography_feature_count,
        )
    _attach_traceability_surfaces(point_layers, bundle_paths)
    animal_atlas_summary = _build_animal_atlas_summary(
        point_layers,
        animal_localities,
        animal_coordinate_review,
    )
    map_policy = resolve_map_scope_policy(geography_scope)
    point_traceability = build_map_point_traceability(
        report=report,
        point_layers=point_layers,
    )
    write_summary_json_fn(
        bundle_paths.map_point_traceability_json_path,
        point_traceability,
    )
    bundle_paths.map_point_traceability_markdown_path.write_text(
        render_map_point_traceability_markdown(point_traceability),
        encoding="utf-8",
    )
    map_publication_contract = build_map_publication_contract(
        report=report,
        policy=map_policy,
        point_layers=point_layers,
        polygon_layers=polygon_layers,
        countries=countries,
        map_html_name=bundle_paths.map_html_path.name,
        summary_json_name=bundle_paths.summary_json_path.name,
        traceability_json_name=bundle_paths.map_point_traceability_json_path.name,
    )
    write_summary_json_fn(
        bundle_paths.map_publication_contract_json_path,
        map_publication_contract,
    )
    bundle_paths.map_publication_contract_markdown_path.write_text(
        render_map_publication_contract_markdown(map_publication_contract),
        encoding="utf-8",
    )
    summarized_localities = tuple(summarize_localities(all_samples))
    context_points = _extract_context_points(point_layers)
    evidence_surface = build_atlas_evidence_surface(
        countries=countries,
        human_localities=summarized_localities,
        animal_localities=animal_localities,
        context_points=context_points,
    )
    write_atlas_evidence_surface_json(
        bundle_paths.evidence_surface_json_path,
        evidence_surface,
    )
    bundle_paths.evidence_surface_markdown_path.write_text(
        render_atlas_evidence_surface_markdown(evidence_surface),
        encoding="utf-8",
    )
    scientific_review = build_scientific_review_surface(
        countries=countries,
        human_localities=summarized_localities,
        animal_localities=animal_localities,
        context_points=context_points,
        animal_coordinate_review=animal_coordinate_review,
    )
    write_scientific_review_surface_json(
        bundle_paths.scientific_review_json_path,
        scientific_review,
    )
    bundle_paths.scientific_review_markdown_path.write_text(
        render_scientific_review_surface_markdown(scientific_review),
        encoding="utf-8",
    )
    ranked_sites = rank_localities(
        summarized_localities,
        context_points,
        profile_name="atlas_exploration",
    )
    sensitivity_report = build_ranking_sensitivity_report(
        summarized_localities,
        context_points,
    )
    ranking_engine_manifest = build_ranking_engine_manifest()
    write_candidate_sites_csv(bundle_paths.candidate_sites_csv_path, ranked_sites)
    write_candidate_sites_json(bundle_paths.candidate_sites_json_path, ranked_sites)
    bundle_paths.candidate_sites_markdown_path.write_text(
        render_candidate_site_markdown(ranked_sites, title=title),
        encoding="utf-8",
    )
    write_candidate_site_sensitivity_json(
        bundle_paths.candidate_site_sensitivity_json_path,
        sensitivity_report,
    )
    bundle_paths.candidate_site_sensitivity_markdown_path.write_text(
        render_candidate_site_sensitivity_markdown(sensitivity_report, title=title),
        encoding="utf-8",
    )
    bundle_paths.candidate_ranking_engine_manifest_path.write_text(
        json.dumps(ranking_engine_manifest.as_dict(), indent=2),
        encoding="utf-8",
    )
    extra_artifacts.extend(
        [
            ("Candidate site ranking CSV", bundle_paths.candidate_sites_csv_path.name),
            ("Candidate site ranking JSON", bundle_paths.candidate_sites_json_path.name),
            (
                "Candidate site ranking markdown",
                bundle_paths.candidate_sites_markdown_path.name,
            ),
            (
                "Candidate site sensitivity JSON",
                bundle_paths.candidate_site_sensitivity_json_path.name,
            ),
            (
                "Candidate site sensitivity markdown",
                bundle_paths.candidate_site_sensitivity_markdown_path.name,
            ),
            (
                "Candidate ranking engine manifest",
                bundle_paths.candidate_ranking_engine_manifest_path.name,
            ),
            (
                "Atlas evidence surface JSON",
                bundle_paths.evidence_surface_json_path.name,
            ),
            (
                "Atlas evidence surface markdown",
                bundle_paths.evidence_surface_markdown_path.name,
            ),
            (
                "Atlas scientific review JSON",
                bundle_paths.scientific_review_json_path.name,
            ),
            (
                "Atlas scientific review markdown",
                bundle_paths.scientific_review_markdown_path.name,
            ),
        ]
    )
    write_summary_json_fn(
        bundle_paths.bundle_manifest_path,
        build_multi_country_bundle_manifest(
            report,
            bundle_paths,
            extra_artifacts,
            map_publication_contract=map_publication_contract,
            animal_atlas_summary=animal_atlas_summary,
        ),
    )
    copy_map_assets_fn(staging_output_dir)
    write_summary_json_fn(
        bundle_paths.summary_json_path,
        build_multi_country_map_summary_fn(
            report,
            bundle_paths,
            extra_artifacts,
            map_publication_contract=map_publication_contract,
            animal_atlas_summary=animal_atlas_summary,
        ),
    )
    bundle_paths.map_html_path.write_text(
        render_multi_country_map_html_fn(
            title=title,
            version=version,
            generated_on=generated_on,
            countries=countries,
            policy=map_policy,
            point_layers=point_layers,
            polygon_layers=polygon_layers,
            asset_base_path=asset_base_path,
        ),
        encoding="utf-8",
    )
    bundle_paths.readme_path.write_text(
        render_multi_country_map_markdown_fn(
            title=title,
            version=version,
            generated_on=generated_on,
            countries=countries,
            country_sample_counts=country_sample_counts,
            map_html_name=bundle_paths.map_html_path.name,
            geojson_name=bundle_paths.samples_geojson_path.name,
            summary_json_name=bundle_paths.summary_json_path.name,
            map_publication_contract_json_name=(
                bundle_paths.map_publication_contract_json_path.name
            ),
            map_publication_contract_markdown_name=(
                bundle_paths.map_publication_contract_markdown_path.name
            ),
            point_traceability_json_name=(
                bundle_paths.map_point_traceability_json_path.name
            ),
            point_traceability_markdown_name=(
                bundle_paths.map_point_traceability_markdown_path.name
            ),
            extra_artifacts=extra_artifacts,
            map_publication_contract=map_publication_contract,
            animal_atlas_summary=animal_atlas_summary,
        ),
        encoding="utf-8",
    )


def _extract_context_points(
    point_layers: list[dict[str, object]],
) -> tuple[ContextPointRecord, ...]:
    records: list[ContextPointRecord] = []
    for layer in point_layers:
        if str(layer.get("group", "")).strip() == "primary-evidence":
            continue
        raw_points = layer.get("features")
        if not isinstance(raw_points, list):
            continue
        for raw_point in raw_points:
            if not isinstance(raw_point, dict):
                continue
            latitude = raw_point.get("latitude")
            longitude = raw_point.get("longitude")
            if not isinstance(latitude, (int, float)) or not isinstance(
                longitude, (int, float)
            ):
                continue
            records.append(
                ContextPointRecord(
                    source=str(layer.get("source_name", "")),
                    layer_key=str(layer.get("key", "")),
                    layer_label=str(layer.get("label", "")),
                    category=str(raw_point.get("subtitle", "")),
                    country=str(raw_point.get("country", "")),
                    record_id=str(raw_point.get("title", "")),
                    name=str(raw_point.get("title", "")),
                    latitude=float(latitude),
                    longitude=float(longitude),
                    geometry_type="Point",
                    subtitle=str(raw_point.get("subtitle", "")),
                    description=str(layer.get("description", "")),
                    source_url=str(raw_point.get("source_url", "")),
                    record_count=_as_optional_int(layer.get("count")) or 1,
                    popup_rows=(),
                    time_start_bp=_as_optional_int(raw_point.get("time_start_bp")),
                    time_end_bp=_as_optional_int(raw_point.get("time_end_bp")),
                    time_mean_bp=_as_optional_int(raw_point.get("time_mean_bp")),
                    time_label=str(raw_point.get("time_label", "")),
                )
            )
    return tuple(records)


def _as_optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    return None


def _build_animal_atlas_summary(
    point_layers: list[dict[str, object]],
    animal_localities: tuple[object, ...],
    animal_coordinate_review: AnimalCoordinateVisibilityReview,
) -> dict[str, object]:
    animal_layers = [
        layer
        for layer in point_layers
        if str(layer.get("group", "")).strip()
        in {"animal-domesticated-evidence", "animal-comparator-evidence"}
    ]
    species_layers = [
        {
            "latin_name": str(layer.get("species_latin_name", "")),
            "common_name": str(layer.get("species_common_name", "")),
            "animal_scope": str(layer.get("animal_scope", "")),
            "locality_count": int(layer.get("count", 0) or 0),
        }
        for layer in animal_layers
    ]
    chronology_buckets = sorted(
        {
            str(feature.get("chronology_bucket", "")).strip()
            for layer in animal_layers
            for feature in layer.get("features", [])
            if isinstance(feature, dict) and str(feature.get("chronology_bucket", "")).strip()
        }
    )
    coordinate_confidence_counts: dict[str, int] = {}
    for layer in animal_layers:
        for feature in layer.get("features", []):
            if not isinstance(feature, dict):
                continue
            confidence = str(feature.get("coordinate_confidence", "")).strip()
            if not confidence:
                continue
            coordinate_confidence_counts[confidence] = (
                coordinate_confidence_counts.get(confidence, 0) + 1
            )
    visible_caveats = [
        "Approximate or inferred coordinates remain visible with explicit warnings.",
        "Comparator-only evidence remains visible without being counted as domesticated-core support.",
        "Weak or rejected support classes remain labeled in point popups instead of being silently hidden.",
        "Nordic relevance can remain regional rather than one exact named country.",
    ]
    return {
        "total_locality_points": len(animal_localities),
        "direct_coordinate_feature_count": animal_coordinate_review.direct_coordinate_feature_count,
        "named_site_geocoded_feature_count": animal_coordinate_review.named_site_geocoded_feature_count,
        "weaker_geography_feature_count": animal_coordinate_review.weaker_geography_feature_count,
        "total_species": len(species_layers),
        "domesticated_species_count": sum(
            1 for row in species_layers if row["animal_scope"] == "domesticated_core"
        ),
        "comparator_species_count": sum(
            1 for row in species_layers if row["animal_scope"] == "comparator"
        ),
        "layer_groups": [
            "Domesticated-core animal evidence",
            "Comparator animal evidence",
        ]
        if species_layers
        else [],
        "filter_surfaces": [
            "Species focus",
            "Animal scope",
            "Coordinate confidence",
            "Chronology bucket",
            "Nordic animal leads only",
        ]
        if species_layers
        else [],
        "ui_surfaces": [
            "Animal evidence summary panel",
            "Citation-aware animal popups",
            "Species and confidence legend sections",
        ]
        if species_layers
        else [],
        "chronology_buckets": chronology_buckets,
        "coordinate_confidence_counts": coordinate_confidence_counts,
        "visible_caveats": visible_caveats if species_layers else [],
        "species_layers": species_layers,
    }


def _attach_traceability_surfaces(
    point_layers: list[dict[str, object]],
    bundle_paths: AtlasBundlePaths,
) -> None:
    for layer in point_layers:
        layer_key = str(layer.get("key", "")).strip()
        if layer_key == "aadr":
            layer["traceability_artifact"] = bundle_paths.samples_geojson_path.name
            continue
        if str(layer.get("group", "")).strip() in {
            "animal-domesticated-evidence",
            "animal-comparator-evidence",
        }:
            layer["traceability_artifact"] = (
                bundle_paths.animal_point_traceability_json_path.name
            )
