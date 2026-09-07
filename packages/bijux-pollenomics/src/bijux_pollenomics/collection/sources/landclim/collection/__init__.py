"""Stable LandClim collection facade."""

# Imports retained here are compatibility attributes of the former module.
# ruff: noqa: F401

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile

from .....config import NORDIC_BBOX
from .....core.files import write_json
from .....core.geospatial.geojson import feature_list
from .....core.http import fetch_binary
from ....contracts.artifacts import (
    LANDCLIM_BIBLIOGRAPHY_JSON,
    LANDCLIM_GRID_GEOJSON,
    LANDCLIM_SITE_CSV,
    LANDCLIM_SITE_GEOJSON,
    LANDCLIM_TEMPORAL_GRID_GEOJSON,
)
from ....exports.context_points import (
    write_context_points_csv,
    write_context_points_geojson,
)
from ...boundaries.store import load_repository_country_boundaries
from ..catalog import (
    LANDCLIM_DATASET_METADATA,
    LandClimRawAssets,
    build_landclim_bibliography,
    build_landclim_raw_asset_summaries,
    inspect_landclim_ii_archive,
    resolve_landclim_marquer_asset_urls,
    resolve_landclim_tabular_asset_urls,
    validate_landclim_raw_asset,
)
from ..catalog import resolve_landclim_asset_urls as _resolve_landclim_asset_urls
from ..grid import (
    LANDCLIM_GRID_LAYER_KEY,
    build_landclim_grid_geojson,
    feature_key_from_center,
    feature_key_from_geometry,
    grid_geometry_from_nw_cell_label,
)
from ..review import write_landclim_review_outputs
from ..sites import (
    LANDCLIM_SITE_LAYER_KEY,
    build_landclim_site_records,
    landclim_i_site_records,
    landclim_ii_site_records,
    parse_coordinate,
)
from ..time_windows import (
    LANDCLIM_TEMPORAL_GRID_LAYER_KEY,
    build_landclim_temporal_grid_geojson,
)
from .archive_identity import build_landclim_archive_receipt
from .authority import (
    LANDCLIM_ARCHIVE_FILENAME as _LANDCLIM_ARCHIVE_FILENAME,
)
from .authority import (
    LANDCLIM_ASSET_DATASET_IDS as _LANDCLIM_ASSET_DATASET_IDS,
)
from .authority import (
    LANDCLIM_ASSET_SOURCE_URLS as _LANDCLIM_ASSET_SOURCE_URLS,
)
from .authority import (
    LANDCLIM_REQUIRED_ASSETS as _LANDCLIM_REQUIRED_ASSETS,
)
from .model import LandClimDataReport, LandClimRawReceiptError
from .receipt.publication import build_landclim_raw_receipt
from .receipt.validation import (
    object_rows,
    safe_receipt_filename,
    validate_landclim_receipt_datasets,
)
from .receipt.validation import (
    validate_landclim_raw_receipt as _validate_raw_receipt,
)
from .surfaces import (
    collect_landclim_data as _collect_landclim_data,
)
from .surfaces import (
    materialize_landclim_repository_surfaces as _materialize_repository_surfaces,
)


def collect_landclim_data(
    output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
    bbox: tuple[float, float, float, float],
) -> LandClimDataReport:
    """Download and normalize LandClim PANGAEA datasets under data/landclim."""
    return _collect_landclim_data(
        output_root,
        country_boundaries,
        bbox,
        raw_asset_collector=download_landclim_raw_assets,
        raw_receipt_builder=_build_landclim_raw_receipt,
        raw_receipt_validator=validate_landclim_raw_receipt,
        generated_on=lambda: str(date.today()),
    )


def materialize_landclim_repository_surfaces(data_root: Path) -> LandClimDataReport:
    """Refresh normalized LandClim surfaces from the checked-in raw capture."""
    return _materialize_repository_surfaces(
        data_root,
        raw_receipt_validator=validate_landclim_raw_receipt,
        generated_on=lambda: str(date.today()),
    )


def resolve_landclim_asset_urls() -> dict[str, str]:
    """Backward-compatible access to the LandClim source catalog resolver."""
    return _resolve_landclim_asset_urls()


def download_landclim_raw_assets(raw_dir: Path) -> LandClimRawAssets:
    """Download the LandClim raw upstream assets used for normalization."""
    asset_urls = resolve_landclim_asset_urls()
    raw_paths: dict[str, Path] = {}
    for filename, url in asset_urls.items():
        path = Path(raw_dir) / filename
        payload = fetch_binary(url)
        validate_landclim_raw_asset(filename, payload)
        path.write_bytes(payload)
        raw_paths[filename] = path
    return LandClimRawAssets(paths=raw_paths, asset_urls=asset_urls)


def validate_landclim_raw_receipt(raw_dir: Path) -> dict[str, object]:
    """Validate exact LandClim raw bytes and their governed source associations."""
    return _validate_raw_receipt(raw_dir)


def _build_landclim_raw_receipt(
    raw_paths: dict[str, Path],
    asset_urls: dict[str, str],
    *,
    generated_on: str,
) -> dict[str, object]:
    return build_landclim_raw_receipt(
        raw_paths,
        asset_urls,
        generated_on=generated_on,
        summary_builder=build_landclim_raw_asset_summaries,
        archive_receipt_builder=_build_landclim_archive_receipt,
    )


def _validate_landclim_receipt_datasets(
    receipt: dict[str, object], declared_names: set[str]
) -> dict[str, str]:
    return validate_landclim_receipt_datasets(receipt, declared_names)


def _build_landclim_archive_receipt(path: Path) -> dict[str, object]:
    return build_landclim_archive_receipt(path)


def _object_rows(value: object, *, field_name: str) -> list[dict[str, object]]:
    return object_rows(value, field_name=field_name)


def _safe_receipt_filename(value: object) -> str:
    return safe_receipt_filename(value)


# Export order is part of the compatibility contract.
__all__ = [  # noqa: RUF022
    "LandClimRawReceiptError",
    "LandClimDataReport",
    "build_landclim_grid_geojson",
    "build_landclim_temporal_grid_geojson",
    "build_landclim_raw_asset_summaries",
    "build_landclim_site_records",
    "collect_landclim_data",
    "download_landclim_raw_assets",
    "feature_key_from_center",
    "feature_key_from_geometry",
    "grid_geometry_from_nw_cell_label",
    "inspect_landclim_ii_archive",
    "landclim_i_site_records",
    "landclim_ii_site_records",
    "materialize_landclim_repository_surfaces",
    "parse_coordinate",
    "resolve_landclim_asset_urls",
    "resolve_landclim_marquer_asset_urls",
    "resolve_landclim_tabular_asset_urls",
    "validate_landclim_raw_receipt",
]
