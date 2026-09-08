"""Governed age-system policy for SEAD chronology records."""

from __future__ import annotations

from collections.abc import Mapping

from ......core.bp_time import normalize_bp_interval
from ......core.text import clean_optional_text
from ...acquisition.fetch import parse_optional_int
from .models import SeadAgePolicy

CALIBRATED_BP_AGE_TYPES = frozenset(
    {
        "cal bp",
        "calibrated years bp",
        "calendar years before present",
    }
)
CALENDAR_CE_AGE_TYPES = frozenset({"ad", "ce", "anno domini", "common era"})
CALENDAR_BCE_AGE_TYPES = frozenset({"bc", "bce", "before christ", "before common era"})


def sead_claim_age_policy(
    kind: str,
    source_row: Mapping[str, object],
) -> SeadAgePolicy:
    """Classify a source chronology without silently combining age systems."""
    source_age_type = clean_optional_text(source_row.get("age_type"))
    normalized_age_type = " ".join(source_age_type.casefold().split())
    interval = normalize_bp_interval(
        parse_optional_int(source_row.get("time_start_bp")),
        parse_optional_int(source_row.get("time_end_bp")),
    )
    if kind == "relative_period":
        return non_comparable_age_policy(
            source_age_type="relative_period",
            source_age_unit="source_relative_period",
            calibration_status="not_calibrated",
            comparability_status="context_only",
            reason_code="relative_period_requires_governed_mapping",
        )
    if kind == "geochronology":
        return non_comparable_age_policy(
            source_age_type="radiometric_age_unspecified",
            source_age_unit="source_years",
            calibration_status="unknown",
            comparability_status="context_only",
            reason_code="geochronology_calibration_posture_unknown",
        )
    if kind == "analysis_entity_age":
        return non_comparable_age_policy(
            source_age_type="analysis_entity_age_unspecified",
            source_age_unit="source_years",
            calibration_status="unknown",
            comparability_status="unresolved",
            reason_code="analysis_entity_age_basis_unspecified",
        )

    if normalized_age_type in CALIBRATED_BP_AGE_TYPES:
        transformation_id = "sead-cal-bp-canonical-interval-v1"
        source_age_unit = "years_bp"
        calibration_status = "calibrated"
    elif normalized_age_type in CALENDAR_CE_AGE_TYPES | CALENDAR_BCE_AGE_TYPES:
        transformation_id = "sead-calendar-year-to-cal-bp-1950-v1"
        source_age_unit = "calendar_year"
        calibration_status = "not_applicable"
    else:
        return non_comparable_age_policy(
            source_age_type=source_age_type or "unknown",
            source_age_unit="unknown",
            calibration_status="unknown",
            comparability_status="unresolved",
            reason_code="age_type_not_governed",
        )

    if interval is not None and interval[0] < 0:
        return non_comparable_age_policy(
            source_age_type=source_age_type,
            source_age_unit=source_age_unit,
            calibration_status=calibration_status,
            comparability_status="refused",
            reason_code="negative_bp",
            transformation_id=transformation_id,
        )
    if interval is None:
        return non_comparable_age_policy(
            source_age_type=source_age_type,
            source_age_unit=source_age_unit,
            calibration_status=calibration_status,
            comparability_status="refused",
            reason_code="missing_or_invalid_canonical_interval",
            transformation_id=transformation_id,
        )
    return {
        "source_age_type": source_age_type,
        "source_age_unit": source_age_unit,
        "calibration_status": calibration_status,
        "comparability_status": "comparable",
        "younger_bp": interval[0],
        "older_bp": interval[1],
        "reason_codes": (),
        "transformation_id": transformation_id,
    }


def non_comparable_age_policy(
    *,
    source_age_type: str,
    source_age_unit: str,
    calibration_status: str,
    comparability_status: str,
    reason_code: str,
    transformation_id: str | None = None,
) -> SeadAgePolicy:
    """Return a policy result that carries no canonical numeric interval."""
    return {
        "source_age_type": source_age_type,
        "source_age_unit": source_age_unit,
        "calibration_status": calibration_status,
        "comparability_status": comparability_status,
        "younger_bp": None,
        "older_bp": None,
        "reason_codes": (reason_code,),
        "transformation_id": transformation_id,
    }


def source_interval_orientation(source_row: Mapping[str, object]) -> str:
    """Describe the source interval's original endpoint ordering."""
    start = parse_optional_int(source_row.get("time_start_bp"))
    end = parse_optional_int(source_row.get("time_end_bp"))
    if start is None or end is None:
        return "unavailable"
    if start < end:
        return "younger_to_older"
    if start > end:
        return "older_to_younger"
    return "point"
