"""Lossless, bounded static-index bundle tests."""

from __future__ import annotations

from copy import deepcopy
import base64
import gzip
import hashlib
import json

import pytest

from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (
    INDEX_KINDS,
    build_index_bundle,
    decode_index_bundle,
)
from bijux_pollenomics.reporting.map_document.static_assets.indexes import (
    build_indexes,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    canonical_json,
)

from .fixtures.layers import build_point_layers


def _logical_indexes() -> dict[str, object]:
    return {
        **build_indexes(build_point_layers(large=True)),
        "detail_record_asset_keys": {
            "site:1": "details:4",
            "site:2": "details:4",
        },
        "scope_slug": "nordic",
        "version": "v66",
        "build_id": "atlas-" + "a" * 64,
    }


def test_multi_shard_bundle_reconstructs_exact_logical_v2_indexes() -> None:
    logical = _logical_indexes()

    bundle = build_index_bundle(logical)
    decoded = decode_index_bundle(bundle)

    assert isinstance(bundle["shard_count"], int)
    assert bundle["shard_count"] >= len(INDEX_KINDS)
    assert canonical_json(decoded) == canonical_json(logical)
    assert decoded["scope_slug"] == "nordic"
    assert decoded["version"] == "v66"
    assert decoded["build_id"] == "atlas-" + "a" * 64


@pytest.mark.parametrize(
    "tamper", ["missing", "overlap", "digest", "count", "reference_count"]
)
def test_index_bundle_rejects_incomplete_or_tampered_shards(tamper: str) -> None:
    bundle = deepcopy(build_index_bundle(_logical_indexes()))
    shards = bundle["shards"]
    assert isinstance(shards, list)
    assert isinstance(shards[0], dict)
    if tamper == "missing":
        del shards[0]
        for number, shard in enumerate(shards, start=1):
            assert isinstance(shard, dict)
            shard["shard_number"] = number
        bundle["shard_count"] = len(shards)
    elif tamper == "overlap":
        duplicate = deepcopy(shards[0])
        shards.insert(1, duplicate)
        for number, shard in enumerate(shards, start=1):
            assert isinstance(shard, dict)
            shard["shard_number"] = number
        bundle["shard_count"] = len(shards)
    elif tamper == "digest":
        shards[0]["payload_sha256"] = "0" * 64
    elif tamper == "count":
        shards[0]["record_count"] = -1
    else:
        bundle["reference_count"] = -1

    with pytest.raises(ValueError):
        decode_index_bundle(bundle)


def test_index_bundle_refuses_invalid_nested_producer_rows() -> None:
    logical = _logical_indexes()
    country_indexes = logical["country_feature_indexes"]
    assert isinstance(country_indexes, dict)
    country_indexes[next(iter(country_indexes))] = []

    with pytest.raises(TypeError, match="nested rows must be an object"):
        build_index_bundle(logical)


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf")])
def test_index_bundle_refuses_non_finite_time_endpoints(non_finite: float) -> None:
    bundle = deepcopy(build_index_bundle(_logical_indexes()))
    shards = bundle["shards"]
    assert isinstance(shards, list)
    envelope = next(
        shard
        for shard in shards
        if isinstance(shard, dict)
        and shard["index_kind"] == "time_interval_feature_indexes"
    )
    payload = json.loads(
        gzip.decompress(base64.b64decode(envelope["payload_gzip_base64"]))
    )
    entries = payload["entries"]
    assert isinstance(entries, list)
    assert isinstance(entries[0], list)
    entries[0][0] = non_finite
    raw = json.dumps(
        payload,
        ensure_ascii=True,
        allow_nan=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    envelope["decoded_byte_count"] = len(raw)
    envelope["payload_sha256"] = hashlib.sha256(raw).hexdigest()
    envelope["payload_gzip_base64"] = base64.b64encode(
        gzip.compress(raw, compresslevel=9, mtime=0)
    ).decode("ascii")

    with pytest.raises(ValueError, match="time interval index row is invalid"):
        decode_index_bundle(bundle)
