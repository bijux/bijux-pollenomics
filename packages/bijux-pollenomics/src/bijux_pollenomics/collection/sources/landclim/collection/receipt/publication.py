"""Construction of governed LandClim raw receipts."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ...catalog import LANDCLIM_DATASET_METADATA
from ..authority import LANDCLIM_ARCHIVE_FILENAME, LANDCLIM_ASSET_DATASET_IDS

AssetSummaryBuilder = Callable[
    [dict[str, Path], dict[str, str]], list[dict[str, object]]
]
ArchiveReceiptBuilder = Callable[[Path], dict[str, object]]


def build_landclim_raw_receipt(
    raw_paths: dict[str, Path],
    asset_urls: dict[str, str],
    *,
    generated_on: str,
    summary_builder: AssetSummaryBuilder,
    archive_receipt_builder: ArchiveReceiptBuilder,
) -> dict[str, object]:
    """Bind raw assets to source authorities and deterministic identities."""
    summaries = summary_builder(raw_paths, asset_urls)
    assets = []
    for summary in summaries:
        filename = str(summary["filename"])
        dataset_id = LANDCLIM_ASSET_DATASET_IDS[filename]
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
            if LANDCLIM_ASSET_DATASET_IDS.get(filename) == dataset_id
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
    archive_path = raw_paths.get(LANDCLIM_ARCHIVE_FILENAME)
    if archive_path is not None:
        archive_summaries.append(archive_receipt_builder(archive_path))
    return {
        "schema_version": "landclim-raw-receipt.v1",
        "generated_on": generated_on,
        "source": "LandClim",
        "asset_count": len(assets),
        "datasets": datasets,
        "assets": assets,
        "archive_summaries": archive_summaries,
    }
