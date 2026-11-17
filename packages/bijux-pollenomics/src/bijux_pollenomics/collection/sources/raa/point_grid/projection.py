"""SWEREF99 projection and exact half-open integer cells without country inference."""

from __future__ import annotations

from hashlib import sha256
import math
from pathlib import Path

import pyproj
from pyproj import CRS, Transformer, datadir
from pyproj.exceptions import ProjError

from bijux_pollenomics.core.filesystem import read_regular_file

GRID: dict[str, object] = {
    "crs": "EPSG:4619",
    "axis_order": "longitude_latitude",
    "coordinate_unit": "degree",
    "origin": [0, 0],
    "cell_size_degrees": 1,
    "endpoint_ownership": "west_south_inclusive_east_north_exclusive",
    "index_rule": "mathematical_floor_without_snapping_or_epsilon",
    "unoccupied_cells": "not_exported_not_archaeological_zero",
}


class NativePointProjection:
    """Keep one explicit same-frame inverse projection for a single consumer call."""

    def __init__(self) -> None:
        """Use projected binary X/Y and geographic longitude/latitude explicitly."""
        self.source = CRS.from_epsg(3006)
        self.target = CRS.from_epsg(4619)
        self.transformer = Transformer.from_crs(
            self.source, self.target, always_xy=True, allow_ballpark=False
        )
        area = self.source.area_of_use
        if area is None:
            raise ValueError("Native POINT projection requires a declared support area")
        self.bounds = area.bounds

    def inverse_point(self, east: float, north: float) -> tuple[float, float] | None:
        """Exclude unsupported locations without moving or repairing source points."""
        if any(
            type(value) not in (int, float) or not math.isfinite(value)
            for value in (east, north)
        ):
            return None
        try:
            longitude, latitude = self.transformer.transform(east, north, errcheck=True)
        except ProjError:
            return None
        west, south, eastern, northern = self.bounds
        if (
            not math.isfinite(longitude)
            or not math.isfinite(latitude)
            or not west <= longitude <= eastern
            or not south <= latitude <= northern
        ):
            return None
        return float(longitude), float(latitude)

    def identity(self) -> dict[str, object]:
        """Bind operation, dependency and support rectangle without accuracy claims."""
        return {
            "source_crs": "EPSG:3006",
            "target_crs": "EPSG:4619",
            "source_axis_order": "x_easting_y_northing",
            "source_unit": "metre",
            "target_axis_order": "longitude_latitude",
            "always_xy": True,
            "allow_ballpark": False,
            "operation_definition": self.transformer.definition,
            "operation_description": self.transformer.description,
            "reported_operation_accuracy_metres": self.transformer.accuracy,
            "reported_accuracy_is_not_native_coordinate_accuracy": True,
            "location_support": "EPSG3006_area_of_use_rectangle_not_country_containment",
            "location_support_bounds": list(self.bounds),
            "pyproj_version": pyproj.__version__,
            "PROJ_version": pyproj.proj_version_str,
            "PROJ_database_sha256": sha256(
                read_regular_file(
                    Path(datadir.get_data_dir()) / "proj.db", max_bytes=64 * 1024**2
                )
            ).hexdigest(),
        }


def grid_cell(longitude: float, latitude: float) -> tuple[int, int]:
    """Assign exact integer edges to their eastern/northern one-degree cell."""
    if (
        not math.isfinite(longitude)
        or not math.isfinite(latitude)
        or not -180 <= longitude < 180
        or not -90 <= latitude < 90
    ):
        raise ValueError("Native POINT grid coordinates are outside its finite domain")
    return math.floor(longitude), math.floor(latitude)
