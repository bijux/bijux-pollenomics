"""Guard the independent author-R side of published-window comparisons."""

from __future__ import annotations

import csv
from decimal import Decimal
from math import sqrt

import pytest

from bijux_pollenomics_dev.essd_reproduction.published_window_provenance import (
    _author_r_values,
    _mean_vector_diagnostics,
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


def test_mean_vector_diagnostics_preserve_mass_and_absolute_gaps() -> None:
    rows = [
        {
            "grid_id": grid,
            "metric": "mean",
            "taxon": f"taxon-{index}",
            "archive": str((50, 30, 20)[index] if index < 3 else 0),
            "author_r": str((55, 28, 17)[index] if index < 3 else 0),
        }
        for grid in ("512", "562")
        for index in range(31)
    ]
    diagnostics = _mean_vector_diagnostics(rows)
    assert len(diagnostics) == 2
    assert diagnostics[0]["archive_mean_sum_percentage_points"] == "100"
    assert diagnostics[0]["author_r_mean_sum_percentage_points"] == "100"
    assert diagnostics[0]["mean_l1_gap_percentage_points"] == "10"
    assert diagnostics[0]["mean_total_variation_fraction"] == "0.05"
    expected_hellinger = sqrt(
        sum(
            (sqrt(left / 100) - sqrt(right / 100)) ** 2
            for left, right in zip((50, 30, 20), (55, 28, 17), strict=True)
        )
        / 2
    )
    assert float(diagnostics[0]["mean_hellinger_distance"]) == pytest.approx(
        expected_hellinger, abs=1e-15
    )
    assert diagnostics[0]["largest_gap_taxon"] == "taxon-0"
    assert diagnostics[0]["second_largest_gap_taxon"] == "taxon-2"
    assert Decimal(diagnostics[0]["two_largest_gap_share"]) == Decimal("0.8")
    with pytest.raises(ValueError, match="taxon axis"):
        _mean_vector_diagnostics(rows[:-1])
    with pytest.raises(ValueError, match="nonnegative and closed"):
        _mean_vector_diagnostics([{**rows[0], "archive": "-1"}, *rows[1:]])
    with pytest.raises(ValueError, match="nonnegative and closed"):
        _mean_vector_diagnostics([{**rows[0], "archive": "49"}, *rows[1:]])
