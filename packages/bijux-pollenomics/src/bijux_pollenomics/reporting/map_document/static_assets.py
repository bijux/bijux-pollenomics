from __future__ import annotations

import base64
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any
import zlib

from ...core.geojson import JsonObject
from .evidence import normalize_atlas_evidence, validate_feature_signal_references

ATLAS_BOOTSTRAP_MAX_BYTES = 65_536
ATLAS_CHUNK_MAX_BYTES = 4_194_304
ATLAS_CHUNK_TARGET_BYTES = 2_097_152
# Compressed detail chunks can safely use more of the decoded-payload budget than
# JSON node chunks, whose script wrapper expands quotes and escape sequences.
# The margin also bounds gzip/base64 overhead for an incompressible detail payload.
ATLAS_DETAIL_CHUNK_TARGET_BYTES = 3_140_000
ATLAS_DOCUMENT_MAX_BYTES = 524_288
ATLAS_STATIC_ASSETS_MAX_BYTES = 134_217_728
ATLAS_STATIC_ASSETS_MAX_FILES = 512
ATLAS_INITIAL_MAX_REQUESTS = 4
ATLAS_INITIAL_MAX_BYTES = 1_048_576
ATLAS_INTERACTION_MAX_REQUESTS = 128
ATLAS_INTERACTION_MAX_BYTES = 67_108_864
ATLAS_FILTER_MAIN_THREAD_MAX_MS = 50
_SAFE_RELEASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


@dataclass(frozen=True)
class StaticAtlasAssets:
    manifest_path: Path
    manifest: dict[str, object]
    asset_paths: tuple[Path, ...]

    @property
    def script_tags(self) -> str:
        """Return no eager tags; the runtime applies protocol-aware integrity first."""
        return ""


def validate_atlas_release_id(version: str) -> None:
    """Reject release identifiers that are unsafe in paths or script contexts."""
    if not isinstance(version, str) or not _SAFE_RELEASE_ID.fullmatch(version):
        raise ValueError("atlas version must be a safe release identifier")


