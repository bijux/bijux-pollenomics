from __future__ import annotations

from ..models import SourceFamilyContract, SourceFamilyLayerContract


def build_hyde_source_family_contract() -> SourceFamilyContract:
    """Declare required host products without asserting native release admission."""
    return SourceFamilyContract(
        source_key="hyde",
        display_name="HYDE 3.5 modeled land-use context",
        domain_group="modelled_land_use_context",
        evidence_role="external_model_comparison",
        primary_question=(
            "How do separately admitted HYDE 3.5 modeled quantities compare at "
            "matched spatial and temporal support, with independent inputs audited?"
        ),
        raw_layer=SourceFamilyLayerContract(
            layer_key="raw",
            repository_path="data/hyde/3.5/raw",
            required=True,
            purpose="native release inventory, exact captured files and release-specific rights",
            example_artifacts=("data/hyde/3.5/raw/source_manifest.json",),
        ),
        normalized_layer=SourceFamilyLayerContract(
            layer_key="normalized",
            repository_path="data/hyde/3.5/normalized",
            required=True,
            purpose="admitted native grid/time/variable/scenario products preserving units and missingness",
            example_artifacts=("data/hyde/3.5/normalized/manifest.json",),
        ),
        reviewed_layer=SourceFamilyLayerContract(
            layer_key="reviewed",
            repository_path="data/hyde/3.5/review",
            required=True,
            purpose="qualified source semantics, country inclusion and shared-input comparison review",
            example_artifacts=("data/hyde/3.5/review/source_review.json",),
        ),
        published_layer=SourceFamilyLayerContract(
            layer_key="published",
            repository_path="docs/report/regions/nordic/hyde/3.5",
            required=True,
            purpose="matched modeled-context comparisons with denominators and limitations",
            example_artifacts=("docs/report/regions/nordic/hyde/3.5/manifest.json",),
        ),
        coverage_metric_keys=(
            "hyde_admitted_cell_count",
            "hyde_admitted_country_count",
        ),
    )
