"""Linear groups and contrasts of the retained strict-native ABBO moments."""

from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np

TAXA = {
    "Betula": 29,
    "Cyperaceae": 74,
    "Juniperus communis": 4416,
    "Pinus sylvestris": 1287,
    "Poaceae": 417,
}
WINDOWS = {3: (1500, 2000), 4: (2000, 2500), 5: (2500, 3000), 9: (4500, 5000)}
GROUPS = (
    ("Betula + Pinus sylvestris", ("Betula", "Pinus sylvestris")),
    ("Juniperus communis", ("Juniperus communis",)),
    ("Cyperaceae + Poaceae", ("Cyperaceae", "Poaceae")),
)
COMPONENTS = (
    "age",
    "count",
    "shared_ppe",
    "total",
    "mean_gradient_ppe",
    "age_ppe_interaction",
)
EVENT = "all_four_windows_defined_with_complete_five_taxon_members"


def _real(value: Any) -> np.ndarray:
    if np.ma.isMaskedArray(value):
        raise ValueError("Masked measurements cannot lose their observation mask")
    array = np.asarray(value)
    if array.dtype.kind not in "iuf" or not np.isfinite(array).all():
        raise ValueError("Moment projection requires finite real numeric values")
    return np.asarray(array, dtype=float)


def _covariance(value: Any, size: int) -> np.ndarray:
    matrix = _real(value)
    if matrix.shape != (size, size):
        raise ValueError("Covariance and mean axes differ")
    scale = float(np.max(np.abs(matrix)))
    normalized = matrix / scale if scale else matrix
    if (
        np.any(np.diag(matrix) < 0)
        or not np.allclose(normalized, normalized.T, rtol=0, atol=1e-10)
        or np.linalg.eigvalsh((normalized + normalized.T) / 2).min() < -1e-10
    ):
        raise ValueError("Source covariance is not symmetric positive semidefinite")
    return matrix


def project_linear_moments(
    mean: Any, covariance: Any, transform: Any
) -> tuple[np.ndarray, np.ndarray]:
    """Project matching means/covariance; no nonlinear cover policy is applied."""
    vector, operator = _real(mean), _real(transform)
    if (
        vector.ndim != 1
        or not len(vector)
        or operator.ndim != 2
        or operator.shape[1] != len(vector)
        or not operator.shape[0]
    ):
        raise ValueError("Linear transform and mean axes differ")
    matrix = _covariance(covariance, len(vector))
    return operator @ vector, operator @ matrix @ operator.T


