from __future__ import annotations

from .models import SourceFamilyContract, SourceFamilyLayerContract


def build_pollen_source_family_contracts() -> tuple[SourceFamilyContract, ...]:
    return (
        SourceFamilyContract(
            source_key="landclim",
            display_name="LandClim pollen context",
            domain_group="pollen_context",
            evidence_role="primary_context",
            primary_question=(
                "Which tracked LandClim pollen-site records exist and survive "
                "normalization into map-ready context layers?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/landclim/raw",
                required=True,
                purpose="tracked upstream pollen-site source capture",
                example_artifacts=("data/landclim/raw/landclim_sources.json",),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/landclim/normalized",
                required=True,
                purpose="tracked pollen-site and grid outputs prepared for interpretation",
                example_artifacts=(
                    "data/landclim/normalized/nordic_pollen_site_sequences.geojson",
                    "data/landclim/normalized/nordic_reveals_grid_cells.geojson",
                    "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson",
                    "data/landclim/normalized/landclim_bibliography.json",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/landclim/review",
                required=True,
                purpose="source-specific review of temporal support and normalization quality",
                example_artifacts=("data/landclim/review/spatiotemporal_review.json",),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/world",
                required=True,
                purpose="published pollen-context layers used in atlas outputs",
                example_artifacts=(
                    "docs/report/regions/nordic/nordic_pollen_sites.geojson",
                    "docs/report/regions/nordic/nordic_reveals_temporal_grid_cells.geojson",
                ),
            ),
            coverage_metric_keys=(
                "landclim_site_count",
                "landclim_grid_cell_count",
                "landclim_temporal_grid_feature_count",
            ),
        ),
        SourceFamilyContract(
            source_key="neotoma",
            display_name="Neotoma pollen context",
            domain_group="pollen_context",
            evidence_role="primary_context",
            primary_question=(
                "Which tracked Neotoma pollen records survive normalization and "
                "remain visible in atlas-ready context layers?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/neotoma/raw",
                required=True,
                purpose="tracked Neotoma acquisition and downloaded source tables",
                example_artifacts=("data/neotoma/raw/neotoma_pollen_sites.json",),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/neotoma/normalized",
                required=True,
                purpose="tracked normalized Neotoma context ready for downstream layering",
                example_artifacts=(
                    "data/neotoma/normalized/nordic_pollen_sites.geojson",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/neotoma/review",
                required=True,
                purpose="site-level temporal comparability review for Neotoma pollen context",
                example_artifacts=("data/neotoma/review/temporal_review.json",),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/world",
                required=True,
                purpose="published Neotoma context layers used in atlas outputs",
                example_artifacts=(
                    "docs/report/regions/nordic/nordic_pollen_sites.geojson",
                ),
            ),
            coverage_metric_keys=("neotoma_point_count",),
        ),
    )
