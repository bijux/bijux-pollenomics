"""Reconcile retained Neotoma inventory selection with download request scope."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.sources.boundaries.store import (
    load_repository_country_boundaries,
)
from bijux_pollenomics.collection.sources.neotoma.collection import (
    build_neotoma_bbox_geojson,
    extract_neotoma_dataset_ids,
    filter_neotoma_dataset_inventory_rows,
)

INVENTORY = Path("data/neotoma/raw/neotoma_pollen_dataset_inventory.json")
DOWNLOAD_MANIFEST = Path(
    "data/neotoma/raw/neotoma_pollen_dataset_downloads/manifest.json"
)
BOUNDARY_ROOT = Path("data/boundaries/raw")
BBOX = (4.0, 54.0, 35.0, 72.0)


def _rows(value: object, label: str) -> list[dict[str, object]]:
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"Neotoma {label} must contain object rows")
    return value


def _row_id(row: dict[str, object], queried_index: int) -> dict[str, object]:
    site = row.get("site")
    if not isinstance(site, dict) or not isinstance(site.get("siteid"), int):
        raise ValueError(f"Neotoma inventory row {queried_index} lacks siteid")
    return {
        "queried_row_index": queried_index,
        "site_id": site["siteid"],
        "dataset_ids": extract_neotoma_dataset_ids([row]),
    }


def reconcile(
    inventory: dict[str, object],
    manifest: dict[str, object],
    selected_now: list[dict[str, object]],
) -> dict[str, object]:
    """Check retained JSON rows and IDs without claiming original HTTP custody."""
    if (
        inventory.get("endpoint") != "https://api.neotomadb.org/v2.0/data/datasets"
        or inventory.get("datasettype") != "pollen"
        or inventory.get("loc") != build_neotoma_bbox_geojson(BBOX)
        or manifest.get("endpoint_template")
        != "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}"
    ):
        raise ValueError(
            "Neotoma stored acquisition metadata differs from the consumer"
        )
    queried = _rows(inventory.get("rows"), "queried inventory")
    retained = _rows(inventory.get("retained_rows"), "retained inventory")
    if inventory.get("queried_row_count") != len(queried) or inventory.get(
        "retained_row_count"
    ) != len(retained):
        raise ValueError("Neotoma inventory row counts differ from retained JSON")
    retained_indices: list[int] = []
    cursor = 0
    for row in retained:
        try:
            index = queried.index(row, cursor)
        except ValueError as exc:
            raise ValueError(
                "Neotoma retained inventory is not an ordered lossless subset of queried rows"
            ) from exc
        retained_indices.append(index)
        cursor = index + 1
    requested_ids = extract_neotoma_dataset_ids(retained)
    if (
        inventory.get("retained_dataset_count") != len(requested_ids)
        or manifest.get("requested_dataset_count") != len(requested_ids)
        or manifest.get("downloaded_dataset_count") != len(requested_ids)
        or manifest.get("requested_dataset_ids") != requested_ids
        or manifest.get("downloaded_dataset_ids") != requested_ids
    ):
        raise ValueError("Neotoma retained inventory IDs differ from download manifest")
    current_indices: list[int] = []
    cursor = 0
    for row in selected_now:
        try:
            index = queried.index(row, cursor)
        except ValueError as exc:
            raise ValueError(
                "Current Neotoma selector returned an unqueried row"
            ) from exc
        current_indices.append(index)
        cursor = index + 1
    retained_set = set(retained_indices)
    current_set = set(current_indices)
    return {
        "queried_row_count": len(queried),
        "retained_row_count": len(retained),
        "requested_dataset_count": len(requested_ids),
        "retained_rows_are_ordered_copies_of_queried_json_objects": True,
        "retained_dataset_ids_match_manifest_request_and_download_ids": True,
        "current_selector_row_count": len(selected_now),
        "current_selector_dataset_count": len(
            extract_neotoma_dataset_ids(selected_now)
        ),
        "retained_only_rows": [
            _row_id(queried[index], index)
            for index in sorted(retained_set - current_set)
        ],
        "current_only_rows": [
            _row_id(queried[index], index)
            for index in sorted(current_set - retained_set)
        ],
    }


def build(repository: Path) -> dict[str, Any]:
    """Bind the retained inventory and request manifest to current selector inputs."""
    inputs = [INVENTORY, DOWNLOAD_MANIFEST]
    inputs.extend(
        BOUNDARY_ROOT / f"{country}.geojson"
        for country in ("denmark", "finland", "norway", "sweden")
    )
    hashes = {
        path.as_posix(): sha256((repository / path).read_bytes()).hexdigest()
        for path in inputs
    }
    inventory = json.loads((repository / INVENTORY).read_bytes())
    manifest = json.loads((repository / DOWNLOAD_MANIFEST).read_bytes())
    selected_now = filter_neotoma_dataset_inventory_rows(
        _rows(inventory.get("rows"), "queried inventory"),
        bbox=BBOX,
        country_boundaries=load_repository_country_boundaries(repository / "data"),
    )
    return {
        "schema_version": "neotoma-acquisition-scope.v1",
        "source_family": "neotoma",
        "inputs_sha256": hashes,
        "retained_json_reconciliation": reconcile(inventory, manifest, selected_now),
        "original_http_receipt_status": "unavailable",
        "missing_original_authority": (
            "Original GET /datasets request and response bytes with exact datasettype, "
            "loc, limit and offset for every page; response status, timestamp, total "
            "or termination evidence and byte digest; plus each of 209 original "
            "GET /downloads/{datasetid} response byte digests. The retained JSON "
            "files and nine-part archive are producer-serialized objects."
        ),
    }


def main() -> None:
    """Write the retained Neotoma acquisition-scope receipt under artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent repository artifact output required")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build(repository), indent=2) + "\n")


if __name__ == "__main__":
    main()
