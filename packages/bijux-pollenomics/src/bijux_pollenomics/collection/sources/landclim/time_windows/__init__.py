"""LandClim temporal-grid acquisition and scientific contracts."""

from __future__ import annotations

from collections.abc import Mapping as Mapping
import csv as csv
from io import TextIOWrapper as TextIOWrapper
import math as math
from pathlib import Path as Path
import re as re
from zipfile import ZipFile as ZipFile

from .....core.bp_time import mean_bp_year_from_interval as mean_bp_year_from_interval
from .....core.bp_time import parse_bp_window_label as parse_bp_window_label
from .....core.temporal_semantics import (
    build_temporal_semantics as build_temporal_semantics,
)
from .....core.text import clean_optional_text as clean_optional_text
from ....intake.workbooks import list_xlsx_sheet_names as list_xlsx_sheet_names
from ....intake.workbooks import read_xlsx_sheet_rows as read_xlsx_sheet_rows
from ....spatial import classify_country as classify_country
from ....spatial import point_in_bbox as point_in_bbox
from ..catalog import LANDCLIM_DATASET_METADATA as LANDCLIM_DATASET_METADATA
from ..catalog import LANDCLIM_II_MEANS_DIRECTORY as LANDCLIM_II_MEANS_DIRECTORY
from ..catalog import (
    LANDCLIM_II_STANDARD_ERRORS_DIRECTORY as LANDCLIM_II_STANDARD_ERRORS_DIRECTORY,
)
from ..catalog import time_window_from_tw_filename as time_window_from_tw_filename
from ..catalog import time_window_sort_key as time_window_sort_key
from ..grid import grid_geometry_from_center as grid_geometry_from_center
from ..grid import grid_geometry_from_nw_cell_label as grid_geometry_from_nw_cell_label
from ..grid import landclim_ii_quality_lookup as landclim_ii_quality_lookup
from ..grid import (
    normalize_landclim_time_window_label as normalize_landclim_time_window_label,
)
from ..grid import summarize_quality_labels as summarize_quality_labels
from ..sites import parse_coordinate as parse_coordinate
from ..sites import parse_float as parse_float
from ..sites import resolve_landclim_country as resolve_landclim_country
from .features import _bibliography_reference_keys as _bibliography_reference_keys
from .features import _temporal_grid_feature as _temporal_grid_feature
from .landclim_i import (
    _landclim_i_header_index as _landclim_i_header_index,
    _landclim_i_values_by_cell as _landclim_i_values_by_cell,
    _merge_landclim_i_time_windows,
)
from .landclim_ii import (
    _landclim_ii_standard_errors as _landclim_ii_standard_errors,
    _merge_landclim_ii_time_windows,
)
from .marquer import (
    _marquer_cell_geometries as _marquer_cell_geometries,
    _marquer_grid_floor as _marquer_grid_floor,
    _merge_marquer_time_windows,
)
from .values import (
    _grouped_values as _grouped_values,
    _numeric_mapping as _numeric_mapping,
    _numeric_values as _numeric_values,
    _polygon_center as _polygon_center,
    _properties as _properties,
    _require_uncertainty_pair as _require_uncertainty_pair,
)

__all__ = [
    "LANDCLIM_TEMPORAL_GRID_LAYER_KEY",
    "build_landclim_temporal_grid_geojson",
]

LANDCLIM_TEMPORAL_GRID_LAYER_KEY = "landclim-reveals-temporal-grid"
_LANDCLIM_I_MEAN_SUFFIX = "meanLC"
_LANDCLIM_I_STANDARD_ERROR_SUFFIX = "SE"
_MARQUER_GRID_WINDOW_PATTERN = re.compile(r"GC(?P<cell>\d+)-(?P<window>\d+)")


def build_landclim_temporal_grid_geojson(
    raw_paths: dict[str, Path],
    bbox: tuple[float, float, float, float],
    country_boundaries: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    """Build one map-ready polygon feature per LandClim cell and time window."""
    features: dict[tuple[str, str, str], dict[str, object]] = {}
    marquer_path = raw_paths.get("marquer_2017_reveals_taxa_grid_cells.xlsx")
    if marquer_path is not None:
        _merge_marquer_time_windows(
            features,
            marquer_path,
            bbox=bbox,
            country_boundaries=country_boundaries,
        )
    _merge_landclim_i_time_windows(
        features,
        raw_paths["landclim_i_land_cover_types.xlsx"],
        value_group="land_cover_types",
        bbox=bbox,
        country_boundaries=country_boundaries,
    )
    _merge_landclim_i_time_windows(
        features,
        raw_paths["landclim_i_plant_functional_types.xlsx"],
        value_group="plant_functional_types",
        bbox=bbox,
        country_boundaries=country_boundaries,
    )
    _merge_landclim_ii_time_windows(
        features,
        raw_paths["landclim_ii_reveals_results.zip"],
        quality_by_grid=landclim_ii_quality_lookup(
            raw_paths["landclim_ii_grid_cell_quality.xlsx"]
        ),
        bbox=bbox,
        country_boundaries=country_boundaries,
    )
    return {
        "type": "FeatureCollection",
        "features": [
            feature
            for _, feature in sorted(
                features.items(),
                key=lambda item: (
                    item[0][0],
                    time_window_sort_key(item[0][2]),
                    item[0][1],
                ),
            )
        ],
    }