def write_static_atlas_assets(
    output_dir: Path,
    *,
    slug: str,
    version: str,
    point_layers: Sequence[JsonObject],
    polygon_layers: Sequence[JsonObject],
    detail_records: Sequence[JsonObject] | None = None,
    scientific_signals: Sequence[JsonObject] | None = None,
    edge_records: Sequence[JsonObject] | None = None,
    sequence_records: Sequence[JsonObject] | None = None,
) -> StaticAtlasAssets:
    """Write deterministic hashed map chunks and their small bootstrap manifest."""
    output_dir = Path(output_dir)
    if not output_dir.is_dir() or output_dir.is_symlink():
        raise ValueError("static atlas output directory must be an existing directory")
    if not slug or Path(slug).name != slug or not slug.replace("-", "").isalnum():
        raise ValueError("static atlas slug must be a safe filename component")
    validate_atlas_release_id(version)

    evidence = normalize_atlas_evidence(
        detail_records=detail_records,
        scientific_signals=scientific_signals,
        edge_records=edge_records,
        sequence_records=sequence_records,
    )
    validate_feature_signal_references(point_layers, evidence.scientific_signals)

    layer_metadata, node_payloads = _build_node_payloads(
        slug=slug,
        version=version,
        point_layers=point_layers,
        polygon_layers=polygon_layers,
    )
    detail_partitions = _partition_features(
        [dict(record) for record in evidence.detail_records],
        target_bytes=ATLAS_DETAIL_CHUNK_TARGET_BYTES,
    )
    first_detail_sequence = 1 + len(node_payloads)
    detail_asset_keys = [
        f"details:{first_detail_sequence + index}"
        for index in range(len(detail_partitions))
    ]
    indexes = {
        **_build_indexes(point_layers),
        "detail_record_asset_keys": {
            str(record["record_id"]): asset_key
            for asset_key, partition in zip(
                detail_asset_keys, detail_partitions, strict=True
            )
            for record in partition
        },
    }
    build_id = (
        "atlas-"
        + hashlib.sha256(
            _canonical_json(
                {
                    "scope_slug": slug,
                    "version": version,
                    "layer_metadata": layer_metadata,
                    "node_payloads": node_payloads,
                    "indexes": indexes,
                    "detail_records": evidence.detail_records,
                    "scientific_signals": evidence.scientific_signals,
                    "edge_records": evidence.edge_records,
                    "sequence_records": evidence.sequence_records,
                }
            ).encode("utf-8")
        ).hexdigest()
    )
    payloads: list[tuple[str, int, dict[str, object]]] = []
    payloads.append(
        (
            "provenance",
            len(layer_metadata),
            {
                "schema_version": "atlas-provenance-chunk.v3",
                "scope_slug": slug,
                "version": version,
                "build_id": build_id,
                "status": (
                    "record_level_available"
                    if evidence.detail_records
                    else "layer_metadata_only"
                ),
                "reason_code": (
                    None
                    if evidence.detail_records
                    else "record_level_provenance_model_not_available"
                ),
                "layers": layer_metadata,
                "scientific_signals": list(evidence.scientific_signals),
                "details_status": (
                    "available" if evidence.detail_records else "unavailable"
                ),
                "details_reason_code": (
                    None
                    if evidence.detail_records
                    else "record_level_evidence_not_available"
                ),
                "classifications_status": (
                    "available" if evidence.scientific_signals else "unavailable"
                ),
                "classifications_reason_code": (
                    None
                    if evidence.scientific_signals
                    else "accepted_scientific_classifications_not_available"
                ),
            },
        )
    )
    payloads.extend(
        ("nodes", _node_payload_record_count(payload), payload)
        for payload in node_payloads
    )
    payloads.extend(
        (
            "details",
            len(partition),
            {
                "schema_version": "atlas-details-chunk.v1",
                "scope_slug": slug,
                "version": version,
                "build_id": build_id,
                "records": partition,
            },
        )
        for partition in detail_partitions
    )
    for domain, records, reason_code in (
        (
            "edges",
            evidence.edge_records,
            "governed_map_edge_model_not_available",
        ),
        (
            "sequences",
            evidence.sequence_records,
            "governed_sequence_detail_model_not_available",
        ),
    ):
        payloads.append(
            (
                domain,
                len(records),
                {
                    "schema_version": f"atlas-{domain}-chunk.v1",
                    "scope_slug": slug,
                    "version": version,
                    "build_id": build_id,
                    "status": "available" if records else "unavailable",
                    "reason_code": None if records else reason_code,
                    "records": list(records),
                },
            )
        )
    indexes = {**indexes, "scope_slug": slug, "version": version, "build_id": build_id}
    payloads.append(("indexes", _index_reference_count(indexes), indexes))

    assets: list[dict[str, object]] = []
    asset_paths: list[Path] = []
    for sequence, (domain, record_count, source_payload) in enumerate(payloads):
        asset_key = f"{domain}:{sequence}"
        payload = {**source_payload, "build_id": build_id, "asset_key": asset_key}
        payload_json = _canonical_json(payload)
        _validate_decoded_payload_size(payload_json, asset_key=asset_key)
        payload_sha256 = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        payload_encoding = "gzip_base64" if domain == "details" else "json"
        script_bytes = _chunk_script_bytes(
            asset_key=asset_key,
            payload_sha256=payload_sha256,
            payload_json=payload_json,
            payload_encoding=payload_encoding,
        )
        digest = hashlib.sha256(script_bytes).hexdigest()
        filename = f"{slug}.atlas-{domain}.{sequence:04d}.{digest[:16]}.js"
        path = output_dir / filename
        _write_immutable(path, script_bytes)
        row: dict[str, object] = {
            "asset_key": asset_key,
            "domain": domain,
            "sequence": sequence,
            "path": filename,
            "sha256": digest,
            "integrity": "sha256-"
            + base64.b64encode(hashlib.sha256(script_bytes).digest()).decode("ascii"),
            "payload_sha256": payload_sha256,
            "payload_encoding": payload_encoding,
            "byte_count": len(script_bytes),
            "record_count": record_count,
            "initial_load": domain not in {"nodes", "details"},
        }
        if domain == "nodes":
            row.update(_node_asset_selection(payload))
        assets.append(row)
        asset_paths.append(path)

    manifest: dict[str, object] = {
        "schema_version": "atlas-static-bootstrap.v1",
        "scope_slug": slug,
        "version": version,
        "build_id": build_id,
        "load_strategy": "selection_aware_static_scripts",
        "offline_file_compatible": True,
        "transport_integrity": {
            "http_https": "subresource_integrity_plus_payload_sha256",
            "file": "payload_sha256_after_script_registration",
            "file_pre_execution_sri": False,
        },
        "compatibility": {
            "provenance_schema": "atlas-provenance-chunk.v3",
            "node_schema": "atlas-node-chunk.v1",
            "detail_schema": "atlas-details-chunk.v1",
            "edge_schema": "atlas-edges-chunk.v1",
            "sequence_schema": "atlas-sequences-chunk.v1",
            "index_schema": "atlas-static-indexes.v2",
        },
        "budgets": {
            "bootstrap_max_bytes": ATLAS_BOOTSTRAP_MAX_BYTES,
            "chunk_max_bytes": ATLAS_CHUNK_MAX_BYTES,
            "document_max_bytes": ATLAS_DOCUMENT_MAX_BYTES,
            "static_assets_max_bytes": ATLAS_STATIC_ASSETS_MAX_BYTES,
            "static_assets_max_files": ATLAS_STATIC_ASSETS_MAX_FILES,
            "initial_max_requests": ATLAS_INITIAL_MAX_REQUESTS,
            "initial_max_bytes": ATLAS_INITIAL_MAX_BYTES,
            "interaction_max_requests": ATLAS_INTERACTION_MAX_REQUESTS,
            "interaction_max_bytes": ATLAS_INTERACTION_MAX_BYTES,
            "filter_main_thread_max_ms": ATLAS_FILTER_MAIN_THREAD_MAX_MS,
        },
        "domains": {
            "nodes": {
                "status": "available",
                "record_count": sum(
                    _node_payload_record_count(payload) for payload in node_payloads
                ),
            },
            "edges": {
                "status": "available" if evidence.edge_records else "unavailable",
                "record_count": len(evidence.edge_records),
                "reason_code": (
                    None
                    if evidence.edge_records
                    else "governed_map_edge_model_not_available"
                ),
            },
            "sequences": {
                "status": ("available" if evidence.sequence_records else "unavailable"),
                "record_count": len(evidence.sequence_records),
                "reason_code": (
                    None
                    if evidence.sequence_records
                    else "governed_sequence_detail_model_not_available"
                ),
            },
            "provenance": {
                "status": (
                    "record_level_available"
                    if evidence.detail_records
                    else "layer_metadata_only"
                ),
                "record_count": (
                    len(evidence.detail_records)
                    if evidence.detail_records
                    else len(layer_metadata)
                ),
                "reason_code": (
                    None
                    if evidence.detail_records
                    else "record_level_provenance_model_not_available"
                ),
            },
            "details": {
                "status": "available" if evidence.detail_records else "unavailable",
                "record_count": len(evidence.detail_records),
                "reason_code": (
                    None
                    if evidence.detail_records
                    else "record_level_evidence_not_available"
                ),
            },
            "classifications": {
                "status": (
                    "available" if evidence.scientific_signals else "unavailable"
                ),
                "record_count": len(evidence.scientific_signals),
                "reason_code": (
                    None
                    if evidence.scientific_signals
                    else "accepted_scientific_classifications_not_available"
                ),
            },
            "indexes": {
                "status": "available",
                "record_count": _index_reference_count(indexes),
            },
        },
        "assets": assets,
    }
    manifest_bytes = (_canonical_json(manifest) + "\n").encode("utf-8")
    if len(manifest_bytes) > ATLAS_BOOTSTRAP_MAX_BYTES:
        raise ValueError("static atlas bootstrap exceeds its byte budget")
    manifest_path = output_dir / f"{slug}_map_assets.json"
    manifest_path.write_bytes(manifest_bytes)
    result = StaticAtlasAssets(
        manifest_path=manifest_path,
        manifest=manifest,
        asset_paths=tuple(asset_paths),
    )
    validate_static_atlas_assets(result)
    return result


