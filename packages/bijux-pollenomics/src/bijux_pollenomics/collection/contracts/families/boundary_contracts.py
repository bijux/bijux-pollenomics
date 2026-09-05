from __future__ import annotations

from .models import SourceFamilyContract, SourceFamilyLayerContract


def build_boundary_source_family_contracts() -> tuple[SourceFamilyContract, ...]:
    return (
        SourceFamilyContract(
            source_key="boundaries",
            display_name="Boundary framing",
            domain_group="framing_context",
            evidence_role="framing_domain",
            primary_question=(
                "Which tracked framing geometries constrain interpretation of country "
                "and atlas outputs?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/boundaries/raw",
                required=True,
                purpose="tracked upstream boundary geometry capture",
                example_artifacts=("data/boundaries/raw/sweden.geojson",),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/boundaries/normalized",
                required=True,
                purpose="tracked normalized boundary layers ready for publication",
                example_artifacts=(
                    "data/boundaries/normalized/nordic_country_boundaries.geojson",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/boundaries/review",
                required=True,
                purpose="source-specific review of geometry coverage and framing limits",
                example_artifacts=(
                    "data/boundaries/review/boundary_review.json",
                    "data/boundaries/review/manifest.json",
                    "data/boundaries/review/country-decisions/animal_adna.json",
                    "data/boundaries/review/country-decisions/landclim.json",
                    "data/boundaries/review/country-decisions/neotoma.json",
                    "data/boundaries/review/country-decisions/sead.json",
                ),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/world",
                required=True,
                purpose="published boundary layers used in map framing",
                example_artifacts=(
                    "docs/report/regions/nordic/nordic_country_boundaries.geojson",
                ),
            ),
            coverage_metric_keys=("boundary_country_count",),
        ),
    )
