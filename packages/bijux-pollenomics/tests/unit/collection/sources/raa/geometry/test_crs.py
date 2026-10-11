"""Declared EPSG identity is verified against source WKT, not a label alone."""

import copy
from typing import Any, cast

from pyproj import CRS
import pytest

from bijux_pollenomics.collection.sources.raa.geometry.crs import inspect_crs


def profile() -> dict[str, Any]:
    return {
        "metadata": {
            "gpkg_spatial_ref_sys": [
                {
                    "srs_id": 3006,
                    "organization": "EPSG",
                    "organization_coordsys_id": 3006,
                    "definition": CRS.from_epsg(3006).to_wkt(),
                }
            ]
        }
    }


def test_wkt_axes_are_not_transport_order() -> None:
    result = inspect_crs(profile())
    assert result["status"] == "declared_crs_verified"
    assert result["transport_axis_order"] == "x_easting_y_northing"
    axes = cast(list[dict[str, object]], result["declared_axis_metadata"])
    assert axes[0]["direction"] == "north"
    assert result["coordinate_transformation_performed"] is False


@pytest.mark.parametrize(
    "definition,reason",
    [
        (CRS.from_epsg(4326).to_wkt(), "source_wkt_disagrees_with_epsg3006"),
        ("source WKT", "source_wkt_unreadable"),
        (None, "source_wkt_unreadable"),
    ],
)
def test_mislabeled_or_missing_wkt(definition: str | None, reason: str) -> None:
    value = profile()
    value["metadata"]["gpkg_spatial_ref_sys"][0]["definition"] = definition
    result = inspect_crs(value)
    assert result["status"] == "refused"
    assert result["reason_codes"] == [reason]


def test_duplicate_and_missing_srs_are_explicit() -> None:
    value = profile()
    rows = value["metadata"]["gpkg_spatial_ref_sys"]
    rows.append(copy.deepcopy(rows[0]))
    assert inspect_crs(value)["reason_codes"] == ["source_srs_cardinality"]
    rows.clear()
    assert inspect_crs(value)["reason_codes"] == ["source_srs_cardinality"]