def validate_static_atlas_assets(assets: StaticAtlasAssets) -> None:
    """Fail closed when a generated static asset violates identity or size budgets."""
    manifest_bytes = assets.manifest_path.read_bytes()
    if len(manifest_bytes) > ATLAS_BOOTSTRAP_MAX_BYTES:
        raise ValueError("static atlas bootstrap exceeds its byte budget")
    if json.loads(manifest_bytes) != assets.manifest:
        raise ValueError("static atlas bootstrap bytes do not match the manifest")
    rows = assets.manifest.get("assets")
    if not isinstance(rows, list) or len(rows) != len(assets.asset_paths):
        raise ValueError("static atlas asset inventory is incomplete")
    if len(rows) > ATLAS_STATIC_ASSETS_MAX_FILES:
        raise ValueError("static atlas asset count exceeds its budget")
    build_id = assets.manifest.get("build_id")
    if (
        not isinstance(build_id, str)
        or not build_id.startswith("atlas-")
        or len(build_id) != 70
    ):
        raise ValueError("static atlas build identity is invalid")
    if assets.manifest.get("transport_integrity") != {
        "http_https": "subresource_integrity_plus_payload_sha256",
        "file": "payload_sha256_after_script_registration",
        "file_pre_execution_sri": False,
    }:
        raise ValueError("static atlas transport-integrity posture is invalid")
    total_bytes = 0
    initial_bytes = 0
    initial_requests = 0
    asset_keys: set[str] = set()
    decoded_payloads: dict[str, dict[str, object]] = {}
    for row, path in zip(rows, assets.asset_paths, strict=True):
        if not isinstance(row, dict) or path.name != row.get("path"):
            raise ValueError("static atlas asset order or path changed")
        asset_key = row.get("asset_key")
        if not isinstance(asset_key, str) or asset_key in asset_keys:
            raise ValueError("static atlas asset identity is missing or duplicated")
        asset_keys.add(asset_key)
        domain = row.get("domain")
        if domain not in {
            "nodes",
            "details",
            "edges",
            "sequences",
            "provenance",
            "indexes",
        }:
            raise ValueError("static atlas asset domain is invalid")
        if row.get("initial_load") is not (domain not in {"nodes", "details"}):
            raise ValueError("static atlas initial-load declaration is invalid")
        expected_payload_encoding = "gzip_base64" if domain == "details" else "json"
        if row.get("payload_encoding") != expected_payload_encoding:
            raise ValueError("static atlas payload encoding declaration is invalid")
        payload = path.read_bytes()
        byte_count = len(payload)
        total_bytes += byte_count
        if byte_count > ATLAS_CHUNK_MAX_BYTES:
            raise ValueError(f"static atlas chunk exceeds its byte budget: {path.name}")
        if row.get("byte_count") != byte_count:
            raise ValueError(f"static atlas chunk byte count changed: {path.name}")
        if row.get("sha256") != hashlib.sha256(payload).hexdigest():
            raise ValueError(f"static atlas chunk digest changed: {path.name}")
        expected_integrity = "sha256-" + base64.b64encode(
            hashlib.sha256(payload).digest()
        ).decode("ascii")
        if row.get("integrity") != expected_integrity:
            raise ValueError(f"static atlas chunk integrity changed: {path.name}")
        payload_sha256 = row.get("payload_sha256")
        if not isinstance(payload_sha256, str) or len(payload_sha256) != 64:
            raise ValueError(f"static atlas payload digest is invalid: {path.name}")
        if row.get("initial_load") is True:
            initial_requests += 1
            initial_bytes += byte_count
        decoded_payloads[asset_key] = _decode_chunk_script(
            payload,
            expected_asset_key=asset_key,
            expected_payload_sha256=payload_sha256,
            expected_payload_encoding=expected_payload_encoding,
        )
    if total_bytes > ATLAS_STATIC_ASSETS_MAX_BYTES:
        raise ValueError("static atlas assets exceed their total byte budget")
    if initial_requests > ATLAS_INITIAL_MAX_REQUESTS:
        raise ValueError("static atlas initial request count exceeds its budget")
    if initial_bytes > ATLAS_INITIAL_MAX_BYTES:
        raise ValueError("static atlas initial bytes exceed their budget")
    _validate_static_payloads(assets.manifest, rows, decoded_payloads)


