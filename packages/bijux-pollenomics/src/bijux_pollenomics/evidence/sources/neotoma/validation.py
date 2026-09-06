"""Validate governed Neotoma relational materializations."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping
from pathlib import Path, PurePosixPath

from .contract import (
    COUNTRY_CODES,
    COUNTRY_SURFACE_COUNT_FIELDS,
    MATERIALIZATION_MANIFEST_SCHEMA_VERSION,
    PART_SCHEMA_VERSION,
    RECONCILIATION_SCHEMA_VERSION,
    RELATIONAL_SNAPSHOT_SCHEMA_VERSION,
    SURFACE_ID_FIELDS,
    accumulate_country_partition,
    accumulate_site_attribution,
    expect_equal,
    materialization_digest,
    non_negative_integer,
    required_text,
    surface_schema_version,
    validate_reconciliation_counts,
)

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


def validate_neotoma_relational_materialization(
    output_root: Path,
) -> dict[str, object]:
    """Validate schemas, counts, paths, ordering, and all published digests."""
    root = Path(output_root)
    if not root.is_absolute():
        raise ValueError("Neotoma materialization path must be absolute")
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"Neotoma materialization root is not a directory: {root}")
    manifest_path = root / "manifest.json"
    manifest = _read_json_object(manifest_path)
    expect_equal(
        manifest.get("schema_version"),
        MATERIALIZATION_MANIFEST_SCHEMA_VERSION,
        "manifest schema_version",
    )
    expect_equal(
        manifest.get("relational_snapshot_schema_version"),
        RELATIONAL_SNAPSHOT_SCHEMA_VERSION,
        "relational snapshot schema_version",
    )
    expect_equal(manifest.get("source_family"), "neotoma", "manifest source_family")
    source_snapshot_id = required_text(
        manifest.get("source_snapshot_id"), "manifest source_snapshot_id"
    )
    build_id = required_text(manifest.get("build_id"), "manifest build_id")
    rows_per_part = _positive_integer(
        manifest.get("rows_per_part"), "manifest rows_per_part"
    )
    surfaces = manifest.get("surfaces")
    if not isinstance(surfaces, Mapping) or set(surfaces) != set(SURFACE_ID_FIELDS):
        raise ValueError("Manifest surfaces do not match the Neotoma v2 surfaces")

    expected_files = {"manifest.json"}
    digest_records: list[dict[str, str]] = []
    surface_row_counts: dict[str, int] = {}
    country_partitions: dict[str, Counter[str]] = {}
    site_statuses: Counter[str] = Counter()
    site_eligibility: Counter[str] = Counter()
    for surface_name, id_field in SURFACE_ID_FIELDS.items():
        surface = surfaces.get(surface_name)
        if not isinstance(surface, Mapping):
            raise ValueError(f"Invalid surface manifest: {surface_name}")
        surface_schema = surface_schema_version(surface_name)
        expect_equal(
            surface.get("schema_version"),
            surface_schema,
            f"{surface_name} schema_version",
        )
        expect_equal(surface.get("id_field"), id_field, f"{surface_name} id_field")
        row_count = non_negative_integer(
            surface.get("row_count"), f"{surface_name} row_count"
        )
        surface_row_counts[surface_name] = row_count
        part_count = non_negative_integer(
            surface.get("part_count"), f"{surface_name} part_count"
        )
        parts = surface.get("parts")
        if not isinstance(parts, list) or len(parts) != part_count:
            raise ValueError(f"Invalid part count for surface {surface_name}")
        observed_rows = 0
        observed_ids: list[str] = []
        country_partition: Counter[str] | None = None
        if surface_name in COUNTRY_SURFACE_COUNT_FIELDS:
            country_partition = Counter(dict.fromkeys(COUNTRY_CODES, 0))
        for expected_number, part in enumerate(parts, start=1):
            if not isinstance(part, Mapping):
                raise ValueError(f"Invalid part manifest for surface {surface_name}")
            expect_equal(
                part.get("schema_version"),
                PART_SCHEMA_VERSION,
                f"{surface_name} part manifest schema_version",
            )
            expect_equal(
                part.get("surface_schema_version"),
                surface_schema,
                f"{surface_name} part manifest surface_schema_version",
            )
            expect_equal(
                part.get("part_number"),
                expected_number,
                f"{surface_name} part manifest part_number",
            )
            expected_relative_path = (
                f"surfaces/{surface_name}/part-{expected_number:05d}.json"
            )
            relative_path = _safe_relative_path(part.get("path"))
            expect_equal(
                relative_path,
                expected_relative_path,
                f"{surface_name} part path",
            )
            if relative_path in expected_files:
                raise ValueError(f"Duplicate materialization path: {relative_path}")
            expected_files.add(relative_path)
            part_path = root.joinpath(*PurePosixPath(relative_path).parts)
            digest = _validated_sha256(part.get("sha256"), relative_path)
            actual_digest = hashlib.sha256(_read_regular_file(part_path)).hexdigest()
            if actual_digest != digest:
                raise ValueError(f"SHA-256 mismatch for {relative_path}")
            part_payload = _read_json_object(part_path)
            expect_equal(
                part_payload.get("schema_version"),
                PART_SCHEMA_VERSION,
                f"{relative_path} schema_version",
            )
            expect_equal(
                part_payload.get("surface_schema_version"),
                surface_schema,
                f"{relative_path} surface_schema_version",
            )
            expect_equal(
                part_payload.get("relational_snapshot_schema_version"),
                RELATIONAL_SNAPSHOT_SCHEMA_VERSION,
                f"{relative_path} snapshot schema_version",
            )
            expect_equal(
                part_payload.get("source_snapshot_id"),
                source_snapshot_id,
                f"{relative_path} source_snapshot_id",
            )
            expect_equal(
                part_payload.get("build_id"), build_id, f"{relative_path} build_id"
            )
            expect_equal(
                part_payload.get("surface"), surface_name, f"{relative_path} surface"
            )
            expect_equal(
                part_payload.get("part_number"),
                expected_number,
                f"{relative_path} part_number",
            )
            expect_equal(
                part_payload.get("part_count"),
                part_count,
                f"{relative_path} part_count",
            )
            rows = part_payload.get("rows")
            if not isinstance(rows, list):
                raise ValueError(f"Part rows must be a list: {relative_path}")
            part_row_count = non_negative_integer(
                part_payload.get("row_count"), f"{relative_path} row_count"
            )
            manifest_part_row_count = non_negative_integer(
                part.get("row_count"), f"{relative_path} manifest row_count"
            )
            expect_equal(
                manifest_part_row_count,
                part_row_count,
                f"{relative_path} manifest rows",
            )
            if part_row_count != len(rows):
                raise ValueError(f"Part row loss detected: {relative_path}")
            if part_row_count > rows_per_part:
                raise ValueError(f"Part exceeds rows_per_part: {relative_path}")
            row_ids = _row_ids(rows, id_field=id_field, surface_name=surface_name)
            if country_partition is not None:
                accumulate_country_partition(
                    rows,
                    surface_name=surface_name,
                    partition=country_partition,
                )
            if surface_name == "sites":
                accumulate_site_attribution(
                    rows,
                    statuses=site_statuses,
                    eligibility=site_eligibility,
                )
            if row_ids != sorted(row_ids):
                raise ValueError(f"Rows are not stably ordered: {relative_path}")
            observed_ids.extend(row_ids)
            observed_rows += part_row_count
            digest_records.append({"path": relative_path, "sha256": digest})
        if observed_rows != row_count:
            raise ValueError(f"Surface row loss detected: {surface_name}")
        if len(observed_ids) != len(set(observed_ids)):
            raise ValueError(f"Duplicate row identifiers in surface {surface_name}")
        if observed_ids != sorted(observed_ids):
            raise ValueError(f"Parts are not globally ordered: {surface_name}")
        if country_partition is not None:
            country_partitions[surface_name] = country_partition

    reconciliation = manifest.get("reconciliation")
    if not isinstance(reconciliation, Mapping):
        raise ValueError("Manifest reconciliation artifact is missing")
    expect_equal(
        reconciliation.get("schema_version"),
        RECONCILIATION_SCHEMA_VERSION,
        "reconciliation manifest schema_version",
    )
    reconciliation_path = _safe_relative_path(reconciliation.get("path"))
    expect_equal(reconciliation_path, "reconciliation.json", "reconciliation path")
    if reconciliation_path in expected_files:
        raise ValueError(f"Duplicate materialization path: {reconciliation_path}")
    expected_files.add(reconciliation_path)
    reconciliation_digest = _validated_sha256(
        reconciliation.get("sha256"), reconciliation_path
    )
    reconciliation_file = root / reconciliation_path
    actual_reconciliation_digest = hashlib.sha256(
        _read_regular_file(reconciliation_file)
    ).hexdigest()
    if actual_reconciliation_digest != reconciliation_digest:
        raise ValueError("SHA-256 mismatch for reconciliation.json")
    reconciliation_payload = _read_json_object(reconciliation_file)
    expect_equal(
        reconciliation_payload.get("schema_version"),
        RECONCILIATION_SCHEMA_VERSION,
        "reconciliation schema_version",
    )
    expect_equal(
        reconciliation_payload.get("relational_snapshot_schema_version"),
        RELATIONAL_SNAPSHOT_SCHEMA_VERSION,
        "reconciliation snapshot schema_version",
    )
    expect_equal(
        reconciliation_payload.get("source_family"),
        "neotoma",
        "reconciliation source_family",
    )
    expect_equal(
        reconciliation_payload.get("source_snapshot_id"),
        source_snapshot_id,
        "reconciliation source_snapshot_id",
    )
    expect_equal(
        reconciliation_payload.get("build_id"),
        build_id,
        "reconciliation build_id",
    )
    if not isinstance(reconciliation_payload.get("reconciliation"), Mapping):
        raise ValueError("Reconciliation payload is missing its accounting object")
    reconciliation_accounting = reconciliation_payload["reconciliation"]
    if not isinstance(reconciliation_accounting, Mapping):
        raise ValueError("Reconciliation payload is missing its accounting object")
    validate_reconciliation_counts(
        reconciliation_accounting,
        surface_row_counts,
        country_partitions=country_partitions,
        site_statuses=site_statuses,
        site_eligibility=site_eligibility,
    )
    digest_records.append(
        {"path": reconciliation_path, "sha256": reconciliation_digest}
    )
    expect_equal(
        manifest.get("materialization_sha256"),
        materialization_digest(digest_records),
        "materialization_sha256",
    )

    actual_files: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not allowed in materialization: {path}")
        if path.is_file():
            actual_files.add(path.relative_to(root).as_posix())
    if actual_files != expected_files:
        unexpected = sorted(actual_files - expected_files)
        missing = sorted(expected_files - actual_files)
        raise ValueError(
            f"Materialization file-set mismatch; unexpected={unexpected}, missing={missing}"
        )
    return copy.deepcopy(dict(manifest))


def _row_ids(rows: list[object], *, id_field: str, surface_name: str) -> list[str]:
    identifiers: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError(f"Non-object row in surface {surface_name}")
        identifiers.append(
            required_text(row.get(id_field), f"{surface_name}.{id_field}")
        )
    return identifiers


def _safe_relative_path(value: object) -> str:
    text = required_text(value, "manifest relative path")
    path = PurePosixPath(text)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"Unsafe materialization path: {text}")
    if path.as_posix() != text:
        raise ValueError(f"Non-canonical materialization path: {text}")
    return text


def _read_regular_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Materialization file is missing or unsafe: {path}")
    return path.read_bytes()


def _read_json_object(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(_read_regular_file(path))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"Invalid JSON materialization file: {path}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"Materialization JSON root must be an object: {path}")
    return payload


def _positive_integer(value: object, label: str) -> int:
    number = non_negative_integer(value, label)
    if number < 1:
        raise ValueError(f"{label} must be at least 1")
    return number


def _validated_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"Invalid SHA-256 for {label}")
    return value
