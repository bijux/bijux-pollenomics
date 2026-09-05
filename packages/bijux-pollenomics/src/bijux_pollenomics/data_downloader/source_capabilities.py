from __future__ import annotations

from collections.abc import Mapping
import csv
from dataclasses import asdict, dataclass
import hashlib
import io
import json
from pathlib import Path
import stat

__all__ = [
    "CAPABILITY_DIMENSIONS",
    "NEOTOMA_CLASSIFICATION_EVIDENCE",
    "NEOTOMA_PROPAGATION_EVIDENCE",
    "SEAD_ADMITTED_ACQUISITION_ADMISSION",
    "SourceCapabilityProfile",
    "build_source_capability_audit_payload",
    "build_source_capability_contract_payload",
    "build_source_capability_profiles",
]


CAPABILITY_DIMENSIONS = (
    "site_identity",
    "coordinates",
    "four_country_coverage",
    "within_site_hierarchy",
    "numeric_chronology",
    "chronology_uncertainty",
    "relative_chronology",
    "taxon_identity",
    "native_ecological_class",
    "derived_pollen_group",
    "derived_ecological_role",
    "crop_cereal_resolution",
    "quantitative_observation",
    "observation_unit",
    "dataset_provenance",
    "pollen_propagation_event",
    "non_pollen_context",
)

SEAD_ADMITTED_ACQUISITION_ADMISSION = (
    "data/sead/raw/acquisitions/"
    "sead-live-d1fd2058913372eda1c12e526e0eb7c8a6cec415e9f9e9b5b92b8896597b35ac/"
    "admission.json"
)

# These repository-owned surfaces are deliberately absent until their governed
# producers are part of the deterministic data rebuild. Ignored release-working
# artifacts are not durable materialization evidence for a clean checkout.
NEOTOMA_CLASSIFICATION_EVIDENCE = "data/neotoma/review/classification_evidence.json"
NEOTOMA_PROPAGATION_EVIDENCE = "data/neotoma/derived/pollen_propagation_evidence.json"

_SUPPORT_STATUSES = frozenset({"supported", "partial", "unsupported"})
_MATERIALIZATION_STATUSES = frozenset(
    {"complete", "partial", "missing", "not_applicable"}
)
_NORMATIVE_CONTRACT_ID = "bijux-pollenomics-source-capability-matrix"
_NORMATIVE_CONTRACT_VERSION = "1.0.0"
_NORMATIVE_SOURCE_KEYS = (
    "animal_adna",
    "boundaries",
    "landclim",
    "neotoma",
    "raa",
    "sead",
    "svar",
)


@dataclass(frozen=True)
class SourceCapabilityProfile:
    source_key: str
    evidence_class: str
    allowed_role: str
    prohibited_claims: tuple[str, ...]
    support_by_dimension: dict[str, str]
    evidence_paths_by_dimension: dict[str, tuple[str, ...]]
    human_review_required: bool
    human_review_reason: str | None


@dataclass(frozen=True)
class _CapabilityAuditRow:
    source_key: str
    dimension: str
    support: str
    materialization: str
    evidence_paths: tuple[str, ...]
    present_evidence_paths: tuple[str, ...]
    missing_evidence_paths: tuple[str, ...]
    evidence_file_count: int
    required_evidence_count: int
    coverage_metrics: dict[str, int | None]
    human_review_required: bool
    reason_codes: tuple[str, ...]


