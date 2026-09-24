"""Guard the independent author-R side of published-window comparisons."""

from __future__ import annotations

import csv
from decimal import Decimal

import pytest

from bijux_pollenomics_dev.essd_reproduction.published_window_provenance import (
    _author_r_values,
)


def test_author_r_selection_keeps_only_exact_regional_bin_and_scales_units(
    tmp_path,
) -> None:
    path = tmp_path / "author.csv"
    fields = (
        "source",
        "grid_id",
        "scope",
        "site_id",
        "bin_id_bp",
        "taxon",
        "metric",
        "unit",
        "author_reference",
        "installed_lra",
        "signed_residual",
        "within_declared_tolerance",
    )
    row = {
        "source": "ESSD_LandClim_author_R_example",
        "grid_id": "512",
        "scope": "regional",
        "site_id": "",
        "bin_id_bp": "225",
        "taxon": "Oak",
        "metric": "mean",
        "unit": "fraction",
        "author_reference": "0.125",
        "installed_lra": "0.1250000000001",
        "signed_residual": "0.0000000000001",
        "within_declared_tolerance": "True",
    }

    def write(rows):
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    write([row, {**row, "scope": "site", "site_id": "A"}])
    assert _author_r_values(path, {"Oak": "Quercus"}) == {
        ("512", "Quercus", "mean"): (Decimal("12.500"), Decimal("12.5000000000100"))
    }
    write([row, row])
    with pytest.raises(ValueError, match="Duplicate author-R"):
        _author_r_values(path, {"Oak": "Quercus"})
    write([{**row, "within_declared_tolerance": "False"}])
    with pytest.raises(ValueError, match="unsupported axes or parity"):
        _author_r_values(path, {"Oak": "Quercus"})
