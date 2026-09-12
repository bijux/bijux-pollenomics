"""Explicit calendar support for private HYDE comparison; no legacy BP coercion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..quarantine import IntakeRefusal


@dataclass(frozen=True)
class CalendarYear:
    """Start of a numbered CE/BCE year, with no year zero in source notation."""

    year: int
    era: Literal["CE", "BCE"]

    def __post_init__(self) -> None:
        if type(self.year) is not int or self.year < 1 or self.era not in ("CE", "BCE"):
            raise IntakeRefusal(
                "hyde_calendar_year_invalid", repr((self.year, self.era))
            )

    @property
    def astronomical_year(self) -> int:
        return self.year if self.era == "CE" else 1 - self.year

    @property
    def signed_bp(self) -> int:
        """Elapsed calendar-year starts relative to 1950 CE, including modern dates."""
        return 1950 - self.astronomical_year


@dataclass(frozen=True)
class TimeSupport:
    """An exact year-start instant or a half-open calendar interval [start, end)."""

    start: CalendarYear
    end: CalendarYear
    kind: Literal["instant", "interval"]
    convention: str = "calendar-year-start-no-year-zero.v1"

    def __post_init__(self) -> None:
        if self.convention != "calendar-year-start-no-year-zero.v1":
            raise IntakeRefusal("hyde_calendar_convention_unsupported", self.convention)
        span = self.end.astronomical_year - self.start.astronomical_year
        if self.kind not in ("instant", "interval") or span < 0:
            raise IntakeRefusal("hyde_time_support_invalid", repr(self))
        if (self.kind == "instant" and span != 0) or (
            self.kind == "interval" and span == 0
        ):
            raise IntakeRefusal("hyde_time_support_invalid", repr(self))

    @property
    def signed_bp_endpoints(self) -> tuple[int, int]:
        """Preserve start/end order; interval end is exclusive and BP runs backward."""
        return self.start.signed_bp, self.end.signed_bp