def build_source_capability_profiles() -> tuple[SourceCapabilityProfile, ...]:
    """Declare source-native capability independently of repository state."""
    profiles = (
        _profile(
            "landclim",
            evidence_class="modelled_vegetation_or_land_cover",
            allowed_role="modelled vegetation and land-cover context",
            unsupported={"relative_chronology"},
            partial={
                "four_country_coverage",
                "within_site_hierarchy",
                "chronology_uncertainty",
                "taxon_identity",
                "derived_pollen_group",
                "derived_ecological_role",
                "crop_cereal_resolution",
                "dataset_provenance",
                "pollen_propagation_event",
            },
            evidence_paths=_source_evidence_paths("landclim"),
            prohibited_claims=(
                "model output is an observed pollen find",
                "model gradients prove migration or causation",
            ),
            human_review_reason="qualified_model_semantics_review_missing",
        ),
        _profile(
            "neotoma",
            evidence_class="observed_paleoecological",
            allowed_role="sample- and taxon-resolved observed pollen evidence",
            unsupported=set(),
            partial={
                "four_country_coverage",
                "chronology_uncertainty",
                "relative_chronology",
                "derived_pollen_group",
                "derived_ecological_role",
            },
            evidence_paths=_source_evidence_paths("neotoma"),
            prohibited_claims=(
                "site envelopes are first-occurrence events",
                "incompatible observation units are interchangeable",
            ),
            human_review_reason="qualified_ecological_classification_review_missing",
        ),
        _profile(
            "sead",
            evidence_class="observed_archaeological_environmental",
            allowed_role="multidisciplinary environmental archaeology evidence",
            unsupported=set(),
            partial={
                "four_country_coverage",
                "chronology_uncertainty",
                "derived_pollen_group",
                "derived_ecological_role",
                "crop_cereal_resolution",
                "pollen_propagation_event",
            },
            evidence_paths=_source_evidence_paths("sead"),
            prohibited_claims=(
                "site inventory presence is chronology",
                "context-only dates are pollen propagation events",
            ),
            human_review_reason="full_sead_observation_taxon_graph_not_materialized",
        ),
        _profile(
            "raa",
            evidence_class="archaeological_context",
            allowed_role="Sweden-only archaeological context",
            unsupported={
                "four_country_coverage",
                "taxon_identity",
                "native_ecological_class",
                "derived_pollen_group",
                "derived_ecological_role",
                "crop_cereal_resolution",
                "pollen_propagation_event",
            },
            partial={
                "within_site_hierarchy",
                "numeric_chronology",
                "chronology_uncertainty",
                "quantitative_observation",
                "observation_unit",
            },
            evidence_paths=_source_evidence_paths("raa"),
            prohibited_claims=(
                "named periods are numeric BP without a governed crosswalk",
                "archaeological density is population or pollen presence",
            ),
            human_review_reason="qualified_raa_source_review_missing",
        ),
        _profile(
            "svar",
            evidence_class="modern_environmental_context",
            allowed_role="Sweden lake identity and sampling context",
            unsupported={
                "four_country_coverage",
                "numeric_chronology",
                "chronology_uncertainty",
                "relative_chronology",
                "taxon_identity",
                "native_ecological_class",
                "derived_pollen_group",
                "derived_ecological_role",
                "crop_cereal_resolution",
                "pollen_propagation_event",
            },
            partial={"within_site_hierarchy", "dataset_provenance"},
            evidence_paths=_source_evidence_paths("svar"),
            prohibited_claims=(
                "modern lake attributes are historical pollen chronology",
                "environmental similarity is propagation",
            ),
            human_review_reason="qualified_svar_publication_review_missing",
        ),
        _profile(
            "aadr",
            evidence_class="human_ancient_dna",
            allowed_role="human ancient-DNA sample and locality context",
            unsupported={
                "native_ecological_class",
                "derived_pollen_group",
                "derived_ecological_role",
                "crop_cereal_resolution",
                "pollen_propagation_event",
            },
            partial={
                "four_country_coverage",
                "chronology_uncertainty",
                "relative_chronology",
                "quantitative_observation",
                "observation_unit",
            },
            evidence_paths=_source_evidence_paths("aadr"),
            prohibited_claims=(
                "human ancient DNA is pollen evidence",
                "co-occurrence proves ecological or demographic causation",
            ),
            human_review_reason="qualified_human_adna_source_review_missing",
        ),
        _profile(
            "animal_adna",
            evidence_class="observed_genetic_or_zooarchaeological",
            allowed_role="animal genetic and zooarchaeological context",
            unsupported={
                "derived_pollen_group",
                "derived_ecological_role",
                "crop_cereal_resolution",
                "pollen_propagation_event",
            },
            partial={
                "four_country_coverage",
                "chronology_uncertainty",
                "relative_chronology",
                "native_ecological_class",
                "quantitative_observation",
                "observation_unit",
            },
            evidence_paths=_source_evidence_paths("animal_adna"),
            prohibited_claims=(
                "animal ancient DNA is pollen evidence",
                "animal-human-pollen co-occurrence proves causation",
            ),
            human_review_reason="qualified_animal_adna_source_review_missing",
        ),
        _profile(
            "boundaries",
            evidence_class="geographic_framing",
            allowed_role="map framing and governed country assignment",
            unsupported={
                "within_site_hierarchy",
                "numeric_chronology",
                "chronology_uncertainty",
                "relative_chronology",
                "taxon_identity",
                "native_ecological_class",
                "derived_pollen_group",
                "derived_ecological_role",
                "crop_cereal_resolution",
                "quantitative_observation",
                "observation_unit",
                "pollen_propagation_event",
            },
            partial=set(),
            evidence_paths=_source_evidence_paths("boundaries"),
            prohibited_claims=(
                "modern borders are historical ecological barriers",
                "country framing supplies observations or chronology",
            ),
            human_review_reason="qualified_boundary_inclusion_review_missing",
        ),
    )
    _validate_profiles(profiles)
    return profiles


def build_source_capability_contract_payload() -> dict[str, object]:
    """Build the immutable source-support side of the capability contract."""
    profiles = build_source_capability_profiles()
    return {
        "schema_version": "source-capability-contract.v1",
        "dimension_count": len(CAPABILITY_DIMENSIONS),
        "source_count": len(profiles),
        "normative_contract": {
            "contract_id": _NORMATIVE_CONTRACT_ID,
            "schema_version": _NORMATIVE_CONTRACT_VERSION,
            "source_count": len(_NORMATIVE_SOURCE_KEYS),
            "source_keys": list(_NORMATIVE_SOURCE_KEYS),
        },
        "extension_sources": ["aadr"],
        "dimensions": list(CAPABILITY_DIMENSIONS),
        "sources": [asdict(profile) for profile in profiles],
    }


