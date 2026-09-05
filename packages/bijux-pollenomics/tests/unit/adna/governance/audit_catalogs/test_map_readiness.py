"""Animal map-readiness accounting tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.adna.governance.audit_catalogs.map_readiness import (
    _map_publication_key,
    build_cross_species_map_readiness,
)

pytestmark = pytest.mark.generated_artifacts


def test_map_publication_identity_separates_sibling_sites() -> None:
    shared = {
        "species_latin_name": "Equus caballus",
        "project_accession": "PRJEB1",
        "source_locator": "table 1",
        "coordinate_basis": "supplementary_table_coordinates",
        "original_place_text": "shared context",
        "resolved_place_text": "shared context",
    }
    site_a = {
        **shared,
        "site_label": "Site A",
        "latitude_text": "55.0",
        "longitude_text": "12.0",
    }
    site_b = {
        **shared,
        "site_label": "Site B",
        "latitude_text": "56.0",
        "longitude_text": "13.0",
    }

    assert _map_publication_key(
        site_a, project_field="project_accession"
    ) != _map_publication_key(site_b, project_field="project_accession")


def test_map_readiness_reconciles_point_ready_and_unpublished_counts(
    catalog_data_root: Path,
) -> None:
    readiness = build_cross_species_map_readiness(catalog_data_root)

    horse_row = next(
        row
        for row in readiness["rows"]
        if row["species_latin_name"] == "Equus caballus"
    )
    sheep_row = next(
        row for row in readiness["rows"] if row["species_latin_name"] == "Ovis aries"
    )
    assert readiness["totals"]["direct_coordinate_backed"] == 234
    assert readiness["totals"]["indirectly_geocoded"] == 2
    assert readiness["totals"]["coordinate_provenance_mappable_count"] == 236
    assert readiness["totals"]["publication_candidate_count"] == 233
    assert readiness["totals"]["not_materialized_count"] == 3
    assert readiness["totals"]["refused_from_mapping"] == 7
    assert readiness["totals"]["unresolved"] == 0
    assert readiness["publication_accounting"]["overall_ok"]
    assert {
        (row["project_accession"], row["site_label"])
        for row in readiness["not_materialized_rows"]
    } == {
        ("PRJEB22390", "Botai archaeological site horse context"),
        ("PRJEB90261", "Lobos"),
        ("SRP073444", "Site 1040 near Wadi Halfa dromedary context"),
    }
    assert {row["reason_code"] for row in readiness["not_materialized_rows"]} == {
        "no_sample_backed_locality_candidate"
    }
    assert horse_row["direct_coordinate_backed"] == 207
    assert horse_row["indirectly_geocoded"] == 1
    assert sheep_row["refused_from_mapping"] == 1
