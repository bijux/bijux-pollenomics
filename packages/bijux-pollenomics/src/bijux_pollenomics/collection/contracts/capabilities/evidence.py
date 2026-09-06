from __future__ import annotations

import csv
import hashlib
import io
import json
import stat
from collections.abc import Mapping
from pathlib import Path

from . import receipts, sead
from .constants import (
    _SEAD_NORMALIZED_ROOT,
    _SEAD_RUN_ID,
    SEAD_NORMALIZED_EVIDENCE_MANIFEST,
)
from .primitives import _non_negative_int, _positive_int


def _resolve_path(output_root: Path, repository_path: str) -> Path:
    if repository_path.startswith("data/"):
        return output_root / repository_path.removeprefix("data/")
    return output_root.parent / repository_path


def _path_has_content(path: Path, repository_path: str) -> bool:
    """Accept only structurally governed evidence at the exact declared path."""
    try:
        file_stat = path.lstat()
    except OSError:
        return False
    if (
        not stat.S_ISREG(file_stat.st_mode)
        or path.is_symlink()
        or file_stat.st_size <= 0
        or path.name.startswith(".")
    ):
        return False
    if (
        path.name == "admission.json"
        and path.parent.name == _SEAD_RUN_ID
        and path.parent.parent.name == "acquisitions"
    ):
        return sead._valid_sead_admission(path)
    if path.suffix in {".json", ".geojson"}:
        return _valid_json_evidence(path, repository_path)
    if path.suffix == ".csv" or path.suffix == ".anno":
        return _valid_delimited_evidence(path)
    return False


def _valid_json_evidence(path: Path, repository_path: str) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    if repository_path.endswith(".geojson"):
        return _valid_geojson(payload)
    if "/neotoma/relational/surfaces/" in repository_path:
        return _valid_neotoma_part(path, payload)
    if repository_path == "data/neotoma/relational/manifest.json":
        return _valid_neotoma_manifest(path, payload)
    if repository_path == SEAD_NORMALIZED_EVIDENCE_MANIFEST:
        return sead._valid_sead_evidence_manifest(path, payload)
    if repository_path.startswith(f"{_SEAD_NORMALIZED_ROOT}/"):
        return sead._valid_sead_evidence_member(path, payload, repository_path)
    if "/sead/raw/acquisitions/" in repository_path and "/payloads/" in repository_path:
        return sead._valid_sead_table_payload(path, payload)
    if repository_path == "data/landclim/raw/landclim_sources.json":
        return receipts._valid_landclim_receipt(path, payload)
    if repository_path == "data/boundaries/raw/source_manifest.json":
        return receipts._valid_boundary_receipt(path, payload)
    if repository_path == "data/aadr/v66/release_manifest.json":
        return receipts._valid_aadr_receipt(path, payload)
    if repository_path == "data/svar/raw/svar_lake_registry_manifest.json":
        return (
            payload.get("source") == "SMHI SVAR"
            and _positive_int(payload.get("matched_lake_count"))
            == _positive_int(payload.get("normalized_lake_count"))
            and isinstance(payload.get("source_url"), str)
            and isinstance(payload.get("wfs_url"), str)
        )
    if repository_path == "data/raa/normalized/sweden_archaeology_layer.json":
        counts = payload.get("counts")
        return (
            payload.get("source") == "Riksantikvarieämbetet"
            and isinstance(counts, dict)
            and bool(counts)
            and all(_non_negative_int(value) is not None for value in counts.values())
            and _positive_int(payload.get("density_feature_count")) is not None
        )
    if repository_path == "data/raa/raw/fornsok_domains.json":
        return len(payload) >= 5 and all(
            isinstance(value, list) and value for value in payload.values()
        )
    return _valid_versioned_json(payload)


def _valid_geojson(payload: Mapping[str, object]) -> bool:
    features = payload.get("features")
    if payload.get("type") != "FeatureCollection" or not isinstance(features, list):
        return False
    if not features:
        return False
    return all(
        isinstance(feature, dict)
        and feature.get("type") == "Feature"
        and isinstance(feature.get("geometry"), dict)
        and isinstance(feature.get("properties"), dict)
        and bool(feature["properties"])
        for feature in features
    )


def _valid_versioned_json(payload: Mapping[str, object]) -> bool:
    schema_version = payload.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version.strip():
        return False
    collections = [
        value
        for key, value in payload.items()
        if key != "schema_version" and isinstance(value, (list, dict)) and value
    ]
    if not collections:
        return False
    for count_key, collection_key in (
        ("row_count", "rows"),
        ("cell_count", "cells"),
        ("asset_count", "assets"),
        ("country_count", "countries"),
    ):
        if count_key in payload and collection_key in payload:
            collection = payload[collection_key]
            if not isinstance(collection, list) or payload[count_key] != len(
                collection
            ):
                return False
    return True


def _valid_delimited_evidence(path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    delimiter = "\t" if path.suffix == ".anno" else ","
    rows = [row for row in csv.reader(io.StringIO(content), delimiter=delimiter) if row]
    if len(rows) < 2:
        return False
    column_count = len(rows[0])
    return column_count > 1 and all(len(row) == column_count for row in rows[1:])


def _valid_neotoma_part(path: Path, payload: Mapping[str, object]) -> bool:
    rows = payload.get("rows")
    surface = path.parent.name
    if (
        payload.get("schema_version") != "neotoma-relational-part.v1"
        or payload.get("source_family") != "neotoma"
        or payload.get("surface") != surface
        or not isinstance(rows, list)
        or not rows
        or payload.get("row_count") != len(rows)
    ):
        return False
    manifest_path = path.parents[2] / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        surface_record = manifest["surfaces"][surface]
        relative_path = path.relative_to(path.parents[2]).as_posix()
        part_record = next(
            record
            for record in surface_record["parts"]
            if record.get("path") == relative_path
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        StopIteration,
        TypeError,
    ):
        return False
    return bool(
        part_record.get("row_count") == len(rows)
        and part_record.get("sha256") == hashlib.sha256(path.read_bytes()).hexdigest()
    )


def _valid_neotoma_manifest(path: Path, payload: Mapping[str, object]) -> bool:
    surfaces = payload.get("surfaces")
    reconciliation = payload.get("reconciliation")
    if (
        payload.get("schema_version")
        != "neotoma-relational-materialization-manifest.v1"
        or payload.get("source_family") != "neotoma"
        or not isinstance(surfaces, dict)
        or not surfaces
        or not isinstance(reconciliation, dict)
    ):
        return False
    reconciliation_path = path.parent / str(reconciliation.get("path", ""))
    try:
        return (
            reconciliation_path.is_file()
            and reconciliation.get("sha256")
            == hashlib.sha256(reconciliation_path.read_bytes()).hexdigest()
            and all(
                isinstance(record, dict)
                and _positive_int(record.get("row_count")) is not None
                and isinstance(record.get("parts"), list)
                and len(record["parts"]) == record.get("part_count")
                for record in surfaces.values()
            )
        )
    except OSError:
        return False
