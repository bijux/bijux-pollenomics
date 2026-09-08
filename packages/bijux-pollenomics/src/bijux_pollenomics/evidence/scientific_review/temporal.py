"""BP interval validation and period classification for scientific review."""

from __future__ import annotations

from ...adna import AdnaLocalitySummary
from ...collection.contracts.models import ContextPointRecord
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
    mean_bp = locality.time_mean_bp
    if mean_bp is None:
        return "project_level_or_unresolved"
    for label, start, end in _PERIOD_BINS:
        if end is None and mean_bp >= start:
            return label
        if end is not None and start <= mean_bp <= end:
            return label
    return "project_level_or_unresolved"


def _locality_overlaps_point(
    locality: AdnaLocalitySummary,
    point: ContextPointRecord,
) -> bool:
    locality_interval = _locality_interval(locality)
    point_interval = _context_point_interval(point)
    if locality_interval is None or point_interval is None:
        return False
    return closed_bp_intervals_overlap(locality_interval, point_interval)


def _locality_interval(locality: AdnaLocalitySummary) -> BpInterval | None:
    return _validated_interval(locality.time_start_bp, locality.time_end_bp)


def _context_point_interval(point: ContextPointRecord) -> BpInterval | None:
    return _validated_interval(point.time_start_bp, point.time_end_bp)


def _validated_interval(
    younger_bp: int | None,
    older_bp: int | None,
) -> BpInterval | None:
    try:
        return canonical_bp_interval(younger_bp, older_bp)
    except InvalidBpIntervalError:
        return None
