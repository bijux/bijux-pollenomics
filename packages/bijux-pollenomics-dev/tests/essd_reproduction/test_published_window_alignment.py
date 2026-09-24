"""Check author and archive BP intervals before comparing published estimates."""

from __future__ import annotations

from decimal import Decimal

import pytest

from bijux_pollenomics_dev.essd_reproduction.published_window_alignment import (
    window_rows,
)


def test_only_exact_bp_bounds_are_admitted_for_same_window_comparison() -> None:
    edges = [Decimal(value) for value in (-65, 100, 350, *range(750, 11751, 500))]
    lookup = [(str(index), str(index * 500)) for index in range(1, 26)]
    rows = window_rows(edges, lookup)
    assert len(rows) == 25
    assert [row["tw_index"] for row in rows if row["exact_bounds"] == "True"] == ["2"]
    assert (
        rows[0]["published_minus_author_start_bp"],
        rows[0]["published_minus_author_end_bp"],
    ) == ("65", "0")
    assert (
        rows[2]["published_minus_author_start_bp"],
        rows[2]["published_minus_author_end_bp"],
    ) == ("0", "-50")
    assert (
        rows[3]["published_minus_author_start_bp"],
        rows[3]["published_minus_author_end_bp"],
    ) == ("-50", "-50")


def test_repeated_or_unsorted_author_axis_refuses() -> None:
    edges = [Decimal(value) for value in (-65, 100, 350, *range(750, 11751, 500))]
    lookup = [(str(index), str(index * 500)) for index in range(1, 26)]
    with pytest.raises(ValueError, match="Author BP bin or lookup axis"):
        window_rows([*edges[:4], edges[3], *edges[5:]], lookup)
    with pytest.raises(ValueError, match="Author BP bin or lookup axis"):
        window_rows(edges, [*lookup[:4], lookup[3], *lookup[5:]])
