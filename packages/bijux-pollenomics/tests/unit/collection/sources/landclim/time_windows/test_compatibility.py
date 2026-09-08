"""Import and signature compatibility for LandClim time-window functions."""

from __future__ import annotations

import hashlib
import inspect
import json

from bijux_pollenomics.collection.sources.landclim import time_windows

_LEGACY_FUNCTION_ORDER = [
    "build_landclim_temporal_grid_geojson",
    "_merge_marquer_time_windows",
    "_marquer_cell_geometries",
    "_marquer_grid_floor",
    "_merge_landclim_i_time_windows",
    "_merge_landclim_ii_time_windows",
    "_temporal_grid_feature",
    "_landclim_i_values_by_cell",
    "_bibliography_reference_keys",
    "_landclim_i_header_index",
    "_landclim_ii_standard_errors",
    "_numeric_values",
    "_numeric_mapping",
    "_require_uncertainty_pair",
    "_polygon_center",
    "_properties",
    "_grouped_values",
]


def test_public_export_order_and_constant_are_unchanged() -> None:
    assert time_windows.__all__ == [
        "LANDCLIM_TEMPORAL_GRID_LAYER_KEY",
        "build_landclim_temporal_grid_geojson",
    ]
    assert time_windows.LANDCLIM_TEMPORAL_GRID_LAYER_KEY == (
        "landclim-reveals-temporal-grid"
    )


def test_all_legacy_callable_signatures_are_unchanged() -> None:
    signatures = [
        (name, str(inspect.signature(getattr(time_windows, name))))
        for name in _LEGACY_FUNCTION_ORDER
    ]
    payload = (json.dumps(signatures, separators=(",", ":")) + "\n").encode()
    assert len(signatures) == 17
    assert hashlib.sha256(payload).hexdigest() == (
        "15920dfaa600c49ac85a403b96d95db4ccff7080292460cc1eab2aac73146117"
    )


def test_legacy_dependency_and_private_imports_remain_reachable() -> None:
    for name in (
        "LANDCLIM_DATASET_METADATA",
        "Mapping",
        "Path",
        "TextIOWrapper",
        "ZipFile",
        "build_temporal_semantics",
        "classify_country",
        "clean_optional_text",
        "csv",
        "landclim_ii_quality_lookup",
        "list_xlsx_sheet_names",
        "math",
        "parse_bp_window_label",
        "parse_float",
        "point_in_bbox",
        "read_xlsx_sheet_rows",
        "re",
        "resolve_landclim_country",
        "time_window_sort_key",
    ):
        assert hasattr(time_windows, name)
