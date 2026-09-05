from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Literal, TypedDict

from bijux_pollenomics.core.bp_time import (
    build_bp_interval_label,
)
from bijux_pollenomics.core.text import clean_optional_text


class AgeRangeAggregate(TypedDict):
    units: str
    ageold: float | None
    ageyoung: float | None


NeotomaAgeSystem = Literal[
    "calibrated_radiocarbon_bp",
    "calendar_bp",
    "uncalibrated_radiocarbon_bp",
    "varve_bp",
]

_AGE_SYSTEM_BY_NORMALIZED_UNITS: dict[str, NeotomaAgeSystem] = {
    "cal bp": "calendar_bp",
    "calendar years before present": "calendar_bp",
    "calendar years bp": "calendar_bp",
    "calibrated radiocarbon years bp": "calibrated_radiocarbon_bp",
    "calibrated years bp": "calibrated_radiocarbon_bp",
    "radiocarbon years bp": "uncalibrated_radiocarbon_bp",
    "uncalibrated radiocarbon years bp": "uncalibrated_radiocarbon_bp",
    "varve years bp": "varve_bp",
}
_COMPARABLE_AGE_SYSTEMS = frozenset({"calibrated_radiocarbon_bp", "calendar_bp"})
_AGE_SYSTEM_PRIORITY: dict[NeotomaAgeSystem, int] = {
    "calibrated_radiocarbon_bp": 0,
    "calendar_bp": 1,
    "uncalibrated_radiocarbon_bp": 2,
    "varve_bp": 3,
}


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
            _first_populated_value(item, ("ageold", "ageolder", "older"))
        )
        age_young = numeric_age_value(
            _first_populated_value(item, ("ageyoung", "ageyounger", "younger"))
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
    """Return a finite, non-negative age while preserving zero as evidence."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        numeric = float(value)
        return numeric if isfinite(numeric) and numeric >= 0 else None
    text = clean_optional_text(value)
    if not text:
        return None
    try:
        numeric = float(text)
    except ValueError:
        return None
    return numeric if isfinite(numeric) and numeric >= 0 else None


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
    """Choose one age system for a display-only site coverage interval."""
    selected_system = neotoma_selected_age_system(age_ranges)
    if selected_system is None:
        return None
    intervals = [
        interval
        for age_range in age_ranges
        if neotoma_age_range_system(clean_optional_text(age_range.get("units")))
        == selected_system
        if (interval := _age_range_interval(age_range)) is not None
    ]
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
    selected_system = neotoma_selected_age_system(age_ranges)
    selected_ranges = sorted(
        [
            age_range
            for age_range in age_ranges
            if neotoma_age_range_system(clean_optional_text(age_range.get("units")))
            == selected_system
            and _age_range_interval(age_range) is not None
        ],
        key=lambda age_range: clean_optional_text(age_range.get("units")).casefold(),
    )
    if selected_ranges and interval is not None:
        units = clean_optional_text(selected_ranges[0].get("units"))
        value = build_bp_interval_label(interval[0], interval[1]).replace(" BP", "")
        if units and value:
            return f"{value} {units}"
    if interval is None:
        return ""
    return build_bp_interval_label(interval[0], interval[1])


def neotoma_age_range_units_supported(units: str) -> bool:
    """Return whether units can represent canonical calendar-BP site context."""
    return neotoma_age_range_system(units) in _COMPARABLE_AGE_SYSTEMS


def neotoma_age_range_system(units: str) -> NeotomaAgeSystem | None:
    """Classify an exact governed Neotoma age-unit label without inference."""
    normalized = " ".join(units.casefold().split())
    return _AGE_SYSTEM_BY_NORMALIZED_UNITS.get(normalized)


def neotoma_selected_age_system(
    age_ranges: Sequence[Mapping[str, object]],
) -> NeotomaAgeSystem | None:
    """Select one comparable system with a complete valid site interval."""
    candidates = {
        system
        for age_range in age_ranges
        if (
            system := neotoma_age_range_system(
                clean_optional_text(age_range.get("units"))
            )
        )
        in _COMPARABLE_AGE_SYSTEMS
        and _age_range_interval(age_range) is not None
    }
    if not candidates:
        return None
    return min(candidates, key=_AGE_SYSTEM_PRIORITY.__getitem__)


def neotoma_age_range_priority(age_range: Mapping[str, object]) -> tuple[int, str]:
    """Order governed age systems without treating them as interchangeable."""
    units = clean_optional_text(age_range.get("units"))
    normalized = units.casefold()
    system = neotoma_age_range_system(units)
    priority = (
        len(_AGE_SYSTEM_PRIORITY) if system is None else _AGE_SYSTEM_PRIORITY[system]
    )
    return (priority, normalized)


def round_age_value(value: object) -> int | None:
    """Round one Neotoma numeric age value to an integer BP year."""
    numeric = numeric_age_value(value)
    if numeric is None:
        return None
    return int(round(numeric))


def _age_range_interval(
    age_range: Mapping[str, object],
) -> tuple[int, int] | None:
    younger = round_age_value(age_range.get("ageyoung"))
    older = round_age_value(age_range.get("ageold"))
    if younger is None or older is None or younger > older:
        return None
    return (younger, older)


def _first_populated_value(
    item: Mapping[str, object], keys: Sequence[str]
) -> object | None:
    for key in keys:
        if key not in item:
            continue
        value = item[key]
        if value is not None and clean_optional_text(value):
            return value
    return None
