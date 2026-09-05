from __future__ import annotations

from .constants import (
    CAPABILITY_DIMENSIONS,
    NEOTOMA_CLASSIFICATION_EVIDENCE,
    NEOTOMA_PROPAGATION_EVIDENCE,
    SEAD_ADMITTED_ACQUISITION_ADMISSION,
    SEAD_NORMALIZED_EVIDENCE_EVENTS,
    SEAD_NORMALIZED_EVIDENCE_MANIFEST,
    SEAD_NORMALIZED_OBSERVATIONS,
    SEAD_NORMALIZED_RELATIONS,
    _SEAD_NORMALIZED_CHRONOLOGY,
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
            "four_country_coverage": (
                "data/country_dimension_coverage.json",
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
                SEAD_NORMALIZED_OBSERVATIONS,
            ),
            "within_site_hierarchy": (
                f"{acquisition}/payloads/tbl_sample_groups.json",
                f"{acquisition}/payloads/tbl_physical_samples.json",
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
                SEAD_NORMALIZED_RELATIONS,
            ),
            "numeric_chronology": (
                f"{acquisition}/payloads/tbl_geochronology.json",
                f"{acquisition}/payloads/tbl_analysis_entity_ages.json",
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
                _SEAD_NORMALIZED_CHRONOLOGY,
            ),
            "chronology_uncertainty": (
                f"{acquisition}/payloads/tbl_dating_uncertainty.json",
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
                _SEAD_NORMALIZED_CHRONOLOGY,
            ),
            "relative_chronology": (
                f"{acquisition}/payloads/tbl_relative_ages.json",
                f"{acquisition}/payloads/tbl_relative_dates.json",
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
                _SEAD_NORMALIZED_CHRONOLOGY,
            ),
            "taxon_identity": (
                f"{acquisition}/payloads/tbl_abundances.json",
                f"{acquisition}/payloads/tbl_taxa_tree_master.json",
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
                SEAD_NORMALIZED_RELATIONS,
            ),
            "native_ecological_class": (
                f"{acquisition}/payloads/tbl_ecocodes.json",
                f"{acquisition}/payloads/tbl_ecocode_definitions.json",
                f"{acquisition}/payloads/tbl_ecocode_groups.json",
                f"{acquisition}/payloads/tbl_ecocode_systems.json",
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
                SEAD_NORMALIZED_RELATIONS,
            ),
            "derived_pollen_group": (
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
                SEAD_NORMALIZED_RELATIONS,
                "data/sead/derived/pollen_groups.json",
            ),
            "derived_ecological_role": (
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
                SEAD_NORMALIZED_RELATIONS,
                "data/sead/derived/ecological_roles.json",
            ),
            "crop_cereal_resolution": (
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
                SEAD_NORMALIZED_RELATIONS,
                "data/sead/derived/crop_cereal_resolution.json",
            ),
            "quantitative_observation": (
                f"{acquisition}/payloads/tbl_abundances.json",
                f"{acquisition}/payloads/tbl_analysis_numerical_values.json",
                f"{acquisition}/payloads/tbl_analysis_integer_values.json",
                f"{acquisition}/payloads/tbl_analysis_categorical_values.json",
                f"{acquisition}/payloads/tbl_analysis_boolean_values.json",
                f"{acquisition}/payloads/tbl_measured_values.json",
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
                SEAD_NORMALIZED_OBSERVATIONS,
            ),
            "observation_unit": (
                f"{acquisition}/payloads/tbl_value_types.json",
                f"{acquisition}/payloads/tbl_dimensions.json",
                f"{acquisition}/payloads/tbl_units.json",
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
                SEAD_NORMALIZED_OBSERVATIONS,
                SEAD_NORMALIZED_RELATIONS,
            ),
            "dataset_provenance": (
                SEAD_ADMITTED_ACQUISITION_ADMISSION,
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
            ),
            "pollen_propagation_event": (
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
                SEAD_NORMALIZED_EVIDENCE_EVENTS,
                "data/sead/derived/pollen_propagation_events.json",
            ),
            "non_pollen_context": (
                f"{acquisition}/payloads/tbl_sites.json",
                SEAD_NORMALIZED_EVIDENCE_MANIFEST,
                SEAD_NORMALIZED_OBSERVATIONS,
            ),
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
    evidence_by_dimension = {
        dimension: source_evidence.get(dimension, ())
        for dimension in CAPABILITY_DIMENSIONS
    }
    if source_key == "sead":
        evidence_by_dimension = {
            dimension: (
                paths
                if not paths or SEAD_ADMITTED_ACQUISITION_ADMISSION in paths
                else (SEAD_ADMITTED_ACQUISITION_ADMISSION, *paths)
            )
            for dimension, paths in evidence_by_dimension.items()
        }
    return evidence_by_dimension
