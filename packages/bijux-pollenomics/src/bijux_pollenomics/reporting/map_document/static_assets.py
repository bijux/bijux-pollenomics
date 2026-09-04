from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...core.geojson import JsonObject

ATLAS_BOOTSTRAP_MAX_BYTES = 65_536
ATLAS_CHUNK_MAX_BYTES = 4_194_304
ATLAS_CHUNK_TARGET_BYTES = 2_097_152
ATLAS_DOCUMENT_MAX_BYTES = 524_288
ATLAS_STATIC_ASSETS_MAX_BYTES = 134_217_728
ATLAS_STATIC_ASSETS_MAX_FILES = 512

_CHUNK_GLOBAL = "__BIJUX_ATLAS_CHUNKS__"


@dataclass(frozen=True)
class StaticAtlasAssets:
    manifest_path: Path
    manifest: dict[str, object]
    asset_paths: tuple[Path, ...]

    @property
    def bootstrap_json(self) -> str:
        return _canonical_json(self.manifest)

    @property
    def script_tags(self) -> str:
        return "\n".join(
            f'<script src="./{path.name}"></script>' for path in self.asset_paths
        )


def write_static_atlas_assets(
    output_dir: Path,
    *,
    slug: str,
    version: str,
    point_layers: Sequence[JsonObject],
    polygon_layers: Sequence[JsonObject],
) -> StaticAtlasAssets:
    """Write deterministic hashed map chunks and their small bootstrap manifest."""
    output_dir = Path(output_dir)
    if not output_dir.is_dir() or output_dir.is_symlink():
        raise ValueError("static atlas output directory must be an existing directory")
    if not slug or Path(slug).name != slug or not slug.replace("-", "").isalnum():
        raise ValueError("static atlas slug must be a safe filename component")

    layer_metadata, node_payloads = _build_node_payloads(
        slug=slug,
        version=version,
        point_layers=point_layers,
        polygon_layers=polygon_layers,
    )
    payloads: list[tuple[str, int, dict[str, object]]] = []
    payloads.append(
        (
            "provenance",
            len(layer_metadata),
            {
                "schema_version": "atlas-provenance-chunk.v1",
                "scope_slug": slug,
                "version": version,
                "status": "layer_metadata_only",
                "reason_code": "record_level_provenance_model_not_available",
                "layers": layer_metadata,
            },
        )
    )
    payloads.extend(
        ("nodes", _node_payload_record_count(payload), payload)
        for payload in node_payloads
    )
    payloads.extend(
        (
            domain,
            0,
            {
                "schema_version": f"atlas-{domain}-chunk.v1",
                "scope_slug": slug,
                "version": version,
                "status": "unavailable",
                "reason_code": reason_code,
                "records": [],
            },
        )
        for domain, reason_code in (
            ("edges", "governed_map_edge_model_not_available"),
            ("sequences", "governed_sequence_detail_model_not_available"),
        )
    )
    indexes = _build_indexes(point_layers)
    payloads.append(("indexes", _index_reference_count(indexes), indexes))

    assets: list[dict[str, object]] = []
    asset_paths: list[Path] = []
    for sequence, (domain, record_count, payload) in enumerate(payloads):
        script_bytes = _chunk_script_bytes(domain, payload)
        digest = hashlib.sha256(script_bytes).hexdigest()
        filename = f"{slug}.atlas-{domain}.{sequence:04d}.{digest[:16]}.js"
        path = output_dir / filename
        _write_immutable(path, script_bytes)
        assets.append(
            {
                "domain": domain,
                "sequence": sequence,
                "path": filename,
                "sha256": digest,
                "byte_count": len(script_bytes),
                "record_count": record_count,
            }
        )
        asset_paths.append(path)

    manifest: dict[str, object] = {
        "schema_version": "atlas-static-bootstrap.v1",
        "scope_slug": slug,
        "version": version,
        "load_strategy": "ordered_static_scripts",
        "offline_file_compatible": True,
        "budgets": {
            "bootstrap_max_bytes": ATLAS_BOOTSTRAP_MAX_BYTES,
            "chunk_max_bytes": ATLAS_CHUNK_MAX_BYTES,
            "document_max_bytes": ATLAS_DOCUMENT_MAX_BYTES,
            "static_assets_max_bytes": ATLAS_STATIC_ASSETS_MAX_BYTES,
            "static_assets_max_files": ATLAS_STATIC_ASSETS_MAX_FILES,
        },
        "domains": {
            "nodes": {
                "status": "available",
                "record_count": sum(
                    _node_payload_record_count(payload) for payload in node_payloads
                ),
            },
            "edges": {
                "status": "unavailable",
                "record_count": 0,
                "reason_code": "governed_map_edge_model_not_available",
            },
            "sequences": {
                "status": "unavailable",
                "record_count": 0,
                "reason_code": "governed_sequence_detail_model_not_available",
            },
            "provenance": {
                "status": "layer_metadata_only",
                "record_count": len(layer_metadata),
                "reason_code": "record_level_provenance_model_not_available",
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
    total_bytes = 0
    for row, path in zip(rows, assets.asset_paths, strict=True):
        if not isinstance(row, dict) or path.name != row.get("path"):
            raise ValueError("static atlas asset order or path changed")
        payload = path.read_bytes()
        byte_count = len(payload)
        total_bytes += byte_count
        if byte_count > ATLAS_CHUNK_MAX_BYTES:
            raise ValueError(f"static atlas chunk exceeds its byte budget: {path.name}")
        if row.get("byte_count") != byte_count:
            raise ValueError(f"static atlas chunk byte count changed: {path.name}")
        if row.get("sha256") != hashlib.sha256(payload).hexdigest():
            raise ValueError(f"static atlas chunk digest changed: {path.name}")
    if total_bytes > ATLAS_STATIC_ASSETS_MAX_BYTES:
        raise ValueError("static atlas assets exceed their total byte budget")


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
        metadata.append(
            {
                "layer_index": layer_index,
                "layer_kind": layer_kind,
                "layer": layer,
                "feature_count": len(features),
            }
        )
        offset = 0
        for part_number, part in enumerate(_partition_features(features), start=1):
            payloads.append(
                {
                    "schema_version": "atlas-node-chunk.v1",
                    "scope_slug": slug,
                    "version": version,
                    "layer_index": layer_index,
                    "layer_kind": layer_kind,
                    "layer_key": str(layer.get("key", "")),
                    "part_number": part_number,
                    "feature_offset": offset,
                    "features": part,
                }
            )
            offset += len(part)
    return metadata, payloads


def _partition_features(
    features: list[dict[str, object]],
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
        if current and candidate_bytes > ATLAS_CHUNK_TARGET_BYTES:
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
        "schema_version": "atlas-static-indexes.v1",
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
        outer_key: {
            inner_key: values for inner_key, values in sorted(inner_rows.items())
        }
        for outer_key, inner_rows in sorted(rows.items())
    }


def _index_reference_count(payload: dict[str, object]) -> int:
    country_rows = payload.get("country_feature_indexes")
    if not isinstance(country_rows, dict):
        return 0
    return sum(
        len(indexes)
        for layers in country_rows.values()
        if isinstance(layers, dict)
        for indexes in layers.values()
        if isinstance(indexes, list)
    )


def _node_payload_record_count(payload: dict[str, object]) -> int:
    features = payload.get("features")
    if not isinstance(features, list):
        raise TypeError("static atlas node chunk has no feature records")
    return len(features)


def _chunk_script_bytes(domain: str, payload: dict[str, object]) -> bytes:
    encoded = _canonical_json(payload)
    if domain == "nodes":
        statement = (
            f"globalThis.{_CHUNK_GLOBAL}=globalThis.{_CHUNK_GLOBAL}||{{nodes:[]}};"
            f"globalThis.{_CHUNK_GLOBAL}.nodes.push({encoded});\n"
        )
    else:
        statement = (
            f"globalThis.{_CHUNK_GLOBAL}=globalThis.{_CHUNK_GLOBAL}||{{nodes:[]}};"
            f"globalThis.{_CHUNK_GLOBAL}.{domain}={encoded};\n"
        )
    return statement.encode("utf-8")


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
    "ATLAS_STATIC_ASSETS_MAX_BYTES",
    "ATLAS_STATIC_ASSETS_MAX_FILES",
    "StaticAtlasAssets",
    "validate_static_atlas_assets",
    "validate_static_atlas_document",
    "write_static_atlas_assets",
]
