"""Fail-closed validation for static atlas manifests and asset payloads."""

import base64
from collections.abc import Mapping, Sequence
import hashlib
import json

from ..temporal_admission import feature_interval, read_calendar_profile
from .asset_inventory import normalize_asset_inventory
from .budgets import (
    ATLAS_BOOTSTRAP_MAX_BYTES,
    ATLAS_CHUNK_MAX_BYTES,
    ATLAS_DOCUMENT_MAX_BYTES,
    ATLAS_INITIAL_MAX_BYTES,
    ATLAS_INITIAL_MAX_REQUESTS,
    ATLAS_STATIC_ASSETS_MAX_BYTES,
    ATLAS_STATIC_ASSETS_MAX_FILES,
)
from .index_bundles import decode_index_bundle
from .indexes import build_indexes
from .models import StaticAtlasAssets
from .nodes import node_asset_selection
from .serialization import decode_chunk_script


def validate_static_atlas_assets(assets: StaticAtlasAssets) -> None:
    """Fail closed when a generated static asset violates identity or size budgets."""
    manifest_bytes = assets.manifest_path.read_bytes()
    if len(manifest_bytes) > ATLAS_BOOTSTRAP_MAX_BYTES:
        raise ValueError("static atlas bootstrap exceeds its byte budget")
    if json.loads(manifest_bytes) != assets.manifest:
        raise ValueError("static atlas bootstrap bytes do not match the manifest")
    temporal_profile = read_calendar_profile(assets.manifest)
    bootstrap_schema = assets.manifest.get("schema_version")
    inventory = assets.manifest.get("assets")
    if temporal_profile is not None:
        view_sha = assets.manifest.get("native_view_sha256")
        if (
            bootstrap_schema != "atlas-static-bootstrap.v3"
            or not isinstance(inventory, Mapping)
            or read_calendar_profile(inventory) != temporal_profile
            or not isinstance(view_sha, str)
            or len(view_sha) != 64
            or any(char not in "0123456789abcdef" for char in view_sha)
        ):
            raise ValueError("Signed static bootstrap binding is invalid")
    elif bootstrap_schema == "atlas-static-bootstrap.v1":
        if not isinstance(inventory, list):
            raise ValueError("static atlas v1 asset inventory is invalid")
    elif bootstrap_schema == "atlas-static-bootstrap.v2":
        if not isinstance(inventory, Mapping):
            raise ValueError("static atlas v2 asset inventory is invalid")
    else:
        raise ValueError("static atlas bootstrap schema is invalid")
    rows = normalize_asset_inventory(inventory)
    if len(rows) != len(assets.asset_paths):
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
    compatibility = assets.manifest.get("compatibility")
    requires_decoded_counts = isinstance(compatibility, Mapping) and compatibility.get(
        "index_schema"
    ) in {"atlas-static-indexes.v3", "atlas-static-indexes.v4"}
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
        if row.get("initial_load") is not (
            domain not in {"nodes", "details", "indexes"}
        ):
            raise ValueError("static atlas initial-load declaration is invalid")
        expected_payload_encodings = (
            {"gzip_base64", "json"}
            if domain in {"nodes", "provenance"}
            else {"gzip_base64"}
            if domain == "details"
            else {"json"}
        )
        payload_encoding = row.get("payload_encoding")
        if not isinstance(payload_encoding, str) or payload_encoding not in (
            expected_payload_encodings
        ):
            raise ValueError("static atlas payload encoding declaration is invalid")
        expected_decoded_byte_count = row.get("decoded_byte_count")
        if expected_decoded_byte_count is None and requires_decoded_counts:
            raise ValueError("static atlas decoded payload byte count is missing")
        if expected_decoded_byte_count is not None and (
            isinstance(expected_decoded_byte_count, bool)
            or not isinstance(expected_decoded_byte_count, int)
            or not 0 < expected_decoded_byte_count <= ATLAS_CHUNK_MAX_BYTES
        ):
            raise ValueError("static atlas decoded payload byte count is invalid")
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
        decoded_payloads[asset_key] = decode_chunk_script(
            payload,
            expected_asset_key=asset_key,
            expected_payload_sha256=payload_sha256,
            expected_payload_encoding=payload_encoding,
            expected_decoded_byte_count=expected_decoded_byte_count,
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


def _validate_static_payloads(
    manifest: Mapping[str, object],
    asset_rows: Sequence[Mapping[str, object]],
    payloads: Mapping[str, Mapping[str, object]],
) -> None:
    compatibility = manifest.get("compatibility")
    if not isinstance(compatibility, Mapping):
        raise ValueError("static atlas compatibility declaration is missing")
    profile = read_calendar_profile(manifest)
    if profile is not None and (
        compatibility.get("node_schema") != "atlas-node-chunk.v2"
        or compatibility.get("index_schema") != "atlas-static-indexes.v4"
    ):
        raise ValueError("Signed static compatibility declaration disagrees")
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
        if read_calendar_profile(payload) != profile:
            raise ValueError("Static payload temporal profile differs from bootstrap")
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
            index_payload = decode_index_bundle(payload)
    if detail_record_order != sorted(detail_record_order):
        raise ValueError("static atlas detail records are not stably ordered")
    if index_payload is None:
        raise ValueError("static atlas index payload is missing")
    if profile is not None:
        _validate_signed_nodes(manifest, asset_rows, payloads, index_payload, profile)
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


def _validate_signed_nodes(
    manifest: Mapping[str, object],
    asset_rows: Sequence[Mapping[str, object]],
    payloads: Mapping[str, Mapping[str, object]],
    indexes: Mapping[str, object],
    profile: str,
) -> None:
    """Reconcile signed payload/index extents against the complete native node set."""
    if read_calendar_profile(indexes) != profile:
        raise ValueError("Signed logical indexes lost their temporal profile")
    metadata: dict[int, Mapping[str, object]] = {}
    for payload in payloads.values():
        if payload.get("schema_version") != "atlas-provenance-chunk.v3":
            continue
        layers = payload.get("layers")
        if not isinstance(layers, list) or payload.get("scientific_signals") != []:
            raise ValueError("Signed provenance cannot add source classification")
        for item in layers:
            if not isinstance(item, Mapping):
                raise ValueError("Signed layer metadata is invalid")
            layer_index, layer = item.get("layer_index"), item.get("layer")
            if (
                type(layer_index) is not int
                or layer_index in metadata
                or item.get("layer_kind") != "point"
                or not isinstance(layer, Mapping)
                or layer.get("semantic_role") != "exploratory_lra_model_anchor"
            ):
                raise ValueError("Signed transport cannot mix source layers")
            metadata[layer_index] = item
    if sorted(metadata) != list(range(len(metadata))):
        raise ValueError("Signed layer metadata indexes are incomplete")
    features_by_layer: dict[int, dict[int, dict[str, object]]] = {
        key: {} for key in metadata
    }
    for row in asset_rows:
        domain = row.get("domain")
        if domain in {"edges", "sequences"}:
            payload = payloads[str(row["asset_key"])]
            if (
                row.get("record_count") != 0
                or payload.get("records") != []
                or payload.get("status") != "unavailable"
            ):
                raise ValueError("Signed transport cannot mix edge or sequence data")
        if domain != "nodes":
            continue
        payload = payloads[str(row["asset_key"])]
        layer_index = payload.get("layer_index")
        if (
            type(layer_index) is not int
            or layer_index not in metadata
            or payload.get("layer_kind") != "point"
        ):
            raise ValueError("Signed node layer ownership is invalid")
        layer = metadata[layer_index]["layer"]
        if not isinstance(layer, Mapping) or payload.get("layer_key") != layer.get(
            "key"
        ):
            raise ValueError("Signed node layer identity disagrees")
        features, positions = payload.get("features"), payload.get("feature_indexes")
        if (
            not isinstance(features, list)
            or not isinstance(positions, list)
            or len(features) != len(positions)
            or row.get("record_count") != len(features)
        ):
            raise ValueError("Signed node feature inventory is invalid")
        for feature, position in zip(features, positions, strict=True):
            if (
                type(position) is not int
                or position < 0
                or position in features_by_layer[layer_index]
                or not isinstance(feature, dict)
                or feature_interval(feature, temporal_profile=profile) is None
            ):
                raise ValueError(
                    "Signed node feature chronology or position is invalid"
                )
            features_by_layer[layer_index][position] = feature
        selection = node_asset_selection(dict(payload))
        if any(row.get(key) != value for key, value in selection.items()):
            raise ValueError(
                "Signed asset selection metadata differs from native nodes"
            )
    reconstructed = []
    for layer_index, item in metadata.items():
        rows = features_by_layer[layer_index]
        layer = item["layer"]
        if not isinstance(layer, Mapping):
            raise AssertionError("Validated signed layer changed type")
        if (
            sorted(rows) != list(range(len(rows)))
            or type(item.get("feature_count")) is not int
            or item["feature_count"] != len(rows)
        ):
            raise ValueError("Signed native node membership is incomplete")
        reconstructed.append(
            {**layer, "features": [rows[index] for index in sorted(rows)]}
        )
    expected = build_indexes(reconstructed, temporal_profile=profile)
    if any(indexes.get(key) != value for key, value in expected.items()):
        raise ValueError("Signed index membership differs from actual native nodes")
    domains = manifest.get("domains")
    nodes = domains.get("nodes") if isinstance(domains, Mapping) else None
    if not isinstance(nodes, Mapping) or nodes.get("record_count") != sum(
        len(rows) for rows in features_by_layer.values()
    ):
        raise ValueError("Signed node denominator does not reconcile")


__all__ = ["validate_static_atlas_assets", "validate_static_atlas_document"]
