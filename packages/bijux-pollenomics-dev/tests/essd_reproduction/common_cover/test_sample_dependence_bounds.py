"""Exact sample-weight concentration and fully dependent grain controls."""

from __future__ import annotations

from copy import deepcopy
import csv
from fractions import Fraction
from math import comb, factorial
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.essd_reproduction.common_cover import (
    cohort,
    within_site_homogeneity,
)
from bijux_pollenomics_dev.essd_reproduction.common_cover import (
    sample_dependence_bounds as subject,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin import (
    sources,
)
from bijux_pollenomics_lra.models.errors import ValidationError

from .test_within_site_homogeneity import loaded_fixture


def test_fixed_77_coordinate_union_has_a_rigorous_rational_failure_bound() -> None:
    exponential_lower = sum(
        (Fraction(9**k, factorial(k)) for k in range(9)), Fraction()
    )
    assert exponential_lower > 3080
    assert 2 * subject.FAMILY_COORDINATES / exponential_lower < Fraction(1, 20)
    assert 2 * subject.SQUARED_RADIUS_FACTOR == 9


@pytest.mark.parametrize(
    "table",
    [
        [[3, 1], [0, 6]],
        [[0, 3, 0], [5, 0, 2], [4, 1, 0]],
        [[1, 2]] * 6,
        [[1, 0]] * 64,
        [[10000, 0], [0, 1]],
    ],
)
def test_weights_means_and_grid_radius_are_exact_and_outward(
    table: list[list[int]],
) -> None:
    result = subject.sample_unit_bounds(table)
    efforts = list(map(sum, table))
    total = sum(efforts)
    expected = tuple(
        Fraction(sum(row[j] for row in table), total) for j in range(len(table[0]))
    )
    squared = sum((Fraction(n, total) ** 2 for n in efforts), Fraction())
    assert result.observed_fractions == expected and sum(expected) == 1
    assert result.sum_squared_weights == squared
    assert result.radius_upper is not None
    radius = result.radius_upper
    assert radius**2 >= Fraction(9, 2) * squared
    assert (radius - Fraction(1, subject.RADIUS_GRID)) ** 2 < Fraction(9, 2) * squared
    assert result.lower == tuple(max(Fraction(), p - radius) for p in expected)
    assert result.upper == tuple(min(Fraction(1), p + radius) for p in expected)


def test_grain_dependence_does_not_create_fictitious_sample_precision() -> None:
    ordinary = subject.sample_unit_bounds([[3, 1], [0, 6]])
    more_grains = subject.sample_unit_bounds([[300, 100], [0, 600]])
    assert ordinary.sum_squared_weights == more_grains.sum_squared_weights
    assert ordinary.observed_fractions == more_grains.observed_fractions
    assert ordinary.radius_upper == more_grains.radius_upper
    assert ordinary.lower == more_grains.lower and ordinary.upper == more_grains.upper


def test_perfectly_clustered_grains_have_conservative_exact_finite_sample_coverage() -> (
    None
):
    # Each independent sample puts ALL100 grains on one taxon: grains inside
    # a sample are perfectly dependent. Enumerate all65 binomial outcome masses.
    failure = Fraction()
    for successes in range(65):
        table = [[100, 0]] * successes + [[0, 100]] * (64 - successes)
        result = subject.sample_unit_bounds(table)
        assert result.lower is not None and result.upper is not None
        if not result.lower[0] <= Fraction(1, 2) <= result.upper[0]:
            failure += Fraction(comb(64, successes), 2**64)
    assert 0 < failure <= Fraction(1, 1540)
    assert 77 * failure < Fraction(1, 20)


def test_heterogeneous_sample_expectations_and_taxon_permutation_are_not_forced_common() -> (
    None
):
    table = [[100, 0, 0]] * 16 + [[0, 0, 100]] * 16
    result = subject.sample_unit_bounds(table)
    # Independent deterministic sample vectors have different expectations;
    # their weighted target equals(.5,0,.5), without a common probability model.
    assert result.observed_fractions == (Fraction(1, 2), Fraction(), Fraction(1, 2))
    permuted = subject.sample_unit_bounds([row[::-1] for row in table[::-1]])
    assert result.sum_squared_weights == permuted.sum_squared_weights
    assert result.radius_upper == permuted.radius_upper
    assert permuted.lower is not None and permuted.upper is not None
    assert result.lower == permuted.lower[::-1]
    assert result.upper == permuted.upper[::-1]


def test_one_sample_retains_full_radius_and_zero_rows_have_zero_weight() -> None:
    table = [[3, 1]]
    one = subject.sample_unit_bounds(table)
    with_zero = subject.sample_unit_bounds([[0, 0], *table, [0, 0]])
    assert one.radius_upper is not None and one.radius_upper > 1
    assert one.full_coordinate_domain is True
    assert one.lower == (Fraction(), Fraction())
    assert one.upper == (Fraction(1), Fraction(1))
    assert with_zero.sample_count == 3 and with_zero.positive_effort_samples == 1
    assert one.observed_fractions == with_zero.observed_fractions
    assert one.sum_squared_weights == with_zero.sum_squared_weights
    assert one.radius_upper == with_zero.radius_upper


def test_all_zero_effort_refuses_without_inventing_sample_fractions() -> None:
    result = subject.sample_unit_bounds([[0, 0], [0, 0]])
    assert result.refusal == "zero_full_panel_effort" and result.sample_count == 2
    assert result.panel_total == result.positive_effort_samples == 0
    assert result.pooled_counts == (0, 0)
    assert all(
        value is None
        for value in (
            result.observed_fractions,
            result.sum_squared_weights,
            result.radius_upper,
            result.lower,
            result.upper,
            result.full_coordinate_domain,
        )
    )


@pytest.mark.parametrize("value", [None, True, -1, 0.1, "1", float("inf"), 10001])
def test_original_native_count_admission_is_preserved(value: Any) -> None:
    with pytest.raises(ValidationError):
        subject.sample_unit_bounds([[value, 1], [1, 2]])


def test_masked_missingness_refuses_and_all_false_mask_preserves_exact_output() -> None:
    table = [[3, 1], [0, 6]]
    with pytest.raises(ValidationError):
        subject.sample_unit_bounds(
            np.ma.array(table, mask=[[True, False], [False, False]])
        )
    assert subject.sample_unit_bounds(
        np.ma.array(table, mask=False)
    ) == subject.sample_unit_bounds(table)


def test_all_original_windows_samples_and_measurement_panels_are_retained_without_simulation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    loaded = loaded_fixture()
    before = deepcopy(loaded)
    monkeypatch.setattr(
        within_site_homogeneity,
        "draw_table",
        lambda *_: pytest.fail("No sampler"),
    )
    rows = subject.evaluate(loaded)
    assert loaded == before and len(rows) == 32
    assert sum(row["sample_count"] for row in rows) == 110
    assert sum(len(row["taxa"].split("|")) for row in rows) == 77
    assert sum(not row["matched_window"] for row in rows) == 6
    for row in rows:
        assert row["status"] == "computed" and row["full_coordinate_domain"] is True
        for field in (
            "count",
            "observed_fraction",
            "expected_fraction_lower",
            "expected_fraction_upper",
        ):
            assert (row[f"Fraxinus_{field}"] == "") is (row["core"] == "BUS")


@pytest.mark.parametrize("defect", ["missing", "count", "axis", "unit"])
def test_existing_sample_parent_and_count_conservation_still_refuses(
    defect: str,
) -> None:
    loaded = loaded_fixture()
    if defect == "missing":
        loaded["sample_panels"].pop()
    elif defect == "count":
        loaded["sample_panels"][0]["counts"][0] += 1
    elif defect == "axis":
        loaded["sample_panels"][0]["taxa"].reverse()
    else:
        loaded["sample_panels"][0]["source_unit"] = "percent"
    with pytest.raises(ValidationError):
        subject.evaluate(loaded)


@pytest.mark.parametrize("change", ["none", "raw", "source"])
def test_cli_reads_once_retains_exact_csv_and_checks_terminal_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    change: str,
) -> None:
    loaded = loaded_fixture()
    output = tmp_path / "artifacts/bounds.csv"
    output.parent.mkdir()
    revisions, reads = [], []

    def revision(repository: Path) -> str:
        revisions.append(repository)
        return "2" * 40 if change == "source" and len(revisions) > 1 else "1" * 40

    def intake(repository: Path) -> dict[str, Any]:
        reads.append(repository)
        return loaded

    monkeypatch.setattr(subject, "_revision", revision)
    monkeypatch.setattr(cohort, "load_sample_count_groups", intake)
    monkeypatch.setattr(
        sys, "argv", ["bounds", "--repository", str(tmp_path), "--output", str(output)]
    )
    if change == "raw":
        loaded["scientific_inputs"] = [{"path": "raw.json"}]
        monkeypatch.setattr(
            sources,
            "read_bound",
            lambda *_: (_ for _ in ()).throw(ValueError("changed raw")),
        )
    if change != "none":
        with pytest.raises((ValueError, ValidationError)):
            subject.main()
        assert not output.exists()
    else:
        with pytest.raises(SystemExit) as terminal:
            subject.main()
        assert terminal.value.code == 0
        with output.open() as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 32 and len(output.read_bytes()) < 65536
        assert all(Fraction(row["radius_upper_exact"]) >= 1 for row in rows)
        assert "simulations=0" in capsys.readouterr().out
    assert reads == [tmp_path]
