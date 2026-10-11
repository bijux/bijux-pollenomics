"""Keep source CRS declarations separate from GeoPackage x/y transport order."""

from __future__ import annotations

from typing import Any

from pyproj import CRS
from pyproj.exceptions import CRSError


def inspect_crs(profile: dict[str, Any]) -> dict[str, object]:
    """Refuse a mislabeled/malformed source WKT without transforming coordinates."""
    metadata = profile["metadata"]
    rows = [r for r in metadata["gpkg_spatial_ref_sys"] if r["srs_id"] == 3006]
    result: dict[str, object] = {
        "source_srs_rows": rows,
        "transport_axis_order": "x_easting_y_northing",
        "transport_axis_authority": "OGC GeoPackage1.4 section2.1.3",
        "coordinate_transformation_performed": False,
        "pyproj_version_scope": "runtime_dependency_recorded_in_manifest",
    }
    reason: str | None = None
    if len(rows) != 1:
        reason = "source_srs_cardinality"
    elif (
        type(rows[0]["srs_id"]) is not int
        or rows[0]["organization"] != "EPSG"
        or type(rows[0]["organization_coordsys_id"]) is not int
        or rows[0]["organization_coordsys_id"] != 3006
    ):
        reason = "source_srs_authority_mismatch"
    else:
        definition = rows[0]["definition"]
        try:
            if not isinstance(definition, str) or not definition:
                raise ValueError("missing definition")
            declared = CRS.from_wkt(definition)
            if not declared.equals(CRS.from_epsg(3006)):
                reason = "source_wkt_disagrees_with_epsg3006"
            result["declared_axis_metadata"] = [
                {
                    "name": axis.name,
                    "abbreviation": axis.abbrev,
                    "direction": axis.direction,
                    "unit": axis.unit_name,
                }
                for axis in declared.axis_info
            ]
        except (CRSError, ValueError):
            reason = "source_wkt_unreadable"
    result.update(
        status="refused" if reason else "declared_crs_verified",
        reason_codes=[reason] if reason else [],
    )
    return result
