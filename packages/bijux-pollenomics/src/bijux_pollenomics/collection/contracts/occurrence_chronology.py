"""Admit dated occurrence context separately from site and navigation coverage."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass

from ...core.temporal_semantics import (
    BpInterval,
    InvalidBpIntervalError,
    canonical_bp_interval,
    temporal_semantics_has_numeric_interval,
)

# These declarations belong to maintained LandClim, SEAD site and lake-context
# producers. Their numeric extents describe coverage, rather than dated records.
_COVERAGE_CLASSES = frozenset(
    {
        "pollen_site_sequence_coverage",
        "nearby_lake_context_summary",
        "neotoma_site_age_range_context",
        "sead_dating_range_and_relative_period",
    }
)
_COVERAGE_PRECISIONS = frozenset(
    {
        "site_sequence_interval",
        "site_interval",
        "site_interval_with_uncertainty",
        "site_interval_with_context",
        "source_interval_window_summary",
        "site_extrema_without_continuity",
    }
)


def _declared_numeric_posture(temporal_semantics: Mapping[str, object] | None) -> bool:
    if not isinstance(temporal_semantics, Mapping):
        return False
    if any(
        key in temporal_semantics and not isinstance(temporal_semantics[key], str)
        for key in (
            "schema_version",
            "comparability_posture",
            "refusal_reason_code",
            "evidence_class",
            "precision_posture",
            "chronology_role",
        )
    ):
        return False
    return (
        temporal_semantics.get("comparability_posture")
        in {
            "numeric_interval",
            "numeric_interval_with_caveat",
            "mixed_interval_and_context",
        }
        and temporal_semantics.get("refusal_reason_code", "") == ""
        and (
            "schema_version" not in temporal_semantics
            or temporal_semantics["schema_version"] == "temporal-semantics.v1"
        )
    )


def occurrence_support_interval(
    *,
    temporal_semantics: Mapping[str, object] | None,
    time_start_bp: int | None,
    time_end_bp: int | None,
    source_layer_key: str = "",
) -> BpInterval | None:
    """Return explicit record/model support eligible for fieldwork time scoring.

    Numeric coverage remains useful spatial and display context. It cannot
    establish an occurrence inside that coverage. ADNA callers supply separately
    admitted sample components; their locality hull is never a record support.
    This admission does not infer source epochs, calibration or authentication.
    """
    if source_layer_key == "sead-sites":
        return None
    if not _declared_numeric_posture(temporal_semantics) or temporal_semantics is None:
        return None
    if not temporal_semantics_has_numeric_interval(dict(temporal_semantics)):
        return None
    if (
        temporal_semantics.get("evidence_class") in _COVERAGE_CLASSES
        or temporal_semantics.get("precision_posture") in _COVERAGE_PRECISIONS
        or temporal_semantics.get("chronology_role") == "locality_sample_coverage_hull"
    ):
        return None
    if time_start_bp != temporal_semantics.get(
        "time_start_bp"
    ) or time_end_bp != temporal_semantics.get("time_end_bp"):
        return None
    try:
        return canonical_bp_interval(time_start_bp, time_end_bp)
    except InvalidBpIntervalError:
        return None


@dataclass(frozen=True)
class ContextOccurrenceSupport:
    """One source-owned component retained independently of a spatial point hull."""

    support_id: str
    time_start_bp: int | None
    time_end_bp: int | None
    temporal_semantics: dict[str, object]

    def __post_init__(self) -> None:
        if not isinstance(self.support_id, str) or not self.support_id.strip():
            raise ValueError(
                "Context occurrence support requires its source identifier"
            )
        if not isinstance(self.temporal_semantics, dict):
            raise ValueError("Context occurrence support requires declared semantics")
        object.__setattr__(
            self, "temporal_semantics", deepcopy(self.temporal_semantics)
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "support_id": self.support_id,
            "time_start_bp": self.time_start_bp,
            "time_end_bp": self.time_end_bp,
            "temporal_semantics": deepcopy(self.temporal_semantics),
        }


def occurrence_support_intervals(
    *,
    temporal_semantics: Mapping[str, object] | None,
    time_start_bp: int | None,
    time_end_bp: int | None,
    occurrence_supports: tuple[ContextOccurrenceSupport, ...] | None = None,
    source_layer_key: str = "",
) -> tuple[BpInterval, ...]:
    """Return admitted member intervals without filling gaps or counting duplicates.

    Whole-record explicit contextual/refused metadata constrains all components.
    An absent aggregate declaration permits separately validated owned members.
    """
    if occurrence_supports is None:
        interval = occurrence_support_interval(
            temporal_semantics=temporal_semantics,
            time_start_bp=time_start_bp,
            time_end_bp=time_end_bp,
            source_layer_key=source_layer_key,
        )
        return (interval,) if interval is not None else ()
    if temporal_semantics is not None and not _declared_numeric_posture(
        temporal_semantics
    ):
        return ()
    intervals = {}
    for support in occurrence_supports:
        interval = occurrence_support_interval(
            temporal_semantics=support.temporal_semantics,
            time_start_bp=support.time_start_bp,
            time_end_bp=support.time_end_bp,
        )
        if interval is not None:
            intervals[(interval.younger_bp, interval.older_bp)] = interval
    return tuple(intervals[key] for key in sorted(intervals))
