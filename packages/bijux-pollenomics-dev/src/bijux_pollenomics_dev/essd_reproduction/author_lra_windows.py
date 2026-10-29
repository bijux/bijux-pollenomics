"""Select authenticated author time columns without treating missing windows as ecology."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re


@dataclass(frozen=True)
class AuthorWindow:
    """One finite source-declared calibrated-BP interval and its availability mask."""

    index: int
    label_bp: str
    younger_bp: int
    older_bp: int
    source_count_total: int
    unavailable_sites: tuple[str, ...]

    @property
    def temporal_bin(self) -> dict[str, str | int]:
        """Use the same bounds for the request template and source chronology."""
        return {
            "bin_id": "author-TW" + str(self.index),
            "younger_bp": self.younger_bp,
            "older_bp": self.older_bp,
        }

    @property
    def eligible_count(self) -> int:
        """Count records eligible under the declared author-window membership rules."""
        return 17 - len(self.unavailable_sites)


WINDOWS = (
    AuthorWindow(
        4, "1000", 750, 1250, 22582, ("COMERSLA", "EXEBRID", "WHH05", "WHH11")
    ),
    AuthorWindow(5, "1500", 1250, 1750, 20732, ("EXEBRID", "WHH11")),
    AuthorWindow(6, "2000", 1750, 2250, 23009, ("EXEBRID", "WHH05", "WHH11")),
)


def source_window(index: int) -> AuthorWindow:
    """Refuse undeclared windows rather than reinterpret an existing input set."""
    if type(index) is not int:
        raise ValueError("Integer author window identity required")
    for window in WINDOWS:
        if window.index == index:
            return window
    raise ValueError("Only source windows 4, 5 and 6 are admitted")


def selected_counts(
    rows: list[list[str]],
    taxa: list[str],
    site_id: str,
    expected_radius_m: float,
    window: AuthorWindow,
) -> tuple[float, list[int]] | None:
    """Read one source column; unavailable source-filled zero is not an observation."""
    if (
        window not in WINDOWS
        or len(rows) != 34
        or any(len(row) != 26 for row in rows)
        or len(taxa) != 31
        or len(set(taxa)) != 31
        or rows[1][0] != "radius"
        or rows[2][0] != "model"
        or [row[0] for row in rows[3:]] != taxa
        or rows[0][0] != "TW"
        or len(set(rows[0])) != 26
        or rows[0].count(window.label_bp) != 1
    ):
        raise ValueError("Author prepared time/taxon axis changed: " + site_id)
    column = rows[0].index(window.label_bp)
    if column != window.index:
        raise ValueError("Author source window index/label differs")
    cells = [row[column] for row in rows[3:]]
    if any(re.fullmatch(r"[0-9]+", value) is None for value in cells):
        raise ValueError("Explicit nonnegative integer source counts required")
    radius = float(rows[1][column])
    model = rows[2][column]
    counts = [int(value) for value in cells]
    if (
        not math.isfinite(radius)
        or not math.isfinite(expected_radius_m)
        or expected_radius_m <= 0
    ):
        raise ValueError("Finite positive source site geometry required")
    if not any(counts):
        if radius != 0 or model != "0" or site_id not in window.unavailable_sites:
            raise ValueError(
                "Source-filled unavailable window disagrees with its native mask"
            )
        return None
    if (
        radius != expected_radius_m
        or model != "2"
        or site_id in window.unavailable_sites
    ):
        raise ValueError(
            "Author positive lake window disagrees with source site metadata"
        )
    return radius, counts
