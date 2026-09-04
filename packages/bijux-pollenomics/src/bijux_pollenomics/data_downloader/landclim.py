from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
from pathlib import Path
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile

from ..config import NORDIC_BBOX
from ..core.files import write_json
from ..core.geojson import feature_list
from ..core.http import fetch_binary
from .contracts import (
    LANDCLIM_BIBLIOGRAPHY_JSON,
    LANDCLIM_GRID_GEOJSON,
    LANDCLIM_SITE_CSV,
    LANDCLIM_SITE_GEOJSON,
    LANDCLIM_TEMPORAL_GRID_GEOJSON,
)
from .exports.context_points import (
    write_context_points_csv,
    write_context_points_geojson,
)
from .shared import load_repository_country_boundaries
from .sources.landclim.catalog import (
    LANDCLIM_DATASET_METADATA,
    LandClimRawAssets,
    build_landclim_raw_asset_summaries,
    build_landclim_bibliography,
    inspect_landclim_ii_archive,
    resolve_landclim_marquer_asset_urls,
    resolve_landclim_tabular_asset_urls,
    validate_landclim_raw_asset,
)
from .sources.landclim.catalog import (
    resolve_landclim_asset_urls as _resolve_landclim_asset_urls,
)
from .sources.landclim.grid import (
    LANDCLIM_GRID_LAYER_KEY,
    build_landclim_grid_geojson,
    feature_key_from_center,
    feature_key_from_geometry,
    grid_geometry_from_nw_cell_label,
)
from .sources.landclim.sites import (
    LANDCLIM_SITE_LAYER_KEY,
    build_landclim_site_records,
    landclim_i_site_records,
    landclim_ii_site_records,
    parse_coordinate,
)
from .sources.landclim.review import write_landclim_review_outputs
from .sources.landclim.time_windows import (
    LANDCLIM_TEMPORAL_GRID_LAYER_KEY,
    build_landclim_temporal_grid_geojson,
)

_LANDCLIM_ASSET_DATASET_IDS = {
    "marquer_2017_reveals_taxa_grid_cells.xlsx": "900966",
    "landclim_i_land_cover_types.xlsx": "897303",
    "landclim_i_plant_functional_types.xlsx": "897303",
    "landclim_ii_reveals_results.zip": "937075",
    "landclim_ii_grid_cell_quality.xlsx": "937075",
    "landclim_ii_contributors.xlsx": "937075",
    "landclim_ii_site_metadata.xlsx": "937075",
    "landclim_ii_taxa_pft_ppe_fsp_values.csv": "937075",
}
_LANDCLIM_ASSET_SOURCE_URLS = {
    "marquer_2017_reveals_taxa_grid_cells.xlsx": (
        "https://store.pangaea.de/Publications/Marquer-etal_2017/"
        "MARQUER_QSR2017.xlsx"
    ),
    "landclim_i_land_cover_types.xlsx": (
        "https://store.pangaea.de/Publications/Gaillard-Lemdahl_2019/"
        "LandClimILCTs.xlsx"
    ),
    "landclim_i_plant_functional_types.xlsx": (
        "https://store.pangaea.de/Publications/Gaillard-Lemdahl_2019/"
        "LandClimIPFTs.xlsx"
    ),
    "landclim_ii_reveals_results.zip": (
        "https://download.pangaea.de/dataset/937075/files/"
        "LANDCLIMII.RV.results.JUN2021.zip"
    ),
    "landclim_ii_grid_cell_quality.xlsx": (
        "https://download.pangaea.de/dataset/937075/files/GC_quality_by_TW.xlsx"
    ),
    "landclim_ii_contributors.xlsx": (
        "https://download.pangaea.de/dataset/937075/files/"
        "LandClimII_contributors.xlsx"
    ),
    "landclim_ii_site_metadata.xlsx": (
        "https://download.pangaea.de/dataset/937075/files/LandClimII_metadata.xlsx"
    ),
    "landclim_ii_taxa_pft_ppe_fsp_values.csv": (
        "https://download.pangaea.de/dataset/937075/files/"
        "Taxa_to_PFT_PPE_and_FSP_values.csv"
    ),
}
_LANDCLIM_ARCHIVE_FILENAME = "landclim_ii_reveals_results.zip"
_LANDCLIM_REQUIRED_ASSETS = frozenset(
    set(_LANDCLIM_ASSET_DATASET_IDS) - {"landclim_ii_contributors.xlsx"}
)


