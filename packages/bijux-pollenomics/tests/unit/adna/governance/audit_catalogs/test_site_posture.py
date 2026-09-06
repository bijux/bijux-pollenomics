"""Animal site-posture audit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.adna.governance.audit_catalogs.site_posture import (
    build_coordinate_caveat_surface,
    build_overbroad_site_ledger,
    build_unresolved_site_ledger,
)

pytestmark = pytest.mark.generated_artifacts


def test_site_ledgers_retain_unresolved_and_region_refused_denominators(
    catalog_data_root: Path,
) -> None:
    unresolved = build_unresolved_site_ledger(catalog_data_root)
    overbroad = build_overbroad_site_ledger(catalog_data_root)

    assert len(unresolved) == 95
    assert len(overbroad) == 4
    assert "PRJEB30282" not in {row["project_accession"] for row in overbroad}


def test_coordinate_caveat_surface_groups_point_and_refused_rows(
    catalog_data_root: Path,
) -> None:
    caveat_surface = build_coordinate_caveat_surface(catalog_data_root)

    assert len(caveat_surface["direct_coordinates"]) == 274
    assert len(caveat_surface["place_name_resolution"]) == 4
    assert len(caveat_surface["still_weak_geography"]) == 6
    assert {
        (row["project_accession"], row["site_label"])
        for row in caveat_surface["place_name_resolution"]
        if row["project_accession"] == "PRJEB30282"
    } == {
        ("PRJEB30282", "Bundsø"),
        ("PRJEB30282", "Trelleborg"),
    }
    assert {
        (row["project_accession"], row["site_label"], row["mapping_posture"])
        for row in caveat_surface["still_weak_geography"]
        if row["project_accession"] == "PRJEB59481"
    } == {
        ("PRJEB59481", "Kastelholm", "refused_unresolved_location"),
        ("PRJEB59481", "Stora Förvar", "refused_unresolved_location"),
    }
    assert any(
        row["site_label"] == "Actiparc" for row in caveat_surface["direct_coordinates"]
    )
