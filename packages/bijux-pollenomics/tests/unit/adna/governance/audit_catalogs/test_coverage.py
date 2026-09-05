"""Tracked-species coverage catalog tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.adna.governance.audit_catalogs.coverage import (
    build_cross_species_coverage_dashboard,
    build_shipped_adna_product_audit,
)

pytestmark = pytest.mark.generated_artifacts


def test_coverage_dashboard_reports_shipped_and_missing_surfaces(
    catalog_data_root: Path,
    report_root: Path,
) -> None:
    dashboard = build_cross_species_coverage_dashboard(catalog_data_root, report_root)
    product_audit = build_shipped_adna_product_audit(catalog_data_root, report_root)

    horse_row = next(
        row
        for row in dashboard["rows"]
        if row["species_latin_name"] == "Equus caballus"
    )
    assert horse_row["raw_inventory_present"]
    assert horse_row["raw_source_snapshot_present"]
    assert horse_row["citation_manifest_present"]
    assert horse_row["country_output_count"] == 0
    assert horse_row["atlas_layer_count"] == 0
    assert product_audit["species_with_source_snapshots"] == 10
    assert "Equus caballus" in product_audit["missing_public_outputs"]
