from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .models import _RawArchive


def load_raw_archive(
    raw_archive_root: Path,
    *,
    expected_part_count: int,
    raw_source: str,
    archive_label: str,
    endpoint: str,
    dataset_type: str,
    sha256_pattern: Any,
    validate_directory: Callable[[Path, str], Path],
    read_file: Callable[[Path], bytes],
    parse_object: Callable[[bytes, Path], dict[str, object]],
    parse_mapping: Callable[[object, str], Mapping[str, object]],
    parse_positive_integer: Callable[[object, str], int],
    parse_non_negative_integer: Callable[[object, str], int],
    parse_integer_list: Callable[[object, str], list[int]],
    expect_equal: Callable[[object, object, str], None],
    download_dataset_id: Callable[[Mapping[str, object], str], int],
    canonical_digest: Callable[[object], str],
) -> _RawArchive:
    root = validate_directory(raw_archive_root, "Neotoma raw archive")
    manifest_path = root / "manifest.json"
    manifest_bytes = read_file(manifest_path)
    manifest = parse_object(manifest_bytes, manifest_path)
    expected_manifest = {
        "source": raw_source,
        "archive_dir": archive_label,
        "endpoint_template": endpoint,
        "datasettype": dataset_type,
        "part_count": expected_part_count,
    }
    for field, expected in expected_manifest.items():
        expect_equal(manifest.get(field), expected, f"raw manifest {field}")

    parts = manifest.get("parts")
    if not isinstance(parts, list) or len(parts) != expected_part_count:
        raise ValueError("Raw manifest must contain exactly nine part records")
    rows_per_part = parse_positive_integer(
        manifest.get("rows_per_part"), "rows_per_part"
    )
    expected_files = {"manifest.json"}
    all_rows: list[dict[str, object]] = []
    all_dataset_ids: list[int] = []
    digest_records: list[dict[str, object]] = []
    for part_number, record_value in enumerate(parts, start=1):
        record = parse_mapping(record_value, f"raw part {part_number}")
        filename = f"part-{part_number:03d}.json"
        expect_equal(
            record.get("filename"), filename, f"raw part {part_number} filename"
        )
        expect_equal(
            record.get("part_number"), part_number, f"raw part {part_number} number"
        )
        if filename in expected_files:
            raise ValueError(f"Duplicate raw archive path: {filename}")
        expected_files.add(filename)
        part_path = root / filename
        part_bytes = read_file(part_path)
        part_digest = hashlib.sha256(part_bytes).hexdigest()
        recorded_digest = record.get("sha256")
        if recorded_digest is not None:
            if not isinstance(recorded_digest, str) or not sha256_pattern.fullmatch(
                recorded_digest
            ):
                raise ValueError(f"Invalid SHA-256 in raw manifest for {filename}")
            if recorded_digest != part_digest:
                raise ValueError(f"Raw part SHA-256 mismatch: {filename}")
        payload = parse_object(part_bytes, part_path)
        for field, expected in (
            ("generated_on", manifest.get("generated_on")),
            ("source", raw_source),
            ("endpoint_template", endpoint),
            ("datasettype", dataset_type),
            ("part_number", part_number),
            ("part_count", expected_part_count),
        ):
            expect_equal(payload.get(field), expected, f"{filename} {field}")
        rows = payload.get("rows")
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise ValueError(f"Raw part rows must contain objects: {filename}")
        row_count = parse_non_negative_integer(
            record.get("row_count"), f"{filename} rows"
        )
        expect_equal(payload.get("row_count"), row_count, f"{filename} row_count")
        if len(rows) != row_count or row_count > rows_per_part:
            raise ValueError(f"Raw part row-count mismatch: {filename}")
        part_ids = parse_integer_list(
            payload.get("downloaded_dataset_ids"), f"{filename} dataset IDs"
        )
        manifest_part_ids = parse_integer_list(
            record.get("downloaded_dataset_ids"), f"raw manifest {filename} dataset IDs"
        )
        if part_ids != sorted(part_ids) or len(part_ids) != len(set(part_ids)):
            raise ValueError(
                f"Raw part dataset IDs are not unique and sorted: {filename}"
            )
        expect_equal(manifest_part_ids, part_ids, f"{filename} manifest dataset IDs")
        expect_equal(
            payload.get("downloaded_dataset_count"), len(part_ids), f"{filename} count"
        )
        expect_equal(
            record.get("downloaded_dataset_count"),
            len(part_ids),
            f"{filename} manifest count",
        )
        row_ids = [download_dataset_id(row, filename) for row in rows]
        expect_equal(row_ids, part_ids, f"{filename} row dataset IDs")
        all_rows.extend(rows)
        all_dataset_ids.extend(part_ids)
        digest_records.append(
            {"filename": filename, "sha256": part_digest, "row_count": row_count}
        )

    actual_files = {
        path.name for path in root.iterdir() if path.is_file() or path.is_symlink()
    }
    if actual_files != expected_files:
        raise ValueError(
            "Raw archive files do not exactly match its nine-part manifest"
        )
    if len(all_dataset_ids) != len(set(all_dataset_ids)):
        raise ValueError("Raw archive contains duplicate downloaded dataset IDs")
    manifest_ids = parse_integer_list(
        manifest.get("downloaded_dataset_ids"), "manifest downloaded dataset IDs"
    )
    requested_ids = parse_integer_list(
        manifest.get("requested_dataset_ids"), "manifest requested dataset IDs"
    )
    if manifest_ids != sorted(manifest_ids) or requested_ids != sorted(requested_ids):
        raise ValueError("Raw manifest dataset IDs must be sorted")
    expect_equal(all_dataset_ids, manifest_ids, "raw aggregate dataset IDs")
    expect_equal(
        manifest.get("downloaded_dataset_count"), len(manifest_ids), "downloaded count"
    )
    expect_equal(
        manifest.get("requested_dataset_count"), len(requested_ids), "request count"
    )
    expect_equal(manifest.get("row_count"), len(all_rows), "raw aggregate row count")
    if requested_ids != manifest_ids:
        raise ValueError("Raw archive does not provide every requested dataset")
    identity = {
        "schema": "neotoma-raw-content-identity.v1",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "parts": digest_records,
    }
    return _RawArchive(
        rows=tuple(all_rows),
        source_snapshot_id=f"sha256:{canonical_digest(identity)}",
        part_digests=tuple(str(record["sha256"]) for record in digest_records),
    )
