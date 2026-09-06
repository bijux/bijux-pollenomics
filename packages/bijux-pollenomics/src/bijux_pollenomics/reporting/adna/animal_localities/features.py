"""Point-feature semantics for traceable animal atlas evidence rows."""

from __future__ import annotations

from ..atlas_evidence_rows import AnimalAtlasEvidenceRow
from ...geography import NORDIC_COUNTRIES


def _build_point_feature(
    *,
    row: AnimalAtlasEvidenceRow,
    dataset_review: dict[str, object],
    review_lookup: dict[str, dict[str, str]],
) -> dict[str, object]:
    primary_accession = row.primary_project_accession
    review = review_lookup.get(primary_accession, {})
    warning_rows = _warning_rows_for(
        row=row,
        dataset_review=dataset_review,
        review=review,
    )
    scope = row.animal_scope
    temporal_semantics = _temporal_semantics_for(row)
    temporal_window_label = str(
        temporal_semantics.get("temporal_window_label", "")
    ).strip()
    popup_rows = [
        {"label": "Species", "value": row.species_latin_name},
        {"label": "Support class", "value": row.support_class},
        {"label": "Animal scope", "value": scope.replace("_", " ")},
        {"label": "Mapped sample count", "value": str(row.sample_count)},
        {
            "label": "Mapped sample identifiers",
            "value": ", ".join(row.sample_record_ids),
        },
        {
            "label": "Source-native taxa",
            "value": ", ".join(row.source_native_taxon_labels),
        },
        {
            "label": "Taxon alignment",
            "value": ", ".join(row.taxon_alignment_statuses).replace("_", " "),
        },
        {
            "label": "Project accession",
            "value": ", ".join(row.project_accessions) or "No project accession",
        },
        {"label": "Paper title", "value": row.paper_title},
        {"label": "Paper DOI", "value": row.paper_doi},
        {"label": "Publication year", "value": row.publication_year},
        {"label": "Journal", "value": row.journal_title},
        {"label": "Chronology", "value": row.chronology.original_text},
        {
            "label": "Chronology evidence class",
            "value": row.chronology.evidence_class.replace("_", " "),
        },
        {
            "label": "Chronology precision posture",
            "value": row.chronology.precision_posture.replace("_", " "),
        },
        {"label": "Temporal window", "value": temporal_window_label},
        {
            "label": "Temporal comparison posture",
            "value": str(temporal_semantics.get("comparability_posture", "")).replace(
                "_", " "
            ),
        },
        {
            "label": "Temporal comparison note",
            "value": str(temporal_semantics.get("comparison_note", "")).strip(),
        },
        {"label": "Support note", "value": row.support_note},
        {"label": "Coordinate basis", "value": row.coordinate_basis},
        {"label": "Coordinate confidence", "value": row.coordinate_confidence},
        {"label": "Coordinate method", "value": row.geocoding_method},
        {"label": "Coordinate gazetteer", "value": row.geocoder_or_gazetteer},
        {"label": "Original place text", "value": row.original_place_text},
        {"label": "Resolved place text", "value": row.resolved_place_text},
        {
            "label": "Supplementary location source",
            "value": ", ".join(row.supplementary_sources),
        },
        {"label": "Coordinate rationale", "value": row.confidence_rationale},
        {"label": "Source locator", "value": row.source_locator},
        {"label": "Source support status", "value": row.source_support_status},
        {"label": "Source evidence text", "value": row.exact_source_text},
        {
            "label": "Nordic relevance",
            "value": (
                "nordic_lead" if row.nordic_inclusion else "non_nordic_or_comparator"
            ),
        },
        {"label": "Nordic note", "value": row.nordic_inclusion_reason},
        {"label": "Interpretation", "value": row.interpretation_note},
    ]
    popup_rows.extend(warning_rows)
    return {
        "feature_id": row.feature_id,
        "evidence_row_id": row.evidence_row_id,
        "site_record_id": row.site_record_id,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "country": row.political_entity,
        "title": row.locality,
        "subtitle": f"{row.species_common_name.title()} atlas evidence row",
        "species_latin_name": row.species_latin_name,
        "species_common_name": row.species_common_name,
        "evidence_role": "direct",
        "animal_scope": scope,
        "support_class": row.support_class,
        "temporal_semantics": temporal_semantics,
        "temporal_window_key": temporal_semantics["temporal_window_key"],
        "temporal_window_label": temporal_window_label,
        "temporal_comparability_posture": temporal_semantics["comparability_posture"],
        "temporal_comparison_note": temporal_semantics["comparison_note"],
        "nordic_inclusion": row.nordic_inclusion,
        "nordic_inclusion_reason": row.nordic_inclusion_reason,
        "coordinate_basis": row.coordinate_basis,
        "coordinate_confidence": row.coordinate_confidence,
        "sample_count": row.sample_count,
        "sample_record_ids": list(row.sample_record_ids),
        "sample_group_ids": list(row.sample_group_ids),
        "source_native_taxon_labels": list(row.source_native_taxon_labels),
        "source_native_tax_ids": list(row.source_native_tax_ids),
        "source_native_scientific_names": list(
            row.source_native_scientific_names
        ),
        "taxon_alignment_statuses": list(row.taxon_alignment_statuses),
        "sample_namespace": row.sample_namespace,
        "paper_title": row.paper_title,
        "publication_year": row.publication_year,
        "paper_doi": row.paper_doi,
        "journal_title": row.journal_title,
        "supplementary_sources": list(row.supplementary_sources),
        "project_accessions": list(row.project_accessions),
        "primary_project_accession": row.primary_project_accession,
        "inclusion_statuses": list(row.inclusion_statuses),
        "inclusion_notes": list(row.inclusion_notes),
        "latitude_text": row.latitude_text,
        "longitude_text": row.longitude_text,
        "geocoding_method": row.geocoding_method,
        "geocoder_or_gazetteer": row.geocoder_or_gazetteer,
        "confidence_rationale": row.confidence_rationale,
        "original_place_text": row.original_place_text,
        "resolved_place_text": row.resolved_place_text,
        "source_artifact_path": row.source_artifact_path,
        "source_artifact_kind": row.source_artifact_kind,
        "source_locator": row.source_locator,
        "source_support_status": row.source_support_status,
        "exact_source_text": row.exact_source_text,
        "popup_rows": [item for item in popup_rows if item["value"]],
        "source_url": row.paper_url,
        "media_links": [],
        "time_start_bp": row.chronology.time_start_bp,
        "time_end_bp": row.chronology.time_end_bp,
        "time_mean_bp": row.chronology.time_mean_bp,
        "time_year_bp": row.chronology.time_mean_bp,
        "time_label": row.chronology.original_text,
    }


