from __future__ import annotations

from .models import SourceFamilyContract, SourceFamilyLayerContract


def build_hydrography_source_family_contracts() -> tuple[SourceFamilyContract, ...]:
    return (
        SourceFamilyContract(
            source_key="svar",
            display_name="SMHI SVAR lake registry",
            domain_group="hydrography_context",
            evidence_role="sampling_domain",
            primary_question=(
                "Which official Sweden lake-register geometries and stable lake "
                "identities are available for sampling-oriented ranking?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/svar/raw",
                required=True,
                purpose="tracked SMHI SVAR WFS capture metadata and source manifest",
                example_artifacts=("data/svar/raw/svar_lake_registry_manifest.json",),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/svar/normalized",
                required=True,
                purpose="tracked normalized Sweden lake registry with stable lake identities and geometry",
                example_artifacts=(
                    "data/svar/normalized/sweden_lake_registry.geojson",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/svar/review",
                required=True,
                purpose="source-specific review of evidence-linked lake identity, area, and sampling readiness",
                example_artifacts=(
                    "data/svar/review/lake_candidate_registry_review.json",
                    "data/svar/review/sweden_lake_candidate_registry.geojson",
                ),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/countries/sweden",
                required=True,
                purpose="published Sweden lake ranking and fieldwork surfaces derived from the official lake registry",
                example_artifacts=(
                    "docs/report/countries/sweden/sweden_lake_evidence_richness_v66.geojson",
                ),
            ),
            coverage_metric_keys=("svar_lake_count",),
        ),
    )
