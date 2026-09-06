"""Source inventory catalog tests."""

from __future__ import annotations

import pytest

from bijux_pollenomics.adna.governance.audit_catalogs.source_inventory import (
    build_cross_species_archive_inventory,
    build_cross_species_bibliography,
    build_species_freshness_table,
)

pytestmark = pytest.mark.generated_artifacts


def test_cross_species_bibliography_deduplicates_shared_literature() -> None:
    bibliography = build_cross_species_bibliography()

    assert any(
        row["paper_doi"] == "10.1038/s41586-021-04018-9"
        and "Equus caballus" in row["species_latin_names"]
        for row in bibliography
    )


def test_cross_species_archive_inventory_reports_access_policies() -> None:
    inventory = build_cross_species_archive_inventory()

    assert any(
        row["project_accession"] == "PRJEB22390"
        and row["access_policy"] == "public_downloadable"
        for row in inventory
    )


def test_cross_species_freshness_table_tracks_nordic_mapping_posture() -> None:
    freshness_rows = build_species_freshness_table()
    sheep_row = next(
        row for row in freshness_rows if row["species_latin_name"] == "Ovis aries"
    )

    assert sheep_row["has_nordic_mapped_lead"]
    assert not sheep_row["has_nordic_unmapped_lead"]
    assert sheep_row["inventory_last_checked_on"] == "2026-09-06"