def project_retained_result(payload: dict[str, Any]) -> dict[str, Any]:
    """Preserve the saved five-taxon conditional law through groups and contrasts."""
    if (
        payload.get("schema_version") != "abborrtjarnen-age-ppe-account.v1"
        or payload.get("status") != "conditional_age_count_ppe_delta_mixture"
        or payload.get("conditioning_event") != EVENT
    ):
        raise ValueError("Only the declared strict-native ABBO profile is supported")
    requested, complete, undefined = (
        payload[name]
        for name in ("requested_draws", "complete_draws", "undefined_draws")
    )
    if (
        any(type(n) is not int for n in (requested, complete, undefined))
        or not 0 < complete <= requested
        or undefined < 0
        or requested != complete + undefined
        or payload["complete_probability"] != complete / requested
    ):
        raise ValueError("Conditional population accounting differs")
    unconditional = payload["unconditional"]
    if (
        unconditional.get("status")
        != ("refused_undefined_mass" if undefined else "defined_for_all_saved_rows")
        or unconditional.get("undefined_fraction") != undefined / requested
        or unconditional["mean"] is not None
        or unconditional["covariance"] is not None
        or unconditional.get("defined_moments_reference")
        != (None if undefined else "conditional_on_complete")
    ):
        raise ValueError(
            "Undefined unconditional moments cannot become a numeric result"
        )
    support = payload["source_support"]
    original, measured, incomplete = (
        support["original_samples"],
        support["explicit_five_panel_complete"],
        support["incomplete_five_panel_samples"],
    )
    if (
        type(original) is not int
        or type(measured) is not int
        or not 0 < measured <= original
        or not isinstance(incomplete, list)
        or measured + len(incomplete) != original
        or len({row["sample_id"] for row in incomplete}) != len(incomplete)
        or any(
            type(row["sample_id"]) is not int
            or row["sample_id"] <= 0
            or not row["missing_taxa"]
            or not set(row["missing_taxa"]) <= set(TAXA)
            for row in incomplete
        )
    ):
        raise ValueError("Source measured-panel mask and sample population differ")
    axis = payload["component_axis"]
    if any(
        type(row["window_id"]) is not int
        or type(row["native_taxon_id"]) is not int
        or not isinstance(row["taxon"], str)
        for row in axis
    ):
        raise ValueError("Native window and taxon IDs must retain integer identity")
    expected = {
        (window, taxon, native) for window in WINDOWS for taxon, native in TAXA.items()
    }
    actual = [(row["window_id"], row["taxon"], row["native_taxon_id"]) for row in axis]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("Native window/taxon identity differs from the selected panel")
    moments = payload["conditional_on_complete"]
    if (
        moments.get("status") != "conditional_on_complete"
        or type(moments.get("draws")) is not int
        or moments["draws"] != complete
    ):
        raise ValueError("Nested conditional moments describe a different population")
    vector = _real(moments["mean"])
    if vector.shape != (20,) or np.any(vector < 0) or np.any(vector > 1):
        raise ValueError("Source means must be twenty closed-panel fractions")
    operator = np.array(
        [
            [
                int(row["window_id"] == window and row["taxon"] in members)
                for row in axis
            ]
            for window in WINDOWS
            for _, members in GROUPS
        ]
    )
    means = operator @ vector
    if not np.allclose(means.reshape(4, 3).sum(axis=1), 1, rtol=0, atol=1e-10):
        raise ValueError("Source means do not close on the declared five-taxon panel")
    raw = moments["covariance_components"]
    matrices = {name: _covariance(raw[name], 20) for name in COMPONENTS}
    closure = np.array(
        [[int(row["window_id"] == window) for row in axis] for window in WINDOWS]
    )
    for matrix in matrices.values():
        scale = float(np.max(np.abs(matrix)))
        if scale and np.max(np.abs(matrix @ closure.T)) / scale > 1e-10:
            raise ValueError(
                "Source covariance violates per-window closed-panel totals"
            )
    for total, summands in (
        ("total", ("age", "count", "shared_ppe")),
        ("shared_ppe", ("mean_gradient_ppe", "age_ppe_interaction")),
    ):
        if not np.allclose(
            matrices[total], sum(matrices[n] for n in summands), rtol=1e-10, atol=1e-16
        ):
            raise ValueError("Source covariance component accounting differs")
    projected = {
        name: (10000 * operator @ matrix @ operator.T)
        for name, matrix in matrices.items()
    }
    components = []
    for i, (window, group) in enumerate((w, g) for w in WINDOWS for g in range(3)):
        components.append(
            {
                "window_id": window,
                "younger_bp": WINDOWS[window][0],
                "older_bp": WINDOWS[window][1],
                "group": GROUPS[group][0],
                "mean_percent": float(100 * means[i]),
                "standard_deviation_percentage_points": float(
                    np.sqrt(max(0, projected["total"][i, i]))
                ),
                "variance_components_percentage_points_squared": {
                    n: float(c[i, i]) for n, c in projected.items()
                },
            }
        )
    contrasts = []
    for younger, older in combinations(range(4), 2):
        for group in range(3):
            a, b = younger * 3 + group, older * 3 + group
            variance = {
                n: float(c[a, a] + c[b, b] - c[a, b] - c[b, a])
                for n, c in projected.items()
            }
            contrasts.append(
                {
                    "younger_window_id": list(WINDOWS)[younger],
                    "older_window_id": list(WINDOWS)[older],
                    "group": GROUPS[group][0],
                    "mean_difference_percentage_points": float(
                        100 * (means[b] - means[a])
                    ),
                    "standard_deviation_percentage_points": float(
                        np.sqrt(max(0, variance["total"]))
                    ),
                    "variance_components_percentage_points_squared": variance,
                }
            )
    return {
        "schema_version": "abborrtjarnen-grouped-conditional-moments.v1",
        "status": "conditional_linear_projection_of_retained_result",
        "conditioning_event": EVENT,
        "requested_draws": requested,
        "complete_draws": complete,
        "undefined_draws": undefined,
        "complete_probability": complete / requested,
        "unconditional": unconditional,
        "source_support": support,
        "source_limits": payload.get("limits", []),
        "denominator": "closed literal five-taxon panel; not whole vegetation or terrestrial pollen",
        "cover_policy": "positive REVEALS inverse closure; no LOVE cover transformation",
        "uncertainty": "retained age mixture plus conditional first-order count/shared-PPE covariance; SD is not a confidence interval",
        "groups": [
            {"label": label, "members": list(members)} for label, members in GROUPS
        ],
        "components": components,
        "contrasts": contrasts,
        "covariance_components_percent_squared": {
            n: c.tolist() for n, c in projected.items()
        },
        "scientific_admission": "unchanged_from_source",
        "measured_accuracy_claimed": False,
        "new_model_fits": 0,
        "new_age_or_ppe_draws": 0,
    }
