"""SEAD chronology normalization and interval semantics."""

from __future__ import annotations

import re

from bijux_pollenomics.core.bp_time import normalize_bp_interval

from .values import parse_optional_int

BP_REFERENCE_YEAR = 1950
_CALIBRATED_BP_AGE_TYPES = frozenset(
    {"cal bp", "calibrated years bp", "calendar years before present"}
)
_COMMON_ERA_AGE_TYPES = frozenset({"ad", "ce", "anno domini", "common era"})
_BEFORE_COMMON_ERA_AGE_TYPES = frozenset(
    {"bc", "bce", "before christ", "before common era"}
)


_PERIOD_LABEL_PATTERNS = (
    (re.compile(r"\bquaternary\b", re.IGNORECASE), "quaternary"),
    (re.compile(r"\bholocene\b", re.IGNORECASE), "holocene"),
    (re.compile(r"\bmesolithic\b", re.IGNORECASE), "mesolithic"),
    (re.compile(r"\bneolithic\b", re.IGNORECASE), "neolithic"),
    (re.compile(r"\bbronze\b", re.IGNORECASE), "bronze_age"),
    (re.compile(r"\biron\b", re.IGNORECASE), "iron_age"),
    (re.compile(r"\broman\b", re.IGNORECASE), "roman_period"),
    (re.compile(r"\bviking\b", re.IGNORECASE), "viking_age"),
    (re.compile(r"\bmedieval\b", re.IGNORECASE), "medieval"),
    (re.compile(r"\bhistoric|modern|present\b", re.IGNORECASE), "historic_or_modern"),
)


def sead_dating_interval(
    dating_range: dict[str, object],
    *,
    age_type: str,
) -> tuple[int, int] | None:
    """Normalize one SEAD dating range into the shared BP interval convention."""
    low_value = parse_optional_int(dating_range.get("low_value"))
    high_value = parse_optional_int(dating_range.get("high_value"))
    age_type_text = " ".join(age_type.casefold().split())
    if age_type_text in _CALIBRATED_BP_AGE_TYPES:
        return _normalize_optional_interval(low_value, high_value)
    if _is_before_common_era_age_type(age_type_text):
        return _calendar_year_interval_to_bp(
            low_value,
            high_value,
            treat_as_bce=True,
        )
    if _is_common_era_age_type(age_type_text):
        return _calendar_year_interval_to_bp(
            low_value,
            high_value,
            treat_as_bce=False,
        )
    return None


def merge_sead_intervals(intervals: list[tuple[int, int]]) -> tuple[int, int] | None:
    """Merge canonical SEAD BP intervals into one site span."""
    canonical_intervals = [
        interval for interval in intervals if sead_interval_is_canonical(interval)
    ]
    if not canonical_intervals:
        return None
    return (
        min(start for start, _ in canonical_intervals),
        max(end for _, end in canonical_intervals),
    )


def sead_interval_is_canonical(interval: tuple[int, int]) -> bool:
    """Return whether an interval can enter canonical BP site projections."""
    return 0 <= interval[0] <= interval[1]


def _relative_interval_from_range(
    dating_range: dict[str, object],
    *,
    age_type: str,
) -> tuple[int, int] | None:
    text = " ".join(age_type.casefold().split())
    if text not in _CALIBRATED_BP_AGE_TYPES:
        return None
    return _normalize_optional_interval(
        parse_optional_int(dating_range.get("low_value")),
        parse_optional_int(dating_range.get("high_value")),
    )


_RELATIVE_BP_LABEL_PATTERN = re.compile(
    r"^CAL_PERIOD_(?P<older>\d+)[_-](?P<younger>\d+)_BP$",
    re.IGNORECASE,
)
_RELATIVE_CALENDAR_LABEL_PATTERN = re.compile(
    r"^CAL_(?P<start>-?\d+)(?:-(?P<end>-?\d+))?_(?P<era>AD|BC)(?P<open>-)?$",
    re.IGNORECASE,
)


def _interval_from_relative_age_label(label: str) -> tuple[int, int] | None:
    bp_match = _RELATIVE_BP_LABEL_PATTERN.fullmatch(label.strip())
    if bp_match:
        return normalize_bp_interval(
            int(bp_match.group("younger")),
            int(bp_match.group("older")),
        )
    calendar_match = _RELATIVE_CALENDAR_LABEL_PATTERN.fullmatch(label.strip())
    if not calendar_match:
        return None
    era = calendar_match.group("era").upper()
    start_year = int(calendar_match.group("start"))
    end_text = calendar_match.group("end")
    end_year = int(end_text) if end_text is not None else start_year
    if calendar_match.group("open"):
        end_year = BP_REFERENCE_YEAR
    return normalize_bp_interval(
        _historical_year_to_bp(start_year, era=era),
        _historical_year_to_bp(end_year, era=era),
    )


def _historical_year_to_bp(year: int, *, era: str) -> int:
    if era == "BC" or year < 0:
        return _bce_year_to_bp(abs(year)) or 0
    return _ce_year_to_bp(year) or 0


def _normalize_optional_interval(
    start_value: int | None,
    end_value: int | None,
) -> tuple[int, int] | None:
    if start_value is None and end_value is None:
        return None
    if start_value is None:
        start_value = end_value
    if end_value is None:
        end_value = start_value
    return normalize_bp_interval(start_value, end_value)


def _calendar_year_interval_to_bp(
    start_year: int | None,
    end_year: int | None,
    *,
    treat_as_bce: bool,
) -> tuple[int, int] | None:
    if treat_as_bce:
        return _normalize_optional_interval(
            _bce_year_to_bp(start_year),
            _bce_year_to_bp(end_year),
        )
    return _normalize_optional_interval(
        _ce_year_to_bp(start_year),
        _ce_year_to_bp(end_year),
    )


def _ce_year_to_bp(year_ce: int | None) -> int | None:
    if year_ce is None:
        return None
    return BP_REFERENCE_YEAR - year_ce


def _bce_year_to_bp(year_bce: int | None) -> int | None:
    if year_bce is None:
        return None
    return year_bce + (BP_REFERENCE_YEAR - 1)


def _is_common_era_age_type(age_type_text: str) -> bool:
    return " ".join(age_type_text.split()) in _COMMON_ERA_AGE_TYPES


def _is_before_common_era_age_type(age_type_text: str) -> bool:
    return " ".join(age_type_text.split()) in _BEFORE_COMMON_ERA_AGE_TYPES


def _normalized_period_label(label: str, description: str) -> str:
    text = " ".join(part for part in (label, description) if part).strip()
    for pattern, normalized_label in _PERIOD_LABEL_PATTERNS:
        if pattern.search(text):
            return normalized_label
    return "unmapped_period_label"


def _normalized_period_labels(rows: list[dict[str, object]]) -> list[str]:
    labels = []
    for row in rows:
        label = str(row.get("normalized_period_label", "")).strip()
        if label and label not in labels:
            labels.append(label)
    return labels


def _uncertainty_labels(
    *row_groups: list[dict[str, object]],
) -> list[str]:
    labels: list[str] = []
    for rows in row_groups:
        for row in rows:
            label = str(row.get("uncertainty_label", "")).strip()
            if label and label not in labels:
                labels.append(label)
    return labels


__all__ = [
    "merge_sead_intervals",
    "sead_dating_interval",
    "sead_interval_is_canonical",
]
