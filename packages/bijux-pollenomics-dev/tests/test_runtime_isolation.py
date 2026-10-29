"""Keep dev tools on explicitly reviewed host integration surfaces."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEV_SRC = REPO_ROOT / "packages" / "bijux-pollenomics-dev" / "src"

# Dev is an installed client of the host package. Each use of host code must be
# reviewed here by file, module and imported symbol; the default is refusal.
# scientific_evidence reads two private constants to verify generated evidence,
# not to run the application. Keep those exact names visible until a public
# verification facade replaces them.
APPROVED_HOST_IMPORTS: dict[str, dict[str, frozenset[str]]] = {
    "bijux_pollenomics_dev/source_completion/sead/boolean_staging.py": {
        "bijux_pollenomics.collection.sources.sead.evidence.source_keys.identities": frozenset(
            {"canonical_site_uuid"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/sead/categorical_staging.py": {
        "bijux_pollenomics.collection.sources.sead.evidence.source_keys.identities": frozenset(
            {"canonical_site_uuid"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/sead/integer_staging.py": {
        "bijux_pollenomics.collection.sources.sead.evidence.source_keys.identities": frozenset(
            {"canonical_site_uuid"}
        ),
    },
    # Saved-score checks share the canonical sample identity schema.
    "bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/optimizer_inputs/cohort_predictions.py": {
        "bijux_pollenomics.analysis.lra_validation.experiments.inputs": frozenset(
            {"SAMPLE_FIELDS"}
        ),
    },
    # The retained author reader verifies authored bytes and the current managed footer.
    "bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/author_site_evaluations.py": {
        "bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts": frozenset(
            {"authored_reader", "parse_routes", "render_route"}
        ),
        "bijux_pollenomics.reporting.presentation.report_portal.scientific_qualifications": frozenset(
            {"validate_evidence"}
        ),
    },
    # Structural portal verification uses these exact host-owned rendering helpers.
    "bijux_pollenomics_dev/docs/report_portal_check.py": {
        "bijux_pollenomics.reporting.presentation.report_portal.narrative_quality": frozenset(
            {"_build_quality_row"}
        ),
        "bijux_pollenomics.reporting.presentation.report_portal.pages": frozenset(
            {"_render_portal_pages"}
        ),
    },
    # The native RAA support producer verifies the governed GeoPackage profile and
    # retains its read-only SQL policy; these private bindings are not host API exports.
    "bijux_pollenomics_dev/source_completion/archaeology/native_lead_support/native.py": {
        "bijux_pollenomics.collection.sources.raa.materialization.contracts": frozenset(
            {"GEOMETRY_TYPES", "SOURCE_COLUMNS"}
        ),
        "bijux_pollenomics.collection.sources.raa.materialization.reading": frozenset(
            {"_authorize", "quote_identifier"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/archaeology/native_lead_support/producer.py": {
        "bijux_pollenomics.collection.sources.raa.geometry.binary": frozenset(
            {"describe_geometry"}
        ),
        "bijux_pollenomics.collection.sources.raa.materialization.contracts": frozenset(
            {"GEOMETRY_TYPES"}
        ),
        "bijux_pollenomics.collection.sources.raa.materialization.reading": frozenset(
            {"read_only_database"}
        ),
    },
    "bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py": {
        "bijux_pollenomics.reporting.map_document": frozenset(
            {"render_multi_country_map_html"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets": frozenset(
            {"write_static_atlas_assets"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets.indexes": frozenset(
            {"build_indexes"}
        ),
        "bijux_pollenomics.reporting.map_document.temporal_admission": frozenset(
            {"feature_occurrence_intervals"}
        ),
        "bijux_pollenomics.reporting.map_publication": frozenset({"MapScopePolicy"}),
    },
    "bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/source_rows.py": {
        "bijux_pollenomics.adna.domain.models": frozenset({"AdnaChronology"}),
        "bijux_pollenomics.adna.domain.models.localities": frozenset(
            {"AdnaSampleChronologySupport"}
        ),
        "bijux_pollenomics.adna.species.homo_sapiens.records": frozenset(
            {"_parse_sample_row"}
        ),
    },
    "bijux_pollenomics_dev/reader_reports/scientific_routes.py": {
        "bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts": frozenset(
            {"Route", "load_routes", "render_route"}
        ),
        "bijux_pollenomics.reporting.presentation.report_portal.scientific_qualifications": frozenset(
            {"validate_evidence"}
        ),
    },
    "bijux_pollenomics_dev/ci/atlas_browser/artifact_candidate.py": {
        "bijux_pollenomics.analysis.lra.api": frozenset({"read_lra_product"}),
    },
    "bijux_pollenomics_dev/ci/atlas_browser/landclim_export/reconcile.py": {
        "bijux_pollenomics.reporting.context.polygons": frozenset(
            {"build_external_polygon_layer"}
        ),
        "bijux_pollenomics.reporting.modeled_context.publication_projection": frozenset(
            {"project_modeled_context_layers"}
        ),
    },
    "bijux_pollenomics_dev/ci/atlas_media/gallery.py": {
        "bijux_pollenomics.reporting.source_chronology.source_label_presets": frozenset(
            {"build_neotoma_source_label_preset_catalog"}
        ),
    },
    "bijux_pollenomics_dev/ci/atlas_media/publication.py": {
        "bijux_pollenomics.reporting.source_chronology.source_label_presets": frozenset(
            {"NEOTOMA_SOURCE_LABEL_PRESETS"}
        ),
    },
    "bijux_pollenomics_dev/ci/atlas_media/source_authority.py": {
        "bijux_pollenomics.core.temporal_semantics": frozenset(
            {"BpInterval", "closed_bp_intervals_overlap"}
        ),
        "bijux_pollenomics.reporting.source_chronology.source_label_presets": frozenset(
            {
                "MEMBERSHIP_SEMANTICS",
                "NEOTOMA_SOURCE_LABEL_PRESETS",
                "NEOTOMA_SOURCE_LABEL_TAXA",
                "build_neotoma_source_label_preset_catalog",
            }
        ),
    },
    "bijux_pollenomics_dev/ci/scientific_evidence.py": {
        "bijux_pollenomics.analysis.propagation.outputs": frozenset(
            {
                "PROPAGATION_PRODUCER_ID",
                "PROPAGATION_PRODUCER_SOURCE_PATHS",
                "PROPAGATION_PRODUCER_VERSION",
                "PropagationMaterializationResult",
                "PropagationOutputRefusalError",
                "materialize_propagation_outputs",
            }
        ),
        "bijux_pollenomics.analysis.propagation.outputs.models": frozenset(
            {"_CLASSIFICATION_AUTHORITY", "_OUTPUT_NAMES"}
        ),
        "bijux_pollenomics.evidence.classification.audit_outputs": frozenset(
            {
                "ClassificationAuditMaterializationResult",
                "ClassificationAuditOutputPaths",
                "ClassificationAuditRefusalError",
                "materialize_classification_audit",
            }
        ),
        "bijux_pollenomics.evidence.classification.audit_outputs.constants": frozenset(
            {"OUTPUT_NAMES"}
        ),
        "bijux_pollenomics.evidence.classification.neotoma": frozenset(
            {"build_neotoma_classification_accounting"}
        ),
        "bijux_pollenomics.evidence.sources.neotoma": frozenset(
            {"read_validated_neotoma_relational_manifest"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/comparison.py": {
        "bijux_pollenomics.collection.sources.landclim.published_inventory": frozenset(
            {"LandClimPublishedEstimateInventory"}
        ),
        "bijux_pollenomics.collection.sources.landclim.published_inventory.contracts": frozenset(
            {"EVIDENCE_ROLE", "VALUE_UNIT"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/author_pollen_spatial/fitted_prediction.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"Fold", "SiteRecord"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial": frozenset(
            {
                "HALF_COUNT",
                "HALF_COUNT_POLICY",
                "SiteCoordinate",
                "SpatialConfig",
                "fit_spatial_model",
                "half_count_composition",
            }
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
        "bijux_pollenomics.analysis.lra_validation.splits": frozenset(
            {"grouped_block_holdouts"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/author_pollen_spatial/hellinger_comparison.py": {
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/author_pollen_spatial/prediction.py": {
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"Fold", "SiteRecord"}
        ),
        "bijux_pollenomics.analysis.lra_validation.splits": frozenset(
            {"grouped_block_holdouts"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/author_pollen_spatial/scoring.py": {
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"score_pollen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial": frozenset(
            {"HALF_COUNT", "HALF_COUNT_POLICY"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/author_pollen_spatial/source.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"site_group_id"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/observed_pollen_baseline.py": {
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"SiteRecord", "site_group_id"}
        ),
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"score_pollen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.splits": frozenset(
            {"grouped_leave_one_out"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/published_window_alignment.py": {
        "bijux_pollenomics.collection.sources.landclim.catalog": frozenset(
            {"time_window_from_tw_filename"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/published_window_correspondence.py": {
        "bijux_pollenomics.collection.sources.landclim.catalog": frozenset(
            {"time_window_from_tw_filename"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/rootsi_input_closure.py": {
        "bijux_pollenomics.collection.sources.landclim.study_inventory": frozenset(
            {
                "LandClimStudyMetadataInventory",
                "StudyMetadataRecord",
                "read_landclim_study_inventory",
                "reopen_landclim_study_inventory",
            }
        ),
        "bijux_pollenomics.collection.sources.rootsi": frozenset(
            {"RootsiSiteMetadataClaim", "normalize_rootsi_site_metadata"}
        ),
        "bijux_pollenomics.collection.sources.rootsi.authority": frozenset(
            {"ARCHIVE_SHA256", "METADATA_MEMBER", "METADATA_SHA256"}
        ),
        "bijux_pollenomics.collection.sources.rootsi.cells": frozenset(
            {"read_rootsi_cell_review"}
        ),
        "bijux_pollenomics.core.owned_tree": frozenset({"publish_new_output_tree"}),
    },
    "bijux_pollenomics_dev/essd_reproduction/rootsi_workbook_replay.py": {
        "bijux_pollenomics.collection.sources.rootsi": frozenset(
            {
                "RootsiSiteMetadataClaim",
                "normalize_rootsi_site_metadata",
            }
        ),
        "bijux_pollenomics.collection.sources.rootsi.authority": frozenset(
            {"ARCHIVE_SHA256", "METADATA_MEMBER", "METADATA_SHA256"}
        ),
        "bijux_pollenomics.collection.sources.rootsi.cells": frozenset(
            {"replay_rootsi_cell_review"}
        ),
        "bijux_pollenomics.core.owned_tree": frozenset({"publish_new_output_tree"}),
    },
    "bijux_pollenomics_dev/source_completion/abborrtjarne_native_counts.py": {
        "bijux_pollenomics.collection.sources.rootsi.cells.decoding": frozenset(
            {"parser"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/landclim_map_export_lineage.py": {
        "bijux_pollenomics.reporting.context.polygons": frozenset(
            {"build_external_polygon_layer"}
        ),
        "bijux_pollenomics.reporting.modeled_context": frozenset(
            {"build_modeled_context_manifest"}
        ),
        "bijux_pollenomics.reporting.modeled_context.publication_projection": frozenset(
            {"project_modeled_context_layers"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/lilla_gloppsjon_direct_pollen.py": {
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset({"Fold"}),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/lilla_gloppsjon_direct_pollen_scoring.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"ValidationRefusal"}
        ),
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance", "score_pollen"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/neotoma/pollen_prerequisites/candidate_series.py": {
        "bijux_pollenomics.analysis.lra.materialization.api": frozenset(
            {"inspect_neotoma_lra_candidate_series"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/neotoma/pollen_prerequisites/concept_priority.py": {
        "bijux_pollenomics.analysis.lra.materialization.models": frozenset(
            {"canonical_bytes"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.taxon_priority": frozenset(
            {"prioritize_neotoma_candidate_taxa"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.reading": frozenset(
            {"read_neotoma_evidence"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/neotoma/pollen_prerequisites/dataset_attribution.py": {
        "bijux_pollenomics.analysis.lra.materialization.models": frozenset(
            {"canonical_bytes"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.taxon_provenance": frozenset(
            {"attribute_neotoma_priority_datasets"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.reading": frozenset(
            {"read_neotoma_evidence"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/neotoma/pollen_prerequisites/sample_decisions.py": {
        "bijux_pollenomics.analysis.lra.materialization.api": frozenset(
            {"inspect_neotoma_lra_pollen_screen"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/neotoma/source_bound_reports.py": {
        "bijux_pollenomics.core.owned_tree": frozenset({"publish_new_output_tree"}),
    },
    "bijux_pollenomics_dev/source_completion/neotoma_screen_summary.py": {
        "bijux_pollenomics.analysis.lra.materialization.models": frozenset(
            {"canonical_bytes"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.reading": frozenset(
            {"json_object"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/nordic_direct_pollen.py": {
        "bijux_pollenomics.analysis.lra.materialization.api": frozenset(
            {"inspect_neotoma_lra_pollen_screen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset({"Fold"}),
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance", "score_pollen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial": frozenset(
            {
                "SiteCoordinate",
                "SpatialConfig",
                "fit_spatial_model",
                "half_count_composition",
            }
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/pollen_age_support/sambosjon.py": {
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance", "score_pollen"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/pollen_reconstruction/english_shared_ppe.py": {
        "bijux_pollenomics.analysis.lra.engine.discovery": frozenset(
            {"load_engine", "required_capability_for_profile"}
        ),
        "bijux_pollenomics.analysis.lra.execution.adapter": frozenset(
            {"_configuration"}
        ),
        "bijux_pollenomics.analysis.lra.execution.service": frozenset(
            {"validate_lra_inputs"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/sambosjon_direct_pollen.py": {
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset({"Fold"}),
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance", "score_pollen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial": frozenset(
            {"SiteCoordinate"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/adna/galician_sample_review.py": {
        "bijux_pollenomics.adna.projects.sample_master.tables.galician_cattle.species": frozenset(
            {"write_galician_sample_species_review"}
        ),
        "bijux_pollenomics.core.repository": frozenset({"repository_data_root"}),
    },
    "bijux_pollenomics_dev/source_completion/sead/analysis_value_components.py": {
        "bijux_pollenomics.evidence.sources.sead": frozenset(
            {
                "SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256",
                "SEAD_GOVERNED_ADMISSION_SHA256",
                "SEAD_GOVERNED_BUILD_ID",
                "SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256",
                "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
                "SEAD_GOVERNED_EVIDENCE_RUN_ID",
                "SEAD_GOVERNED_PARENT_ADMISSION_SHA256",
                "governed_sead_evidence_root",
            }
        ),
    },
    "bijux_pollenomics_dev/source_completion/sead/analysis_value_methods.py": {
        "bijux_pollenomics.evidence.sources.sead": frozenset(
            {"SEAD_GOVERNED_ADMISSION_SHA256", "SEAD_GOVERNED_EVIDENCE_RUN_ID"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/sead/boolean_values.py": {
        "bijux_pollenomics.evidence.sources.sead": frozenset(
            {
                "SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256",
                "SEAD_GOVERNED_ADMISSION_SHA256",
                "SEAD_GOVERNED_BUILD_ID",
                "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
                "SEAD_GOVERNED_EVIDENCE_RUN_ID",
                "SEAD_GOVERNED_PARENT_ADMISSION_SHA256",
                "governed_sead_evidence_root",
            }
        ),
    },
    "bijux_pollenomics_dev/source_completion/sead/categorical_values.py": {
        "bijux_pollenomics.evidence.sources.sead": frozenset(
            {
                "SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256",
                "SEAD_GOVERNED_ADMISSION_SHA256",
                "SEAD_GOVERNED_BUILD_ID",
                "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
                "SEAD_GOVERNED_EVIDENCE_RUN_ID",
                "SEAD_GOVERNED_PARENT_ADMISSION_SHA256",
                "governed_sead_evidence_root",
            }
        ),
    },
    "bijux_pollenomics_dev/source_completion/sead/chronology_age_review.py": {
        "bijux_pollenomics.collection.sources.sead.evidence.review.chronology_claims": frozenset(
            {"write_sead_chronology_age_review"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/sead/record_intervals.py": {
        "bijux_pollenomics.collection.sources.sead.evidence.review.interval_sets": frozenset(
            {"write_sead_interval_set_review"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/sead_analysis_integer_values.py": {
        "bijux_pollenomics.evidence.sources.sead": frozenset(
            {
                "SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256",
                "SEAD_GOVERNED_ADMISSION_SHA256",
                "SEAD_GOVERNED_BUILD_ID",
                "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
                "SEAD_GOVERNED_EVIDENCE_RUN_ID",
                "SEAD_GOVERNED_PARENT_ADMISSION_SHA256",
                "governed_sead_evidence_root",
            }
        ),
    },
    "bijux_pollenomics_dev/source_completion/sead_country_source_units.py": {
        "bijux_pollenomics.evidence.sources.sead": frozenset(
            {
                "SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256",
                "SEAD_GOVERNED_ADMISSION_SHA256",
                "SEAD_GOVERNED_BUILD_ID",
                "SEAD_GOVERNED_COUNTRY_AUTHORITY_ID",
                "SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256",
                "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
                "SEAD_GOVERNED_EVIDENCE_RUN_ID",
                "SEAD_GOVERNED_EVIDENCE_SCOPE_ID",
                "governed_sead_evidence_root",
                "read_validated_sead_evidence_documents",
            }
        ),
    },
    "bijux_pollenomics_dev/source_completion/sead_map_candidate.py": {
        "bijux_pollenomics.reporting.map_document.static_assets.asset_inventory": frozenset(
            {"normalize_asset_inventory"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets.serialization": frozenset(
            {"decode_chunk_script"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/swedish_chronology_block.py": {
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset({"Fold"}),
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance", "score_pollen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/swedish_direct_pollen.py": {
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset({"Fold"}),
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance", "score_pollen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial": frozenset(
            {
                "SiteCoordinate",
                "SpatialConfig",
                "fit_spatial_model",
                "half_count_composition",
            }
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/bokesjon_native_counts.py": {
        "bijux_pollenomics.collection.sources.rootsi.cells.decoding": frozenset(
            {"parser"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/bussjosjon_native_counts.py": {
        "bijux_pollenomics.collection.sources.rootsi.cells.decoding": frozenset(
            {"parser"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/author_pollen_spatial/development_search.py": {
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset({"Fold"}),
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance", "score_pollen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial": frozenset(
            {"SpatialConfig", "fit_spatial_model", "half_count_composition"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/study_inputs.py": {
        "bijux_pollenomics.collection.sources.landclim.study_inventory": frozenset(
            {
                "LandClimStudyMetadataInventory",
                "StudyMetadataRecord",
                "read_landclim_study_inventory",
                "reopen_landclim_study_inventory",
            }
        ),
    },
    "bijux_pollenomics_dev/lra_validation/experiment_ledger.py": {
        "bijux_pollenomics.analysis.lra_validation.evaluation.api": frozenset(
            {"reopen_cohort_admission"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/empd2_nfi_reference/admission.py": {
        "bijux_pollenomics.analysis.lra_validation.channels": frozenset(
            {"ObservationChannels", "PollenChannel"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"SiteRecord", "site_group_id"}
        ),
        "bijux_pollenomics.analysis.lra_validation.evaluation.api": frozenset(
            {"ExternalInput", "Support"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/empd2_nfi_reference/decisions.py": {
        "bijux_pollenomics.analysis.lra_validation.channels": frozenset(
            {"ObservationChannels"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"SiteRecord", "canonical_json", "manifest_sha256"}
        ),
        "bijux_pollenomics.analysis.lra_validation.evaluation.api": frozenset(
            {
                "COHORT_DECISION_PROFILE",
                "EvaluationSite",
                "ExternalInput",
                "ReviewedEvaluationCohort",
                "admit_reviewed_evaluation_cohort",
            }
        ),
    },
    "bijux_pollenomics_dev/source_completion/empd2_nfi_reference/evidence.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"canonical_json"}
        ),
        "bijux_pollenomics.core.geospatial.distance": frozenset(
            {"wgs84_inverse_geodesic"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/empd2_nfi_reference/parameters.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"canonical_json"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/empd2_nfi_reference/pollen_index.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"canonical_json"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/empd2_nfi_reference/projection.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"canonical_json", "manifest_sha256"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/empd2_nfi_reference/taxon_mapping.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"canonical_json"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/hyde_nordic_window.py": {
        "bijux_pollenomics.collection.sources.hyde.ascii": frozenset(
            {"NativeAsciiWindow", "read_hyde_ascii_window"}
        ),
        "bijux_pollenomics.collection.sources.hyde.ascii.geometry": frozenset(
            {"native_axis_geometry"}
        ),
        "bijux_pollenomics.collection.sources.hyde.local.contracts": frozenset(
            {"checked_path", "decode", "digest", "encode", "sha256"}
        ),
        "bijux_pollenomics.collection.sources.hyde.netcdf": frozenset(
            {
                "HydeNetcdfDeclarationInventory",
                "read_hyde_netcdf_declaration_inventory",
            }
        ),
        "bijux_pollenomics.collection.sources.quarantine": frozenset({"IntakeRefusal"}),
        "bijux_pollenomics.core.owned_tree": frozenset({"publish_new_output_tree"}),
    },
    "bijux_pollenomics_dev/taxa_review/neotoma.py": {
        "bijux_pollenomics.evidence.classification": frozenset(
            {"build_neotoma_classification_accounting"}
        ),
    },
    "bijux_pollenomics_dev/taxa_review/lra_prerequisites/__main__.py": {
        "bijux_pollenomics.analysis.lra.materialization.reading": frozenset(
            {"read_neotoma_evidence"}
        ),
    },
    "bijux_pollenomics_dev/taxa_review/lra_prerequisites/decisions.py": {
        "bijux_pollenomics.analysis.lra.materialization.models": frozenset(
            {"canonical_bytes"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.reading": frozenset(
            {"NeotomaEvidence"}
        ),
    },
    "bijux_pollenomics_dev/taxa_review/lra_prerequisites/projection.py": {
        "bijux_pollenomics.analysis.lra.materialization.models": frozenset(
            {"canonical_bytes"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.candidate_groups": frozenset(
            {"summarize_neotoma_candidate_groups"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.frontier": frozenset(
            {"assess_neotoma_lra_frontier"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.lakeparameters": frozenset(
            {"assess_neotoma_lakeparameters"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.pollen_screen": frozenset(
            {"assess_neotoma_pollen_screen"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.site_evidence": frozenset(
            {"assess_neotoma_candidate_site_evidence"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.reading": frozenset(
            {"NeotomaEvidence"}
        ),
    },
    "bijux_pollenomics_dev/taxa_review/sead.py": {
        "bijux_pollenomics.collection.sources.sead.evidence.review": frozenset(
            {"validate_sead_scientific_classification_review"}
        ),
    },
    "bijux_pollenomics_dev/ci/atlas_browser/boundary_orientation_candidate.py": {
        "bijux_pollenomics.core.geospatial.geojson": frozenset({"JsonObject"}),
        "bijux_pollenomics.reporting.map_document": frozenset(
            {"render_multi_country_map_html"}
        ),
        "bijux_pollenomics.reporting.scope_policy": frozenset({"MAP_SCOPE_POLICIES"}),
    },
    "bijux_pollenomics_dev/ci/atlas_browser/context_frame_candidate.py": {
        "bijux_pollenomics.reporting.geography": frozenset(
            {"build_published_geography_plan"}
        ),
        "bijux_pollenomics.reporting.lra_products.api": frozenset(
            {"render_lra_report"}
        ),
        "bijux_pollenomics.reporting.map_document": frozenset(
            {"render_multi_country_map_html"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets": frozenset(
            {"write_static_atlas_assets"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets.asset_inventory": frozenset(
            {"normalize_asset_inventory"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets.serialization": frozenset(
            {"decode_chunk_script"}
        ),
        "bijux_pollenomics.reporting.map_publication": frozenset(
            {"resolve_map_scope_policy"}
        ),
        "bijux_pollenomics.reporting.modeled_context": frozenset(
            {"build_modeled_context_manifest"}
        ),
        "bijux_pollenomics.reporting.modeled_context.publication_projection": frozenset(
            {"project_modeled_context_layers"}
        ),
    },
    "bijux_pollenomics_dev/ci/atlas_browser/cross_border_neighbor_candidate.py": {
        "bijux_pollenomics.core.geospatial.distance": frozenset(
            {"wgs84_inverse_geodesic"}
        ),
        "bijux_pollenomics.core.geospatial.geojson": frozenset({"JsonObject"}),
        "bijux_pollenomics.reporting.map_document": frozenset(
            {"render_multi_country_map_html"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets": frozenset(
            {"write_static_atlas_assets"}
        ),
        "bijux_pollenomics.reporting.scope_policy": frozenset({"MAP_SCOPE_POLICIES"}),
    },
    "bijux_pollenomics_dev/ci/atlas_browser/modeled_panel_candidate.py": {
        "bijux_pollenomics.reporting.geography": frozenset(
            {"build_published_geography_plan"}
        ),
        "bijux_pollenomics.reporting.map_document": frozenset(
            {"render_multi_country_map_html"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets": frozenset(
            {"write_static_atlas_assets"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets.asset_inventory": frozenset(
            {"normalize_asset_inventory"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets.serialization": frozenset(
            {"decode_chunk_script"}
        ),
        "bijux_pollenomics.reporting.map_publication": frozenset(
            {"resolve_map_scope_policy"}
        ),
        "bijux_pollenomics.reporting.modeled_context": frozenset(
            {"build_modeled_context_manifest"}
        ),
        "bijux_pollenomics.reporting.modeled_context.publication_projection": frozenset(
            {"project_modeled_context_layers"}
        ),
    },
    "bijux_pollenomics_dev/ci/atlas_browser/nordic_source_candidate.py": {
        "bijux_pollenomics.core.geospatial.geojson": frozenset({"JsonObject"}),
        "bijux_pollenomics.reporting.geography": frozenset(
            {"build_published_geography_plan"}
        ),
        "bijux_pollenomics.reporting.map_document": frozenset(
            {"render_multi_country_map_html"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets": frozenset(
            {"write_static_atlas_assets"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets.asset_inventory": frozenset(
            {"normalize_asset_inventory"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets.index_bundles": frozenset(
            {"decode_index_bundle"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets.serialization": frozenset(
            {"decode_chunk_script"}
        ),
        "bijux_pollenomics.reporting.map_publication": frozenset(
            {"resolve_map_scope_policy"}
        ),
    },
    "bijux_pollenomics_dev/ci/atlas_browser/playback_keyboard_candidate.py": {
        "bijux_pollenomics.core.geospatial.geojson": frozenset({"JsonObject"}),
        "bijux_pollenomics.reporting.map_document": frozenset(
            {"render_multi_country_map_html"}
        ),
        "bijux_pollenomics.reporting.scope_policy": frozenset({"MAP_SCOPE_POLICIES"}),
    },
    "bijux_pollenomics_dev/ci/atlas_browser/source_detail_candidate.py": {
        "bijux_pollenomics.reporting.geography": frozenset(
            {"build_published_geography_plan"}
        ),
        "bijux_pollenomics.reporting.map_document": frozenset(
            {"render_multi_country_map_html"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets": frozenset(
            {"write_static_atlas_assets"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets.asset_inventory": frozenset(
            {"normalize_asset_inventory"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets.index_bundles": frozenset(
            {"decode_index_bundle"}
        ),
        "bijux_pollenomics.reporting.map_document.static_assets.serialization": frozenset(
            {"decode_chunk_script"}
        ),
        "bijux_pollenomics.reporting.map_publication": frozenset(
            {"resolve_map_scope_policy"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/author_lra_report.py": {
        "bijux_pollenomics.analysis.lra.outputs.reading": frozenset(
            {"read_lra_product"}
        ),
        "bijux_pollenomics.analysis.lra_validation.experiments": frozenset(
            {"read_withheld_predictions"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/author_lra_run.py": {
        "bijux_pollenomics.analysis.lra_validation.experiments": frozenset(
            {"prepare_experiment_predictions"}
        ),
    },
    "bijux_pollenomics_dev/lra_validation/change_time_challenge.py": {
        "bijux_pollenomics.analysis.propagation.event_estimation": frozenset(
            {"GovernedSample", "estimate_first_observed"}
        ),
        "bijux_pollenomics.analysis.propagation.network": frozenset(
            {"PhenomenonEvent"}
        ),
    },
    "bijux_pollenomics_dev/lra_validation/neotoma_first_observed.py": {
        "bijux_pollenomics.core.temporal_semantics": frozenset({"BpInterval"}),
        "bijux_pollenomics.core.chronology.relations": frozenset(
            {"TemporalRelationKind", "bp_interval_relation_kind"}
        ),
        "bijux_pollenomics.analysis.propagation.event_estimation": frozenset(
            {"GovernedSample"}
        ),
    },
    "bijux_pollenomics_dev/lra_validation/propagation_challenge.py": {
        "bijux_pollenomics.analysis.propagation.event_estimation": frozenset(
            {"GovernedSample", "estimate_first_observed"}
        ),
        "bijux_pollenomics.analysis.propagation.network": frozenset(
            {
                "PhenomenonEvent",
                "PropagationCandidate",
                "evaluate_propagation_pair",
                "run_propagation_sensitivity",
            }
        ),
    },
    "bijux_pollenomics_dev/lra_validation/site_leakage_challenge.py": {
        "bijux_pollenomics.analysis.lra_validation": frozenset(
            {
                "ForwardInputs",
                "SiteRecord",
                "ValidationRefusal",
                "grouped_leave_one_out",
                "predict_withheld_site",
                "score_vegetation",
            }
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"manifest_sha256"}
        ),
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance"}
        ),
        "bijux_pollenomics.core.geospatial.distance": frozenset(
            {"wgs84_inverse_geodesic"}
        ),
    },
    "bijux_pollenomics_dev/lra_validation/spatial_eligibility_challenge.py": {
        "bijux_pollenomics.analysis.propagation.network": frozenset(
            {
                "EventValidationError",
                "PhenomenonEvent",
                "PropagationCandidate",
                "evaluate_propagation_pair",
                "generate_propagation_network",
                "generate_propagation_network_exhaustive",
            }
        ),
        "bijux_pollenomics.core.geospatial.distance": frozenset(
            {"wgs84_inverse_geodesic"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/bjaresjo_context.py": {
        "bijux_pollenomics.core.temporal_semantics": frozenset(
            {"BpInterval", "closed_bp_intervals_overlap"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/landclim_modeled_panels.py": {
        "bijux_pollenomics.reporting.context.polygons": frozenset(
            {"build_external_polygon_layer"}
        ),
        "bijux_pollenomics.reporting.modeled_context": frozenset(
            {"build_modeled_context_manifest"}
        ),
        "bijux_pollenomics.reporting.modeled_context.contracts": frozenset(
            {"PANGAEA_COUNTRY_CELL_COUNTS", "PANGAEA_DATASET_DOI"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/neotoma_acquisition_scope.py": {
        "bijux_pollenomics.collection.sources.boundaries.store": frozenset(
            {"load_repository_country_boundaries"}
        ),
        "bijux_pollenomics.collection.sources.neotoma.collection": frozenset(
            {
                "build_neotoma_bbox_geojson",
                "extract_neotoma_dataset_ids",
                "filter_neotoma_dataset_inventory_rows",
            }
        ),
    },
    "bijux_pollenomics_dev/source_completion/neotoma_publication_readiness.py": {
        "bijux_pollenomics.analysis.lra.materialization.neotoma.publication_intake": frozenset(
            {"parse_dataset_publications"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/neotoma_variable_surface.py": {
        "bijux_pollenomics.collection.sources.neotoma.production": frozenset(
            {"load_validated_neotoma_raw_archive"}
        ),
        "bijux_pollenomics.collection.sources.neotoma.relational.identifiers": frozenset(
            {"digest"}
        ),
        "bijux_pollenomics.collection.sources.neotoma.relational.variables": frozenset(
            {"variable_id"}
        ),
        "bijux_pollenomics.core.text": frozenset({"clean_optional_text"}),
        "bijux_pollenomics.evidence.sources.neotoma": frozenset(
            {"validate_neotoma_relational_materialization"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/nordic_author_target_pollen.py": {
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset({"Fold"}),
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance", "score_pollen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/nordic_pollen_development.py": {
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"Fold", "ValidationRefusal"}
        ),
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance", "score_pollen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial": frozenset(
            {
                "SiteCoordinate",
                "SpatialConfig",
                "fit_spatial_model",
                "half_count_composition",
            }
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/nordic_pollen_transfer.py": {
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset({"Fold"}),
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance", "score_pollen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial": frozenset(
            {
                "SiteCoordinate",
                "SpatialConfig",
                "fit_spatial_model",
                "half_count_composition",
            }
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/openland_intake.py": {
        "bijux_pollenomics.collection.sources.open_land.authority": frozenset(
            {
                "ADMITTED_CSV_MEMBERS",
                "ARCHIVE_EXPANDED_BYTES",
                "ARCHIVE_MEMBER_COUNT",
                "ARCHIVE_SHA256",
                "SOURCE_CITATION_DOI",
                "SOURCE_COMMIT",
                "SOURCE_DATA_LICENSE",
                "SOURCE_REPOSITORY",
            }
        ),
    },
    "bijux_pollenomics_dev/source_completion/sead_analysis_numerical_values.py": {
        "bijux_pollenomics.evidence.sources.sead": frozenset(
            {
                "SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256",
                "SEAD_GOVERNED_ADMISSION_SHA256",
                "SEAD_GOVERNED_BUILD_ID",
                "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
                "SEAD_GOVERNED_EVIDENCE_RUN_ID",
                "SEAD_GOVERNED_PARENT_ADMISSION_SHA256",
                "governed_sead_evidence_root",
            }
        ),
    },
    "bijux_pollenomics_dev/source_completion/sead_pollen_screen.py": {
        "bijux_pollenomics.evidence.sources.sead": frozenset(
            {
                "SEAD_GOVERNED_ADMISSION_SHA256",
                "SEAD_GOVERNED_BUILD_ID",
                "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
                "SEAD_GOVERNED_EVIDENCE_RUN_ID",
                "SEAD_GOVERNED_PARENT_ADMISSION_SHA256",
                "governed_sead_evidence_root",
            }
        ),
    },
    "bijux_pollenomics_dev/source_completion/sead_public_custody.py": {
        "bijux_pollenomics.collection.sources.sead.acquisition.governed": frozenset(
            {"validate_governed_sead_admission"}
        ),
        "bijux_pollenomics.evidence.sources.sead": frozenset(
            {"SEAD_GOVERNED_ADMISSION_SHA256", "SEAD_GOVERNED_EVIDENCE_RUN_ID"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/sead_relations/workflow.py": {
        "bijux_pollenomics.collection.sources.sead.acquisition.governed": frozenset(
            {"governed_sead_expected_identity"}
        ),
        "bijux_pollenomics.collection.sources.sead.evidence.source_keys.validation": frozenset(
            {"validate_sead_source_key_ledger_against_acquisition"}
        ),
        "bijux_pollenomics.evidence.sources.sead": frozenset(
            {
                "SEAD_GOVERNED_ADMISSION_SHA256",
                "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
                "SEAD_GOVERNED_EVIDENCE_RUN_ID",
                "governed_sead_evidence_root",
                "read_validated_sead_evidence_document",
            }
        ),
    },
    "bijux_pollenomics_dev/source_completion/solsoe_source_lineage.py": {
        "bijux_pollenomics.analysis.lra_validation.spatial": frozenset(
            {"SiteCoordinate"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
        "bijux_pollenomics.collection.intake.workbooks": frozenset(
            {"read_xlsx_sheet_rows"}
        ),
        "bijux_pollenomics.collection.sources.landclim.study_inventory": frozenset(
            {"read_landclim_study_inventory", "require_landclim_site_radius_metres"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/sweden_land_use_replay.py": {
        "bijux_pollenomics.reporting.service": frozenset({"generate_country_report"}),
    },
    "bijux_pollenomics_dev/source_completion/swedish_support_sensitivity.py": {
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset({"Fold"}),
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance", "score_pollen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/swedish_training_scope.py": {
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance", "score_pollen"}
        ),
    },
    "bijux_pollenomics_dev/taxa_review/neotoma_priority.py": {
        "bijux_pollenomics.analysis.lra.materialization.neotoma.pollen_screen": frozenset(
            {"assess_neotoma_pollen_screen"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.publication_intake": frozenset(
            {"build_candidate_publication_report"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.taxon_priority": frozenset(
            {"prioritize_neotoma_candidate_taxa"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.taxon_provenance": frozenset(
            {"attribute_neotoma_priority_datasets"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.reading": frozenset(
            {"read_neotoma_evidence"}
        ),
    },
    "bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/author_grid/admission.py": {
        "bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts": frozenset(
            {"authored_reader", "parse_routes", "verified_authored_reader"}
        ),
        "bijux_pollenomics.reporting.presentation.report_portal.scientific_qualifications": frozenset(
            {"validate_evidence"}
        ),
    },
    "bijux_pollenomics_dev/lra_validation/predictive_uncertainty/example.py": {
        "bijux_pollenomics.analysis.lra.uncertainty.projection": frozenset({"project"}),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"SiteRecord", "site_group_id"}
        ),
        "bijux_pollenomics.analysis.lra_validation.prediction": frozenset(
            {"ForwardInputs"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial": frozenset(
            {
                "SiteCoordinate",
                "JointSpatialDraw",
                "SpatialConfig",
                "UnavailableSpatialDraw",
                "propagate_withheld_spatial_draws",
            }
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.uncertainty.contracts": frozenset(
            {"UPSTREAM_SOURCES", "CONDITIONED_SOURCES"}
        ),
        "bijux_pollenomics.analysis.lra_validation.splits": frozenset(
            {"grouped_leave_one_out"}
        ),
    },
}


def host_import_violations(source: str, relative_path: str) -> tuple[str, ...]:
    """Inspect executable imports, excluding import-like text in strings/comments."""
    allowed = APPROVED_HOST_IMPORTS.get(relative_path, {})
    failures: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module != "bijux_pollenomics" and not module.startswith(
                "bijux_pollenomics."
            ):
                continue
            names = {alias.name for alias in node.names}
            if "*" in names or not names <= allowed.get(module, frozenset()):
                failures.append(
                    f"{relative_path}:{node.lineno} imports {module}: {sorted(names)}"
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "bijux_pollenomics" or alias.name.startswith(
                    "bijux_pollenomics."
                ):
                    failures.append(
                        f"{relative_path}:{node.lineno} imports {alias.name}"
                    )
        elif isinstance(node, ast.Call):
            dynamic = (
                isinstance(node.func, ast.Name)
                and node.func.id == "__import__"
                or isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
            )
            if dynamic and node.args and isinstance(node.args[0], ast.Constant):
                target = node.args[0].value
                if isinstance(target, str) and (
                    target == "bijux_pollenomics"
                    or target.startswith("bijux_pollenomics.")
                ):
                    failures.append(
                        f"{relative_path}:{node.lineno} dynamically imports {target}"
                    )
    return tuple(failures)


def test_dev_package_uses_only_reviewed_host_imports() -> None:
    failures = [
        violation
        for path in sorted(DEV_SRC.rglob("*.py"))
        for violation in host_import_violations(
            path.read_text(encoding="utf-8"), path.relative_to(DEV_SRC).as_posix()
        )
    ]
    assert not failures, "unreviewed dev-to-host imports:\n" + "\n".join(failures)


def test_new_host_bindings_remain_file_and_symbol_specific() -> None:
    """An admitted source import must not authorize sibling files or symbols."""
    approved = {
        "bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py": (
            "bijux_pollenomics.reporting.map_document",
            "render_multi_country_map_html",
        ),
        "bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/source_rows.py": (
            "bijux_pollenomics.adna.species.homo_sapiens.records",
            "_parse_sample_row",
        ),
        "bijux_pollenomics_dev/reader_reports/scientific_routes.py": (
            "bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts",
            "Route",
        ),
        "bijux_pollenomics_dev/ci/atlas_browser/landclim_export/reconcile.py": (
            "bijux_pollenomics.reporting.context.polygons",
            "build_external_polygon_layer",
        ),
        "bijux_pollenomics_dev/source_completion/neotoma/pollen_prerequisites/candidate_series.py": (
            "bijux_pollenomics.analysis.lra.materialization.api",
            "inspect_neotoma_lra_candidate_series",
        ),
        "bijux_pollenomics_dev/source_completion/neotoma/source_bound_reports.py": (
            "bijux_pollenomics.core.owned_tree",
            "publish_new_output_tree",
        ),
        "bijux_pollenomics_dev/source_completion/pollen_reconstruction/english_shared_ppe.py": (
            "bijux_pollenomics.analysis.lra.execution.adapter",
            "_configuration",
        ),
    }
    for path, (module, symbol) in approved.items():
        statement = f"from {module} import {symbol}"
        assert not host_import_violations(statement, path)
        assert host_import_violations(statement, path + ".other")
        assert host_import_violations(f"from {module} import {symbol}_other", path)
        assert host_import_violations(f"import {module}", path)


def test_import_boundary_rejects_new_symbols_modules_and_dynamic_imports() -> None:
    path = "bijux_pollenomics_dev/taxa_review/neotoma.py"
    assert not host_import_violations(
        "from bijux_pollenomics.evidence.classification import build_neotoma_classification_accounting",
        path,
    )
    for source in (
        "from bijux_pollenomics.evidence.classification import unreviewed",
        "from bijux_pollenomics.evidence.sources.neotoma import read_validated_neotoma_relational_manifest",
        "import bijux_pollenomics.analysis.lra.api",
        "from bijux_pollenomics.evidence.classification import *",
        "__import__('bijux_pollenomics.analysis.lra.api')",
    ):
        assert host_import_violations(source, path)
    assert not host_import_violations(
        'script = "from bijux_pollenomics.analysis.lra.api import read_lra_product"',
        path,
    )


def test_scientific_evidence_binding_stays_symbol_and_reader_specific() -> None:
    path = "bijux_pollenomics_dev/reader_reports/scientific_routes.py"
    module = "bijux_pollenomics.reporting.presentation.report_portal.scientific_qualifications"
    assert not host_import_violations(f"from {module} import validate_evidence", path)
    for statement, reader in (
        (f"from {module} import validate_evidence", path + ".other"),
        (f"from {module} import parse_qualification", path),
        (f"from {module} import Qualification", path),
        (f"from {module} import *", path),
        (f"import {module}", path),
        (f"__import__({module!r})", path),
    ):
        assert host_import_violations(statement, reader)


def test_raa_native_bindings_remain_file_module_and_symbol_specific() -> None:
    """Read-only source verification authorizes no neighboring host capability."""
    owner = "bijux_pollenomics_dev/source_completion/archaeology/native_lead_support/"
    bindings = (
        ("native.py", "materialization.contracts", "GEOMETRY_TYPES"),
        ("native.py", "materialization.contracts", "SOURCE_COLUMNS"),
        ("native.py", "materialization.reading", "_authorize"),
        ("native.py", "materialization.reading", "quote_identifier"),
        ("producer.py", "geometry.binary", "describe_geometry"),
        ("producer.py", "materialization.contracts", "GEOMETRY_TYPES"),
        ("producer.py", "materialization.reading", "read_only_database"),
    )
    for filename, suffix, symbol in bindings:
        path = owner + filename
        module = "bijux_pollenomics.collection.sources.raa." + suffix
        statement = f"from {module} import {symbol}"
        assert not host_import_violations(statement, path)
        for source, reader in (
            (statement, owner + "cli.py"),
            (f"from {module} import {symbol}_other", path),
            (f"from {module}.other import {symbol}", path),
            (f"from {module} import *", path),
            (f"import {module}", path),
            (f"__import__({module!r})", path),
        ):
            assert host_import_violations(source, reader)
    assert host_import_violations(
        "from bijux_pollenomics.collection.sources.raa.materialization.contracts import SOURCE_COLUMNS",
        owner + "producer.py",
    )
    assert host_import_violations(
        "from bijux_pollenomics.collection.sources.raa.materialization.reading import read_only_database",
        owner + "native.py",
    )


def test_temporal_producer_bindings_remain_file_module_and_symbol_specific() -> None:
    """Pair algebra grants neither source admission nor neighboring host access."""
    bindings = (
        ("source_completion/bjaresjo_context.py", "temporal_semantics", "BpInterval"),
        (
            "source_completion/bjaresjo_context.py",
            "temporal_semantics",
            "closed_bp_intervals_overlap",
        ),
        (
            "lra_validation/neotoma_first_observed.py",
            "temporal_semantics",
            "BpInterval",
        ),
        (
            "lra_validation/neotoma_first_observed.py",
            "chronology.relations",
            "TemporalRelationKind",
        ),
        (
            "lra_validation/neotoma_first_observed.py",
            "chronology.relations",
            "bp_interval_relation_kind",
        ),
    )
    for suffix, owner, symbol in bindings:
        path = "bijux_pollenomics_dev/" + suffix
        module = "bijux_pollenomics.core." + owner
        statement = f"from {module} import {symbol}"
        assert not host_import_violations(statement, path)
        for source, reader in (
            (statement, path + ".other"),
            (f"from {module} import {symbol}_other", path),
            (f"from {module}.other import {symbol}", path),
            (f"from {module} import *", path),
            (f"import {module}", path),
            (f"__import__({module!r})", path),
        ):
            assert host_import_violations(source, reader)


def test_author_grid_reader_bindings_remain_file_module_and_symbol_specific() -> None:
    """Keep historical/current reading authority capabilities inside the one owner."""
    path = "bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/author_grid/admission.py"
    prefix = "bijux_pollenomics.reporting.presentation.report_portal."
    for module, symbol in (
        ("scientific_accounts", "authored_reader"),
        ("scientific_accounts", "parse_routes"),
        ("scientific_accounts", "verified_authored_reader"),
        ("scientific_qualifications", "validate_evidence"),
    ):
        qualified = prefix + module
        statement = f"from {qualified} import {symbol}"
        assert not host_import_violations(statement, path)
        assert host_import_violations(statement, path + ".other")
        assert host_import_violations(f"from {qualified} import {symbol}_other", path)
        assert host_import_violations(f"from {qualified}_other import {symbol}", path)
        assert host_import_violations(f"from {qualified} import *", path)
        assert host_import_violations(f"import {qualified}", path)
        assert host_import_violations(f"__import__({qualified!r})", path)


def test_author_retained_reader_bindings_remain_file_module_and_symbol_specific() -> (
    None
):
    """Managed-footer verification grants only its four declared host bindings."""
    path = "bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/author_site_evaluations.py"
    accounts = (
        "bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts"
    )
    qualifications = "bijux_pollenomics.reporting.presentation.report_portal.scientific_qualifications"
    bindings = (
        (accounts, "authored_reader"),
        (accounts, "parse_routes"),
        (accounts, "render_route"),
        (qualifications, "validate_evidence"),
    )
    for module, symbol in bindings:
        statement = f"from {module} import {symbol}"
        assert not host_import_violations(statement, path)
        for source, owner in (
            (statement, path + ".other"),
            (f"from {module}.other import {symbol}", path),
            (f"from {module} import {symbol}_other", path),
            (f"from {module} import {symbol}, unreviewed", path),
            (f"from {module} import *", path),
            (f"import {module}", path),
            (f"__import__({module!r})", path),
        ):
            assert host_import_violations(source, owner)
    assert host_import_violations(f"from {accounts} import validate_evidence", path)
    assert host_import_violations(f"from {qualifications} import parse_routes", path)


def test_cohort_prediction_schema_binding_remains_file_module_and_symbol_specific() -> (
    None
):
    """Limit the saved-score reader to its canonical sample identity schema."""
    reader = "bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/optimizer_inputs/cohort_predictions.py"
    module = "bijux_pollenomics.analysis.lra_validation.experiments.inputs"
    statement = f"from {module} import SAMPLE_FIELDS"
    assert not host_import_violations(statement, reader)
    for source, path in (
        (statement, reader.replace("cohort_predictions.py", "other.py")),
        (f"from {module} import SAMPLE_FIELDS_other", reader),
        (f"from {module}.other import SAMPLE_FIELDS", reader),
        (f"from {module} import *", reader),
        (f"import {module}", reader),
        (f"__import__({module!r})", reader),
        (f"importlib.import_module({module!r})", reader),
    ):
        assert host_import_violations(source, path)


def test_sead_staging_identity_bindings_remain_file_module_and_symbol_specific() -> (
    None
):
    """Staging may canonicalize its site key without broader host capabilities."""
    module = "bijux_pollenomics.collection.sources.sead.evidence.source_keys.identities"
    for filename in (
        "categorical_staging.py",
        "integer_staging.py",
        "boolean_staging.py",
    ):
        path = "bijux_pollenomics_dev/source_completion/sead/" + filename
        statement = f"from {module} import canonical_site_uuid"
        assert not host_import_violations(statement, path)
        for source, owner in (
            (statement, path + ".other"),
            (f"from {module}.other import canonical_site_uuid", path),
            (f"from {module} import canonical_site_uuid_other", path),
            (f"from {module} import canonical_site_uuid, unreviewed", path),
            (f"from {module} import *", path),
            (f"import {module}", path),
            (f"__import__({module!r})", path),
            (f"importlib.import_module({module!r})", path),
        ):
            assert host_import_violations(source, owner)


def test_predictive_uncertainty_bindings_remain_file_module_and_symbol_specific() -> (
    None
):
    """One example's reviewed host symbols grant no neighboring capability."""
    path = "bijux_pollenomics_dev/lra_validation/predictive_uncertainty/example.py"
    for module, symbols in APPROVED_HOST_IMPORTS[path].items():
        for symbol in symbols:
            statement = f"from {module} import {symbol}"
            assert not host_import_violations(statement, path)
            for source, reader in (
                (statement, path.replace("example.py", "other.py")),
                (f"from {module} import {symbol}_other", path),
                (f"from {module}.other import {symbol}", path),
                (f"from {module} import *", path),
                (f"import {module}", path),
                (f"__import__({module!r})", path),
                (f"importlib.import_module({module!r})", path),
            ):
                assert host_import_violations(source, reader)
