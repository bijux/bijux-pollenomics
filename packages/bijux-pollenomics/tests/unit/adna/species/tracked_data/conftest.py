"""Tracked animal evidence fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.adna.species.tracked_data import (
    materialize_tracked_species_adna,
)


@pytest.fixture(scope="package")
def tracked_data_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    data_root = tmp_path_factory.mktemp("tracked-animal-evidence") / "data"
    materialize_tracked_species_adna(data_root)
    return data_root
