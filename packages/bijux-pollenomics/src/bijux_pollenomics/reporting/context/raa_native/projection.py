"""Explicit approximate SWEREF99 display operation for synthetic cell footprints."""

from __future__ import annotations

import math
from typing import Any

import pyproj
from pyproj import Transformer

SUPPORT_BOUNDS = (10.03, 54.96, 24.17, 69.07)


def project_cells(
    cells: tuple[tuple[int, int, int], ...], source_sha256: str
) -> tuple[dict[str, Any], dict[str, int], dict[str, object]]:
    """Clip display rectangles only, preserving original full-cell units and IDs."""
    transformer = Transformer.from_crs(
        4619,
        4326,
        always_xy=True,
        authority="EPSG",
        allow_ballpark=False,
        only_best=True,
    )
    if transformer.is_network_enabled:
        raise ValueError("Native registry display requires offline projection")
    operation_ids = [
        operation.to_json_dict().get("id", {})
        for operation in (transformer.operations or ())
    ]
    area = transformer.area_of_use
    if (
        {"authority": "EPSG", "code": 1879} not in operation_ids
        or transformer.definition != "proj=noop ellps=GRS80"
        or transformer.accuracy != 1.0
        or area is None
        or tuple(area.bounds) != SUPPORT_BOUNDS
    ):
        raise ValueError("Native registry display operation differs from EPSG1879")
    features: list[dict[str, object]] = []
    partial_cells = partial_uuids = 0
    for west, south, count in cells:
        native = (west, south, west + 1, south + 1)
        clipped = (
            max(west, SUPPORT_BOUNDS[0]),
            max(south, SUPPORT_BOUNDS[1]),
            min(west + 1, SUPPORT_BOUNDS[2]),
            min(south + 1, SUPPORT_BOUNDS[3]),
        )
        if clipped[0] >= clipped[2] or clipped[1] >= clipped[3]:
            raise ValueError("Native registry cell has no supported display footprint")
        partial = clipped != native
        partial_cells += partial
        partial_uuids += count if partial else 0
        ring: list[list[float]] = []
        for x, y in (
            (clipped[0], clipped[1]),
            (clipped[2], clipped[1]),
            (clipped[2], clipped[3]),
            (clipped[0], clipped[3]),
            (clipped[0], clipped[1]),
        ):
            longitude, latitude = transformer.transform(x, y, errcheck=True)
            if not all(math.isfinite(v) for v in (longitude, latitude)):
                raise ValueError("Native registry display coordinate is not finite")
            ring.append([float(longitude), float(latitude)])
        cell_id = f"raa:{source_sha256}:EPSG4619:1degree:{west}:{south}"
        features.append(
            {
                "type": "Feature",
                "id": cell_id,
                "geometry": {"type": "Polygon", "coordinates": [ring]},
                "properties": {
                    "cell_id": cell_id,
                    "count": count,
                    "native_cell_bounds": list(native),
                    "native_grid_crs": "EPSG:4619",
                    "partial_display_footprint": partial,
                    "count_unit": "native_registry_UUID_per_original_1degree_cell",
                    "source_sha256": source_sha256,
                    "contribution_role": "display_only",
                    "scientific_selection_enabled": False,
                },
            }
        )
    accounting = {
        "mapped_cells": len(cells),
        "mapped_full_cell_uuids": sum(c[2] for c in cells),
        "partial_footprint_cells": partial_cells,
        "full_cell_uuids_in_partial_cells": partial_uuids,
        "withheld_cells": 0,
        "withheld_uuids": 0,
    }
    identity: dict[str, object] = {
        "source_crs": "EPSG:4619",
        "target_crs": "OGC:CRS84",
        "operation": "EPSG:1879",
        "operation_definition": transformer.definition,
        "always_xy": True,
        "allow_ballpark": False,
        "network_enabled": False,
        "operation_stated_accuracy_metres": transformer.accuracy,
        "native_coordinate_accuracy_established": False,
        "coordinate_epoch": "unknown; capture time is not coordinate epoch",
        "support_bounds": list(SUPPORT_BOUNDS),
        "footprint_policy": "display_only_clipping; full native cell count retained",
        "country_clipping": False,
        "count_prorating": False,
        "pyproj_version": pyproj.__version__,
        "PROJ_version": pyproj.proj_version_str,
    }
    return {"type": "FeatureCollection", "features": features}, accounting, identity
