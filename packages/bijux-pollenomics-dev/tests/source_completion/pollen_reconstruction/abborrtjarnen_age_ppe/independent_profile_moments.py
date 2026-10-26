"""Verify common-event moments and explicitly changed conditioning populations."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np

from .independent_ledger import Observation, close
from .independent_sources import AXIS, BINS

if TYPE_CHECKING:
    from .independent_profile_comparison import ProfileComparison


def check_profile_comparison(
    packet: dict[str, Any],
    old: dict[str, Any],
    active: Observation,
    comparison: ProfileComparison,
    reference_path: str,
) -> dict[str, Any]:
    """Check common-event reproduction separately from changed-event differences."""
    from .independent_result import COMPONENTS, check_moments

    native = comparison.observed
    common = check_moments(old, native)
    expected = {
        "native_reference_result": reference_path,
        "rows_checked": active.rows,
        "support_transition_counts": {
            f"native_{k[0]}->source_{k[-1]}": v
            for k, v in comparison.transitions.items()
        },
        "window_status_transition_counts": {
            str(b): dict(v) for b, v in comparison.window_transitions.items()
        },
        "native_complete_draws": native.complete,
        "source_complete_draws": active.complete,
        "complete_probability_difference": (active.complete - native.complete)
        / active.rows,
        "comparison_population": "Source-complete C_source versus native-complete C_native; conditional populations differ, not a count or law perturbation within C_native.",
    }
    if any(packet[k] != v for k, v in expected.items()):
        raise ValueError("Saved native/source conditional populations differ")
    diagnostic = packet["common_native_population_check"]
    if (
        diagnostic["draws"] != native.complete
        or diagnostic["contrasts_checked"] != 30
        or diagnostic["passed"] is not True
        or not 0 <= diagnostic["maximum_moment_gap"] <= 1e-12
    ):
        raise ValueError("Saved common-native moment diagnostic differs")
    fields = (
        "conditional_mean_difference",
        "conditional_covariance_component_differences",
        "conditional_contrast_differences",
    )
    if not active.complete or not native.complete:
        if any(packet[k] is not None for k in fields):
            raise ValueError(
                "Undefined conditional population acquired moment differences"
            )
        return {
            "common_native_maximum_moment_gap": common["maximum_moment_gap"],
            "profile_difference_entries_checked": 0,
        }
    source, strict = active.moments.finish(), native.moments.finish()
    gap = close(
        packet[fields[0]],
        source["mean"] - strict["mean"],
        "changed-event mean difference",
    )
    matrices = packet[fields[1]]
    if set(matrices) != set(COMPONENTS):
        raise ValueError("Changed-event covariance component axes differ")
    for field, key in COMPONENTS.items():
        gap = max(
            gap,
            close(matrices[field], source[key] - strict[key], f"changed-event {field}"),
        )
    contrasts = packet[fields[2]]
    if len(contrasts) != 30:
        raise ValueError("Changed-event contrast population differs")
    for index, row in enumerate(contrasts):
        younger, older = [(a, b) for a in BINS for b in BINS if a < b][index // 5]
        taxon = index % 5

        if (row["younger_window_id"], row["older_window_id"], row["taxon"]) != (
            younger,
            older,
            AXIS[taxon],
        ):
            raise ValueError("Changed-event contrast identities differ")
        vector = np.zeros(20)
        (
            vector[5 * BINS.index(older) + taxon],
            vector[5 * BINS.index(younger) + taxon],
        ) = 1, -1
        gap = max(
            gap,
            close(
                row["mean_difference_change"],
                vector @ (source["mean"] - strict["mean"]),
                "changed-event contrast mean",
            ),
        )
        if set(row["variance_component_changes"]) != set(COMPONENTS):
            raise ValueError("Changed-event contrast covariance axes differ")
        for field, key in COMPONENTS.items():
            gap = max(
                gap,
                close(
                    row["variance_component_changes"][field],
                    vector @ (source[key] - strict[key]) @ vector,
                    "changed-event contrast variance",
                ),
            )
        gap = max(
            gap,
            close(
                row["standard_deviation_change"],
                math.sqrt(max(0, float(vector @ source["total"] @ vector)))
                - math.sqrt(max(0, float(vector @ strict["total"] @ vector))),
                "changed-event contrast spread",
            ),
        )
    return {
        "common_native_maximum_moment_gap": common["maximum_moment_gap"],
        "maximum_profile_difference_gap": gap,
        "profile_difference_entries_checked": 20 + 6 * 400,
        "profile_contrasts_checked": 30,
        "maximum_common_ledger_cover_gap": comparison.maximum_common_cover_gap,
    }
