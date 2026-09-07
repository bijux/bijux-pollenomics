"""Temporal-density contract tests for source chronology."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from bijux_pollenomics.reporting.source_chronology.time_density import (
    TIME_DENSITY_BIN_COUNT,
    build_time_density,
    time_density_matches_facet,
)

from .support import source_result


def test_empty_density_has_no_invented_extent_or_bins() -> None:
    density = build_time_density([])

    assert density == {
        "schema_version": "source-chronology-time-density.v1",
        "temporal_direction": "oldest_to_present",
        "interval_semantics": "[younger_bp, older_bp]",
        "bin_admission": "closed_interval_overlap",
        "bins_are_additive": False,
        "node_count": 0,
        "observation_denominator": 0,
        "time_min_bp": None,
        "time_max_bp": None,
        "bins": [],
    }


def test_instant_density_uses_one_closed_bin() -> None:
    source_node = next(
        node
        for node in source_result().nodes
        if node.node_level == "source_sample_presence"
    )
    node = replace(source_node, younger_bp=100, older_bp=100)

    density = build_time_density([node])

    assert density["bins"] == [
        {
            "ordinal": 0,
            "younger_bp": 100,
            "older_bp": 100,
            "node_count": 1,
            "observation_denominator": 1,
        }
    ]


def test_spanning_density_is_oldest_first_and_non_additive() -> None:
    source_node = next(
        node
        for node in source_result().nodes
        if node.node_level == "source_sample_presence"
    )
    spanning = replace(source_node, node_id="spanning", younger_bp=0, older_bp=120)
    boundary = replace(
        source_node,
        node_id="boundary",
        observation_ids=("observation-2", "observation-3"),
        younger_bp=60,
        older_bp=60,
    )

    density = build_time_density([spanning, boundary])
    bins = density["bins"]

    assert isinstance(bins, list)
    assert len(bins) == TIME_DENSITY_BIN_COUNT
    assert bins[0]["older_bp"] == 120
    assert bins[-1]["younger_bp"] == 0
    assert [row["ordinal"] for row in bins] == list(range(TIME_DENSITY_BIN_COUNT))
    assert density["node_count"] == 2
    assert density["observation_denominator"] == 3
    assert sum(row["node_count"] for row in bins) == 14
    assert sum(row["observation_denominator"] for row in bins) == 16


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("node_count", True),
        ("node_count", 1.0),
        ("observation_denominator", "1"),
        ("node_count", 2),
        ("observation_denominator", 2),
    ],
)
def test_density_rejects_malformed_or_impossible_bin_counts(
    field: str, value: object
) -> None:
    node = next(
        node
        for node in source_result().nodes
        if node.node_level == "source_sample_presence"
    )
    density = build_time_density([node])
    facet = {
        "node_count": 1,
        "observation_denominator": 1,
        "time_min_bp": 100,
        "time_max_bp": 125,
    }
    tampered = deepcopy(density)
    bins = tampered["bins"]
    assert isinstance(bins, list) and isinstance(bins[0], dict)
    bins[0][field] = value

    assert time_density_matches_facet(tampered, facet) is False