def build_source_capability_audit_payload(
    output_root: Path,
    *,
    coverage_metrics_by_source: Mapping[str, Mapping[str, int | None]],
    source_blockers: Mapping[str, tuple[str, ...]],
) -> dict[str, object]:
    """Observe repository materialization without changing source capability."""
    output_root = Path(output_root)
    rows: list[_CapabilityAuditRow] = []
    evidence_validity: dict[tuple[Path, str], bool] = {}
    for profile in build_source_capability_profiles():
        for dimension in CAPABILITY_DIMENSIONS:
            support = profile.support_by_dimension[dimension]
            evidence_paths = profile.evidence_paths_by_dimension[dimension]
            present_paths: list[str] = []
            for repository_path in evidence_paths:
                resolved_path = _resolve_path(output_root, repository_path)
                cache_key = (resolved_path, repository_path)
                if cache_key not in evidence_validity:
                    evidence_validity[cache_key] = _path_has_content(
                        resolved_path, repository_path
                    )
                if evidence_validity[cache_key]:
                    present_paths.append(repository_path)
            present = tuple(present_paths)
            missing = tuple(path for path in evidence_paths if path not in present)
            materialization = _materialization_status(
                support=support,
                evidence_paths=evidence_paths,
                present_evidence_paths=present,
            )
            reasons: list[str] = []
            if materialization == "not_applicable":
                reasons.append("source_dimension_unsupported")
            elif materialization == "missing":
                reasons.append("governed_dimension_evidence_missing")
            elif materialization == "complete":
                reasons.append("governed_dimension_evidence_complete")
            else:
                reasons.append("governed_dimension_evidence_incomplete")
            if materialization != "not_applicable":
                reasons.extend(source_blockers.get(profile.source_key, ()))
                if profile.human_review_required and profile.human_review_reason:
                    reasons.append(profile.human_review_reason)
            rows.append(
                _CapabilityAuditRow(
                    source_key=profile.source_key,
                    dimension=dimension,
                    support=support,
                    materialization=materialization,
                    evidence_paths=evidence_paths,
                    present_evidence_paths=present,
                    missing_evidence_paths=missing,
                    evidence_file_count=len(present),
                    required_evidence_count=len(evidence_paths),
                    coverage_metrics=dict(
                        coverage_metrics_by_source.get(profile.source_key, {})
                    ),
                    human_review_required=(
                        profile.human_review_required
                        and materialization != "not_applicable"
                    ),
                    reason_codes=tuple(dict.fromkeys(reasons)),
                )
            )
    return {
        "schema_version": "source-capability-materialization-audit.v1",
        "dimension_count": len(CAPABILITY_DIMENSIONS),
        "source_count": len(build_source_capability_profiles()),
        "row_count": len(rows),
        "support_vocabulary": sorted(_SUPPORT_STATUSES),
        "materialization_vocabulary": sorted(_MATERIALIZATION_STATUSES),
        "rows": [asdict(row) for row in rows],
    }


def _profile(
    source_key: str,
    *,
    evidence_class: str,
    allowed_role: str,
    unsupported: set[str],
    partial: set[str],
    evidence_paths: dict[str, tuple[str, ...]],
    prohibited_claims: tuple[str, ...],
    human_review_reason: str | None,
) -> SourceCapabilityProfile:
    support = {
        dimension: (
            "unsupported"
            if dimension in unsupported
            else "partial"
            if dimension in partial
            else "supported"
        )
        for dimension in CAPABILITY_DIMENSIONS
    }
    governed_evidence_paths = {
        dimension: () if dimension in unsupported else paths
        for dimension, paths in evidence_paths.items()
    }
    return SourceCapabilityProfile(
        source_key=source_key,
        evidence_class=evidence_class,
        allowed_role=allowed_role,
        prohibited_claims=prohibited_claims,
        support_by_dimension=support,
        evidence_paths_by_dimension=governed_evidence_paths,
        human_review_required=human_review_reason is not None,
        human_review_reason=human_review_reason,
    )


