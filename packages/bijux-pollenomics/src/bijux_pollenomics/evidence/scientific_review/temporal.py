"""BP interval validation and period classification for scientific review."""

from __future__ import annotations

from ...adna import AdnaLocalitySummary
from ...adna.domain.locality import locality_sample_intervals
from ...collection.contracts.models import ContextPointRecord
from ...collection.contracts.occurrence_chronology import occurrence_support_intervals
from ...core.temporal_semantics import (
    BpInterval,
    InvalidBpIntervalError,
    canonical_bp_interval,
    closed_bp_intervals_overlap,
)

_PERIOD_BINS = (
    ("0-1000 BP", 0, 1000),
    ("1001-3000 BP", 1001, 3000),
    ("3001-6000 BP", 3001, 6000),
    ("6001+ BP", 6001, None),
)


def _period_label_for(locality: AdnaLocalitySummary) -> str:
    intervals = _locality_intervals(locality)
    if not intervals:
        return "project_level_or_unresolved"
    for label, start, end in _PERIOD_BINS:
        if all(
            interval.younger_bp >= start and (end is None or interval.older_bp <= end)
            for interval in intervals
        ):
            return label
    return "project_level_or_unresolved"


def _locality_overlaps_point(
    locality: AdnaLocalitySummary,
    point: ContextPointRecord,
) -> bool:
    locality_intervals = _locality_intervals(locality)
    point_intervals = _context_point_intervals(point)
    return any(
        closed_bp_intervals_overlap(interval, point_interval)
        for interval in locality_intervals
        for point_interval in point_intervals
    )


def _locality_interval(locality: AdnaLocalitySummary) -> BpInterval | None:
    intervals = _locality_intervals(locality)
    distinct = {(interval.younger_bp, interval.older_bp) for interval in intervals}
    return intervals[0] if len(distinct) == 1 else None


def _locality_intervals(locality: AdnaLocalitySummary) -> tuple[BpInterval, ...]:
    return tuple(
        interval for _sample_id, interval in locality_sample_intervals(locality)
    )


def _context_point_intervals(point: ContextPointRecord) -> tuple[BpInterval, ...]:
    return occurrence_support_intervals(
        source_layer_key=point.layer_key,
        temporal_semantics=point.temporal_semantics,
        time_start_bp=point.time_start_bp,
        time_end_bp=point.time_end_bp,
        occurrence_supports=point.occurrence_supports,
    )


def _context_point_interval(point: ContextPointRecord) -> BpInterval | None:
    """Return one actual interval only when admitted supports have one extent."""
    intervals = _context_point_intervals(point)
    return intervals[0] if len(intervals) == 1 else None


def _validated_interval(
    younger_bp: int | None,
    older_bp: int | None,
) -> BpInterval | None:
    try:
        return canonical_bp_interval(younger_bp, older_bp)
    except InvalidBpIntervalError:
        return None