class LandClimRawReceiptError(ValueError):
    """Raised when the governed LandClim raw receipt does not match its assets."""


@dataclass(frozen=True)
class LandClimDataReport:
    output_dir: Path
    site_count: int
    grid_cell_count: int
    raw_manifest_path: Path
    normalized_sites_csv_path: Path
    normalized_sites_geojson_path: Path
    normalized_grid_geojson_path: Path
    normalized_temporal_grid_geojson_path: Path
    bibliography_path: Path
    review_path: Path
    summary_path: Path


def collect_landclim_data(
    output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
    bbox: tuple[float, float, float, float],
) -> LandClimDataReport:
    """Download and normalize LandClim PANGAEA datasets under data/landclim."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    raw_assets = download_landclim_raw_assets(raw_dir)
    raw_paths = raw_assets.paths
    site_records = build_landclim_site_records(
        raw_paths, bbox=bbox, country_boundaries=country_boundaries
    )
    grid_geojson = build_landclim_grid_geojson(
        raw_paths, bbox=bbox, country_boundaries=country_boundaries
    )
    temporal_grid_geojson = build_landclim_temporal_grid_geojson(
        raw_paths, bbox=bbox, country_boundaries=country_boundaries
    )

    raw_manifest_path = raw_dir / "landclim_sources.json"
    write_json(
        raw_manifest_path,
        _build_landclim_raw_receipt(
            raw_paths,
            raw_assets.asset_urls,
            generated_on=str(date.today()),
        ),
    )
    validate_landclim_raw_receipt(raw_dir)

    normalized_sites_csv_path = LANDCLIM_SITE_CSV.source_path_under(output_root)
    normalized_sites_geojson_path = LANDCLIM_SITE_GEOJSON.source_path_under(output_root)
    normalized_grid_geojson_path = LANDCLIM_GRID_GEOJSON.source_path_under(output_root)
    normalized_temporal_grid_geojson_path = (
        LANDCLIM_TEMPORAL_GRID_GEOJSON.source_path_under(output_root)
    )
    bibliography_path = LANDCLIM_BIBLIOGRAPHY_JSON.source_path_under(output_root)
    summary_path = normalized_dir / "landclim_summary.json"
    write_context_points_csv(normalized_sites_csv_path, site_records)
    write_context_points_geojson(normalized_sites_geojson_path, site_records)
    write_json(normalized_grid_geojson_path, grid_geojson)
    write_json(normalized_temporal_grid_geojson_path, temporal_grid_geojson)
    bibliography = build_landclim_bibliography()
    write_json(bibliography_path, bibliography)
    review_path = write_landclim_review_outputs(
        output_root,
        records=site_records,
        temporal_grid_geojson=temporal_grid_geojson,
        bibliography=bibliography,
    )
    write_json(
        summary_path,
        {
            "generated_on": str(date.today()),
            "source": "LandClim",
            "site_count": len(site_records),
            "grid_cell_count": len(feature_list(grid_geojson)),
            "temporal_grid_feature_count": len(feature_list(temporal_grid_geojson)),
            "numeric_site_interval_count": sum(
                1
                for record in site_records
                if record.time_start_bp is not None and record.time_end_bp is not None
            ),
            "bibliography_dataset_count": len(LANDCLIM_DATASET_METADATA),
            "site_layer_key": LANDCLIM_SITE_LAYER_KEY,
            "grid_layer_key": LANDCLIM_GRID_LAYER_KEY,
            "temporal_grid_layer_key": LANDCLIM_TEMPORAL_GRID_LAYER_KEY,
        },
    )

    return LandClimDataReport(
        output_dir=output_root,
        site_count=len(site_records),
        grid_cell_count=len(feature_list(grid_geojson)),
        raw_manifest_path=raw_manifest_path,
        normalized_sites_csv_path=normalized_sites_csv_path,
        normalized_sites_geojson_path=normalized_sites_geojson_path,
        normalized_grid_geojson_path=normalized_grid_geojson_path,
        normalized_temporal_grid_geojson_path=normalized_temporal_grid_geojson_path,
        bibliography_path=bibliography_path,
        review_path=review_path,
        summary_path=summary_path,
    )


def materialize_landclim_repository_surfaces(data_root: Path) -> LandClimDataReport:
    """Refresh normalized LandClim surfaces from the checked-in raw capture."""
    data_root = Path(data_root)
    output_root = data_root / "landclim"
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    validate_landclim_raw_receipt(raw_dir)
    normalized_dir.mkdir(parents=True, exist_ok=True)
    raw_paths = {
        path.name: path
        for path in raw_dir.iterdir()
        if path.is_file() and path.name != "landclim_sources.json"
    }
    country_boundaries = load_repository_country_boundaries(data_root)
    site_records = build_landclim_site_records(
        raw_paths,
        bbox=NORDIC_BBOX,
        country_boundaries=country_boundaries,
    )
    grid_geojson = build_landclim_grid_geojson(
        raw_paths,
        bbox=NORDIC_BBOX,
        country_boundaries=country_boundaries,
    )
    temporal_grid_geojson = build_landclim_temporal_grid_geojson(
        raw_paths,
        bbox=NORDIC_BBOX,
        country_boundaries=country_boundaries,
    )
    normalized_sites_csv_path = LANDCLIM_SITE_CSV.path_under(data_root)
    normalized_sites_geojson_path = LANDCLIM_SITE_GEOJSON.path_under(data_root)
    normalized_grid_geojson_path = LANDCLIM_GRID_GEOJSON.path_under(data_root)
    normalized_temporal_grid_geojson_path = LANDCLIM_TEMPORAL_GRID_GEOJSON.path_under(
        data_root
    )
    bibliography_path = LANDCLIM_BIBLIOGRAPHY_JSON.path_under(data_root)
    summary_path = normalized_dir / "landclim_summary.json"
    write_context_points_csv(normalized_sites_csv_path, site_records)
    write_context_points_geojson(normalized_sites_geojson_path, site_records)
    write_json(normalized_grid_geojson_path, grid_geojson)
    write_json(normalized_temporal_grid_geojson_path, temporal_grid_geojson)
    bibliography = build_landclim_bibliography()
    write_json(bibliography_path, bibliography)
    review_path = write_landclim_review_outputs(
        output_root,
        records=site_records,
        temporal_grid_geojson=temporal_grid_geojson,
        bibliography=bibliography,
    )
    write_json(
        summary_path,
        {
            "generated_on": str(date.today()),
            "source": "LandClim",
            "site_count": len(site_records),
            "numeric_site_interval_count": sum(
                1
                for record in site_records
                if record.time_start_bp is not None and record.time_end_bp is not None
            ),
            "grid_cell_count": len(feature_list(grid_geojson)),
            "temporal_grid_feature_count": len(feature_list(temporal_grid_geojson)),
            "bibliography_dataset_count": len(LANDCLIM_DATASET_METADATA),
            "site_layer_key": LANDCLIM_SITE_LAYER_KEY,
            "grid_layer_key": LANDCLIM_GRID_LAYER_KEY,
            "temporal_grid_layer_key": LANDCLIM_TEMPORAL_GRID_LAYER_KEY,
        },
    )
    return LandClimDataReport(
        output_dir=output_root,
        site_count=len(site_records),
        grid_cell_count=len(feature_list(grid_geojson)),
        raw_manifest_path=raw_dir / "landclim_sources.json",
        normalized_sites_csv_path=normalized_sites_csv_path,
        normalized_sites_geojson_path=normalized_sites_geojson_path,
        normalized_grid_geojson_path=normalized_grid_geojson_path,
        normalized_temporal_grid_geojson_path=normalized_temporal_grid_geojson_path,
        bibliography_path=bibliography_path,
        review_path=review_path,
        summary_path=summary_path,
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
    raw_dir = Path(raw_dir)
    if not raw_dir.is_dir() or raw_dir.is_symlink():
        raise LandClimRawReceiptError(
            "LandClim raw directory must be an existing non-symlink directory"
        )
    receipt_path = raw_dir / "landclim_sources.json"
    if not receipt_path.is_file() or receipt_path.is_symlink():
        raise LandClimRawReceiptError("LandClim raw receipt is missing or unsafe")
    try:
        loaded = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LandClimRawReceiptError("LandClim raw receipt is unreadable") from error
    if not isinstance(loaded, dict):
        raise LandClimRawReceiptError("LandClim raw receipt must be a JSON object")
    receipt: dict[str, object] = loaded
    if receipt.get("schema_version") != "landclim-raw-receipt.v1":
        raise LandClimRawReceiptError("Unsupported LandClim raw receipt schema")
    if receipt.get("source") != "LandClim":
        raise LandClimRawReceiptError("LandClim raw receipt source is invalid")

    assets = _object_rows(receipt.get("assets"), field_name="assets")
    asset_count = receipt.get("asset_count")
    if not isinstance(asset_count, int) or isinstance(asset_count, bool):
        raise LandClimRawReceiptError("LandClim raw receipt asset_count is invalid")
    if asset_count != len(assets):
        raise LandClimRawReceiptError("LandClim raw receipt asset_count is invalid")
    asset_by_filename: dict[str, dict[str, object]] = {}
    for asset in assets:
        filename = _safe_receipt_filename(asset.get("filename"))
        if filename in asset_by_filename:
            raise LandClimRawReceiptError(
                f"Duplicate LandClim raw receipt asset: {filename}"
            )
        asset_by_filename[filename] = asset

    actual_entries = {
        path.name: path
        for path in raw_dir.iterdir()
        if path.name != receipt_path.name
    }
    declared_names = set(asset_by_filename)
    missing_required = sorted(_LANDCLIM_REQUIRED_ASSETS - declared_names)
    unknown_declared = sorted(declared_names - set(_LANDCLIM_ASSET_DATASET_IDS))
    if missing_required or unknown_declared:
        raise LandClimRawReceiptError(
            "LandClim governed asset set is invalid; "
            f"missing_required={missing_required}; unknown={unknown_declared}"
        )
    actual_names = set(actual_entries)
    if declared_names != actual_names:
        missing = sorted(declared_names - actual_names)
        unlisted = sorted(actual_names - declared_names)
        raise LandClimRawReceiptError(
            f"LandClim raw asset inventory mismatch; missing={missing}; unlisted={unlisted}"
        )

    dataset_by_file = _validate_landclim_receipt_datasets(receipt, declared_names)
    for filename in sorted(declared_names):
        path = actual_entries[filename]
        if not path.is_file() or path.is_symlink():
            raise LandClimRawReceiptError(
                f"LandClim raw asset is missing or unsafe: {filename}"
            )
        asset = asset_by_filename[filename]
        expected_dataset_id = _LANDCLIM_ASSET_DATASET_IDS.get(filename)
        if expected_dataset_id is None:
            raise LandClimRawReceiptError(
                f"LandClim raw receipt contains an unknown asset: {filename}"
            )
        dataset_id = asset.get("dataset_id")
        expected_doi = LANDCLIM_DATASET_METADATA[expected_dataset_id]["doi"]
        if (
            dataset_id != expected_dataset_id
            or dataset_by_file.get(filename) != expected_dataset_id
            or asset.get("dataset_doi") != expected_doi
        ):
            raise LandClimRawReceiptError(
                f"LandClim dataset/DOI association is invalid for {filename}"
            )
        source_url = asset.get("source_url")
        if source_url != _LANDCLIM_ASSET_SOURCE_URLS[filename]:
            raise LandClimRawReceiptError(
                f"LandClim source URL is invalid for {filename}"
            )
        payload = path.read_bytes()
        size_bytes = asset.get("size_bytes")
        sha256 = asset.get("sha256")
        if not isinstance(size_bytes, int) or isinstance(size_bytes, bool):
            raise LandClimRawReceiptError(
                f"LandClim raw asset size is invalid for {filename}"
            )
        if size_bytes != len(payload):
            raise LandClimRawReceiptError(
                f"LandClim raw asset size mismatch for {filename}"
            )
        if sha256 != hashlib.sha256(payload).hexdigest():
            raise LandClimRawReceiptError(
                f"LandClim raw asset digest mismatch for {filename}"
            )

    archive_rows = _object_rows(
        receipt.get("archive_summaries"), field_name="archive_summaries"
    )
    expected_archive_names = (
        {_LANDCLIM_ARCHIVE_FILENAME}
        if _LANDCLIM_ARCHIVE_FILENAME in declared_names
        else set()
    )
    archive_by_filename = {
        _safe_receipt_filename(row.get("filename")): row for row in archive_rows
    }
    if len(archive_by_filename) != len(archive_rows):
        raise LandClimRawReceiptError("Duplicate LandClim archive summary")
    if set(archive_by_filename) != expected_archive_names:
        raise LandClimRawReceiptError("LandClim archive summary inventory is invalid")
    for filename, expected_summary in archive_by_filename.items():
        actual_summary = _build_landclim_archive_receipt(actual_entries[filename])
        if expected_summary != actual_summary:
            raise LandClimRawReceiptError(
                f"LandClim archive member summary mismatch for {filename}"
            )
    return receipt


def _build_landclim_raw_receipt(
    raw_paths: dict[str, Path],
    asset_urls: dict[str, str],
    *,
    generated_on: str,
) -> dict[str, object]:
    summaries = build_landclim_raw_asset_summaries(raw_paths, asset_urls)
    assets = []
    for summary in summaries:
        filename = str(summary["filename"])
        dataset_id = _LANDCLIM_ASSET_DATASET_IDS[filename]
        assets.append(
            {
                "filename": filename,
                "dataset_id": dataset_id,
                "dataset_doi": LANDCLIM_DATASET_METADATA[dataset_id]["doi"],
                "source_url": summary["source_url"],
                "size_bytes": summary["size_bytes"],
                "sha256": summary["sha256"],
            }
        )
    datasets = []
    for dataset_id in LANDCLIM_DATASET_METADATA:
        files = sorted(
            filename
            for filename in raw_paths
            if _LANDCLIM_ASSET_DATASET_IDS.get(filename) == dataset_id
        )
        if not files:
            continue
        metadata = LANDCLIM_DATASET_METADATA[dataset_id]
        dataset: dict[str, object] = {
            "dataset_id": dataset_id,
            "doi": metadata["doi"],
            "source_url": metadata["doi"],
            "label": metadata["label"],
            "files": files,
        }
        datasets.append(dataset)
    archive_summaries = []
    archive_path = raw_paths.get(_LANDCLIM_ARCHIVE_FILENAME)
    if archive_path is not None:
        archive_summaries.append(_build_landclim_archive_receipt(archive_path))
    return {
        "schema_version": "landclim-raw-receipt.v1",
        "generated_on": generated_on,
        "source": "LandClim",
        "asset_count": len(assets),
        "datasets": datasets,
        "assets": assets,
        "archive_summaries": archive_summaries,
    }


def _validate_landclim_receipt_datasets(
    receipt: dict[str, object], declared_names: set[str]
) -> dict[str, str]:
    dataset_rows = _object_rows(receipt.get("datasets"), field_name="datasets")
    dataset_by_file: dict[str, str] = {}
    seen_dataset_ids: set[str] = set()
    for dataset in dataset_rows:
        dataset_id = dataset.get("dataset_id")
        if not isinstance(dataset_id, str) or dataset_id not in LANDCLIM_DATASET_METADATA:
            raise LandClimRawReceiptError("LandClim receipt dataset_id is invalid")
        if dataset_id in seen_dataset_ids:
            raise LandClimRawReceiptError(
                f"Duplicate LandClim receipt dataset: {dataset_id}"
            )
        seen_dataset_ids.add(dataset_id)
        metadata = LANDCLIM_DATASET_METADATA[dataset_id]
        if (
            dataset.get("doi") != metadata["doi"]
            or dataset.get("source_url") != metadata["doi"]
            or dataset.get("label") != metadata["label"]
        ):
            raise LandClimRawReceiptError(
                f"LandClim dataset authority is invalid for {dataset_id}"
            )
        files = dataset.get("files")
        if not isinstance(files, list) or not files:
            raise LandClimRawReceiptError(
                f"LandClim dataset files are invalid for {dataset_id}"
            )
        for value in files:
            filename = _safe_receipt_filename(value)
            if filename in dataset_by_file:
                raise LandClimRawReceiptError(
                    f"LandClim asset belongs to multiple datasets: {filename}"
                )
            dataset_by_file[filename] = dataset_id
    if set(dataset_by_file) != declared_names:
        raise LandClimRawReceiptError(
            "LandClim dataset file inventory does not cover every declared asset"
        )
    return dataset_by_file


def _build_landclim_archive_receipt(path: Path) -> dict[str, object]:
    try:
        structure = inspect_landclim_ii_archive(path)
        with ZipFile(path) as archive:
            infos = sorted(
                (info for info in archive.infolist() if not info.is_dir()),
                key=lambda info: info.filename,
            )
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                raise LandClimRawReceiptError(
                    "LandClim II archive contains duplicate member paths"
                )
            members = []
            uncompressed_size_bytes = 0
            for info in infos:
                member_path = PurePosixPath(info.filename)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise LandClimRawReceiptError(
                        "LandClim II archive contains an unsafe member path"
                    )
                payload = archive.read(info)
                uncompressed_size_bytes += len(payload)
                members.append(
                    {
                        "path": info.filename,
                        "size_bytes": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                )
    except (BadZipFile, OSError) as error:
        raise LandClimRawReceiptError("LandClim II archive is unreadable") from error
    member_payload = json.dumps(
        members,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "filename": path.name,
        "member_count": len(members),
        "uncompressed_size_bytes": uncompressed_size_bytes,
        "member_manifest_sha256": hashlib.sha256(member_payload).hexdigest(),
        "member_digest_basis": "sha256-canonical-json-path-size-sha256",
        "mean_file_count": structure["mean_file_count"],
        "standard_error_file_count": structure["standard_error_file_count"],
        "time_windows": structure["time_windows"],
    }


def _object_rows(value: object, *, field_name: str) -> list[dict[str, object]]:
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise LandClimRawReceiptError(
            f"LandClim raw receipt {field_name} must be a list of objects"
        )
    return value


def _safe_receipt_filename(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise LandClimRawReceiptError("LandClim raw receipt filename is invalid")
    path = PurePosixPath(value)
    if path.is_absolute() or len(path.parts) != 1 or path.name != value:
        raise LandClimRawReceiptError(
            f"Unsafe LandClim raw receipt filename: {value}"
        )
    return value


__all__ = [
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
