from __future__ import annotations

import json
from pathlib import Path
import tempfile

from bijux_pollenomics.reporting.adna import (
    build_tracked_animal_atlas_coordinate_review,
    build_tracked_animal_atlas_evidence_rows,
    load_tracked_animal_mappable_localities,
)


def test_animal_atlas_evidence_rows_keep_traceability_fields_and_point_filter() -> None:
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
                            "stable_token": "ovis_aries:project-locality:prjeb59481",
                            "locality_text": "Baltic sheep lead",
                            "political_entity": "Sweden",
                            "source_anchor_tokens": ["PRJEB59481"],
                        },
                        "species_latin_name": "Ovis aries",
                        "species_common_name": "sheep",
                        "source_family": "ENA",
                        "source_releases": ["PRJEB59481"],
                        "record_modalities": ["metadata_only"],
                        "review_strengths": ["paper_pinned"],
                        "provenance_qualities": ["tracked_curated"],
                        "locality": "Baltic sheep lead",
                        "coordinates": {
                            "latitude": 59.4,
                            "longitude": 18.1,
                            "latitude_text": "59.4",
                            "longitude_text": "18.1",
                            "confidence": "approximate",
                        },
                        "sample_count": 1,
                        "sample_ids": ["PRJEB59481:lead"],
                        "datasets": ["animal-adna"],
                        "chronology": {
                            "original_text": "1001-3000 BP",
                            "time_start_bp": 1200,
                            "time_end_bp": 1600,
                            "time_mean_bp": 1400,
                            "dating_basis": "bp_window",
                        },
                        "sample_namespace": "animal-locality",
                        "project_accessions": ["PRJEB59481"],
                        "original_location_text": "Baltic sheep lead",
                        "nordic_inclusion": True,
                        "nordic_inclusion_reason": "Curated Nordic lead",
                        "interpretation_note": "Tracked atlas locality lead",
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
                            "stable_token": "ovis_aries:sample:prjeb59481",
                            "accession_lineage": [
                                "species:Ovis aries",
                                "source:ENA",
                                "project:PRJEB59481",
                                "sample:PRJEB59481",
                            ],
                        },
                        "locality_identity": {
                            "namespace": "animal-locality",
                            "stable_token": "ovis_aries:project-locality:prjeb59481",
                            "locality_text": "Baltic sheep lead",
                            "political_entity": "Sweden",
                            "source_anchor_tokens": ["PRJEB59481"],
                        },
                        "group_id": "PRJEB59481",
                        "project_accession": "PRJEB59481",
                        "supplementary_source": "supplementary/prjeb59481.pdf",
                        "inclusion_status": "nordic_lead_site_curated",
                        "inclusion_note": "Curated into the atlas evidence contract.",
                    }
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
                        "project_accession": "PRJEB59481",
                        "species_latin_name": "Ovis aries",
                        "species_common_name": "sheep",
                        "site_label": "Baltic sheep lead",
                        "original_place_text": "Baltic sheep lead",
                        "resolved_place_text": "Baltic sheep lead",
                        "political_entity": "Sweden",
                        "source_artifact_path": "adna/governance/source_library/papers/10.1000-sheep/article.html",
                        "source_locator": "supplementary table",
                        "coordinate_basis": "named_site_geocoding",
                        "mapping_posture": "mappable_point",
                        "latitude_text": "59.4",
                        "longitude_text": "18.1",
                        "geocoding_method": "manual_named_place_resolution",
                        "geocoder_or_gazetteer": "test archaeological site anchor",
                        "confidence_rationale": "Named-place geocode retained for the atlas.",
                        "coordinate_confidence": "approximate",
                        "paper_doi": "10.1000/sheep",
                        "paper_url": "https://doi.org/10.1000/sheep",
                        "supplementary_source": "supplementary/prjeb59481.pdf",
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
                        "project_accession": "PRJEB59481",
                        "species_latin_name": "Ovis aries",
                        "species_common_name": "sheep",
                        "site_label": "Baltic sheep lead",
                        "political_entity": "Sweden",
                        "source_artifact_path": "adna/governance/source_library/papers/10.1000-sheep/article.html",
                        "source_artifact_kind": "article_html_body_quote",
                        "source_locator": "supplementary table",
                        "exact_source_text": "Baltic sheep lead named in the source support.",
                        "source_support_status": "article_exact_quote",
                        "paper_doi": "10.1000/sheep",
                        "paper_url": "https://doi.org/10.1000/sheep",
                        "supplementary_source": "supplementary/prjeb59481.pdf",
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
                        "project_accession": "PRJEB59481",
                        "support_class": "accepted",
                        "reason": "Mapped locality retained in atlas.",
                        "paper_title": "Baltic short-tailed sheep aDNA",
                        "paper_doi": "10.1000/sheep",
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
                "PRJEB59481,Baltic short-tailed sheep aDNA,10.1000/sheep,2024,Tracked Animal Journal\n"
            ),
            encoding="utf-8",
        )

        rows = build_tracked_animal_atlas_evidence_rows(data_root)
        localities = load_tracked_animal_mappable_localities(data_root)
        coordinate_review = build_tracked_animal_atlas_coordinate_review(rows)

    assert len(rows) == 1
    assert len(localities) == 1
    row = rows[0]
    assert (
        row.feature_id == "animal-atlas-feature:ovis-aries-project-locality-prjeb59481"
    )
    assert (
        row.evidence_row_id
        == "animal-atlas-row:ovis-aries-prjeb59481-ovis-aries-project-locality-prjeb59481"
    )
    assert row.coordinate_basis == "named_site_geocoding"
    assert row.sample_record_ids == ("ovis_aries:sample:prjeb59481",)
    assert row.sample_group_ids == ("PRJEB59481",)
    assert row.paper_doi == "10.1000/sheep"
    assert row.source_locator == "supplementary table"
    assert row.exact_source_text == "Baltic sheep lead named in the source support."
    assert row.coordinate_source_artifact_path.endswith("10.1000-sheep/article.html")
    assert row.coordinate_source_locator == "supplementary table"
    assert coordinate_review.direct_coordinate_feature_count == 0
    assert coordinate_review.named_site_geocoded_feature_count == 1
    assert coordinate_review.weaker_geography_feature_count == 0


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


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
