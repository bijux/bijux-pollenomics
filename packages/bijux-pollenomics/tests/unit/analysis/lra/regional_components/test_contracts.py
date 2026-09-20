"""The plan cannot be used to smuggle an aggregation request."""

from __future__ import annotations

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.regional_components import RegionalComponentPlan


def test_plan_requires_ordered_bp_support_and_no_aggregation() -> None:
    with pytest.raises(LRARefusal) as error:
        RegionalComponentPlan(
            "set",
            "support",
            "bin",
            (5600, 5400),
            ("one",),
            "grouping.json",
            "a" * 64,
            "b" * 64,
            aggregation_requested=True,
        )
    assert error.value.reason_code in {
        "invalid_regional_component_plan",
        "aggregation_not_supported",
    }
