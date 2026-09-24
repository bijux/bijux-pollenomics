"""Layer contracts for evidence-reviewed reference sources."""

from __future__ import annotations

from ..models import SourceFamilyContract, SourceFamilyLayerContract

EMPD2_REVIEW_EVIDENCE = "data/empd2/review/country_coverage_evidence.json"
NFI_REVIEW_EVIDENCE = "data/nfi/review/country_coverage_evidence.json"


def build_reference_source_family_contracts() -> tuple[SourceFamilyContract, ...]:
    """Declare reference sources without promoting review artifacts to products."""
    return (_empd2_contract(), _nfi_contract())


def _empd2_contract() -> SourceFamilyContract:
    return SourceFamilyContract(
        source_key="empd2",
        display_name="EMPD2 pollen reference source",
        domain_group="pollen_reference",
        evidence_role="candidate_reference_observations",
        primary_question=(
            "Which source-bound EMPD2 records have review evidence sufficient for "
            "future admission without treating candidate review as publication?"
        ),
        raw_layer=SourceFamilyLayerContract(
            layer_key="raw",
            repository_path="data/empd2/raw",
            required=True,
            purpose="admitted immutable EMPD2 source capture and custody receipt",
            example_artifacts=("data/empd2/raw/source_manifest.json",),
        ),
        normalized_layer=SourceFamilyLayerContract(
            layer_key="normalized",
            repository_path="data/empd2/normalized",
            required=True,
            purpose="source-bound sites, samples, taxa and sealed count observations",
            example_artifacts=("data/empd2/normalized/manifest.json",),
        ),
        reviewed_layer=SourceFamilyLayerContract(
            layer_key="reviewed",
            repository_path="data/empd2/review",
            required=True,
            purpose="candidate identity, provenance and pairing review evidence",
            example_artifacts=(EMPD2_REVIEW_EVIDENCE,),
        ),
        published_layer=SourceFamilyLayerContract(
            layer_key="published",
            repository_path="docs/report/regions/nordic/empd2",
            required=True,
            purpose="admitted EMPD2 reference observations with explicit denominators",
            example_artifacts=("docs/report/regions/nordic/empd2/manifest.json",),
        ),
        coverage_metric_keys=(
            "empd2_source_reported_sample_count",
            "empd2_source_reported_observation_count",
            "empd2_mechanical_candidate_count",
            "empd2_unresolved_overlap_lead_count",
            "empd2_scientifically_admitted_record_count",
        ),
    )


def _nfi_contract() -> SourceFamilyContract:
    return SourceFamilyContract(
        source_key="nfi",
        display_name="Swedish NFI vegetation reference source",
        domain_group="vegetation_reference",
        evidence_role="candidate_reference_observations",
        primary_question=(
            "Which source-bound Swedish NFI plot-year records have structural review "
            "evidence without opening or publishing held-out vegetation outcomes?"
        ),
        raw_layer=SourceFamilyLayerContract(
            layer_key="raw",
            repository_path="data/nfi/raw",
            required=True,
            purpose="admitted immutable NFI workbook capture and rights receipt",
            example_artifacts=("data/nfi/raw/source_manifest.json",),
        ),
        normalized_layer=SourceFamilyLayerContract(
            layer_key="normalized",
            repository_path="data/nfi/normalized",
            required=True,
            purpose="source-bound plot-year identities with sealed vegetation outcomes",
            example_artifacts=("data/nfi/normalized/manifest.json",),
        ),
        reviewed_layer=SourceFamilyLayerContract(
            layer_key="reviewed",
            repository_path="data/nfi/review",
            required=True,
            purpose="outcome-blind workbook schema and candidate spatial review evidence",
            example_artifacts=(NFI_REVIEW_EVIDENCE,),
        ),
        published_layer=SourceFamilyLayerContract(
            layer_key="published",
            repository_path="docs/report/regions/nordic/nfi",
            required=True,
            purpose="admitted NFI reference observations with governed support and units",
            example_artifacts=("docs/report/regions/nordic/nfi/manifest.json",),
        ),
        coverage_metric_keys=(
            "nfi_plot_year_record_count",
            "nfi_tract_plot_site_count",
            "nfi_proximity_lead_count",
            "nfi_scientifically_admitted_record_count",
        ),
    )
