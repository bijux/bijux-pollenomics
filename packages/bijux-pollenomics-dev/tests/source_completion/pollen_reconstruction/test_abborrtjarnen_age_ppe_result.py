"""Analytical controls for independent joint age/count/shared-PPE observation."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import time
from typing import Any

import numpy as np
import pytest

from .abborrtjarnen_age_ppe.independent_ledger import Observation, check_support
from .abborrtjarnen_age_ppe.independent_moments import (
    PopulationMoments,
    fixed_window,
    pooled_windows,
)
from .abborrtjarnen_age_ppe.independent_result import check_moments
from .abborrtjarnen_age_ppe.independent_sources import Sample, memberships


def test_count_covariance_has_exact_binomial_oracle() -> None:
    cover, counting, gradient = fixed_window((30, 70), np.ones(2), np.ones(2))
    np.testing.assert_allclose(cover, [0.3, 0.7], rtol=0, atol=1e-16)
    expected = np.array([[1, -1], [-1, 1]]) * float(Fraction(21, 10000))
    np.testing.assert_allclose(counting, expected, rtol=0, atol=1e-18)
    np.testing.assert_allclose(
        gradient, [[-0.21, 0.21], [0.21, -0.21]], rtol=0, atol=1e-16
    )


def test_nonuniform_response_and_ppe_match_exact_fraction_derivative() -> None:
    counts = (12, 20, 18)
    k, p = (1, 2, 3), (2, 3, 5)
    q = (Fraction(45, 79), Fraction(25, 79), Fraction(9, 79))
    expected = [
        [-q[i] * (int(i == j) - q[j]) / p[j] for j in range(3)] for i in range(3)
    ]
    cover, counting, gradient = fixed_window(counts, np.array(k), np.array(p))
    np.testing.assert_allclose(cover, list(map(float, q)), rtol=0, atol=1e-16)
    np.testing.assert_allclose(
        gradient, np.array(expected, dtype=float), rtol=0, atol=1e-16
    )
    np.testing.assert_allclose(counting.sum(axis=0), 0, rtol=0, atol=2e-18)
    rounding = 8 * np.finfo(float).eps * np.linalg.norm(counting, 2)
    assert np.linalg.eigvalsh(counting).min() >= -rounding


def test_frozen_age_recovers_fixed_panel_and_zero_interaction() -> None:
    c, n, g = pooled_windows(((30, 70), (60, 140)), np.ones(2), np.ones(2))
    moments = PopulationMoments.empty(4, np.array([0.1, 0.2]))
    moments.add(c, n, g, multiplicity=17)
    result = moments.finish()
    np.testing.assert_allclose(result["age"], 0, rtol=0, atol=0)
    np.testing.assert_allclose(result["count"], n, rtol=0, atol=1e-18)
    np.testing.assert_allclose(result["ppe_gradient_variation"], 0, rtol=0, atol=1e-18)
    contrast = np.array([-1, 0, 1, 0])
    assert abs(contrast @ result["ppe"] @ contrast) < 1e-18
    assert contrast @ result["count"] @ contrast > 0


def test_two_age_gradients_disprove_averaged_gradient_and_sharp_envelope() -> None:
    moments = PopulationMoments.empty(1, np.ones(2))
    for g in ((1, 1), (1, -1)):
        moments.add(np.array([0.5]), np.zeros((1, 1)), np.array([g]))
    result = moments.finish()
    assert result["ppe"].item() == 2
    assert result["ppe_mean_gradient"].item() == 1
    assert result["ppe_gradient_variation"].item() == 1
    # With the same correlation at both ages, opposing cross terms cancel.
    for rho in (-1, -0.4, 0, 0.7, 1):
        sigma = np.array([[1, rho], [rho, 1]])
        exact = sum(np.array(g) @ sigma @ np.array(g) for g in ((1, 1), (1, -1))) / 2
        assert exact == 2
    assert (0, 4) != (2, 2)  # Per-age sharp endpoints are not global extrema.


def test_population_denominator_and_zero_sd_preserve_age_and_count_terms() -> None:
    moments = PopulationMoments.empty(2, np.zeros(2))
    for c in ([0.2, 0.8], [0.8, 0.2]):
        moments.add(np.array(c), np.eye(2) * 0.01, np.ones((2, 2)))
    result = moments.finish()
    np.testing.assert_allclose(result["mean"], 0.5, rtol=0, atol=0)
    np.testing.assert_allclose(
        result["age"], [[0.09, -0.09], [-0.09, 0.09]], rtol=0, atol=3e-17
    )
    np.testing.assert_allclose(result["ppe"], 0, rtol=0, atol=0)
    np.testing.assert_allclose(
        result["total"], result["age"] + result["count"], rtol=0, atol=0
    )


def test_grouped_memberships_preserve_every_saved_row_weight() -> None:
    grouped = PopulationMoments.empty(2, np.array([0.1, 0.2]))
    expanded = PopulationMoments.empty(2, np.array([0.1, 0.2]))
    for counts, multiplicity in (((30, 70), 7), ((60, 40), 3)):
        c, n, g = fixed_window(counts, np.ones(2), np.ones(2))
        grouped.add(c, n, g, multiplicity=multiplicity)
        for _ in range(multiplicity):
            expanded.add(c, n, g)
    assert grouped.observations == expanded.observations == 10
    for key, value in grouped.finish().items():
        np.testing.assert_allclose(
            value,
            expanded.finish()[key],
            rtol=8 * np.finfo(float).eps,
            atol=np.finfo(float).eps,
        )


def test_all_native_members_and_half_open_missing_zero_boundaries() -> None:
    samples = {
        1: Sample(1, 1, (2, 1, 0, 0, 0), 8),
        2: Sample(2, 2, (1, None, 0, 0, 0), 4),
        3: Sample(3, 3, (0, 0, 0, 0, 0), 2),
        4: Sample(4, 4, (0, 0, 0, 3, 1), 6),
        5: Sample(5, 5, (1, 1, 1, 1, 1), 9),
    }
    rows = memberships(np.array([1500, 2000, 2500, 4500, -52]), tuple(samples), samples)
    assert [row.sample_ids for row in rows] == [(1,), (2,), (3,), (4,)]
    assert [row.status for row in rows] == [
        "defined",
        "refused_missing_explicit_panel",
        "refused_zero_panel",
        "defined",
    ]
    assert rows[1].pooled is None and rows[1].panel_subtotal == 1
    assert rows[1].missing == {2: ("Cyperaceae",)}
    assert rows[2].pooled == (0, 0, 0, 0, 0)
    empty = memberships(np.full(5, -52), tuple(samples), samples)
    assert all(row.status == "refused_empty_window" for row in empty)


@pytest.mark.parametrize("counts", [(), (0, 0), (-1, 2), (1.0, 2), (True, 2)])
def test_invalid_count_measurements_refuse(counts: tuple[int, ...]) -> None:
    with pytest.raises(ValueError, match="Invalid independent"):
        fixed_window(counts, np.ones(2), np.ones(2))


def test_empty_conditional_population_is_not_a_zero_covariance() -> None:
    with pytest.raises(ValueError, match="No complete"):
        PopulationMoments.empty(20, np.ones(5)).finish()


@pytest.fixture
def saved_summary_control() -> tuple[dict[str, Any], Observation]:
    """Exercise the real summary serializer on two analytical membership states."""
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe.moments import (
        PopulationMoments as ProducerMoments,
    )

    sd = np.array([0.1, 0.05, 0.02, 0.1, 0])
    ppe = np.array([2, 1, 3, 4, 1])
    actual = ProducerMoments(np.diag(sd**2))
    expected = PopulationMoments.empty(20, sd)
    for a in (10, 25):
        pools = (
            (a, 30, 25, 10, 15),
            (10, a, 30, 25, 15),
            (15, 15, a, 20, 20),
            (40, 20, 20, a, 10),
        )
        c, n, g = pooled_windows(pools, np.ones(5), ppe)
        actual.add(c, n, g)
        expected.add(c, n, g)
    support = {b: Counter({"defined": 3}) for b in (3, 4, 5, 9)}
    support[9] = Counter({"defined": 2, "missing_explicit_five_taxon_member": 1})
    observed = Observation(3, 2, support, {}, expected, 0)
    result = {
        "requested_draws": 3,
        "complete_draws": 2,
        "undefined_draws": 1,
        "complete_probability": 2 / 3,
        "support_by_window": {
            str(b): {"status_counts": dict(counts), "probability_denominator": 3}
            for b, counts in support.items()
        },
        "unconditional": {
            "status": "refused_undefined_mass",
            "undefined_fraction": 1 / 3,
            "mean": None,
            "covariance": None,
            "defined_moments_reference": None,
        },
        "conditional_on_complete": actual.result(),
    }
    return result, observed


def test_real_summary_consumer_matches_independent_population_oracle(
    saved_summary_control: tuple[dict[str, Any], Observation],
) -> None:
    result, observed = saved_summary_control
    checked = check_moments(result, observed)
    assert checked["covariance_entries_checked"] == 2400
    assert checked["contrasts_checked"] == 30
    assert checked["maximum_moment_gap"] < 1e-12


@pytest.mark.parametrize(
    "fault",
    [
        "missing_interaction",
        "population",
        "unconditional",
        "diagnostic",
        "contrast_axis",
    ],
)
def test_summary_contradictions_are_refused(
    saved_summary_control: tuple[dict[str, Any], Observation], fault: str
) -> None:
    saved, observed = saved_summary_control
    result = deepcopy(saved)
    conditional = result["conditional_on_complete"]
    if fault == "missing_interaction":
        conditional["covariance_components"]["shared_ppe"] = conditional[
            "covariance_components"
        ]["mean_gradient_ppe"]
    elif fault == "population":
        result["complete_draws"] = 3
    elif fault == "unconditional":
        result["unconditional"]["defined_moments_reference"] = "conditional_on_complete"
    elif fault == "diagnostic":
        conditional["numeric_checks"]["age"]["minimum_eigenvalue"] = 1
    else:
        conditional["contrasts"][0]["older_window_id"] = 9
    with pytest.raises(ValueError):
        check_moments(result, observed)


def test_membership_preserves_declared_native_column_order() -> None:
    samples = {5: Sample(5, 1, (1, 1, 1, 1, 1), 8), 1: Sample(1, 2, (2, 1, 1, 1, 1), 9)}
    row = memberships(np.array([1550, 1600]), (5, 1), samples)[0]
    assert row.sample_ids == (5, 1)


def test_missing_member_cannot_be_serialized_as_observed_zero_mass() -> None:
    samples = {7: Sample(7, 1, (1, None, 2, 3, 4), 15)}
    member = memberships(np.array([1550]), (7,), samples)[0]
    row = {
        "bin_3_status": "missing_explicit_five_taxon_member",
        "bin_3_sample_ids": "[7]",
        "bin_3_sample_count": "1",
        "bin_3_reported_panel_subtotal": "10",
        "bin_3_panel_mass": "",
        "bin_3_all_reported_pollen_nisp": "15",
        "bin_3_omitted_reported_pollen_nisp": "5",
        "bin_3_missing_members": '{"7":["Cyperaceae"]}',
    }
    check_support(row, 3, member)
    row["bin_3_panel_mass"] = "0"
    with pytest.raises(ValueError, match="support or counted mass"):
        check_support(row, 3, member)


def test_zero_complete_rows_retain_refused_moments_and_all_contrast_identities(
    saved_summary_control: tuple[dict[str, Any], Observation],
) -> None:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe.moments import (
        PopulationMoments as ProducerMoments,
    )

    result, observed = saved_summary_control
    result = deepcopy(result)
    observed.complete = 0
    observed.support[9] = Counter({"missing_explicit_five_taxon_member": 3})
    observed.moments = PopulationMoments.empty(20, np.zeros(5))
    result.update(complete_draws=0, undefined_draws=3, complete_probability=0)
    result["support_by_window"]["9"]["status_counts"] = dict(observed.support[9])
    result["unconditional"]["undefined_fraction"] = 1
    result["conditional_on_complete"] = ProducerMoments(np.zeros((5, 5))).result()
    assert check_moments(result, observed)["covariance_entries_checked"] == 0
    result["conditional_on_complete"]["covariance_components"] = {
        "total": np.zeros((20, 20)).tolist()
    }
    with pytest.raises(ValueError, match="invented moments"):
        check_moments(result, observed)


def main() -> None:
    """Verify an already saved result using clean committed observer sources."""
    from .abborrtjarnen_age_ppe.independent_result import verify_result

    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "source-root", "result", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    entry = Path(__file__).resolve()
    helpers = entry.parent / "abborrtjarnen_age_ppe"
    paths = [entry, *sorted(helpers.glob("independent_*.py"))]
    relative = [str(path.relative_to(repository)) for path in paths]
    prefix = ["git", "-C", str(repository)]
    subprocess.run(
        [*prefix, "ls-files", "--error-unmatch", "--", *relative],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [*prefix, "diff", "--exit-code", "HEAD", "--", *relative],
        check=True,
        capture_output=True,
    )
    revision = subprocess.check_output(
        [*prefix, "rev-parse", "HEAD"], text=True
    ).strip()
    output = args.output.absolute()
    if (
        output.exists()
        or not output.resolve().is_relative_to(repository / "artifacts")
        or any(p.is_symlink() for p in (output, *output.parents))
    ):
        raise ValueError("Observer output must be absent beneath repository artifacts")
    started = time.monotonic()
    checked = verify_result(
        repository,
        args.source_root.resolve(strict=True),
        args.result.resolve(strict=True),
    )
    checked["observer_source_commit"] = revision
    checked["elapsed_seconds"] = time.monotonic() - started
    subprocess.run(
        [*prefix, "diff", "--exit-code", revision, "--", *relative],
        check=True,
        capture_output=True,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(checked, indent=2, allow_nan=False) + "\n")
    print(json.dumps(checked, sort_keys=True))


if __name__ == "__main__":
    main()
