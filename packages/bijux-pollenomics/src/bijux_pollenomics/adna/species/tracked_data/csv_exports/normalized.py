from __future__ import annotations

from bijux_pollenomics.adna.workflow.normalization import AdnaSpeciesNormalizationBundle

from .common import _render_csv


def _render_project_summaries_csv(bundle: AdnaSpeciesNormalizationBundle) -> str:
    fieldnames = (
        "summary_token",
        "species_latin_name",
        "species_common_name",
        "project_accession",
        "study_token",
        "source_family",
        "source_release",
        "result_kind",
        "archive_status",
        "evidence_strength",
        "review_strength",
        "support_class",
        "record_modality",
        "domestication_status",
        "domestication_scope",
        "comparator_status",
        "normalized_breed_label",
        "sequencing_target",
        "material_basis",
        "chronology_basis",
        "dating_basis",
        "geographic_basis",
        "coordinate_policy",
        "chronology_policy",
        "paper_title",
        "paper_doi",
        "paper_url",
        "nordic_relevance",
        "nordic_relevance_reason",
        "interpretation_caveat",
        "notes",
    )
    rows = []
    for summary in bundle.project_summaries:
        rows.append(
            {
                "summary_token": summary.summary_token,
                "species_latin_name": summary.species_latin_name,
                "species_common_name": summary.species_common_name,
                "project_accession": summary.project_accession,
                "study_token": summary.study_token,
                "source_family": summary.source_family,
                "source_release": summary.source_release,
                "result_kind": summary.result_kind,
                "archive_status": summary.archive_status,
                "evidence_strength": summary.evidence_strength,
                "review_strength": summary.review_strength,
                "support_class": summary.support_class,
                "record_modality": summary.record_modality,
                "domestication_status": summary.domestication_status,
                "domestication_scope": summary.domestication_scope,
                "comparator_status": str(summary.comparator_status).lower(),
                "normalized_breed_label": ""
                if summary.normalized_breed_label is None
                else summary.normalized_breed_label,
                "sequencing_target": ""
                if summary.sequencing_target is None
                else summary.sequencing_target,
                "material_basis": ""
                if summary.material_basis is None
                else summary.material_basis,
                "chronology_basis": ""
                if summary.chronology_basis is None
                else summary.chronology_basis,
                "dating_basis": ""
                if summary.dating_basis is None
                else summary.dating_basis,
                "geographic_basis": ""
                if summary.geographic_basis is None
                else summary.geographic_basis,
                "coordinate_policy": summary.coordinate_policy,
                "chronology_policy": summary.chronology_policy,
                "paper_title": ""
                if summary.paper_title is None
                else summary.paper_title,
                "paper_doi": "" if summary.paper_doi is None else summary.paper_doi,
                "paper_url": "" if summary.paper_url is None else summary.paper_url,
                "nordic_relevance": summary.nordic_relevance,
                "nordic_relevance_reason": summary.nordic_relevance_reason,
                "interpretation_caveat": summary.interpretation_caveat,
                "notes": summary.notes,
            }
        )
    return _render_csv(fieldnames, rows)