def _source_evidence_paths(source_key: str) -> dict[str, tuple[str, ...]]:
    """Return exact dimension-owned evidence, including deliberate missing targets."""
    acquisition = SEAD_ADMITTED_ACQUISITION_ADMISSION.rsplit("/", 1)[0]
    neotoma_observation_parts = tuple(
        f"data/neotoma/relational/surfaces/observations/part-{index:05d}.json"
        for index in range(1, 9)
    )
    evidence: dict[str, dict[str, tuple[str, ...]]] = {
        "landclim": {
            "site_identity": (
                "data/landclim/normalized/nordic_pollen_site_sequences.geojson",
            ),
            "coordinates": (
                "data/landclim/normalized/nordic_pollen_site_sequences.geojson",
            ),
            "four_country_coverage": ("data/country_dimension_coverage.json",),
            "within_site_hierarchy": ("data/landclim/normalized/site_hierarchy.json",),
            "numeric_chronology": (
                "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson",
                "data/landclim/review/spatiotemporal_review.json",
            ),
            "chronology_uncertainty": (
                "data/landclim/review/spatiotemporal_review.json",
            ),
            "taxon_identity": (
                "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv",
            ),
            "native_ecological_class": (
                "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv",
            ),
            "derived_pollen_group": (
                "data/landclim/derived/pollen_group_assignments.json",
            ),
            "derived_ecological_role": (
                "data/landclim/derived/ecological_role_assignments.json",
            ),
            "crop_cereal_resolution": (
                "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv",
            ),
            "quantitative_observation": (
                "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson",
            ),
            "observation_unit": (
                "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson",
            ),
            "dataset_provenance": ("data/landclim/raw/landclim_sources.json",),
            "pollen_propagation_event": (
                "data/landclim/derived/pollen_propagation_events.json",
            ),
            "non_pollen_context": (
                "data/landclim/normalized/nordic_reveals_grid_cells.geojson",
            ),
        },
        "neotoma": {
            "site_identity": (
                "data/neotoma/relational/surfaces/sites/part-00001.json",
            ),
            "coordinates": ("data/neotoma/relational/surfaces/sites/part-00001.json",),
            "four_country_coverage": ("data/country_dimension_coverage.json",),
            "within_site_hierarchy": (
                "data/neotoma/relational/surfaces/collection_units/part-00001.json",
                "data/neotoma/relational/surfaces/samples/part-00001.json",
            ),
            "numeric_chronology": (
                "data/neotoma/relational/surfaces/age_claims/part-00001.json",
            ),
            "chronology_uncertainty": (
                "data/neotoma/relational/surfaces/chronology_controls/part-00001.json",
            ),
            "relative_chronology": (
                "data/neotoma/relational/surfaces/relative_chronology/part-00001.json",
            ),
            "taxon_identity": (
                "data/neotoma/relational/surfaces/variables/part-00001.json",
            ),
            "native_ecological_class": (NEOTOMA_CLASSIFICATION_EVIDENCE,),
            "derived_pollen_group": (NEOTOMA_CLASSIFICATION_EVIDENCE,),
            "derived_ecological_role": (NEOTOMA_CLASSIFICATION_EVIDENCE,),
            "crop_cereal_resolution": (NEOTOMA_CLASSIFICATION_EVIDENCE,),
            "quantitative_observation": neotoma_observation_parts,
            "observation_unit": (
                "data/neotoma/relational/surfaces/variables/part-00001.json",
                *neotoma_observation_parts,
            ),
            "dataset_provenance": ("data/neotoma/relational/manifest.json",),
            "pollen_propagation_event": (NEOTOMA_PROPAGATION_EVIDENCE,),
            "non_pollen_context": (
                "data/neotoma/relational/surfaces/non_pollen_context/part-00001.json",
            ),
        },
        "sead": {
            "site_identity": (f"{acquisition}/payloads/tbl_sites.json",),
            "coordinates": (f"{acquisition}/payloads/tbl_sites.json",),
            "four_country_coverage": ("data/country_dimension_coverage.json",),
            "within_site_hierarchy": (
                f"{acquisition}/payloads/tbl_sample_groups.json",
                f"{acquisition}/payloads/tbl_physical_samples.json",
            ),
            "numeric_chronology": (
                f"{acquisition}/payloads/tbl_geochronology.json",
                f"{acquisition}/payloads/tbl_analysis_entity_ages.json",
            ),
            "chronology_uncertainty": (
                f"{acquisition}/payloads/tbl_dating_uncertainty.json",
            ),
            "relative_chronology": (
                f"{acquisition}/payloads/tbl_relative_ages.json",
                f"{acquisition}/payloads/tbl_relative_dates.json",
            ),
            "taxon_identity": (
                f"{acquisition}/payloads/tbl_abundances.json",
                f"{acquisition}/payloads/tbl_taxa_tree_master.json",
            ),
            "native_ecological_class": (
                f"{acquisition}/payloads/tbl_ecocodes.json",
                f"{acquisition}/payloads/tbl_ecocode_definitions.json",
                f"{acquisition}/payloads/tbl_ecocode_groups.json",
                f"{acquisition}/payloads/tbl_ecocode_systems.json",
            ),
            "derived_pollen_group": ("data/sead/derived/pollen_groups.json",),
            "derived_ecological_role": ("data/sead/derived/ecological_roles.json",),
            "crop_cereal_resolution": (
                "data/sead/derived/crop_cereal_resolution.json",
            ),
            "quantitative_observation": (
                f"{acquisition}/payloads/tbl_abundances.json",
                f"{acquisition}/payloads/tbl_analysis_numerical_values.json",
                f"{acquisition}/payloads/tbl_analysis_integer_values.json",
                f"{acquisition}/payloads/tbl_analysis_categorical_values.json",
                f"{acquisition}/payloads/tbl_analysis_boolean_values.json",
                f"{acquisition}/payloads/tbl_measured_values.json",
            ),
            "observation_unit": (
                f"{acquisition}/payloads/tbl_value_types.json",
                f"{acquisition}/payloads/tbl_dimensions.json",
                f"{acquisition}/payloads/tbl_units.json",
            ),
            "dataset_provenance": (SEAD_ADMITTED_ACQUISITION_ADMISSION,),
            "pollen_propagation_event": (
                "data/sead/derived/pollen_propagation_events.json",
            ),
            "non_pollen_context": (f"{acquisition}/payloads/tbl_sites.json",),
        },
        "raa": {
            "site_identity": ("data/raa/normalized/sweden_archaeology_layer.json",),
            "coordinates": ("data/raa/normalized/sweden_archaeology_layer.json",),
            "within_site_hierarchy": ("data/raa/normalized/site_hierarchy.json",),
            "numeric_chronology": ("data/raa/review/spatiotemporal_review.json",),
            "chronology_uncertainty": ("data/raa/review/spatiotemporal_review.json",),
            "relative_chronology": ("data/raa/review/spatiotemporal_review.json",),
            "quantitative_observation": (
                "data/raa/normalized/sweden_archaeology_density.geojson",
            ),
            "observation_unit": ("data/raa/review/spatiotemporal_review.json",),
            "dataset_provenance": ("data/raa/raw/fornsok_domains.json",),
            "non_pollen_context": (
                "data/raa/normalized/sweden_archaeology_layer.json",
            ),
        },
        "svar": {
            "site_identity": (
                "data/svar/review/sweden_lake_candidate_registry.geojson",
            ),
            "coordinates": ("data/svar/review/sweden_lake_candidate_registry.geojson",),
            "within_site_hierarchy": (
                "data/svar/normalized/sweden_lake_hierarchy.json",
            ),
            "quantitative_observation": (
                "data/svar/review/sweden_lake_candidate_registry.geojson",
            ),
            "observation_unit": (
                "data/svar/review/sweden_lake_candidate_registry.geojson",
            ),
            "dataset_provenance": ("data/svar/raw/svar_lake_registry_manifest.json",),
            "non_pollen_context": (
                "data/svar/review/sweden_lake_candidate_registry.geojson",
            ),
        },
        "aadr": {
            "site_identity": (
                "docs/report/countries/sweden/sweden_aadr_v66_localities.csv",
            ),
            "coordinates": (
                "docs/report/countries/sweden/sweden_aadr_v66_samples.geojson",
            ),
            "four_country_coverage": ("data/country_dimension_coverage.json",),
            "within_site_hierarchy": (
                "docs/report/countries/sweden/sweden_aadr_v66_localities.csv",
            ),
            "numeric_chronology": (
                "docs/report/countries/sweden/sweden_aadr_v66_samples.csv",
            ),
            "chronology_uncertainty": (
                "docs/report/countries/sweden/sweden_aadr_v66_bundle.json",
            ),
            "relative_chronology": (
                "docs/report/countries/sweden/sweden_aadr_v66_relative_chronology.json",
            ),
            "taxon_identity": ("data/aadr/v66/taxon_identity.json",),
            "quantitative_observation": (
                "data/aadr/v66/1240k/v66.1240K.aadr.PUB.anno",
            ),
            "observation_unit": ("data/aadr/v66/1240k/v66.1240K.aadr.PUB.anno",),
            "dataset_provenance": ("data/aadr/v66/release_manifest.json",),
            "non_pollen_context": (
                "docs/report/countries/sweden/sweden_aadr_v66_bundle.json",
            ),
        },
        "animal_adna": {
            "site_identity": (
                "data/adna/governance/source_library/project_sample_site_review.json",
            ),
            "coordinates": ("data/adna/governance/coordinate_caveat_surface.json",),
            "four_country_coverage": ("data/country_dimension_coverage.json",),
            "within_site_hierarchy": (
                "data/adna/governance/source_library/project_locality_completeness.json",
            ),
            "numeric_chronology": (
                "data/adna/governance/source_library/sample_chronology_normalization_audit.json",
            ),
            "chronology_uncertainty": (
                "data/adna/governance/source_library/sample_chronology_precision_audit.json",
            ),
            "relative_chronology": (
                "data/adna/governance/source_library/sample_chronology_review.json",
            ),
            "taxon_identity": (
                "data/adna/governance/source_library/project_registry.json",
            ),
            "native_ecological_class": (
                "data/adna/governance/native_ecological_classification.json",
            ),
            "quantitative_observation": (
                "data/adna/governance/animal_quantitative_observations.json",
            ),
            "observation_unit": ("data/adna/governance/animal_observation_units.json",),
            "dataset_provenance": (
                "data/adna/governance/source_library/source_artifact_index.json",
            ),
            "non_pollen_context": (
                "data/adna/governance/animal_sample_foundation_truth.json",
            ),
        },
        "boundaries": {
            "site_identity": (
                "data/boundaries/normalized/nordic_country_boundaries.geojson",
            ),
            "coordinates": (
                "data/boundaries/normalized/nordic_country_boundaries.geojson",
            ),
            "four_country_coverage": (
                "data/boundaries/normalized/nordic_country_boundaries.geojson",
                "data/country_dimension_coverage.json",
            ),
            "dataset_provenance": ("data/boundaries/raw/source_manifest.json",),
            "non_pollen_context": (
                "data/boundaries/normalized/nordic_country_boundaries.geojson",
            ),
        },
    }
    try:
        source_evidence = evidence[source_key]
    except KeyError as exc:
        raise ValueError(f"unknown source capability profile: {source_key}") from exc
    return {
        dimension: source_evidence.get(dimension, ())
        for dimension in CAPABILITY_DIMENSIONS
    }


