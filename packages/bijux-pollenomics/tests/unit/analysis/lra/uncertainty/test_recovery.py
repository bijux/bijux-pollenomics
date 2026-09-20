"""Independent synthetic recovery checks for the supplied finite-law profile."""

from fractions import Fraction
from math import comb
from pathlib import Path

import pytest
from bijux_pollenomics.analysis.lra.uncertainty.admission import admit
from bijux_pollenomics.analysis.lra.uncertainty.contracts import JointLRAPlan
from bijux_pollenomics.analysis.lra.uncertainty.projection import projections
from bijux_pollenomics.analysis.lra.uncertainty.statistics import summaries

from .test_contracts import fixture


def _forward_pollen(cover: Fraction, ppe: Fraction) -> Fraction:
    """Independent two-taxon forward identity with unit deposition."""
    return ppe * cover / (ppe * cover + 1 - cover)


def _inverse_cover(pollen: Fraction, ppe: Fraction) -> Fraction:
    """Algebraic inverse of ``_forward_pollen``, not a production-kernel call."""
    return pollen / (ppe - pollen * (ppe - 1))


def _mass(value: int) -> dict[str, int]:
    return {"numerator": value, "denominator": 256}


def test_exact_known_landscape_recovers_only_with_correct_ppe() -> None:
    masses = [comb(4, k) * 3 ** (4 - k) for k in range(5)]
    assert masses == [81, 108, 54, 12, 1] and sum(masses) == 256

    correct_rows = []
    misspecified_rows = []
    for k, numerator in enumerate(masses):
        truth = Fraction(k, 4)
        pollen = _forward_pollen(truth, Fraction(3))
        recovered = _inverse_cover(pollen, Fraction(3))
        misspecified = _inverse_cover(pollen, Fraction(1))
        assert recovered == truth
        row = {
            "bin_id": "known-landscape",
            "status": "success",
            "mass": _mass(numerator),
            "coordinates": [
                {"role": "regional", "unit": "fraction"},
                {"role": "local", "unit": "fraction"},
            ],
        }
        correct_rows.append({**row, "values": [float(recovered), float(recovered)]})
        misspecified_rows.append(
            {**row, "values": [float(misspecified), float(misspecified)]}
        )

    recovered = summaries(correct_rows, ["known-landscape"])["known-landscape"]
    assert recovered["mean"] == pytest.approx([1 / 4, 1 / 4])
    assert all(
        row == pytest.approx([3 / 64, 3 / 64])
        for row in recovered["population_covariance"]
    )

    wrong = summaries(misspecified_rows, ["known-landscape"])["known-landscape"]
    expected_wrong_mean = Fraction(1063, 2560)
    assert wrong["mean"] == pytest.approx([expected_wrong_mean, expected_wrong_mean])
    assert wrong["mean"] != pytest.approx(recovered["mean"])


def test_half_open_allocation_retains_excluded_closed_endpoint_mass(
    tmp_path: Path,
) -> None:
    _, payload = fixture(tmp_path)
    payload["bins"][0].update(younger_bp=50, older_bp=150)
    projected = projections(admit(JointLRAPlan.from_dict(payload), tmp_path))
    rows = []
    for projection, _, _ in projected:
        success = projection["status"] == "ready"
        rows.append(
            {
                **projection,
                "status": "success" if success else "refused",
                "coordinates": [{"role": "regional", "unit": "fraction"}],
                "values": [0.25],
            }
        )

    result = summaries(rows, ["target"])["target"]
    assert result["successful_mass"] == {"numerator": 1, "denominator": 2}
    assert result["failed_mass"] == {"numerator": 1, "denominator": 2}
    assert result["complete"] is False
    assert result["mean"] is None and result["population_covariance"] is None
