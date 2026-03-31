from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable

from ....core.files import write_json

__all__ = ["build_neotoma_download_archive_parts", "write_neotoma_download_archive"]


def build_neotoma_download_archive_parts(
    download_rows: Iterable[dict[str, object]],
    *,
    rows_per_part: int,
    extract_neotoma_download_dataset_ids_fn,
) -> list[dict[str, object]]:
    """Split large Neotoma download payloads into stable part files."""
    if rows_per_part < 1:
        raise ValueError("rows_per_part must be at least 1")

    rows = list(download_rows)
    part_count = (len(rows) + rows_per_part - 1) // rows_per_part
    parts: list[dict[str, object]] = []
    for index, start in enumerate(range(0, len(rows), rows_per_part), start=1):
        part_rows = rows[start:start + rows_per_part]
        part_dataset_ids = extract_neotoma_download_dataset_ids_fn(part_rows)
        parts.append(
            {
                "filename": f"part-{index:03d}.json",
                "part_number": index,
                "part_count": part_count,
                "row_count": len(part_rows),
                "downloaded_dataset_count": len(part_dataset_ids),
                "downloaded_dataset_ids": part_dataset_ids,
                "rows": part_rows,
            }
        )
    return parts


def write_neotoma_download_archive(
    raw_dir: Path,
    *,
    requested_dataset_ids: Iterable[int],
    downloaded_dataset_ids: Iterable[int],
    download_rows: Iterable[dict[str, object]],
    rows_per_part: int,
    neotoma_data_url: str,
    neotoma_datasettype: str,
    neotoma_download_archive_dirname: str,
    extract_neotoma_download_dataset_ids_fn,
) -> Path:
    """Write the full Neotoma dataset downloads into a chunked archive directory."""
    archive_dir = Path(raw_dir) / neotoma_download_archive_dirname
    archive_dir.mkdir(parents=True, exist_ok=True)
    rows = list(download_rows)

    requested_ids = sorted({int(dataset_id) for dataset_id in requested_dataset_ids})
    returned_ids = sorted({int(dataset_id) for dataset_id in downloaded_dataset_ids})
    parts = build_neotoma_download_archive_parts(
        rows,
        rows_per_part=rows_per_part,
        extract_neotoma_download_dataset_ids_fn=extract_neotoma_download_dataset_ids_fn,
    )

    manifest_parts: list[dict[str, object]] = []
    for part in parts:
        filename = str(part["filename"])
        write_json(
            archive_dir / filename,
            {
                "generated_on": str(date.today()),
                "source": "Neotoma",
                "endpoint_template": f"{neotoma_data_url}/downloads/{{datasetid}}",
                "datasettype": neotoma_datasettype,
                "part_number": part["part_number"],
                "part_count": part["part_count"],
                "row_count": part["row_count"],
                "downloaded_dataset_count": part["downloaded_dataset_count"],
                "downloaded_dataset_ids": part["downloaded_dataset_ids"],
                "rows": part["rows"],
            },
        )
        manifest_parts.append(
            {
                "filename": filename,
                "part_number": part["part_number"],
                "row_count": part["row_count"],
                "downloaded_dataset_count": part["downloaded_dataset_count"],
                "downloaded_dataset_ids": part["downloaded_dataset_ids"],
            }
        )

    manifest_path = archive_dir / "manifest.json"
    write_json(
        manifest_path,
        {
            "generated_on": str(date.today()),
            "source": "Neotoma",
            "archive_dir": str(archive_dir),
            "endpoint_template": f"{neotoma_data_url}/downloads/{{datasetid}}",
            "datasettype": neotoma_datasettype,
            "requested_dataset_count": len(requested_ids),
            "requested_dataset_ids": requested_ids,
            "downloaded_dataset_count": len(returned_ids),
            "downloaded_dataset_ids": returned_ids,
            "row_count": len(rows),
            "rows_per_part": rows_per_part,
            "part_count": len(parts),
            "parts": manifest_parts,
        },
    )
    return manifest_path
