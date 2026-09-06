from __future__ import annotations

import tempfile
from pathlib import Path

from bijux_pollenomics.reporting.adna import build_tracked_animal_atlas_evidence_rows

from .support import _write_json


def test_animal_atlas_evidence_rows_refuse_project_level_flattening_of_multi_site_samples() -> (
    None
):
    with tempfile.TemporaryDirectory() as tmp:
        data_root = Path(tmp)
        species_root = data_root / "adna" / "species" / "ovis_aries"
        species_root.mkdir(parents=True, exist_ok=True)
        _write_json(
            species_root / "normalized" / "locality_summaries.json",
            {
                "schema_version": "adna-locality-summary-export.v1",
                "species_latin_name": "Ovis aries",
                "localities": [
                    {
                        "identity": {
                            "namespace": "animal-locality",
                            "stable_token": "ovis_aries:project-locality:prjtest",
                            "locality_text": "Flattened locality",
                            "political_entity": "Sweden",
                            "source_anchor_tokens": ["PRJTEST"],
                        },
                        "species_latin_name": "Ovis aries",
                        "species_common_name": "sheep",
                        "source_family": "ENA",
                        "source_releases": ["PRJTEST"],
                        "record_modalities": ["metadata_only"],
                        "review_strengths": ["paper_pinned"],
                        "provenance_qualities": ["tracked_curated"],
                        "locality": "Flattened locality",
                        "coordinates": {
                            "latitude": 59.4,
                            "longitude": 18.1,
                            "latitude_text": "59.4",
                            "longitude_text": "18.1",
                            "confidence": "approximate",
                        },
                        "sample_count": 2,
                        "sample_ids": ["PRJTEST:one", "PRJTEST:two"],
                        "datasets": ["animal-adna"],
                        "chronology": {
                            "original_text": "1001-3000 BP",
                            "time_start_bp": 1200,
                            "time_end_bp": 1600,
                            "time_mean_bp": 1400,
                            "dating_basis": "bp_window",
                        },
                        "sample_namespace": "animal-locality",
                        "project_accessions": ["PRJTEST"],
                        "original_location_text": "Flattened locality",
                        "nordic_inclusion": True,
                        "nordic_inclusion_reason": "Curated Nordic lead",
                        "interpretation_note": "This row should be refused.",
                    }
                ],
            },
        )
        _write_json(
            species_root / "normalized" / "sample_records.json",
            {
                "schema_version": "adna-sample-record-export.v1",
                "species_latin_name": "Ovis aries",
                "samples": [
                    {
                        "identity": {
                            "namespace": "ovis_aries:curated_sample",
                            "stable_token": "ovis_aries:sample:one",
                            "accession_lineage": [],
                        },
                        "locality_identity": {
                            "namespace": "ovis_aries:sample_locality",
                            "stable_token": "ovis_aries:project-locality:prjtest",
                            "locality_text": "Site One",
                            "political_entity": "Sweden",
                            "source_anchor_tokens": ["PRJTEST"],
                        },
                        "project_accession": "PRJTEST",
                        "supplementary_source": "supplementary/prjtest.pdf",
                        "inclusion_status": "site_curated",
                        "inclusion_note": "Sample one",
                    },
                    {
                        "identity": {
                            "namespace": "ovis_aries:curated_sample",
                            "stable_token": "ovis_aries:sample:two",
                            "accession_lineage": [],
                        },
                        "locality_identity": {
                            "namespace": "ovis_aries:sample_locality",
                            "stable_token": "ovis_aries:project-locality:prjtest",
                            "locality_text": "Site Two",
                            "political_entity": "Sweden",
                            "source_anchor_tokens": ["PRJTEST"],
                        },
                        "project_accession": "PRJTEST",
                        "supplementary_source": "supplementary/prjtest.pdf",
                        "inclusion_status": "site_curated",
                        "inclusion_note": "Sample two",
                    },
                ],
            },
        )
        _write_json(
            species_root / "normalized" / "coordinate_provenance.json",
            {
                "schema_version": "adna-coordinate-provenance-export.v1",
                "species_latin_name": "Ovis aries",
                "coordinate_provenance": [
                    {
                        "project_accession": "PRJTEST",
                        "species_latin_name": "Ovis aries",
                        "species_common_name": "sheep",
                        "site_label": "Flattened locality",
                        "original_place_text": "Flattened locality",
                        "resolved_place_text": "Flattened locality",
                        "political_entity": "Sweden",
                        "source_artifact_path": "adna/governance/source_library/papers/test/article.html",
                        "source_locator": "supplementary table",
                        "coordinate_basis": "named_site_geocoding",
                        "mapping_posture": "mappable_point",
                        "latitude_text": "59.4",
                        "longitude_text": "18.1",
                        "geocoding_method": "manual_named_place_resolution",
                        "geocoder_or_gazetteer": "test anchor",
                        "confidence_rationale": "Named-place geocode retained for the atlas.",
                        "coordinate_confidence": "approximate",
                        "paper_doi": "10.1000/test",
                        "paper_url": "https://doi.org/10.1000/test",
                        "supplementary_source": "supplementary/prjtest.pdf",
                        "chronology_text": "1001-3000 BP",
                        "time_start_bp": 1200,
                        "time_end_bp": 1600,
                        "dating_basis": "bp_window",
                        "comparator_context": False,
                        "domestication_context": "domesticated_core",
                        "interpretation_note": "Named-place sheep anchor.",
                        "support_gap_note": "",
                    }
                ],
            },
        )
        _write_json(
            species_root / "normalized" / "site_evidence.json",
            {
                "schema_version": "adna-site-evidence-export.v1",
                "species_latin_name": "Ovis aries",
                "site_evidence": [
                    {
                        "project_accession": "PRJTEST",
                        "species_latin_name": "Ovis aries",
                        "species_common_name": "sheep",
                        "site_label": "Flattened locality",
                        "political_entity": "Sweden",
                        "source_artifact_path": "adna/governance/source_library/papers/test/article.html",
                        "source_artifact_kind": "article_html_body_quote",
                        "source_locator": "supplementary table",
                        "exact_source_text": "Two distinct sample sites exist.",
                        "source_support_status": "article_exact_quote",
                        "paper_doi": "10.1000/test",
                        "paper_url": "https://doi.org/10.1000/test",
                        "supplementary_source": "supplementary/prjtest.pdf",
                        "coordinate_basis": "site_level_localities",
                        "latitude_text": "59.4",
                        "longitude_text": "18.1",
                        "chronology_text": "1001-3000 BP",
                        "time_start_bp": 1200,
                        "time_end_bp": 1600,
                        "dating_basis": "bp_window",
                        "comparator_context": False,
                        "domestication_context": "domesticated_core",
                        "interpretation_note": "Site-backed evidence row.",
                        "support_gap_note": "",
                    }
                ],
            },
        )
        _write_json(
            species_root / "reports" / "support_summary.json",
            {"dataset_review": {"product_role": "domesticated_core"}},
        )
        _write_json(
            species_root / "review" / "species_review.json",
            {
                "accepted_projects": [
                    {
                        "project_accession": "PRJTEST",
                        "support_class": "accepted",
                        "reason": "Mapped locality retained in atlas.",
                        "paper_title": "Test sheep aDNA",
                        "paper_doi": "10.1000/test",
                        "nordic_relevance": "nordic_lead",
                        "nordic_relevance_reason": "Curated Nordic lead",
                    }
                ],
                "rejected_projects": [],
                "too_weak_projects": [],
                "comparator_projects": [],
                "nordic_unmapped_leads": [],
            },
        )
        citation_path = species_root / "manifests" / "citation_manifest.csv"
        citation_path.parent.mkdir(parents=True, exist_ok=True)
        citation_path.write_text(
            (
                "project_accession,paper_title,paper_doi,publication_year,journal_title\n"
                "PRJTEST,Test sheep aDNA,10.1000/test,2024,Tracked Animal Journal\n"
            ),
            encoding="utf-8",
        )

        try:
            build_tracked_animal_atlas_evidence_rows(data_root)
        except ValueError as error:
            assert "Project-level flattening detected" in str(error)
        else:
            raise AssertionError("Expected project-level flattening to be refused.")