def validate_static_atlas_document(document: str) -> None:
    """Reject reintroduction of an unbounded inline map payload."""
    byte_count = len(document.encode("utf-8"))
    if byte_count > ATLAS_DOCUMENT_MAX_BYTES:
        raise ValueError(
            f"static atlas document exceeds {ATLAS_DOCUMENT_MAX_BYTES} bytes: {byte_count}"
        )


def _build_node_payloads(
    *,
    slug: str,
    version: str,
    point_layers: Sequence[JsonObject],
    polygon_layers: Sequence[JsonObject],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    metadata: list[dict[str, object]] = []
    payloads: list[dict[str, object]] = []
    indexed_layers = [
        *(("point", layer) for layer in point_layers),
        *(("polygon", layer) for layer in polygon_layers),
    ]
    for layer_index, (layer_kind, source_layer) in enumerate(indexed_layers):
        layer = dict(source_layer)
        if layer_kind == "point":
            raw_features = layer.pop("features", [])
        else:
            geojson = layer.get("geojson")
            safe_geojson = dict(geojson) if isinstance(geojson, dict) else {}
            raw_features = safe_geojson.pop("features", [])
            layer["geojson"] = safe_geojson
        features = (
            [dict(row) for row in raw_features if isinstance(row, dict)]
            if isinstance(raw_features, list)
            else []
        )
        layer["static_feature_count"] = len(features)
        layer["static_facets"] = _layer_facets(layer_kind, features)
        metadata.append(
            {
                "layer_index": layer_index,
                "layer_kind": layer_kind,
                "layer": layer,
                "feature_count": len(features),
            }
        )
        grouped_features: dict[str, list[tuple[int, dict[str, object]]]] = {}
        for feature_index, feature in enumerate(features):
            grouped_features.setdefault(
                _feature_country(layer_kind, feature), []
            ).append((feature_index, feature))
        part_number = 0
        for country_key, indexed_features in sorted(grouped_features.items()):
            for part in _partition_indexed_features(indexed_features):
                part_number += 1
                feature_indexes = [index for index, _feature in part]
                part_features = [feature for _index, feature in part]
                payloads.append(
                    {
                        "schema_version": "atlas-node-chunk.v1",
                        "scope_slug": slug,
                        "version": version,
                        "layer_index": layer_index,
                        "layer_kind": layer_kind,
                        "layer_key": str(layer.get("key", "")),
                        "part_number": part_number,
                        "country_keys": [country_key],
                        "feature_indexes": feature_indexes,
                        "features": part_features,
                    }
                )
    return metadata, payloads


def _partition_features(
    features: list[dict[str, object]],
    *,
    target_bytes: int = ATLAS_CHUNK_TARGET_BYTES,
) -> list[list[dict[str, object]]]:
    if not features:
        return []
    parts: list[list[dict[str, object]]] = []
    current: list[dict[str, object]] = []
    current_bytes = 2
    for feature in features:
        feature_bytes = len(_canonical_json(feature).encode("utf-8"))
        separator_bytes = 1 if current else 0
        candidate_bytes = current_bytes + separator_bytes + feature_bytes
        if current and candidate_bytes > target_bytes:
            parts.append(current)
            current = [feature]
            current_bytes = feature_bytes + 2
        else:
            current.append(feature)
            current_bytes = candidate_bytes
        if current_bytes > ATLAS_CHUNK_MAX_BYTES:
            raise ValueError("one static atlas feature exceeds the chunk byte budget")
    if current:
        parts.append(current)
    return parts


def _partition_indexed_features(
    features: list[tuple[int, dict[str, object]]],
) -> list[list[tuple[int, dict[str, object]]]]:
    feature_rows = [feature for _index, feature in features]
    partitions = _partition_features(feature_rows)
    result: list[list[tuple[int, dict[str, object]]]] = []
    offset = 0
    for partition in partitions:
        result.append(features[offset : offset + len(partition)])
        offset += len(partition)
    return result


def _feature_country(layer_kind: str, feature: dict[str, object]) -> str:
    source: dict[str, object] = feature
    if layer_kind == "polygon":
        properties = feature.get("properties")
        source = properties if isinstance(properties, dict) else {}
    return str(source.get("country", "")).strip() or "UNASSIGNED"


def _layer_facets(
    layer_kind: str, features: list[dict[str, object]]
) -> dict[str, list[str]]:
    if layer_kind != "point":
        return {"coordinate_confidences": [], "temporal_window_labels": []}
    return {
        "coordinate_confidences": sorted(
            {
                str(feature.get("coordinate_confidence", "")).strip()
                for feature in features
                if str(feature.get("coordinate_confidence", "")).strip()
            }
        ),
        "temporal_window_labels": sorted(
            {
                str(feature.get("temporal_window_label", "")).strip()
                for feature in features
                if str(feature.get("temporal_window_label", "")).strip()
            }
        ),
    }


def _build_indexes(point_layers: Sequence[JsonObject]) -> dict[str, object]:
    countries: dict[str, dict[str, list[int]]] = {}
    spatial_cells: dict[str, dict[str, list[int]]] = {}
    time_intervals: list[list[object]] = []
    signals: dict[str, list[str]] = {}
    for layer in point_layers:
        layer_key = str(layer.get("key", "")).strip()
        group = str(layer.get("group", "")).strip()
        species = str(layer.get("species_latin_name", "")).strip()
        for signal in (layer_key, group, species):
            if signal:
                signals.setdefault(signal, []).append(layer_key)
        raw_features = layer.get("features")
        if not isinstance(raw_features, list):
            continue
        for feature_index, feature in enumerate(raw_features):
            if not isinstance(feature, dict):
                continue
            country = str(feature.get("country", "")).strip() or "UNASSIGNED"
            countries.setdefault(country, {}).setdefault(layer_key, []).append(
                feature_index
            )
            latitude = _finite_number(feature.get("latitude"))
            longitude = _finite_number(feature.get("longitude"))
            if latitude is not None and longitude is not None:
                cell = f"{math.floor(latitude)}:{math.floor(longitude)}"
                spatial_cells.setdefault(cell, {}).setdefault(layer_key, []).append(
                    feature_index
                )
            interval = _feature_interval(feature)
            if interval is not None:
                time_intervals.append(
                    [interval[0], interval[1], layer_key, feature_index]
                )
    return {
        "schema_version": "atlas-static-indexes.v2",
        "country_feature_indexes": _sorted_nested_indexes(countries),
        "spatial_degree_feature_indexes": _sorted_nested_indexes(spatial_cells),
        "time_interval_feature_indexes": sorted(
            time_intervals, key=lambda row: (row[0], row[1], row[2], row[3])
        ),
        "signal_layer_indexes": {
            key: sorted(set(value)) for key, value in sorted(signals.items())
        },
    }


def _feature_interval(feature: dict[str, object]) -> tuple[float, float] | None:
    start = _finite_number(feature.get("time_start_bp"))
    end = _finite_number(feature.get("time_end_bp"))
    if "time_start_bp" in feature or "time_end_bp" in feature:
        return (
            (start, end)
            if start is not None and end is not None and start <= end
            else None
        )
    point = _finite_number(feature.get("time_mean_bp"))
    if point is None:
        point = _finite_number(feature.get("time_year_bp"))
    return (point, point) if point is not None else None


def _finite_number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value) if isinstance(value, (int, float, str)) else math.nan
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def _sorted_nested_indexes(
    rows: dict[str, dict[str, list[int]]],
) -> dict[str, dict[str, list[int]]]:
    return {
        outer_key: dict(sorted(inner_rows.items()))
        for outer_key, inner_rows in sorted(rows.items())
    }