def _render_sample_records_csv(bundle: AdnaSpeciesNormalizationBundle) -> str:
    fieldnames = (
        "stable_sample_id",
        "project_accession",
        "sample_basis",
        "sample_evidence_status",
        "sample_identity_resolution",
        "archive_native_sample_id",
        "archive_native_experiment_id",
        "source_native_identity_kind",
        "paper_native_sample_label",
        "supplementary_table_sample_label",
        "sample_lineage_path",
        "sample_lineage_locator",
        "inclusion_status",
        "species_latin_name",
        "species_common_name",
        "source_family",
        "source_release",
        "record_modality",
        "review_strength",
        "provenance_quality",
        "publication",
        "paper_doi",
        "paper_url",
        "supplementary_source",
        "site_label",
        "political_entity",
        "latitude",
        "longitude",
        "latitude_text",
        "longitude_text",
        "coordinate_confidence",
        "chronology_text",
        "chronology_strength",
        "chronology_evidence_class",
        "chronology_precision_posture",
        "chronology_normalization_status",
        "chronology_provenance_path",
        "chronology_provenance_locator",
        "chronology_conflict_note",
        "time_start_bp",
        "time_end_bp",
        "time_mean_bp",
        "dating_basis",
        "inclusion_note",
    )
    rows = []
    for sample in bundle.sample_records:
        site_label = sample.locality_identity.locality_text
        rows.append(
            {
                "stable_sample_id": sample.genetic_id,
                "project_accession": sample.project_accession,
                "sample_basis": sample.sample_basis,
                "sample_evidence_status": sample.sample_evidence_status,
                "sample_identity_resolution": sample.sample_identity_resolution,
                "archive_native_sample_id": sample.archive_native_sample_id,
                "archive_native_experiment_id": sample.archive_native_experiment_id,
                "source_native_identity_kind": sample.source_native_identity_kind,
                "paper_native_sample_label": sample.paper_native_sample_label,
                "supplementary_table_sample_label": sample.supplementary_table_sample_label,
                "sample_lineage_path": sample.sample_lineage_path,
                "sample_lineage_locator": sample.sample_lineage_locator,
                "inclusion_status": sample.inclusion_status,
                "species_latin_name": sample.species_latin_name,
                "species_common_name": sample.species_common_name,
                "source_family": sample.source_family,
                "source_release": sample.source_release,
                "record_modality": sample.record_modality,
                "review_strength": sample.review_strength,
                "provenance_quality": sample.provenance_quality,
                "publication": sample.publication,
                "paper_doi": sample.paper_doi,
                "paper_url": sample.paper_url,
                "supplementary_source": sample.supplementary_source,
                "site_label": site_label,
                "political_entity": ""
                if sample.political_entity is None
                else sample.political_entity,
                "latitude": "" if sample.latitude is None else sample.latitude,
                "longitude": "" if sample.longitude is None else sample.longitude,
                "latitude_text": sample.latitude_text,
                "longitude_text": sample.longitude_text,
                "coordinate_confidence": sample.coordinate_confidence,
                "chronology_text": sample.time_label,
                "chronology_strength": sample.chronology_strength,
                "chronology_evidence_class": sample.chronology.evidence_class,
                "chronology_precision_posture": sample.chronology.precision_posture,
                "chronology_normalization_status": sample.chronology_normalization_status,
                "chronology_provenance_path": sample.chronology_provenance_path,
                "chronology_provenance_locator": sample.chronology_provenance_locator,
                "chronology_conflict_note": sample.chronology_conflict_note,
                "time_start_bp": ""
                if sample.time_start_bp is None
                else sample.time_start_bp,
                "time_end_bp": "" if sample.time_end_bp is None else sample.time_end_bp,
                "time_mean_bp": ""
                if sample.time_mean_bp is None
                else sample.time_mean_bp,
                "dating_basis": sample.dating_basis,
                "inclusion_note": sample.inclusion_note,
            }
        )
    return _render_csv(fieldnames, rows)


def _render_site_evidence_csv(bundle: AdnaSpeciesNormalizationBundle) -> str:
    fieldnames = (
        "project_accession",
        "species_latin_name",
        "species_common_name",
        "site_label",
        "political_entity",
        "paper_doi",
        "paper_url",
        "supplementary_source",
        "source_artifact_path",
        "source_artifact_kind",
        "source_locator",
        "exact_source_text",
        "source_support_status",
        "coordinate_basis",
        "latitude_text",
        "longitude_text",
        "chronology_text",
        "time_start_bp",
        "time_end_bp",
        "dating_basis",
        "comparator_context",
        "domestication_context",
        "interpretation_note",
        "support_gap_note",
    )
    rows = []
    for record in bundle.site_evidence_records:
        rows.append(
            {
                "project_accession": record.project_accession,
                "species_latin_name": record.species_latin_name,
                "species_common_name": record.species_common_name,
                "site_label": record.site_label,
                "political_entity": ""
                if record.political_entity is None
                else record.political_entity,
                "paper_doi": record.paper_doi,
                "paper_url": record.paper_url,
                "supplementary_source": record.supplementary_source,
                "source_artifact_path": record.source_artifact_path,
                "source_artifact_kind": record.source_artifact_kind,
                "source_locator": record.source_locator,
                "exact_source_text": record.exact_source_text,
                "source_support_status": record.source_support_status,
                "coordinate_basis": record.coordinate_basis,
                "latitude_text": record.latitude_text,
                "longitude_text": record.longitude_text,
                "chronology_text": record.chronology_text,
                "time_start_bp": ""
                if record.time_start_bp is None
                else record.time_start_bp,
                "time_end_bp": "" if record.time_end_bp is None else record.time_end_bp,
                "dating_basis": record.dating_basis,
                "comparator_context": str(record.comparator_context).lower(),
                "domestication_context": record.domestication_context,
                "interpretation_note": record.interpretation_note,
                "support_gap_note": record.support_gap_note,
            }
        )
    return _render_csv(fieldnames, rows)


