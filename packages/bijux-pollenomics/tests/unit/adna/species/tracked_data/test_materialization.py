"""Tracked animal materialization stability tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.adna.species.tracked_data import (
    materialize_tracked_species_adna,
)

pytestmark = pytest.mark.generated_artifacts


def test_tracked_species_materialization_reaches_a_fixed_point_in_one_run(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    materialize_tracked_species_adna(data_root)
    first = {
        path.relative_to(data_root): path.read_bytes()
        for path in data_root.rglob("*")
        if path.is_file()
    }
    cattle_readme = first[Path("adna/species/bos_taurus/README.md")].decode("utf-8")
    assert "- Direct-coordinate rows: `5`" in cattle_readme

    materialize_tracked_species_adna(data_root)
    second = {
        path.relative_to(data_root): path.read_bytes()
        for path in data_root.rglob("*")
        if path.is_file()
    }

    assert second == first
