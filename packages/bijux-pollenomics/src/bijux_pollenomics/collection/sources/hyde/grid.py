"""Regular geographic grids and conservative parallel/meridian cell areas."""

from __future__ import annotations

from dataclasses import dataclass
from math import atanh, cos, isfinite, radians, sin, sqrt
from typing import Literal

from ....core.geospatial.distance import WGS84_GEODESIC
from ..quarantine import IntakeRefusal


def finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise IntakeRefusal("hyde_non_finite_number", name)
    try:
        number = float(value)
    except OverflowError as exc:
        raise IntakeRefusal("hyde_non_finite_number", name) from exc
    if not isfinite(number):
        raise IntakeRefusal("hyde_non_finite_number", name)
    return number


@dataclass(frozen=True)
class Bounds:
    """Longitude/latitude edges; wrapped antimeridian regions require explicit splitting."""

    west: float
    south: float
    east: float
    north: float

    def __post_init__(self) -> None:
        for name in ("west", "south", "east", "north"):
            finite_number(getattr(self, name), name)
        if not (
            -180 <= self.west < self.east <= 180
            and -90 <= self.south < self.north <= 90
        ):
            raise IntakeRefusal("hyde_bounds_invalid", repr(self))

    def contains(self, other: Bounds) -> bool:
        return (
            self.west <= other.west
            and self.east >= other.east
            and self.south <= other.south
            and self.north >= other.north
        )

    def overlaps(self, other: Bounds) -> bool:
        return max(self.west, other.west) < min(self.east, other.east) and max(
            self.south, other.south
        ) < min(self.north, other.north)

    @property
    def area_km2(self) -> float:
        """Integrate the WGS84 ellipsoid surface along parallels and meridians.

        The area element is a²(1-e²) cos(phi)/(1-e² sin²(phi))² dphi dlambda.
        This is not a geodesic-corner polygon approximation or an equal-cell-area rule.
        Values lost to floating-point arithmetic are refused.
        """
        eccentricity_squared = WGS84_GEODESIC.es
        eccentricity = sqrt(eccentricity_squared)

        south_u = sin(radians(self.south))
        north_u = sin(radians(self.north))
        # Computing sin(north) - sin(south) directly loses polar cell support.
        # Use midpoint colatitude when both edges lie in the same hemisphere.
        if self.south >= 0 or self.north <= 0:
            midpoint_cos = sin(
                radians(((90 - abs(self.south)) + (90 - abs(self.north))) / 2)
            )
        else:
            midpoint_cos = cos(radians((self.south + self.north) / 2))
        delta_u = 2 * sin(radians((self.north - self.south) / 2)) * midpoint_cos
        cross = eccentricity_squared * south_u * north_u
        difference = (
            delta_u
            * (1 + cross)
            / (
                (1 - eccentricity_squared * south_u * south_u)
                * (1 - eccentricity_squared * north_u * north_u)
            )
            + atanh(eccentricity * delta_u / (1 - cross)) / eccentricity
        ) / 2
        area = (
            radians(self.east - self.west)
            * WGS84_GEODESIC.a**2
            * (1 - eccentricity_squared)
            * difference
            / 1_000_000
        )
        if not isfinite(area) or area <= 0:
            raise IntakeRefusal("hyde_cell_area_precision_limit", repr(self))
        return area


@dataclass(frozen=True)
class GridSpec:
    """Declared regular cell edges; no inference from raster filename or resolution."""

    columns: int
    rows: int
    west: float
    south: float
    longitude_step: float
    latitude_step: float
    row_order: Literal["north_to_south", "south_to_north"]
    crs: str = "EPSG:4326"

    def __post_init__(self) -> None:
        if (
            type(self.columns) is not int
            or type(self.rows) is not int
            or min(self.columns, self.rows) <= 0
        ):
            raise IntakeRefusal(
                "hyde_grid_dimensions_invalid", repr((self.columns, self.rows))
            )
        for name in ("west", "south", "longitude_step", "latitude_step"):
            finite_number(getattr(self, name), name)
        if self.longitude_step <= 0 or self.latitude_step <= 0:
            raise IntakeRefusal("hyde_grid_step_invalid", repr(self))
        if self.crs != "EPSG:4326" or self.row_order not in (
            "north_to_south",
            "south_to_north",
        ):
            raise IntakeRefusal("hyde_grid_convention_unsupported", repr(self))
        _ = self.bounds

    @property
    def bounds(self) -> Bounds:
        return Bounds(
            self.west,
            self.south,
            self.west + self.columns * self.longitude_step,
            self.south + self.rows * self.latitude_step,
        )

    def cell_bounds(self, row: int, column: int) -> Bounds:
        if (
            type(row) is not int
            or type(column) is not int
            or not (0 <= row < self.rows and 0 <= column < self.columns)
        ):
            raise IntakeRefusal("hyde_cell_index_outside_grid", repr((row, column)))
        geographic_row = (
            row if self.row_order == "south_to_north" else self.rows - row - 1
        )
        west = self.west + column * self.longitude_step
        south = self.south + geographic_row * self.latitude_step
        return Bounds(
            west,
            south,
            self.west + (column + 1) * self.longitude_step,
            self.south + (geographic_row + 1) * self.latitude_step,
        )

    def window_bounds(
        self, row_start: int, row_stop: int, column_start: int, column_stop: int
    ) -> Bounds:
        """Return cell-aligned bounds for nonempty half-open source-index ranges.

        Rows follow this grid's declared row order. No geographic snapping or
        native HYDE source admission is implied.
        """
        indices = (row_start, row_stop, column_start, column_stop)
        if not all(type(index) is int for index in indices) or not (
            0 <= row_start < row_stop <= self.rows
            and 0 <= column_start < column_stop <= self.columns
        ):
            raise IntakeRefusal("hyde_grid_window_invalid", repr(indices))
        first = self.cell_bounds(row_start, column_start)
        last = self.cell_bounds(row_stop - 1, column_stop - 1)
        return Bounds(
            first.west,
            min(first.south, last.south),
            last.east,
            max(first.north, last.north),
        )
