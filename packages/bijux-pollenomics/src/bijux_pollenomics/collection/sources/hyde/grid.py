"""Regular geographic grids and conservative parallel/meridian cell areas."""

from __future__ import annotations

from dataclasses import dataclass
from math import atanh, isfinite, radians, sin, sqrt
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
        """
        eccentricity_squared = WGS84_GEODESIC.es
        eccentricity = sqrt(eccentricity_squared)

        def primitive(latitude: float) -> float:
            u = sin(radians(latitude))
            return (
                u / (1 - eccentricity_squared * u * u)
                + atanh(eccentricity * u) / eccentricity
            ) / 2

        return (
            radians(self.east - self.west)
            * WGS84_GEODESIC.a**2
            * (1 - eccentricity_squared)
            * (primitive(self.north) - primitive(self.south))
            / 1_000_000
        )


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
