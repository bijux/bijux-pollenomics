from __future__ import annotations

from pathlib import Path

from .files import write_json


def write_tracked_animal_species(
    species_root: Path,
    *,
    latin_name: str,
    common_name: str,
    locality: str,
    political_entity: str,
    project_accession: str,
    support_class: str,
    product_role: str,
    nordic_inclusion: bool,
    chronology_bucket: str,
    paper_title: str,
    paper_doi: str,
) -> None:
    species_root.mkdir(parents=True, exist_ok=True)
    species_slug = species_root.name
    stable_token = f"{species_slug}:project-locality:{project_accession.lower()}"
    sample_token = f"{species_slug}:sample:{project_accession.lower()}"
    inclusion_status = (
        "comparator_site_curated"
        if product_role == "comparator"
        else "nordic_lead_site_curated"
        if nordic_inclusion
        else "site_curated"
    )
    write_json(
        species_root / "normalized" / "locality_summaries.json",
        {
            "localities": [
                {
                    "identity": {
                        "namespace": "animal-locality",
                        "stable_token": stable_token,
                        "locality_text": locality,
                        "political_entity": political_entity,
                        "source_anchor_tokens": [project_accession],
                    },
                    "species_latin_name": latin_name,
                    "species_common_name": common_name,
                    "source_family": "ENA",
                    "source_releases": ["tracked"],
                    "record_modalities": ["metadata_only"],
                    "review_strengths": ["paper_pinned"],
                    "provenance_qualities": ["tracked_curated"],
                    "locality": locality,
                    "coordinates": {
                        "latitude": 59.4,
                        "longitude": 18.1,
                        "latitude_text": "59.4",
                        "longitude_text": "18.1",
                        "confidence": "approximate",
                    },
                    "sample_count": 1,
                    "sample_ids": [sample_token],
                    "datasets": ["animal-adna"],
                    "chronology": {
                        "original_text": chronology_bucket,
                        "time_start_bp": 1200,
                        "time_end_bp": 1600,
                        "time_mean_bp": 1400,
                        "dating_basis": "bp_window",
                    },
                    "sample_namespace": "animal-locality",
                    "project_accessions": [project_accession],
                    "original_location_text": locality,
                    "nordic_inclusion": nordic_inclusion,
                    "nordic_inclusion_reason": "Curated Nordic lead",
                    "interpretation_note": "Tracked atlas locality lead",
                }
            ]
        },
    )
    write_json(
        species_root / "normalized" / "sample_records.json",
        {
            "schema_version": "adna-sample-record-export.v1",
            "species_latin_name": latin_name,
            "samples": [
                {
                    "identity": {
                        "namespace": f"{species_slug}:curated_sample",
                        "stable_token": sample_token,
                        "accession_lineage": [
                            f"species:{latin_name}",
                            "source:ENA",
                            f"project:{project_accession}",
                            f"sample:{project_accession}",
                        ],
                    },
                    "locality_identity": {
                        "namespace": f"{species_slug}:sample_locality",
                        "stable_token": stable_token,
                        "locality_text": locality,
                        "political_entity": political_entity,
                        "source_anchor_tokens": [
                            project_accession,
                            "project_accession_anchor",
                        ],
                    },
                    "species_latin_name": latin_name,
                    "species_common_name": common_name,
                    "source_family": "ENA",
                    "source_release": project_accession,
                    "record_modality": "archive_reads",
                    "review_strength": "primary_paper_pinned",
                    "provenance_quality": "manual_curation_only",
                    "master_id": project_accession,
                    "group_id": project_accession,
                    "locality": locality,
                    "political_entity": political_entity,
                    "coordinates": {
                        "latitude": None,
                        "longitude": None,
                        "latitude_text": "",
                        "longitude_text": "",
                        "confidence": "withheld",
                    },
                    "publication": paper_title,
                    "year_first_published": "2024",
                    "full_date": chronology_bucket,
                    "chronology": {
                        "original_text": chronology_bucket,
                        "time_start_bp": 1200,
                        "time_end_bp": 1600,
                        "time_mean_bp": 1400,
                        "date_stddev_bp": "",
                        "dating_basis": "bp_window",
                    },
                    "data_type": "archive_project_context",
                    "molecular_sex": "",
                    "datasets": [f"{species_slug}:project:{project_accession}"],
                    "project_accession": project_accession,
                    "paper_doi": paper_doi,
                    "paper_url": f"https://doi.org/{paper_doi}",
                    "supplementary_source": f"supplementary/{project_accession}.pdf",
                    "inclusion_status": inclusion_status,
                    "inclusion_note": "Curated into the atlas evidence contract.",
                    "chronology_strength": "sample_owned_interval",
                    "chronology_normalization_status": "normalized_interval",
                    "chronology_provenance_path": (
                        f"adna/governance/source_library/papers/{paper_doi.replace('/', '-')}/supplementary/{project_accession}.xlsx"
                    ),
                    "chronology_provenance_kind": "supplementary_spreadsheet_row",
                    "chronology_provenance_locator": "Sheet1!row2",
                    "chronology_provenance_text": (
                        f"{locality} | {project_accession} | {chronology_bucket}"
                    ),
                    "sample_basis": "project_accession_anchor",
                    "sample_evidence_status": "direct_table_extracted",
                    "sample_lineage_path": (
                        f"adna/governance/source_library/papers/{paper_doi.replace('/', '-')}/supplementary/{project_accession}.xlsx"
                    ),
                    "sample_lineage_locator": "Sheet1!row2",
                    "sample_lineage_excerpt": (
                        f"{locality} | {project_accession} | {chronology_bucket}"
                    ),
                }
            ],
        },
    )
    write_json(
        species_root / "normalized" / "coordinate_provenance.json",
        {
            "schema_version": "adna-coordinate-provenance-export.v1",
            "species_latin_name": latin_name,
            "coordinate_provenance": [
                {
                    "project_accession": project_accession,
                    "species_latin_name": latin_name,
                    "species_common_name": common_name,
                    "site_label": locality,
                    "original_place_text": locality,
                    "resolved_place_text": locality,
                    "political_entity": political_entity,
                    "source_artifact_path": f"adna/governance/source_library/papers/{paper_doi.replace('/', '-')}/article.html",
                    "source_locator": "supplementary table",
                    "coordinate_basis": "named_site_geocoding",
                    "mapping_posture": "mappable_point",
                    "latitude_text": "59.4",
                    "longitude_text": "18.1",
                    "geocoding_method": "manual_named_place_resolution",
                    "geocoder_or_gazetteer": "test archaeological site anchor",
                    "confidence_rationale": "Test fixture publishes one named-place geocode.",
                    "coordinate_confidence": "approximate",
                    "paper_doi": paper_doi,
                    "paper_url": f"https://doi.org/{paper_doi}",
                    "supplementary_source": f"supplementary/{project_accession}.pdf",
                    "chronology_text": chronology_bucket,
                    "time_start_bp": 1200,
                    "time_end_bp": 1600,
                    "dating_basis": "bp_window",
                    "comparator_context": product_role == "comparator",
                    "domestication_context": product_role,
                    "interpretation_note": "Test fixture named-place coordinate provenance.",
                    "support_gap_note": "",
                }
            ],
        },
    )
    write_json(
        species_root / "normalized" / "site_evidence.json",
        {
            "schema_version": "adna-site-evidence-export.v1",
            "species_latin_name": latin_name,
            "site_evidence": [
                {
                    "project_accession": project_accession,
                    "species_latin_name": latin_name,
                    "species_common_name": common_name,
                    "site_label": locality,
                    "political_entity": political_entity,
                    "source_artifact_path": f"adna/governance/source_library/papers/{paper_doi.replace('/', '-')}/article.html",
                    "source_artifact_kind": "article_html_body_quote",
                    "source_locator": "supplementary table",
                    "exact_source_text": f"{locality} named in supplementary support.",
                    "source_support_status": "article_exact_quote",
                    "paper_doi": paper_doi,
                    "paper_url": f"https://doi.org/{paper_doi}",
                    "supplementary_source": f"supplementary/{project_accession}.pdf",
                    "coordinate_basis": "site_level_localities",
                    "latitude_text": "59.4",
                    "longitude_text": "18.1",
                    "chronology_text": chronology_bucket,
                    "time_start_bp": 1200,
                    "time_end_bp": 1600,
                    "dating_basis": "bp_window",
                    "comparator_context": product_role == "comparator",
                    "domestication_context": product_role,
                    "interpretation_note": "Test fixture site evidence row.",
                    "support_gap_note": "",
                }
            ],
        },
    )
    write_json(
        species_root / "reports" / "support_summary.json",
        {
            "dataset_review": {
                "product_role": product_role,
                "chronology_bucket": chronology_bucket,
            }
        },
    )
    review_bucket = (
        "comparator_projects"
        if support_class == "comparator_only"
        else "accepted_projects"
    )
    write_json(
        species_root / "review" / "species_review.json",
        {
            "accepted_projects": []
            if review_bucket != "accepted_projects"
            else [
                {
                    "project_accession": project_accession,
                    "support_class": support_class,
                    "reason": "Mapped locality retained in atlas.",
                    "paper_title": paper_title,
                    "paper_doi": paper_doi,
                    "nordic_relevance": "nordic_lead"
                    if nordic_inclusion
                    else "non_nordic",
                    "nordic_relevance_reason": "Curated Nordic lead",
                }
            ],
            "rejected_projects": [],
            "too_weak_projects": [],
            "comparator_projects": []
            if review_bucket != "comparator_projects"
            else [
                {
                    "project_accession": project_accession,
                    "support_class": support_class,
                    "reason": "Comparator evidence remains visible with caveats.",
                    "paper_title": paper_title,
                    "paper_doi": paper_doi,
                    "nordic_relevance": "nordic_lead"
                    if nordic_inclusion
                    else "non_nordic",
                    "nordic_relevance_reason": "Curated Nordic lead",
                }
            ],
            "nordic_unmapped_leads": [],
        },
    )
    citation_manifest = (
        "project_accession,paper_title,paper_doi,publication_year,journal_title\n"
        f"{project_accession},{paper_title},{paper_doi},2024,Tracked Animal Journal\n"
    )
    citation_path = species_root / "manifests" / "citation_manifest.csv"
    citation_path.parent.mkdir(parents=True, exist_ok=True)
    citation_path.write_text(citation_manifest, encoding="utf-8")