def _validate_profiles(profiles: tuple[SourceCapabilityProfile, ...]) -> None:
    source_keys = [profile.source_key for profile in profiles]
    if len(source_keys) != len(set(source_keys)):
        raise ValueError("source capability profiles contain duplicate source keys")
    expected_dimensions = set(CAPABILITY_DIMENSIONS)
    for profile in profiles:
        if set(profile.support_by_dimension) != expected_dimensions:
            raise ValueError(
                f"incomplete capability support profile: {profile.source_key}"
            )
        if set(profile.evidence_paths_by_dimension) != expected_dimensions:
            raise ValueError(
                f"incomplete capability evidence profile: {profile.source_key}"
            )
        if not set(profile.support_by_dimension.values()) <= _SUPPORT_STATUSES:
            raise ValueError(f"invalid capability support status: {profile.source_key}")
        for dimension, paths in profile.evidence_paths_by_dimension.items():
            if profile.support_by_dimension[dimension] != "unsupported" and not paths:
                raise ValueError(
                    f"supported capability has no evidence path: {profile.source_key}/{dimension}"
                )
            if len(paths) != len(set(paths)):
                raise ValueError(
                    f"duplicate capability evidence path: {profile.source_key}/{dimension}"
                )


def _resolve_path(output_root: Path, repository_path: str) -> Path:
    if repository_path.startswith("data/"):
        return output_root / repository_path.removeprefix("data/")
    return output_root.parent / repository_path