def _index_reference_count(payload: dict[str, object]) -> int:
    country_rows = payload.get("country_feature_indexes")
    if not isinstance(country_rows, dict):
        return 0
    feature_reference_count = sum(
        len(indexes)
        for layers in country_rows.values()
        if isinstance(layers, dict)
        for indexes in layers.values()
        if isinstance(indexes, list)
    )
    detail_rows = payload.get("detail_record_asset_keys")
    detail_reference_count = len(detail_rows) if isinstance(detail_rows, dict) else 0
    return feature_reference_count + detail_reference_count


def _node_payload_record_count(payload: dict[str, object]) -> int:
    features = payload.get("features")
    if not isinstance(features, list):
        raise TypeError("static atlas node chunk has no feature records")
    return len(features)


def _node_asset_selection(payload: dict[str, object]) -> dict[str, object]:
    features = payload.get("features")
    if not isinstance(features, list):
        raise TypeError("static atlas node chunk has no feature records")
    safe_features = [feature for feature in features if isinstance(feature, dict)]
    intervals = [
        interval
        for feature in safe_features
        if (interval := _node_feature_interval(str(payload["layer_kind"]), feature))
        is not None
    ]
    scientific_signal_ids: set[str] = set()
    for feature in safe_features:
        references = feature.get("scientific_signal_ids", [])
        if isinstance(references, list):
            scientific_signal_ids.update(
                signal_id for signal_id in references if isinstance(signal_id, str)
            )
    return {
        "layer_index": payload["layer_index"],
        "layer_key": payload["layer_key"],
        "layer_kind": payload["layer_kind"],
        "country_keys": payload["country_keys"],
        "bounds": _node_feature_bounds(str(payload["layer_kind"]), safe_features),
        "time_min_bp": min((interval[0] for interval in intervals), default=None),
        "time_max_bp": max((interval[1] for interval in intervals), default=None),
        "untimed_record_count": len(safe_features) - len(intervals),
        "scientific_signal_ids": sorted(scientific_signal_ids),
    }


