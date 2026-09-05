from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypedDict

from bijux_pollenomics.core.bp_time import (
    build_bp_interval_label,
    clamp_bp_year,
    normalize_bp_interval,
)
from bijux_pollenomics.core.text import clean_optional_text


class AgeRangeAggregate(TypedDict):
    units: str
    ageold: float | None
    ageyoung: float | None


def merge_age_ranges(
    age_ranges_by_units: dict[str, AgeRangeAggregate],
    values: object,
) -> None:
    """Aggregate Neotoma age ranges by units."""
    if not isinstance(values, list):
        return
    for item in values:
        if not isinstance(item, dict):
            continue
        units = clean_optional_text(item.get("units") or item.get("agetype"))
        if not units:
            continue
        target = age_ranges_by_units.setdefault(
            units,
            {"units": units, "ageold": None, "ageyoung": None},
        )
        age_old = numeric_age_value(
            item.get("ageold") or item.get("ageolder") or item.get("older")
        )
        age_young = numeric_age_value(
            item.get("ageyoung") or item.get("ageyounger") or item.get("younger")
        )
        if age_old is not None and (
            target["ageold"] is None or age_old > target["ageold"]
        ):
            target["ageold"] = age_old
        if age_young is not None and (
            target["ageyoung"] is None or age_young < target["ageyoung"]
        ):
            target["ageyoung"] = age_young


def numeric_age_value(value: object) -> float | None:
    """Return a numeric age value when a payload field is populated."""
    if isinstance(value, (int, float)):
        return float(value)
    text = clean_optional_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def format_neotoma_age_range(age_range: Mapping[str, object]) -> str:
    """Render one aggregated Neotoma age range for popup display."""
    younger = numeric_age_value(age_range.get("ageyoung"))
    older = numeric_age_value(age_range.get("ageold"))
    if younger is None and older is None:
        return ""
    if younger is None:
        return format_neotoma_age_value(older)
    if older is None:
        return format_neotoma_age_value(younger)
    return f"{format_neotoma_age_value(younger)} to {format_neotoma_age_value(older)}"


def format_neotoma_age_value(value: float | None) -> str:
    """Render a Neotoma numeric age without unnecessary decimal places."""
    if value is None:
        return ""
    rounded = round(value)
    if abs(value - rounded) < 1e-9:
        return str(int(rounded))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def neotoma_time_interval(
    age_ranges: Sequence[Mapping[str, object]],
) -> tuple[int, int] | None:
    """Choose a filterable BP interval from Neotoma site age coverage."""
    preferred_ranges = sorted(
        [
            age_range
            for age_range in age_ranges
            if neotoma_age_range_units_supported(
                clean_optional_text(age_range.get("units"))
            )
        ],
        key=neotoma_age_range_priority,
    )
    intervals: list[tuple[int, int]] = []
    for age_range in preferred_ranges:
        older = clamp_bp_year(round_age_value(age_range.get("ageold")))
        younger = clamp_bp_year(round_age_value(age_range.get("ageyoung")))
        interval = normalize_bp_interval(younger, older)
        if interval is not None:
            intervals.append(interval)
    if not intervals:
        return None
    return (
        min(start for start, _ in intervals),
        max(end for _, end in intervals),
    )


def neotoma_time_label(
    age_ranges: Sequence[Mapping[str, object]],
    interval: tuple[int, int] | None,
) -> str:
    """Render a human-readable Neotoma age-coverage label."""
    preferred_ranges = sorted(
        [
            age_range
            for age_range in age_ranges
            if neotoma_age_range_units_supported(
                clean_optional_text(age_range.get("units"))
            )
        ],
        key=neotoma_age_range_priority,
    )
    if preferred_ranges:
        units = clean_optional_text(preferred_ranges[0].get("units"))
        older = clamp_bp_year(round_age_value(preferred_ranges[0].get("ageold")))
        younger = clamp_bp_year(round_age_value(preferred_ranges[0].get("ageyoung")))
        preferred_interval = normalize_bp_interval(younger, older)
        value = (
            build_bp_interval_label(
                preferred_interval[0], preferred_interval[1]
            ).replace(" BP", "")
            if preferred_interval is not None
            else format_neotoma_age_range(preferred_ranges[0])
        )
        if units and value:
            return f"{value} {units}"
    if interval is None:
        return ""
    return build_bp_interval_label(interval[0], interval[1])


def neotoma_age_range_units_supported(units: str) -> bool:
    """Return whether a Neotoma age range is expressed in BP units."""
    return "bp" in units.casefold()


def neotoma_age_range_priority(age_range: Mapping[str, object]) -> tuple[int, str]:
    """Prefer calibrated BP ranges over uncalibrated BP ranges."""
    units = clean_optional_text(age_range.get("units"))
    normalized = units.casefold()
    if "cal" in normalized and "bp" in normalized:
        return (0, normalized)
    if "bp" in normalized:
        return (1, normalized)
    return (2, normalized)


def round_age_value(value: object) -> int | None:
    """Round one Neotoma numeric age value to an integer BP year."""
    numeric = numeric_age_value(value)
    if numeric is None:
        return None
    return int(round(numeric))