def _path_has_content(path: Path, repository_path: str) -> bool:
    """Accept only structurally governed evidence at the exact declared path."""
    try:
        file_stat = path.lstat()
    except OSError:
        return False
    if (
        not stat.S_ISREG(file_stat.st_mode)
        or path.is_symlink()
        or file_stat.st_size <= 0
        or path.name.startswith(".")
    ):
        return False
    if (
        path.name == "admission.json"
        and path.parent.name.startswith("sead-live-")
        and path.parent.parent.name == "acquisitions"
    ):
        return _valid_sead_admission(path)
    if path.suffix in {".json", ".geojson"}:
        return _valid_json_evidence(path, repository_path)
    if path.suffix == ".csv" or path.suffix == ".anno":
        return _valid_delimited_evidence(path)
    return False


def _valid_json_evidence(path: Path, repository_path: str) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    if repository_path.endswith(".geojson"):
        return _valid_geojson(payload)
    if "/neotoma/relational/surfaces/" in repository_path:
        return _valid_neotoma_part(path, payload)
    if repository_path == "data/neotoma/relational/manifest.json":
        return _valid_neotoma_manifest(path, payload)
    if "/sead/raw/acquisitions/" in repository_path and "/payloads/" in repository_path:
        return _valid_sead_table_payload(path, payload)
    if repository_path == "data/landclim/raw/landclim_sources.json":
        return _valid_landclim_receipt(path, payload)
    if repository_path == "data/boundaries/raw/source_manifest.json":
        return _valid_boundary_receipt(path, payload)
    if repository_path == "data/aadr/v66/release_manifest.json":
        return _valid_aadr_receipt(path, payload)
    if repository_path == "data/svar/raw/svar_lake_registry_manifest.json":
        return (
            payload.get("source") == "SMHI SVAR"
            and _positive_int(payload.get("matched_lake_count"))
            == _positive_int(payload.get("normalized_lake_count"))
            and isinstance(payload.get("source_url"), str)
            and isinstance(payload.get("wfs_url"), str)
        )
    if repository_path == "data/raa/normalized/sweden_archaeology_layer.json":
        counts = payload.get("counts")
        return (
            payload.get("source") == "Riksantikvarieämbetet"
            and isinstance(counts, dict)
            and bool(counts)
            and all(_non_negative_int(value) is not None for value in counts.values())
            and _positive_int(payload.get("density_feature_count")) is not None
        )
    if repository_path == "data/raa/raw/fornsok_domains.json":
        return len(payload) >= 5 and all(
            isinstance(value, list) and value for value in payload.values()
        )
    return _valid_versioned_json(payload)


def _valid_geojson(payload: Mapping[str, object]) -> bool:
    features = payload.get("features")
    if payload.get("type") != "FeatureCollection" or not isinstance(features, list):
        return False
    if not features:
        return False
    return all(
        isinstance(feature, dict)
        and feature.get("type") == "Feature"
        and isinstance(feature.get("geometry"), dict)
        and isinstance(feature.get("properties"), dict)
        and bool(feature["properties"])
        for feature in features
    )