def _render_coordinate_provenance_csv(bundle: AdnaSpeciesNormalizationBundle) -> str:
    fieldnames = (
        "project_accession",
        "species_latin_name",
        "species_common_name",
        "site_label",
        "original_place_text",
        "resolved_place_text",
        "political_entity",
        "source_artifact_path",
        "source_locator",
        "coordinate_basis",
        "mapping_posture",
        "latitude_text",
        "longitude_text",
        "geocoding_method",
        "geocoder_or_gazetteer",
        "confidence_rationale",
        "coordinate_confidence",
        "paper_doi",
        "paper_url",
        "supplementary_source",
        "chronology_text",
        "time_start_bp",
        "time_end_bp",
        "dating_basis",
        "comparator_context",
        "domestication_context",
        "interpretation_note",
        "support_gap_note",
    )
    rows = []
    for record in bundle.coordinate_provenance_records:
        rows.append(
            {
                "project_accession": record.project_accession,
                "species_latin_name": record.species_latin_name,
                "species_common_name": record.species_common_name,
                "site_label": record.site_label,
                "original_place_text": record.original_place_text,
                "resolved_place_text": record.resolved_place_text,
                "political_entity": ""
                if record.political_entity is None
                else record.political_entity,
                "source_artifact_path": record.source_artifact_path,
                "source_locator": record.source_locator,
                "coordinate_basis": record.coordinate_basis,
                "mapping_posture": record.mapping_posture,
                "latitude_text": record.latitude_text,
                "longitude_text": record.longitude_text,
                "geocoding_method": record.geocoding_method,
                "geocoder_or_gazetteer": record.geocoder_or_gazetteer,
                "confidence_rationale": record.confidence_rationale,
                "coordinate_confidence": record.coordinate_confidence,
                "paper_doi": record.paper_doi,
                "paper_url": record.paper_url,
                "supplementary_source": record.supplementary_source,
                "chronology_text": record.chronology_text,
                "time_start_bp": ""
                if record.time_start_bp is None
                else record.time_start_bp,
                "time_end_bp": "" if record.time_end_bp is None else record.time_end_bp,
                "dating_basis": record.dating_basis,
                "comparator_context": str(record.comparator_context).lower(),
                "domestication_context": record.domestication_context,
                "interpretation_note": record.interpretation_note,
                "support_gap_note": record.support_gap_note,
            }
        )
    return _render_csv(fieldnames, rows)


def _render_locality_summaries_csv(bundle: AdnaSpeciesNormalizationBundle) -> str:
    fieldnames = (
        "locality_token",
        "species_latin_name",
        "species_common_name",
        "project_accessions",
        "source_family",
        "source_releases",
        "record_modalities",
        "review_strengths",
        "provenance_qualities",
        "original_location_text",
        "locality",
        "political_entity",
        "latitude",
        "longitude",
        "latitude_text",
        "longitude_text",
        "coordinate_confidence",
        "chronology_text",
        "time_start_bp",
        "time_end_bp",
        "time_mean_bp",
        "dating_basis",
        "chronology_evidence_class",
        "chronology_precision_posture",
        "nordic_inclusion",
        "nordic_inclusion_reason",
        "interpretation_note",
    )
    rows = []
    for summary in bundle.locality_records:
        rows.append(
            {
                "locality_token": summary.locality_token,
                "species_latin_name": summary.species_latin_name,
                "species_common_name": summary.species_common_name,
                "project_accessions": ";".join(summary.project_accessions),
                "source_family": summary.source_family,
                "source_releases": ";".join(summary.source_releases),
                "record_modalities": ";".join(summary.record_modalities),
                "review_strengths": ";".join(summary.review_strengths),
                "provenance_qualities": ";".join(summary.provenance_qualities),
                "original_location_text": summary.original_location_text,
                "locality": "" if summary.locality is None else summary.locality,
                "political_entity": ""
                if summary.identity.political_entity is None
                else summary.identity.political_entity,
                "latitude": "" if summary.latitude is None else summary.latitude,
                "longitude": "" if summary.longitude is None else summary.longitude,
                "latitude_text": summary.latitude_text,
                "longitude_text": summary.longitude_text,
                "coordinate_confidence": summary.coordinate_confidence,
                "chronology_text": summary.time_label,
                "time_start_bp": ""
                if summary.time_start_bp is None
                else summary.time_start_bp,
                "time_end_bp": ""
                if summary.time_end_bp is None
                else summary.time_end_bp,
                "time_mean_bp": ""
                if summary.time_mean_bp is None
                else summary.time_mean_bp,
                "dating_basis": summary.dating_basis,
                "chronology_evidence_class": summary.chronology.evidence_class,
                "chronology_precision_posture": summary.chronology.precision_posture,
                "nordic_inclusion": str(summary.nordic_inclusion).lower(),
                "nordic_inclusion_reason": summary.nordic_inclusion_reason,
                "interpretation_note": summary.interpretation_note,
            }
        )
    return _render_csv(fieldnames, rows)
