"""Focused edge cases for sample-site evidence policy."""

from __future__ import annotations

from types import SimpleNamespace

from bijux_pollenomics.adna.projects.registry.sites import (
    _artifact_kind_from_path,
    _Hierarchy,
    _project_level_locality_status,
    _recommended_next_surface,
    _resolve_hierarchy,
    _review_note_for,
)


def test_artifact_kinds_keep_source_surfaces_distinct() -> None:
    assert _artifact_kind_from_path("paper.pdf") == "supplementary_pdf_text"
    assert _artifact_kind_from_path("table.xlsx") == "supplementary_spreadsheet_row"
    assert (
        _artifact_kind_from_path("archive#Supplementary_Data_1")
        == "supplementary_spreadsheet_row"
    )
    assert _artifact_kind_from_path("article.html") == "article_or_archive_text"
    assert _artifact_kind_from_path("native.tsv") == "tracked_source_artifact"


def test_project_level_statuses_preserve_mapping_uncertainty() -> None:
    assert _project_level_locality_status(None) == "unresolved"
    assert (
        _project_level_locality_status(
            SimpleNamespace(mapping_posture="refused_region_only", coordinate_basis="")
        )
        == "region_only"
    )
    assert (
        _project_level_locality_status(
            SimpleNamespace(
                mapping_posture="mappable_point",
                coordinate_basis="named_site_geocoding",
            )
        )
        == "named_place_inferred"
    )
    assert (
        _project_level_locality_status(
            SimpleNamespace(
                mapping_posture="mappable_point", coordinate_basis="centroid"
            )
        )
        == "project_level_site_only"
    )


def test_hierarchy_resolution_distinguishes_country_from_broader_geography() -> None:
    profile = _Hierarchy("Site", "Municipality", "Region", "Country", "Broader")
    assert (
        _resolve_hierarchy(
            hierarchy_profiles={"Site": profile},
            locality_text="Site context",
            political_entity="",
        )
        == profile
    )
    country = _resolve_hierarchy(
        hierarchy_profiles={}, locality_text="Uppsala", political_entity="Sweden"
    )
    assert country.country_name == "Sweden"
    assert country.broader_geography == ""
    region = _resolve_hierarchy(
        hierarchy_profiles={},
        locality_text="Transect",
        political_entity="Sweden; Norway",
    )
    assert region.country_name == ""
    assert region.broader_geography == "Sweden; Norway"


def test_curation_fallback_and_review_notes_are_deterministic() -> None:
    dossier: dict[str, object] = {
        "sample_site_targets": ["", "primary target"],
        "expected_supplementary_artifacts": ["supplement"],
        "local_artifact_paths": ["local"],
    }
    assert _recommended_next_surface(dossier) == "primary target"
    assert "region" in _review_note_for(status="region_only", site_row=None)
    assert "No location evidence" in _review_note_for(
        status="unresolved", site_row=None
    )
