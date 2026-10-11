"""Guard explicit training-count zero replacement for CLR prediction."""

from __future__ import annotations

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.spatial import half_count_composition


def test_half_count_composition_preserves_input_and_closes_named_axis() -> None:
    counts = {"oak": 3, "pine": 0}
    assert half_count_composition(counts) == {"oak": 0.875, "pine": 0.125}
    assert counts == {"oak": 3, "pine": 0}


@pytest.mark.parametrize(
    "counts",
    [
        {"oak": 0, "pine": 0},
        {"oak": 1},
        {"oak": 1, "pine": -1},
        {"oak": 1, "pine": True},
    ],
)
def test_half_count_composition_refuses_unsupported_counts(
    counts: dict[str, int],
) -> None:
    with pytest.raises(ValidationRefusal):
        half_count_composition(counts)
