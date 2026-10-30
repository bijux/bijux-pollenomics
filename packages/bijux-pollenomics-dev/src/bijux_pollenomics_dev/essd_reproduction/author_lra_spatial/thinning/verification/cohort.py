"""Independent geographic ordering conditional on a nominal WGS84 matrix."""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

from bijux_pollenomics_dev.lra_validation.spatial_reference.geodesic import (
    distance_bounds,
)

from .predictions import number, require, same


def audit_cohort(packet: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct exact selection conditional on the saved nominal distance matrix."""
    cohort, geometries = packet["cohort"], packet["geometries"]
    owners = sorted(packet["groups"])
    require(
        len(owners) == 15 and set(geometries) == set(owners),
        "full identity universe precedes selection",
    )
    require(
        cohort["distance_model"] == "nominal_wgs84_inverse"
        and cohort["tie_policy"] == "exact_metric_then_lexicographic_record_id",
        "declared distance/tie policy",
    )
    same(
        cohort["coordinates"],
        {o: {k: geometries[o][k] for k in ("latitude", "longitude")} for o in owners},
    )
    matrix = cohort["distance_matrix_m"]
    require(
        set(matrix) == set(owners)
        and all(set(row) == set(owners) for row in matrix.values()),
        "complete fifteen-square distance matrix",
    )
    for a in owners:
        for b in owners:
            distance = number(matrix[a][b])
            require(
                distance >= 0
                and distance == matrix[b][a]
                and (a != b or distance == 0),
                "symmetric finite distance matrix",
            )
            lo, hi = distance_bounds(cohort["coordinates"][a], cohort["coordinates"][b])
            require(
                lo <= Fraction.from_float(distance) <= hi,
                "nominal distance outside independent WGS84 envelope",
            )
    with localcontext() as context:
        context.prec = 80
        # Round the independently accumulated exact dyadic sum once, matching
        # the prospectively declared native fsum criterion and exact float ties.
        scores = {
            o: float(
                sum(
                    (Decimal.from_float(number(matrix[o][p])) for p in owners),
                    Decimal(0),
                )
            )
            for o in owners
        }
    order = [min(owners, key=lambda o: (scores[o], o))]
    expected_steps = [
        {
            "step": 1,
            "record_id": order[0],
            "criterion": "minimum_total_distance",
            "value_m": scores[order[0]],
            "candidate_values_m": scores,
        }
    ]
    while len(order) < 10:
        near = {o: min(matrix[o][p] for p in order) for o in owners if o not in order}
        chosen = min(near, key=lambda o: (-near[o], o))
        order.append(chosen)
        expected_steps.append(
            {
                "step": len(order),
                "record_id": chosen,
                "criterion": "maximum_nearest_selected_distance",
                "value_m": near[chosen],
                "candidate_values_m": near,
            }
        )
    same(cohort["selection_order"], order)
    same(order, protocol["cohort"]["expected_selection_order"])
    same(cohort["steps"], expected_steps)
    same(cohort["selected"], sorted(order))
    same(cohort["excluded"], sorted(set(owners) - set(order)))
    nearest = {o: min(matrix[o][p] for p in order) for o in owners}
    same(cohort["nearest_selected_distance_m"], nearest)
    same(cohort["coverage_m"], max(nearest.values()))
    same(
        cohort["min_separation_m"],
        min(matrix[a][b] for i, a in enumerate(order) for b in order[i + 1 :]),
    )
    return {
        "selected_owners": 10,
        "universe_owners": 15,
        "selection_order": order,
        "distance_scope": "Ordering conditional on nominal binary64 WGS84 matrix; independent rational envelope is not an inverse-geodesic recomputation",
    }
