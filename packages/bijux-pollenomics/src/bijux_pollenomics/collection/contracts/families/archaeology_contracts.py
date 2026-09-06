from __future__ import annotations

from ..capabilities import SEAD_ADMITTED_ACQUISITION_ADMISSION
from .models import SourceFamilyContract, SourceFamilyLayerContract


def build_archaeology_source_family_contracts() -> tuple[SourceFamilyContract, ...]:
    return (
        SourceFamilyContract(
            source_key="sead",
            display_name="SEAD archaeology context",
            domain_group="archaeology_context",
            evidence_role="contextual_domain",
            primary_question=(
                "Which SEAD records are captured, normalized, and still safe to use "
                "as contextual archaeology layers?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/sead/raw",
                required=True,
                purpose="admitted SEAD acquisition and exact site payload capture",
                example_artifacts=(
                    SEAD_ADMITTED_ACQUISITION_ADMISSION,
                    SEAD_ADMITTED_ACQUISITION_ADMISSION.replace(
                        "admission.json", "payloads/tbl_sites.json"
                    ),
                ),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/sead/normalized",
                required=True,
                purpose="tracked normalized SEAD context ready for downstream use",
                example_artifacts=(
                    "data/sead/normalized/nordic_environmental_sites.geojson",
                    "data/sead/normalized/nordic_temporal_evidence.geojson",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/sead/review",
                required=True,
                purpose="site-level access, temporal, and normalization-legibility review for SEAD archaeology context",
                example_artifacts=(
                    "data/sead/review/evidence_legibility_review.json",
                    "data/sead/review/access_model.json",
                ),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/world",
                required=True,
                purpose="published archaeology context layers used in atlas outputs",
                example_artifacts=(
                    "docs/report/regions/nordic/nordic_environmental_sites.geojson",
                ),
            ),
            coverage_metric_keys=("sead_point_count",),
        ),
        SourceFamilyContract(
            source_key="raa",
            display_name="RAÄ archaeology context",
            domain_group="archaeology_context",
            evidence_role="contextual_domain",
            primary_question=(
                "Which Sweden-scoped archaeology context layers are captured and "
                "published from RAÄ?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/raa/raw",
                required=True,
                purpose="tracked RAÄ source capture",
                example_artifacts=("data/raa/raw/fornsok_domains.json",),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/raa/normalized",
                required=True,
                purpose="tracked normalized archaeology layers used in density and map products",
                example_artifacts=(
                    "data/raa/normalized/sweden_archaeology_layer.json",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/raa/review",
                required=True,
                purpose="source-specific review of temporal support and publication limits",
                example_artifacts=("data/raa/review/spatiotemporal_review.json",),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/world",
                required=True,
                purpose="published archaeology density and context layers",
                example_artifacts=(
                    "docs/report/regions/nordic/sweden_archaeology_density.geojson",
                ),
            ),
            coverage_metric_keys=("raa_total_site_count", "raa_heritage_site_count"),
        ),
    )