def _node_feature_interval(
    layer_kind: str, feature: dict[str, object]
) -> tuple[float, float] | None:
    if layer_kind == "polygon":
        properties = feature.get("properties")
        return _feature_interval(properties) if isinstance(properties, dict) else None
    return _feature_interval(feature)


def _node_feature_bounds(
    layer_kind: str, features: list[dict[str, object]]
) -> list[float] | None:
    coordinates: list[tuple[float, float]] = []
    for feature in features:
        if layer_kind == "point":
            latitude = _finite_coordinate(feature.get("latitude"))
            longitude = _finite_coordinate(feature.get("longitude"))
            if latitude is not None and longitude is not None:
                coordinates.append((latitude, longitude))
            continue
        geometry = feature.get("geometry")
        if isinstance(geometry, dict):
            _collect_geojson_coordinates(geometry.get("coordinates"), coordinates)
    if not coordinates:
        return None
    latitudes = [latitude for latitude, _longitude in coordinates]
    longitudes = [longitude for _latitude, longitude in coordinates]
    return [min(latitudes), min(longitudes), max(latitudes), max(longitudes)]


def _collect_geojson_coordinates(
    value: object, coordinates: list[tuple[float, float]]
) -> None:
    if not isinstance(value, list):
        return
    if len(value) >= 2:
        longitude = _finite_coordinate(value[0])
        latitude = _finite_coordinate(value[1])
        if longitude is not None and latitude is not None:
            coordinates.append((latitude, longitude))
            return
    for item in value:
        _collect_geojson_coordinates(item, coordinates)


