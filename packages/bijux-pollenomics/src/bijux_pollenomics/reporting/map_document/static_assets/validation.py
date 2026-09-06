"""Fail-closed validation for static atlas manifests and asset payloads."""

import base64
from collections.abc import Mapping, Sequence
import hashlib
import json

from .budgets import (
    ATLAS_BOOTSTRAP_MAX_BYTES,
    ATLAS_CHUNK_MAX_BYTES,
    ATLAS_DOCUMENT_MAX_BYTES,
    ATLAS_INITIAL_MAX_BYTES,
    ATLAS_INITIAL_MAX_REQUESTS,
    ATLAS_STATIC_ASSETS_MAX_BYTES,
    ATLAS_STATIC_ASSETS_MAX_FILES,
)
from .asset_inventory import normalize_asset_inventory
from .index_bundles import decode_index_bundle
from .models import StaticAtlasAssets
from .serialization import decode_chunk_script


def validate_static_atlas_assets(assets: StaticAtlasAssets) -> None:
    """Fail closed when a generated static asset violates identity or size budgets."""
    manifest_bytes = assets.manifest_path.read_bytes()
    if len(manifest_bytes) > ATLAS_BOOTSTRAP_MAX_BYTES:
        raise ValueError("static atlas bootstrap exceeds its byte budget")
    if json.loads(manifest_bytes) != assets.manifest:
        raise ValueError("static atlas bootstrap bytes do not match the manifest")
    bootstrap_schema = assets.manifest.get("schema_version")
    inventory = assets.manifest.get("assets")
    if bootstrap_schema == "atlas-static-bootstrap.v1":
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
    requires_decoded_counts = (
        isinstance(compatibility, Mapping)
        and compatibility.get("index_schema") == "atlas-static-indexes.v3"
    )
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
            index_payload = decode_index_bundle(payload)
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


__all__ = ["validate_static_atlas_assets", "validate_static_atlas_document"]
