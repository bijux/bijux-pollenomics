"""Explicit zero replacement for exploratory CLR fits on measured counts."""

from __future__ import annotations

from collections.abc import Mapping
from math import fsum

from ..contracts import ValidationRefusal


HALF_COUNT = 0.5
HALF_COUNT_POLICY = "add_one_half_to_each_named_training_taxon"


def half_count_composition(counts: Mapping[str, int]) -> dict[str, float]:
    """Close a declared count axis after adding half a grain to each taxon."""
    if len(counts) < 2 or any(
        not isinstance(taxon, str)
        or not taxon
        or type(value) is not int
        or value < 0
        or value > 2**53
        for taxon, value in counts.items()
    ):
        raise ValidationRefusal(
            "invalid_spatial_count_composition",
            "Require two or more named taxa with exact nonnegative integer counts",
        )
    if sum(counts.values()) == 0:
        raise ValidationRefusal(
            "empty_spatial_count_composition", "Observed training count sum is zero"
        )
    total = fsum(float(value) + HALF_COUNT for value in counts.values())
    return {taxon: (value + HALF_COUNT) / total for taxon, value in counts.items()}
