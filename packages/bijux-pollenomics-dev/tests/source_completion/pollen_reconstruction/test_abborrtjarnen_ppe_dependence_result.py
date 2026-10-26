"""Independent controls and saved-result entry for conditional ABBO PPE dependence."""

from __future__ import annotations

import argparse
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.essd_reproduction.pft_covariance.lengths import (
    LengthInterval,
    sum_length_range,
)

from .abborrtjarnen_ppe_dependence.independent_moments import (
    Rational,
    _fraction,
    _require,
    _window,
)
from .abborrtjarnen_ppe_dependence.independent_result import (
    _numeric_result,
    verify_result,
)
from .abborrtjarnen_ppe_dependence.independent_sources import BINS
from .abborrtjarnen_ppe_dependence.independent_witnesses import _planar_sum, _witness


@pytest.mark.parametrize(
    ("gradient", "sd", "expected"),
    [
        ((1, 1, 1), (3, 4, 5), (0, 144)),
        ((1, 1, 1), (7, 2, 1), (16, 100)),
        ((1, -2, 0), (1, 2, 3), (9, 25)),
        ((0, 0, 0), (1, 2, 3), (0, 0)),
        ((1, -1, 2), (0, 0, 0), (0, 0)),
        ((1, 1, 1, 1, 1), (1, 1, 1, 1, 1), (0, 25)),
    ],
)
def test_sharp_bounds_have_constructive_psd_witnesses(
    gradient: tuple[int, ...], sd: tuple[int, ...], expected: tuple[int, int]
) -> None:
    g, s = tuple(map(Fraction, gradient)), tuple(map(Fraction, sd))
    lengths = tuple(abs(a) * b for a, b in zip(g, s, strict=True))
    actual = sum_length_range(tuple(LengthInterval(a, a) for a in lengths))
    assert (actual.lower**2, actual.upper**2) == tuple(map(Fraction, expected))
    for upper in (False, True):
        matrix, scalar, _ = _witness(g, s, upper=upper)
        np.testing.assert_allclose(np.diag(matrix), np.square(sd), rtol=1e-14, atol=0)
        assert np.linalg.eigvalsh(matrix).min() >= -1e-12
        assert abs(scalar - Decimal(expected[int(upper)])) < Decimal("1e-80")
        assert (
            abs(
                float(np.array(gradient) @ matrix @ np.array(gradient))
                - expected[int(upper)]
            )
            < 1e-12
        )


def test_scalar_closure_has_binomial_count_variance_and_shared_ppe_gradient() -> None:
    q, h, variance = _window((30, 70), (Fraction(1),) * 2, (Fraction(1),) * 2)
    assert q == (Fraction(3, 10), Fraction(7, 10))
    assert variance == (Fraction(21, 10000),) * 2
    assert h == (
        (Fraction(-21, 100), Fraction(21, 100)),
        (Fraction(21, 100), Fraction(-21, 100)),
    )


def test_shared_temporal_parameter_cancels_for_identical_compositions() -> None:
    p = tuple(map(Fraction, (1, 2, 3)))
    first = _window((2, 3, 5), p, p)
    second = _window((4, 6, 10), p, p)
    assert first[:2] == second[:2]
    assert first[2] == tuple(2 * v for v in second[2])


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), "0.5"])
def test_non_native_or_nonfinite_scalar_tokens_refuse(value: Any) -> None:
    with pytest.raises(ValueError, match="finite native"):
        _fraction(value)


def test_impossible_vector_resultant_refuses() -> None:
    with pytest.raises(ValueError, match="Unattainable"):
        _planar_sum((Fraction(3), Fraction(1)), Fraction())


