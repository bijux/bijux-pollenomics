"""Deterministic browser-transport fixtures for source chronology tests."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json

ASSET_TABLE_FIELDS = (
    "asset_key",
    "domain",
    "sequence",
    "path",
    "sha256",
    "integrity",
    "payload_sha256",
    "payload_encoding",
    "decoded_byte_count",
    "byte_count",
    "record_count",
    "initial_load",
    "layer_index",
    "layer_key",
    "layer_kind",
    "country_keys",
    "bounds",
    "time_min_bp",
    "time_max_bp",
    "untimed_record_count",
    "scientific_signal_ids",
)


def _index_shard(
    *, shard_number: int, index_kind: str, entries: list[list[object]]
) -> dict[str, object]:
    decoded = json.dumps(
        {
            "schema_version": "atlas-static-index-shard.v1",
            "index_kind": index_kind,
            "entries": entries,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return {
        "shard_number": shard_number,
        "index_kind": index_kind,
        "payload_encoding": "gzip_base64",
        "record_count": len(entries),
        "decoded_byte_count": len(decoded),
        "payload_sha256": hashlib.sha256(decoded).hexdigest(),
        "payload_gzip_base64": base64.b64encode(
            gzip.compress(decoded, mtime=0)
        ).decode(),
    }


def sharded_index_payload(*, duplicate_country: bool = False) -> dict[str, object]:
    """Return a multi-part v3 index bundle with every governed index kind."""
    second_country = "Norway" if duplicate_country else "Sweden"
    definitions: list[tuple[str, list[list[object]]]] = [
        ("country_feature_indexes", [["Norway", "source-samples", [1]]]),
        ("country_feature_indexes", [[second_country, "source-samples", [0, 2]]]),
        ("spatial_degree_feature_indexes", [["59:18", "source-samples", [0, 1]]]),
        ("time_interval_feature_indexes", [[100, 200, "source-samples", 0]]),
        ("signal_layer_indexes", [["source-samples", ["source-samples"]]]),
        ("detail_record_asset_keys", [["neotoma:site:1", "details:1"]]),
    ]
    shards = [
        _index_shard(shard_number=index, index_kind=kind, entries=entries)
        for index, (kind, entries) in enumerate(definitions, start=1)
    ]
    return {
        "schema_version": "atlas-static-indexes.v3",
        "shard_schema": "atlas-static-index-shard.v1",
        "shard_count": len(shards),
        "reference_count": 4,
        "scope_slug": "nordic",
        "version": "test",
        "build_id": "atlas-" + ("a" * 64),
        "asset_key": "indexes:1",
        "shards": shards,
    }


def compressed_node_asset(
    asset_key: str,
    *,
    padding: str = "",
    decoded_byte_count: int | None = None,
    payload_sha256: str | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    """Return one manifest row and gzip envelope for a node payload."""
    payload = {
        "schema_version": "atlas-node-chunk.v1",
        "scope_slug": "nordic",
        "version": "test",
        "build_id": "atlas-" + ("a" * 64),
        "asset_key": asset_key,
        "layer_key": "source-samples",
        "layer_index": 0,
        "layer_kind": "point",
        "feature_indexes": [],
        "features": [],
        "padding": padding,
    }
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    digest = payload_sha256 or hashlib.sha256(encoded).hexdigest()
    row: dict[str, object] = {
        "asset_key": asset_key,
        "domain": "nodes",
        "payload_encoding": "gzip_base64",
        "payload_sha256": digest,
        "decoded_byte_count": (
            len(encoded) if decoded_byte_count is None else decoded_byte_count
        ),
        "record_count": 0,
        "layer_key": "source-samples",
        "layer_index": 0,
        "layer_kind": "point",
    }
    envelope: dict[str, object] = {
        "asset_key": asset_key,
        "payload_encoding": "gzip_base64",
        "payload_sha256": digest,
        "payload_gzip_base64": base64.b64encode(
            gzip.compress(encoded, mtime=0)
        ).decode(),
    }
    return row, envelope


def compressed_provenance_asset(
    asset_key: str = "provenance:0",
    *,
    decoded_byte_count: int | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    """Return one manifest row and gzip envelope for provenance metadata."""
    payload = {
        "schema_version": "atlas-provenance-chunk.v3",
        "scope_slug": "nordic",
        "version": "test",
        "build_id": "atlas-" + ("a" * 64),
        "asset_key": asset_key,
        "layers": [],
        "scientific_signals": [],
    }
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    digest = hashlib.sha256(encoded).hexdigest()
    row: dict[str, object] = {
        "asset_key": asset_key,
        "domain": "provenance",
        "payload_encoding": "gzip_base64",
        "payload_sha256": digest,
        "decoded_byte_count": (
            len(encoded) if decoded_byte_count is None else decoded_byte_count
        ),
        "record_count": 0,
    }
    envelope: dict[str, object] = {
        "asset_key": asset_key,
        "payload_encoding": "gzip_base64",
        "payload_sha256": digest,
        "payload_gzip_base64": base64.b64encode(
            gzip.compress(encoded, mtime=0)
        ).decode(),
    }
    return row, envelope


def compact_bootstrap() -> dict[str, object]:
    """Return a compact v2 inventory with node and non-node rows."""
    node = [
        "nodes:0",
        "nodes",
        0,
        "atlas-nodes.js",
        "a" * 64,
        "sha256-" + ("A" * 43) + "=",
        "b" * 64,
        "gzip_base64",
        300,
        220,
        1,
        False,
        0,
        "source-samples",
        "point",
        ["Sweden"],
        [55.0, 10.0, 70.0, 25.0],
        100.0,
        200.0,
        0,
        [],
    ]
    indexes = [
        "indexes:1",
        "indexes",
        1,
        "atlas-indexes.js",
        "c" * 64,
        "sha256-" + ("B" * 43) + "=",
        "d" * 64,
        "json",
        400,
        520,
        1,
        True,
        *([None] * 9),
    ]
    return {
        "schema_version": "atlas-static-bootstrap.v2",
        "assets": {
            "schema_version": "atlas-static-asset-table.v1",
            "fields": list(ASSET_TABLE_FIELDS),
            "record_count": 2,
            "records": [node, indexes],
        },
    }


__all__ = [
    "ASSET_TABLE_FIELDS",
    "compact_bootstrap",
    "compressed_node_asset",
    "compressed_provenance_asset",
    "sharded_index_payload",
]