def _finite_coordinate(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value) if isinstance(value, (int, float, str)) else math.nan
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _chunk_script_bytes(
    *,
    asset_key: str,
    payload_sha256: str,
    payload_json: str,
    payload_encoding: str,
) -> bytes:
    envelope: dict[str, object] = {
        "asset_key": asset_key,
        "payload_sha256": payload_sha256,
        "payload_encoding": payload_encoding,
    }
    if payload_encoding == "json":
        envelope["payload_json"] = payload_json
    elif payload_encoding == "gzip_base64":
        envelope["payload_gzip_base64"] = base64.b64encode(
            gzip.compress(payload_json.encode("utf-8"), compresslevel=9, mtime=0)
        ).decode("ascii")
    else:
        raise ValueError("static atlas payload encoding is unsupported")
    envelope_json = _canonical_json(envelope)
    statement = (
        "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__="
        "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__||[];"
        f"globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push({envelope_json});\n"
    )
    return statement.encode("utf-8")


def _decode_chunk_script(
    payload: bytes,
    *,
    expected_asset_key: str,
    expected_payload_sha256: str,
    expected_payload_encoding: str,
) -> dict[str, object]:
    prefix = (
        "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__="
        "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__||[];"
        "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push("
    )
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("static atlas chunk is not UTF-8") from exc
    if not text.startswith(prefix) or not text.endswith(");\n"):
        raise ValueError("static atlas chunk wrapper changed")
    try:
        envelope = json.loads(text[len(prefix) : -3])
    except json.JSONDecodeError as exc:
        raise ValueError("static atlas chunk envelope is invalid") from exc
    if not isinstance(envelope, Mapping):
        raise ValueError("static atlas chunk envelope must be an object")
    if envelope.get("asset_key") != expected_asset_key:
        raise ValueError("static atlas chunk envelope identity changed")
    if envelope.get("payload_sha256") != expected_payload_sha256:
        raise ValueError("static atlas chunk envelope digest changed")
    if envelope.get("payload_encoding") != expected_payload_encoding:
        raise ValueError("static atlas chunk envelope encoding changed")
    if expected_payload_encoding == "json":
        payload_json = envelope.get("payload_json")
        if not isinstance(payload_json, str):
            raise ValueError("static atlas chunk JSON payload is missing")
    elif expected_payload_encoding == "gzip_base64":
        payload_gzip_base64 = envelope.get("payload_gzip_base64")
        if not isinstance(payload_gzip_base64, str):
            raise ValueError("static atlas compressed payload is missing")
        try:
            compressed = base64.b64decode(payload_gzip_base64, validate=True)
            payload_json = gzip.decompress(compressed).decode("utf-8")
        except (ValueError, OSError, EOFError, UnicodeDecodeError, zlib.error) as exc:
            raise ValueError("static atlas compressed payload is invalid") from exc
    else:
        raise ValueError("static atlas chunk envelope encoding is unsupported")
    _validate_decoded_payload_size(
        payload_json,
        asset_key=expected_asset_key,
    )
    if (
        hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        != expected_payload_sha256
    ):
        raise ValueError("static atlas chunk payload digest changed")
    try:
        decoded = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        raise ValueError("static atlas chunk payload JSON is invalid") from exc
    if not isinstance(decoded, dict):
        raise ValueError("static atlas chunk payload must be an object")
    return decoded


