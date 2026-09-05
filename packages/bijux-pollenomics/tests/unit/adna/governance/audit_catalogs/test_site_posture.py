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

    assert len(unresolved) == 0
    assert len(overbroad) == 7


def test_coordinate_caveat_surface_groups_point_and_refused_rows(
    catalog_data_root: Path,
) -> None:
    caveat_surface = build_coordinate_caveat_surface(catalog_data_root)

    assert len(caveat_surface["direct_coordinates"]) == 234
    assert len(caveat_surface["place_name_resolution"]) == 2
    assert len(caveat_surface["still_weak_geography"]) == 7
    assert any(
        row["site_label"] == "Actiparc" for row in caveat_surface["direct_coordinates"]
    )