def _warning_rows_for(
    *,
    row: AnimalAtlasEvidenceRow,
    dataset_review: dict[str, object],
    review: dict[str, str],
) -> list[dict[str, str]]:
    warnings: list[str] = []
    if row.coordinate_confidence in {"approximate", "inferred"}:
        warnings.append(
            f"Coordinates are {row.coordinate_confidence}, not excavation-grade exact points."
        )
    if row.animal_scope == "comparator":
        warnings.append(
            "Comparator-only evidence: use for comparison, not domesticated-core claims."
        )
    if row.animal_scope == "wild_or_progenitor_context":
        warnings.append(
            "Wild or progenitor evidence: keep visible as evolutionary context, not "
            "domesticated-core farming support."
        )
    if "project_species_mismatch" in row.taxon_alignment_statuses:
        warnings.append(
            "One or more mapped biological samples have a source-native taxon "
            "different from the configured project species; inspect Source-native "
            "taxa before making domestication claims."
        )
    if not row.nordic_inclusion:
        warnings.append(
            "This locality is outside the Nordic lead set and remains atlas context, not Nordic-localized support."
        )
    elif row.political_entity not in NORDIC_COUNTRIES:
        warnings.append(
            "Nordic relevance is regional or transregional rather than one named Nordic country."
        )
    if row.support_class in {"too_weak", "rejected"}:
        warnings.append(
            "This locality stays visible with an explicit weak or rejected support class."
        )
    if review.get("reason"):
        warnings.append(review["reason"])
    return [{"label": "Warning", "value": warning} for warning in warnings]


def _temporal_semantics_for(row: AnimalAtlasEvidenceRow) -> dict[str, object]:
    return row.chronology.as_temporal_semantics(
        source_family="animal_adna",
        provenance_path=row.source_artifact_path,
        provenance_locator=row.source_locator,
        provenance_excerpt=row.exact_source_text,
    )