def _validate_decoded_payload_size(payload_json: str, *, asset_key: str) -> None:
    if len(payload_json.encode("utf-8")) > ATLAS_CHUNK_MAX_BYTES:
        raise ValueError(
            f"static atlas decoded payload exceeds its byte budget: {asset_key}"
        )


def _validate_static_payloads(
    manifest: Mapping[str, object],
    asset_rows: Sequence[Mapping[str, object]],
    payloads: Mapping[str, Mapping[str, object]],
) -> None:
    compatibility = manifest.get("compatibility")
    if not isinstance(compatibility, Mapping):
        raise ValueError("static atlas compatibility declaration is missing")
    expected_schemas = {
        "provenance": compatibility.get("provenance_schema"),
        "nodes": compatibility.get("node_schema"),
        "details": compatibility.get("detail_schema"),
        "edges": compatibility.get("edge_schema"),
        "sequences": compatibility.get("sequence_schema"),
        "indexes": compatibility.get("index_schema"),
    }
    detail_record_assets: dict[str, str] = {}
    detail_record_order: list[str] = []
    index_payload: Mapping[str, object] | None = None
    for row in asset_rows:
        asset_key = row.get("asset_key")
        domain = row.get("domain")
        if not isinstance(asset_key, str) or not isinstance(domain, str):
            raise ValueError("static atlas asset domain identity is invalid")
        payload = payloads.get(asset_key)
        if payload is None:
            raise ValueError("static atlas decoded payload inventory is incomplete")
        for field in ("build_id", "scope_slug", "version"):
            if payload.get(field) != manifest.get(field):
                raise ValueError(f"static atlas {asset_key} {field} changed")
        if payload.get("asset_key") != asset_key:
            raise ValueError(f"static atlas {asset_key} payload identity changed")
        if payload.get("schema_version") != expected_schemas.get(domain):
            raise ValueError(f"static atlas {asset_key} schema changed")
        if domain == "details":
            records = payload.get("records")
            if not isinstance(records, list) or any(
                not isinstance(record, Mapping) for record in records
            ):
                raise ValueError(f"static atlas {asset_key} detail rows are invalid")
            if row.get("record_count") != len(records):
                raise ValueError(f"static atlas {asset_key} detail count changed")
            for record in records:
                record_id = record.get("record_id")
                if not isinstance(record_id, str) or not record_id:
                    raise ValueError("static atlas detail record identity is invalid")
                if record_id in detail_record_assets:
                    raise ValueError(
                        "static atlas detail record identity is duplicated"
                    )
                detail_record_assets[record_id] = asset_key
                detail_record_order.append(record_id)
        elif domain == "indexes":
            if index_payload is not None:
                raise ValueError("static atlas index payload is duplicated")
            index_payload = payload
    if detail_record_order != sorted(detail_record_order):
        raise ValueError("static atlas detail records are not stably ordered")
    if index_payload is None:
        raise ValueError("static atlas index payload is missing")
    detail_index = index_payload.get("detail_record_asset_keys")
    if not isinstance(detail_index, Mapping) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in detail_index.items()
    ):
        raise ValueError("static atlas detail index is invalid")
    if dict(detail_index) != detail_record_assets:
        raise ValueError("static atlas detail index does not reconcile")
    domains = manifest.get("domains")
    if not isinstance(domains, Mapping):
        raise ValueError("static atlas domain accounting is missing")
    details_domain = domains.get("details")
    if not isinstance(details_domain, Mapping) or details_domain.get(
        "record_count"
    ) != len(detail_record_assets):
        raise ValueError("static atlas detail domain count does not reconcile")


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _write_immutable(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.is_symlink() or path.read_bytes() != payload:
            raise ValueError(f"static atlas asset collision: {path.name}")
        return
    path.write_bytes(payload)


__all__ = [
    "ATLAS_BOOTSTRAP_MAX_BYTES",
    "ATLAS_CHUNK_MAX_BYTES",
    "ATLAS_DOCUMENT_MAX_BYTES",
    "ATLAS_FILTER_MAIN_THREAD_MAX_MS",
    "ATLAS_INITIAL_MAX_BYTES",
    "ATLAS_INITIAL_MAX_REQUESTS",
    "ATLAS_INTERACTION_MAX_BYTES",
    "ATLAS_INTERACTION_MAX_REQUESTS",
    "ATLAS_STATIC_ASSETS_MAX_BYTES",
    "ATLAS_STATIC_ASSETS_MAX_FILES",
    "StaticAtlasAssets",
    "validate_atlas_release_id",
    "validate_static_atlas_assets",
    "validate_static_atlas_document",
    "write_static_atlas_assets",
]
