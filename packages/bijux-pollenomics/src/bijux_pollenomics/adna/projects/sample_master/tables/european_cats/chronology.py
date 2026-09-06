"""Conservative calendar-envelope parsing for the European cat panel."""

from __future__ import annotations

import re

from bijux_pollenomics.core.bp_time import build_bp_interval_label

_CALENDAR_YEAR_RE = re.compile(
    r"(?P<year>\d{1,5})\s*(?:cal\s*)?(?P<era>BC|BCE|AD|CE)\b",
    re.IGNORECASE,
)
_SHARED_ERA_RANGE_RE = re.compile(
    r"(?P<first>\d{1,5})\s*[-–]\s*(?P<second>\d{1,5})\s*"
    r"(?:cal\s*)?(?P<era>BC|BCE|AD|CE)\b",
    re.IGNORECASE,
)


def _calendar_union_bp(value: str) -> tuple[int, int] | None:
    """Return the outer BP envelope of explicitly era-qualified calendar years.

    Percentage weights and uncalibrated laboratory ages are intentionally ignored.
    A range whose era is written once contributes both endpoints; otherwise a year
    contributes only when its own BC/BCE/AD/CE suffix is present.
    """

    text = value.replace(",", "").strip()
    years: list[int] = []
    for match in _CALENDAR_YEAR_RE.finditer(text):
        years.append(_calendar_year_to_bp(match.group("year"), match.group("era")))
    for match in _SHARED_ERA_RANGE_RE.finditer(text):
        years.extend(
            (
                _calendar_year_to_bp(match.group("first"), match.group("era")),
                _calendar_year_to_bp(match.group("second"), match.group("era")),
            )
        )
    if not years:
        return None
    return min(years), max(years)


def _calendar_year_to_bp(year_text: str, era: str) -> int:
    year = int(year_text)
    if era.casefold() in {"bc", "bce"}:
        return year + 1949
    return max(0, 1950 - year)


def _calendar_union_label(value: str) -> str:
    interval = _calendar_union_bp(value)
    if interval is None:
        return ""
    return build_bp_interval_label(*interval)


__all__ = [
    "_calendar_union_bp",
    "_calendar_union_label",
]
