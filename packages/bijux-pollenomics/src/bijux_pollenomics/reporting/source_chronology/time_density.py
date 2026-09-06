"""Non-interpolated temporal density for source-chronology facets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SourceChronologyNode,
)

TIME_DENSITY_BIN_COUNT = 12
TIME_DENSITY_SCHEMA_VERSION = "source-chronology-time-density.v1"


def build_time_density(
    nodes: Sequence[SourceChronologyNode],
) -> dict[str, object]:
    """Count closed-interval source records in oldest-to-present bins.

    A node contributes its complete observation denominator to every bin its
    canonical interval intersects. The bins therefore describe temporal
    coverage and are deliberately non-additive; values are never interpolated,
    prorated, or assigned through interval midpoints.
    """
    node_count = len(nodes)
    observation_denominator = sum(len(node.observation_ids) for node in nodes)
    if not nodes:
        return _payload(
            node_count=0,
            observation_denominator=0,
            time_min_bp=None,
            time_max_bp=None,
            bins=[],
        )

    time_min_bp = min(node.younger_bp for node in nodes)
    time_max_bp = max(node.older_bp for node in nodes)
    if time_min_bp == time_max_bp:
        bins = [
            _bin(
                ordinal=0,
                younger_bp=time_min_bp,
                older_bp=time_max_bp,
                nodes=nodes,
            )
        ]
    else:
        span = time_max_bp - time_min_bp
        boundaries = [
            time_min_bp + (span * index / TIME_DENSITY_BIN_COUNT)
            for index in range(TIME_DENSITY_BIN_COUNT + 1)
        ]
        boundaries[0] = time_min_bp
        boundaries[-1] = time_max_bp
        bins = [
            _bin(
                ordinal=ordinal,
                younger_bp=boundaries[TIME_DENSITY_BIN_COUNT - ordinal - 1],
                older_bp=boundaries[TIME_DENSITY_BIN_COUNT - ordinal],
                nodes=nodes,
            )
            for ordinal in range(TIME_DENSITY_BIN_COUNT)
        ]
    return _payload(
        node_count=node_count,
        observation_denominator=observation_denominator,
        time_min_bp=time_min_bp,
        time_max_bp=time_max_bp,
        bins=bins,
    )


def time_density_matches_facet(
    density: object,
    facet: Mapping[str, object],
) -> bool:
    """Return whether serialized density metadata closes against its facet."""
    if not isinstance(density, Mapping):
        return False
    if (
        density.get("schema_version") != TIME_DENSITY_SCHEMA_VERSION
        or density.get("temporal_direction") != "oldest_to_present"
        or density.get("interval_semantics") != "[younger_bp, older_bp]"
        or density.get("bin_admission") != "closed_interval_overlap"
        or density.get("bins_are_additive") is not False
    ):
        return False
    for field in (
        "node_count",
        "observation_denominator",
        "time_min_bp",
        "time_max_bp",
    ):
        if density.get(field) != facet.get(field):
            return False
    node_count = _nonnegative_integer(facet.get("node_count"))
    observation_denominator = _nonnegative_integer(facet.get("observation_denominator"))
    time_min_bp = _nonnegative_number(facet.get("time_min_bp"))
    time_max_bp = _nonnegative_number(facet.get("time_max_bp"))
    if node_count is None or observation_denominator is None:
        return False
    if node_count == 0:
        if facet.get("time_min_bp") is not None or facet.get("time_max_bp") is not None:
            return False
        expected_bin_count = 0
    else:
        if time_min_bp is None or time_max_bp is None or time_min_bp > time_max_bp:
            return False
        expected_bin_count = 1 if time_min_bp == time_max_bp else 12
    bins = density.get("bins")
    if not isinstance(bins, list) or len(bins) != expected_bin_count:
        return False
    previous_younger: float | int | None = None
    for ordinal, row in enumerate(bins):
        if not isinstance(row, Mapping) or row.get("ordinal") != ordinal:
            return False
        younger_bp = _nonnegative_number(row.get("younger_bp"))
        older_bp = _nonnegative_number(row.get("older_bp"))
        if (
            younger_bp is None
            or older_bp is None
            or younger_bp > older_bp
            or _nonnegative_integer(row.get("node_count")) is None
            or _nonnegative_integer(row.get("observation_denominator")) is None
        ):
            return False
        if ordinal == 0 and older_bp != time_max_bp:
            return False
        if previous_younger is not None and older_bp != previous_younger:
            return False
        previous_younger = younger_bp
    return not bins or previous_younger == time_min_bp


def _nonnegative_integer(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _nonnegative_number(value: object) -> float | int | None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
        or value < 0
    ):
        return None
    return value


def _bin(
    *,
    ordinal: int,
    younger_bp: float,
    older_bp: float,
    nodes: Sequence[SourceChronologyNode],
) -> dict[str, object]:
    overlapping = [
        node
        for node in nodes
        if node.younger_bp <= older_bp and node.older_bp >= younger_bp
    ]
    return {
        "ordinal": ordinal,
        "younger_bp": younger_bp,
        "older_bp": older_bp,
        "node_count": len(overlapping),
        "observation_denominator": sum(
            len(node.observation_ids) for node in overlapping
        ),
    }


def _payload(
    *,
    node_count: int,
    observation_denominator: int,
    time_min_bp: float | None,
    time_max_bp: float | None,
    bins: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": TIME_DENSITY_SCHEMA_VERSION,
        "temporal_direction": "oldest_to_present",
        "interval_semantics": "[younger_bp, older_bp]",
        "bin_admission": "closed_interval_overlap",
        "bins_are_additive": False,
        "node_count": node_count,
        "observation_denominator": observation_denominator,
        "time_min_bp": time_min_bp,
        "time_max_bp": time_max_bp,
        "bins": bins,
    }


__all__ = [
    "TIME_DENSITY_BIN_COUNT",
    "TIME_DENSITY_SCHEMA_VERSION",
    "build_time_density",
    "time_density_matches_facet",
]
