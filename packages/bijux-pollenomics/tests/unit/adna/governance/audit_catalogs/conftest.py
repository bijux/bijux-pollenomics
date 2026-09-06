"""Shared immutable catalog workspace fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from bijux_pollenomics.adna.species.tracked_data import (
    materialize_tracked_species_adna,
)


@pytest.fixture(scope="package")
def catalog_data_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Materialize tracked animal evidence once for read-only catalog tests."""
    data_root = tmp_path_factory.mktemp("animal-audit-catalogs") / "data"
    materialize_tracked_species_adna(data_root)
    return data_root


@pytest.fixture
def report_root(tmp_path: Path) -> Path:
    """Return an isolated mutable report root."""
    return tmp_path / "docs" / "report"