def _valid_versioned_json(payload: Mapping[str, object]) -> bool:
    schema_version = payload.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version.strip():
        return False
    collections = [
        value
        for key, value in payload.items()
        if key != "schema_version" and isinstance(value, (list, dict)) and value
    ]
    if not collections:
        return False
    for count_key, collection_key in (
        ("row_count", "rows"),
        ("cell_count", "cells"),
        ("asset_count", "assets"),
        ("country_count", "countries"),
    ):
        if count_key in payload and collection_key in payload:
            collection = payload[collection_key]
            if not isinstance(collection, list) or payload[count_key] != len(
                collection
            ):
                return False
    return True


def _valid_delimited_evidence(path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    delimiter = "\t" if path.suffix == ".anno" else ","
    rows = [row for row in csv.reader(io.StringIO(content), delimiter=delimiter) if row]
    if len(rows) < 2:
        return False
    column_count = len(rows[0])
    return column_count > 1 and all(len(row) == column_count for row in rows[1:])


def _valid_neotoma_part(path: Path, payload: Mapping[str, object]) -> bool:
    rows = payload.get("rows")
    surface = path.parent.name
    if (
        payload.get("schema_version") != "neotoma-relational-part.v1"
        or payload.get("source_family") != "neotoma"
        or payload.get("surface") != surface
        or not isinstance(rows, list)
        or not rows
        or payload.get("row_count") != len(rows)
    ):
        return False
    manifest_path = path.parents[2] / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        surface_record = manifest["surfaces"][surface]
        relative_path = path.relative_to(path.parents[2]).as_posix()
        part_record = next(
            record
            for record in surface_record["parts"]
            if record.get("path") == relative_path
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        StopIteration,
        TypeError,
    ):
        return False
    return bool(
        part_record.get("row_count") == len(rows)
        and part_record.get("sha256") == hashlib.sha256(path.read_bytes()).hexdigest()
    )


def _valid_neotoma_manifest(path: Path, payload: Mapping[str, object]) -> bool:
    surfaces = payload.get("surfaces")
    reconciliation = payload.get("reconciliation")
    if (
        payload.get("schema_version")
        != "neotoma-relational-materialization-manifest.v1"
        or payload.get("source_family") != "neotoma"
        or not isinstance(surfaces, dict)
        or not surfaces
        or not isinstance(reconciliation, dict)
    ):
        return False
    reconciliation_path = path.parent / str(reconciliation.get("path", ""))
    try:
        return (
            reconciliation_path.is_file()
            and reconciliation.get("sha256")
            == hashlib.sha256(reconciliation_path.read_bytes()).hexdigest()
            and all(
                isinstance(record, dict)
                and _positive_int(record.get("row_count")) is not None
                and isinstance(record.get("parts"), list)
                and len(record["parts"]) == record.get("part_count")
                for record in surfaces.values()
            )
        )
    except OSError:
        return False


def _valid_sead_table_payload(path: Path, payload: Mapping[str, object]) -> bool:
    rows = payload.get("rows")
    admission_path = path.parents[1] / "admission.json"
    if not (
        payload.get("schema_version") == "sead-table-payload.v1"
        and payload.get("table") == path.stem
        and isinstance(rows, list)
        and bool(rows)
        and _valid_sead_admission(admission_path)
    ):
        return False
    try:
        admission = json.loads(admission_path.read_text(encoding="utf-8"))
        copied_files = admission["copied_files"]
        relative_path = path.relative_to(admission_path.parent).as_posix()
        record = next(
            item
            for item in copied_files
            if isinstance(item, dict) and item.get("path") == relative_path
        )
        content = path.read_bytes()
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        StopIteration,
        TypeError,
        ValueError,
    ):
        return False
    return (
        record.get("byte_count") == len(content)
        and record.get("sha256") == hashlib.sha256(content).hexdigest()
    )


def _valid_landclim_receipt(path: Path, payload: Mapping[str, object]) -> bool:
    assets = payload.get("assets")
    if (
        payload.get("schema_version") != "landclim-raw-receipt.v1"
        or payload.get("source") != "LandClim"
        or not isinstance(assets, list)
        or payload.get("asset_count") != len(assets)
        or not assets
    ):
        return False
    try:
        return all(
            isinstance(record, dict)
            and isinstance(record.get("filename"), str)
            and _safe_relative_path(record["filename"])
            and _regular_non_symlink(asset_path := path.parent / record["filename"])
            and record.get("size_bytes") == asset_path.stat().st_size
            and record.get("sha256")
            == hashlib.sha256(asset_path.read_bytes()).hexdigest()
            for record in assets
        )
    except OSError:
        return False