@pytest.fixture
def controlled_result(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, Any], dict[int, tuple[int, ...]], Rational, Rational]:
    """Exercise the actual consumer on invented controls, never source outcomes."""
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_ppe_dependence import (
        calculation,
    )

    monkeypatch.setattr(
        calculation,
        "circular_receiver_annulus",
        lambda **kwargs: SimpleNamespace(factor=1.0, estimated_absolute_error=0.0),
    )
    pooled: dict[int, tuple[int, ...]] = {
        b: (10 + 10 * i, 20, 30, 40, 50 - 10 * i) for i, b in enumerate(BINS)
    }
    sd = (0.1, 0.2, 0.3, 0.4, 0.0)
    result = calculation.calculate(
        {
            "protocol": {
                "physical": {
                    "source_reported_area_ha": 3,
                    "regional_extent_m": 100000,
                    "diffusion_coefficient": 0.12,
                    "turbulence_parameter": 0.25,
                    "wind_speed_m_s": 3,
                    "quadrature_absolute_tolerance": 1e-9,
                    "quadrature_relative_tolerance": 1e-8,
                }
            },
            "parameters": [
                {"ppe": 1.0, "published_sd": s, "fall_speed_m_s": 0.03} for s in sd
            ],
            "windows": [
                {"window_id": b, "pooled_panel_counts": list(n)}
                for b, n in pooled.items()
            ],
        }
    )
    result.update(
        {
            "model_fits": 0,
            "chronology_draws_consumed": 0,
            "historical_core_admission_changed": False,
            "whole_vegetation_or_calibrated_coverage_claim": False,
        }
    )
    return result, pooled, (Fraction(1),) * 5, tuple(map(Fraction, sd))


def test_independent_scalar_observer_checks_complete_controlled_consumer(
    controlled_result: tuple[
        dict[str, Any], dict[int, tuple[int, ...]], Rational, Rational
    ],
) -> None:
    checked = _numeric_result(*controlled_result)
    assert checked["contrasts_checked"] == 30
    assert checked["positive_four_point_moment_witnesses"] == 60
    assert Decimal(checked["minimum_positive_ppe_witness_support"]) > 0


@pytest.mark.parametrize(
    "alteration", ["gradient", "count", "joint", "bound", "identity"]
)
def test_observer_refuses_changed_consumer_quantity(
    controlled_result: tuple[
        dict[str, Any], dict[int, tuple[int, ...]], Rational, Rational
    ],
    alteration: str,
) -> None:
    result = controlled_result[0]
    if alteration == "gradient":
        result["contrasts"][0]["shared_ppe_gradient"][0] += 0.01
    elif alteration == "count":
        result["contrasts"][0]["count_variance"] *= 2
    elif alteration == "joint":
        result["shared_diagonal_joint_covariance"][0][5] = 1
    elif alteration == "bound":
        result["contrasts"][0]["ppe_variance_bounds"]["exact_upper"] = "123"
    else:
        result["contrasts"].pop()
    with pytest.raises(ValueError):
        _numeric_result(*controlled_result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    entry = Path(__file__).resolve()
    observer_files = [
        entry,
        *(
            entry.parent / "abborrtjarnen_ppe_dependence" / name
            for name in (
                "independent_sources.py",
                "independent_moments.py",
                "independent_witnesses.py",
                "independent_result.py",
            )
        ),
    ]
    relative = [str(path.relative_to(repository)) for path in observer_files]
    subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "ls-files",
            "--error-unmatch",
            "--",
            *relative,
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "diff",
            "--exit-code",
            "HEAD",
            "--",
            *relative,
        ],
        check=True,
        capture_output=True,
    )
    destination = args.output.absolute()
    _require(
        not destination.exists()
        and destination.resolve().is_relative_to(repository / "artifacts")
        and not any(p.is_symlink() for p in (destination, *destination.parents)),
        "Observer output must be absent under repository artifacts",
    )
    started = time.monotonic()
    checked = verify_result(
        repository,
        args.source_root.resolve(strict=True),
        args.result.resolve(strict=True),
    )
    checked["observer_source_commit"] = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "HEAD"], text=True
    ).strip()
    checked["elapsed_seconds"] = time.monotonic() - started
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(checked, indent=2, allow_nan=False) + "\n")
    print(json.dumps(checked, sort_keys=True))
