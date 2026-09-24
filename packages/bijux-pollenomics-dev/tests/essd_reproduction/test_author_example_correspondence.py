"""Check cell correspondence without treating unavailable windows as zero cover."""

from __future__ import annotations

import csv

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_example_correspondence import (
    _candidate,
    _metric,
)


def test_blank_unavailable_cell_is_undefined(tmp_path) -> None:
    path = tmp_path / "cover.csv"
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerows([["bin_id", "Pinus"], ["50", "0.25"], ["225", ""]])
    values = _candidate(path, ["50", "225"], ["Pinus"])
    assert values[("50", "Pinus")] == 0.25
    assert values[("225", "Pinus")] != values[("225", "Pinus")]


def test_metric_exports_supported_cells_and_signed_residuals() -> None:
    rows, summary = _metric(
        grid="512",
        scope="site",
        site="WHH05",
        bins=["50", "225"],
        taxa=["Pinus", "Quercus"],
        supported={"225"},
        actual={
            ("50", "Pinus"): float("nan"),
            ("50", "Quercus"): float("nan"),
            ("225", "Pinus"): 0.2,
            ("225", "Quercus"): 0.3,
        },
        expected={
            ("50", "Pinus"): 0.0,
            ("50", "Quercus"): 0.0,
            ("225", "Pinus"): 0.2,
            ("225", "Quercus"): 0.3000000000001,
        },
        metric="mean",
    )
    assert len(rows) == 2
    assert rows[1]["signed_residual"] == pytest.approx(-1e-13)
    assert summary["excluded_unavailable_bins"] == 1
    assert summary["compared_values"] == 2
    assert summary["within_declared_tolerance"] is True


def test_metric_rejects_undefined_supported_estimate() -> None:
    with pytest.raises(ValueError, match="Undefined supported estimate"):
        _metric(
            grid="512",
            scope="regional",
            site="",
            bins=["50"],
            taxa=["Pinus"],
            supported={"50"},
            actual={("50", "Pinus"): float("nan")},
            expected={("50", "Pinus"): 0.0},
            metric="standard_error",
        )


def test_metric_fails_existing_tolerance_without_recalibration() -> None:
    rows, summary = _metric(
        grid="512",
        scope="regional",
        site="",
        bins=["50"],
        taxa=["Pinus"],
        supported={"50"},
        actual={("50", "Pinus"): 0.5},
        expected={("50", "Pinus"): 0.4},
        metric="mean",
    )
    assert rows[0]["within_declared_tolerance"] is False
    assert summary["within_declared_tolerance"] is False