def _valid_boundary_receipt(path: Path, payload: Mapping[str, object]) -> bool:
    artifacts = payload.get("country_artifacts")
    normalized = payload.get("normalized_artifact")
    if (
        payload.get("schema_version") != "natural-earth-boundary-receipt.v1"
        or payload.get("source") != "Natural Earth"
        or not isinstance(artifacts, dict)
        or set(artifacts) != {"Sweden", "Denmark", "Norway", "Finland"}
        or not isinstance(normalized, dict)
    ):
        return False
    try:
        countries_valid = all(
            isinstance(record, dict)
            and isinstance(record.get("path"), str)
            and _safe_relative_path(record["path"])
            and _regular_non_symlink(artifact_path := path.parent / record["path"])
            and record.get("sha256")
            == hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            and _positive_int(record.get("feature_count")) is not None
            for record in artifacts.values()
        )
        normalized_relative = normalized.get("path")
        if not isinstance(normalized_relative, str) or not _safe_relative_path(
            normalized_relative
        ):
            return False
        normalized_path = path.parent.parent / normalized_relative
        return (
            countries_valid
            and _regular_non_symlink(normalized_path)
            and normalized.get("sha256")
            == hashlib.sha256(normalized_path.read_bytes()).hexdigest()
            and _positive_int(normalized.get("feature_count")) is not None
        )
    except OSError:
        return False


def _valid_aadr_receipt(path: Path, payload: Mapping[str, object]) -> bool:
    files = payload.get("downloaded_files")
    records = payload.get("anno_files")
    if (
        payload.get("source") != "AADR"
        or not isinstance(files, list)
        or not isinstance(records, list)
        or not files
        or len(files) != len(records)
    ):
        return False
    relative_paths = [item for item in files if isinstance(item, str)]
    record_names = [
        record.get("filename") for record in records if isinstance(record, dict)
    ]
    if (
        len(relative_paths) != len(files)
        or len(relative_paths) != len(set(relative_paths))
        or len(record_names) != len(records)
        or len(record_names) != len(set(record_names))
        or any(not _safe_relative_path(item) for item in relative_paths)
        or {Path(item).name for item in relative_paths} != set(record_names)
    ):
        return False
    record_by_name = {
        str(record["filename"]): record
        for record in records
        if isinstance(record, dict)
    }
    try:
        return all(
            _regular_non_symlink(artifact_path := path.parent / relative_path)
            and (record := record_by_name.get(artifact_path.name)) is not None
            and record.get("filesize") == artifact_path.stat().st_size
            and record.get("md5")
            == hashlib.md5(
                artifact_path.read_bytes(), usedforsecurity=False
            ).hexdigest()
            for relative_path in relative_paths
        )
    except OSError:
        return False


def _positive_int(value: object) -> int | None:
    parsed = _non_negative_int(value)
    return parsed if parsed is not None and parsed > 0 else None


def _non_negative_int(value: object) -> int | None:
    return (
        value
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
        else None
    )


def _valid_sead_admission(path: Path) -> bool:
    manifest_path = path.parent / "manifest.json"
    try:
        admission = json.loads(path.read_text(encoding="utf-8"))
        declared_scope = admission.get("declared_scope")
        copied_files = admission.get("copied_files")
        if (
            not isinstance(declared_scope, dict)
            or not isinstance(copied_files, list)
            or not copied_files
            or not manifest_path.is_file()
        ):
            return False
        copied_paths = [
            item.get("path") for item in copied_files if isinstance(item, dict)
        ]
        valid_inventory = (
            len(copied_paths) == len(copied_files)
            and all(isinstance(item, str) for item in copied_paths)
            and len(copied_paths) == len(set(copied_paths))
            and all(
                isinstance(item, str) and _safe_relative_path(item)
                for item in copied_paths
            )
            and all(
                isinstance(item, dict)
                and _non_negative_int(item.get("byte_count")) is not None
                and isinstance(item.get("sha256"), str)
                and len(str(item["sha256"])) == 64
                for item in copied_files
            )
        )
        manifest_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        return (
            valid_inventory
            and admission.get("schema_version") == "sead-acquisition-admission.v1"
            and admission.get("source_family") == "sead"
            and admission.get("run_id") == path.parent.name
            and admission.get("acquisition_manifest_sha256") == manifest_digest
            and declared_scope.get("scope_key") == "declared_chronology_relations"
            and declared_scope.get("status") == "complete_for_declared_relations"
            and declared_scope.get("table_count") == 19
            and declared_scope.get("join_count") == 25
            and declared_scope.get("wp01_complete") is False
            and admission.get("release_status") == "refused"
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False


def _safe_relative_path(value: str) -> bool:
    path = Path(value)
    return (
        bool(path.parts)
        and not path.is_absolute()
        and ".." not in path.parts
        and "\\" not in value
    )


def _regular_non_symlink(path: Path) -> bool:
    try:
        path_stat = path.lstat()
    except OSError:
        return False
    return stat.S_ISREG(path_stat.st_mode) and not path.is_symlink()


def _materialization_status(
    *,
    support: str,
    evidence_paths: tuple[str, ...],
    present_evidence_paths: tuple[str, ...],
) -> str:
    if support == "unsupported":
        return "not_applicable"
    if not present_evidence_paths:
        return "missing"
    if any(path not in evidence_paths for path in present_evidence_paths):
        raise ValueError("present capability evidence exceeds the governed inventory")
    if len(present_evidence_paths) == len(evidence_paths):
        return "complete"
    return "partial"
