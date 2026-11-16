"""Source-owned physical cells and window quality for LandClim II."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
import math
from pathlib import Path

from ....core.text import clean_optional_text
from ...intake.workbooks import read_xlsx_sheet_rows
from .catalog import (
    LANDCLIM_II_EXPECTED_TIME_WINDOW_COUNT,
    time_window_from_tw_filename,
)


def _coordinate(token: str | None, field: str) -> Decimal:
    """Preserve decimal source identity without rounding distinct physical cells."""
    try:
        value = Decimal(token) if token is not None else Decimal("NaN")
    except InvalidOperation as error:
        raise ValueError(
            f"LandClim II quality coordinate is invalid: {field}"
        ) from error
    bound = 180 if field == "lonDD" else 90
    if not value.is_finite() or not -bound <= value <= bound:
        raise ValueError(f"LandClim II quality coordinate is invalid: {field}")
    if Decimal(str(float(value))) != value:
        raise ValueError(
            f"LandClim II quality coordinate precision is unsupported: {field}"
        )
    return value


class _QualityRow(dict[str, str]):
    """Keep window-map compatibility while retaining the native physical owner."""

    def __init__(self, *, longitude: str, latitude: str) -> None:
        super().__init__()
        self.coordinates = (
            _coordinate(longitude, "lonDD"),
            _coordinate(latitude, "latDD"),
        )


_LANDCLIM_II_QUALITY_HEADER_PREFIX = ("LCGRID_ID", "lonDD", "latDD")
_LANDCLIM_II_QUALITY_CLASSES = frozenset({"high", "low", "no_pollen_data"})
_LANDCLIM_II_QUALITY_CLASS_BY_CODE = {
    "1": "high",
    "2": "low",
    "nodata": "no_pollen_data",
}


def _landclim_ii_quality_windows() -> tuple[str, ...]:
    return tuple(
        time_window_from_tw_filename(f"TW{index}.csv")
        for index in range(1, LANDCLIM_II_EXPECTED_TIME_WINDOW_COUNT + 1)
    )


def landclim_ii_quality_lookup(path: Path) -> dict[str, dict[str, str]]:
    """Load quality labels for LandClim II grid cells keyed by LCGRID_ID."""
    rows = read_xlsx_sheet_rows(path, "GC_quality_by_TW")
    if not rows:
        raise ValueError("LandClim II quality workbook has no rows")
    canonical_windows = _landclim_ii_quality_windows()
    expected_header = (
        *_LANDCLIM_II_QUALITY_HEADER_PREFIX,
        *(window.removesuffix(" BP") for window in canonical_windows),
    )
    header = tuple(clean_optional_text(value) for value in rows[0])
    if header != expected_header:
        raise ValueError(
            "LandClim II quality workbook header must contain the exact first "
            "columns and 25 ordered bare BP windows"
        )
    quality: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) != len(expected_header):
            raise ValueError(
                f"LandClim II quality workbook row {row_number} has {len(row)} "
                f"columns; expected {len(expected_header)}"
            )
        grid_id, longitude, latitude = (clean_optional_text(value) for value in row[:3])
        for field, value in zip(
            _LANDCLIM_II_QUALITY_HEADER_PREFIX,
            (grid_id, longitude, latitude),
            strict=True,
        ):
            if not value:
                raise ValueError(
                    f"LandClim II quality workbook row {row_number} has empty {field}"
                )
        for field, value, minimum, maximum in (
            ("lonDD", longitude, -180.0, 180.0),
            ("latDD", latitude, -90.0, 90.0),
        ):
            try:
                coordinate = float(value)
            except ValueError as exc:
                raise ValueError(
                    f"LandClim II quality workbook row {row_number} has invalid {field}"
                ) from exc
            if not math.isfinite(coordinate) or not minimum <= coordinate <= maximum:
                raise ValueError(
                    f"LandClim II quality workbook row {row_number} has invalid {field}"
                )
        if grid_id in quality:
            raise ValueError(
                f"LandClim II quality workbook repeats LCGRID_ID {grid_id}"
            )
        row_quality = _QualityRow(longitude=longitude, latitude=latitude)
        for window, value in zip(canonical_windows, row[3:], strict=True):
            code = clean_optional_text(value)
            quality_class = _LANDCLIM_II_QUALITY_CLASS_BY_CODE.get(code)
            if quality_class is None:
                raise ValueError(
                    "LandClim II quality workbook has unsupported quality code "
                    f"{code!r} for {grid_id} {window}"
                )
            row_quality[window] = quality_class
        quality[grid_id] = row_quality
    return quality


def _required_landclim_ii_quality_class(
    quality_by_grid: Mapping[str, Mapping[str, str]],
    *,
    grid_id: str,
    time_window: str,
    longitude_token: str | None = None,
    latitude_token: str | None = None,
) -> str:
    source = quality_by_grid.get(grid_id, {})
    if isinstance(source, _QualityRow) and source.coordinates != (
        _coordinate(longitude_token, "lonDD"),
        _coordinate(latitude_token, "latDD"),
    ):
        raise ValueError(
            f"LandClim II quality physical cell differs for {grid_id}:{time_window}"
        )
    quality_class = source.get(time_window)
    if quality_class not in _LANDCLIM_II_QUALITY_CLASSES:
        raise ValueError(
            "LandClim II quality is missing or invalid for in-scope record "
            f"{grid_id}:{time_window}"
        )
    return quality_class
