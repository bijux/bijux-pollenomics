"""Analytical controls for changed conditioning populations and their contrasts."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from .abborrtjarnen_age_ppe.independent_ledger import STATUS, Observation
from .abborrtjarnen_age_ppe.independent_moments import PopulationMoments, pooled_windows
from .abborrtjarnen_age_ppe.independent_profile_comparison import ProfileComparison
from .abborrtjarnen_age_ppe.independent_profile_moments import check_profile_comparison
from .abborrtjarnen_age_ppe.independent_sources import BINS, memberships
from .test_abborrtjarnen_age_ppe_source_profile import (
    comparison_control,
    saved_membership_row,
)


@pytest.fixture
def compared_moments() -> tuple[
    dict[str, Any], dict[str, Any], Observation, ProfileComparison
]:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe.moments import (
        PopulationMoments as SerializedMoments,
    )
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe.profile_comparison import (
        NativeComparison,
    )

    native, samples, ages = comparison_control()
    sd = np.array([0.1, 0.05, 0.02, 0.1, 0])
    old_rows = [saved_membership_row(1, i, a, native) for i, a in enumerate(ages)]
    comparison = ProfileComparison(native, iter(old_rows), np.ones(5), np.ones(5), sd)
    active = Observation(
        3, 0, {b: Counter() for b in BINS}, {}, PopulationMoments.empty(20, sd), 0
    )
    source, strict = (
        SerializedMoments(np.diag(sd**2)),
        SerializedMoments(np.diag(sd**2)),
    )
    for i, a in enumerate(ages):
        windows = memberships(a, tuple(native), samples)
        comparison.observe(
            saved_membership_row(1, i, a, samples, native), a, tuple(native), windows
        )
        for b, w in zip(BINS, windows, strict=True):
            active.support[b][STATUS[w.status]] += 1
        if all(w.status == "defined" for w in windows):
            values = pooled_windows(
                tuple(w.pooled for w in windows if w.pooled is not None),
                np.ones(5),
                np.ones(5),
            )
            active.moments.add(*values)
            source.add(*values)
            active.complete += 1
            if old_rows[i]["complete"] == "1":
                strict.add(*values)
    comparison.finish(3)
    native_observed = comparison.observed
    old = {
        "requested_draws": 3,
        "complete_draws": 1,
        "undefined_draws": 2,
        "complete_probability": 1 / 3,
        "support_by_window": {
            str(b): {"status_counts": dict(v), "probability_denominator": 3}
            for b, v in native_observed.support.items()
        },
        "unconditional": {
            "status": "refused_undefined_mass",
            "undefined_fraction": 2 / 3,
            "mean": None,
            "covariance": None,
            "defined_moments_reference": None,
        },
        "conditional_on_complete": strict.result(),
    }
    serializer: Any = SimpleNamespace(
        reference_path="controlled-native",
        reference=old,
        moments=strict,
        checked=3,
        transitions=Counter(
            {
                f"native_{k[0]}->source_{k[-1]}": v
                for k, v in comparison.transitions.items()
            }
        ),
        window_transitions={
            str(b): v for b, v in comparison.window_transitions.items()
        },
    )
    packet = NativeComparison.result(serializer, source.result(), 3)
    return packet, old, active, comparison


def test_changed_event_mean_and_age_variance_have_exact_toy_answers(
    compared_moments: tuple[
        dict[str, Any], dict[str, Any], Observation, ProfileComparison
    ],
) -> None:
    packet, old, active, comparison = compared_moments
    checked = check_profile_comparison(
        packet, old, active, comparison, "controlled-native"
    )
    assert checked["profile_difference_entries_checked"] == 2420
    assert checked["profile_contrasts_checked"] == 30
    assert packet["native_complete_draws"] == 1 and packet["source_complete_draws"] == 2
    assert packet["complete_probability_difference"] == 1 / 3
    assert packet["conditional_mean_difference"][0] == pytest.approx(
        1 / 20, rel=0, abs=1e-16
    )
    assert packet["conditional_mean_difference"][1] == pytest.approx(
        -1 / 20, rel=0, abs=1e-16
    )
    assert packet["conditional_covariance_component_differences"]["age"][0][
        0
    ] == pytest.approx(1 / 400, rel=0, abs=1e-17)
    assert packet["conditional_covariance_component_differences"]["count"][0][
        0
    ] == pytest.approx(-11 / 2000, rel=0, abs=1e-17)


@pytest.mark.parametrize(
    "fault",
    [
        "population",
        "transition",
        "common_gap",
        "mean",
        "covariance",
        "contrast_axis",
        "contrast_variance",
        "contrast_spread",
    ],
)
def test_changed_event_packets_cannot_hide_population_or_moment_changes(
    compared_moments: tuple[
        dict[str, Any], dict[str, Any], Observation, ProfileComparison
    ],
    fault: str,
) -> None:
    saved, old, active, comparison = compared_moments
    packet = deepcopy(saved)
    if fault == "population":
        packet["source_complete_draws"] = 3
    elif fault == "transition":
        packet["support_transition_counts"]["native_1->source_0"] = 1
    elif fault == "common_gap":
        packet["common_native_population_check"]["maximum_moment_gap"] = 1e-6
    elif fault == "mean":
        packet["conditional_mean_difference"][0] = 0
    elif fault == "covariance":
        packet["conditional_covariance_component_differences"]["age"][0][0] = 0
    elif fault == "contrast_axis":
        packet["conditional_contrast_differences"][0]["older_window_id"] = 9
    elif fault == "contrast_variance":
        packet["conditional_contrast_differences"][0]["variance_component_changes"][
            "count"
        ] = 0
    else:
        packet["conditional_contrast_differences"][0]["standard_deviation_change"] = 10
    with pytest.raises(ValueError):
        check_profile_comparison(packet, old, active, comparison, "controlled-native")
