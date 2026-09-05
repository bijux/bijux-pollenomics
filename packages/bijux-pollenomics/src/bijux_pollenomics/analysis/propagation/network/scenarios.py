"""Governed propagation sensitivity scenarios."""

from __future__ import annotations
from bijux_pollenomics.analysis.propagation.candidates import (
    CandidatePropagationScenario,
)


def _sensitivity_scenarios() -> tuple[CandidatePropagationScenario, ...]:
    rows = []
    for maximum_distance_km in (25.0, 50.0, 100.0, 200.0):
        for maximum_lag_years in (50.0, 100.0, 200.0, 500.0):
            rows.append(
                CandidatePropagationScenario(
                    scenario_id=(
                        f"rectangular_{maximum_distance_km:g}km_"
                        f"{maximum_lag_years:g}yr_v1"
                    ),
                    maximum_distance_km=maximum_distance_km,
                    maximum_lag_years=maximum_lag_years,
                )
            )
    return tuple(rows)


PROPAGATION_SENSITIVITY_SCENARIOS = _sensitivity_scenarios()
