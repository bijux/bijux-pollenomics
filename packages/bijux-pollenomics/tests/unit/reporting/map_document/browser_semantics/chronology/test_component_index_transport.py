"""Versioned static transport preserves disjoint sample supports and old refusals."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (
    build_index_bundle,
    decode_index_bundle,
)
from bijux_pollenomics.reporting.map_document.static_assets.indexes import build_indexes
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)

from ..support import index_transport_helpers, run_node_json, template_block
from .support import _feature


def _logical() -> dict[str, Any]:
    return {
        **build_indexes([{"key": "human", "features": [_feature()]}]),
        "scope_slug": "sample-chronology",
        "version": "published-source-export",
        "build_id": "atlas-" + "a" * 64,
        "detail_record_asset_keys": {},
    }


def _browser_decode(bundle: dict[str, Any]) -> Any:
    helpers = index_transport_helpers()
    identity = template_block(
        "function staticAtlasTemporalIdentity", "function normalizeStaticAtlasBootstrap"
    )
    return run_node_json(
        "const STATIC_ATLAS_BOOTSTRAP={budgets:{chunk_max_bytes:4194304}};"
        "function staticAtlasFailure(message){throw new Error(message)}"
        "function staticAtlasNonnegativeInteger(value,label){if(!Number.isSafeInteger(value)||value<0)throw new Error(label);return value;}"
        "async function staticAtlasSha256(text){return require('node:crypto').createHash('sha256').update(text).digest('hex');}"
        + identity
        + helpers
        + "const payload="
        + json.dumps(bundle)
        + ";(async()=>{try{const decoded=await staticAtlasMergeIndexShards({asset_key:'indexes:1',record_count:payload.reference_count},payload);console.log(JSON.stringify({decoded}));}catch(error){console.log(JSON.stringify({refusal:error.message}));}})();"
    )


def test_component_bundle_roundtrips_in_python_and_actual_browser_decoder() -> None:
    logical = _logical()
    bundle = build_index_bundle(logical)
    assert bundle["schema_version"] == "atlas-static-indexes.v5"
    assert bundle["shard_schema"] == "atlas-static-index-shard.v3"
    assert decode_index_bundle(bundle) == logical
    observed = _browser_decode(bundle)
    assert "refusal" not in observed
    assert observed["decoded"]["component_time_support"] is True
    assert (
        observed["decoded"]["time_interval_feature_indexes"]
        == logical["time_interval_feature_indexes"]
    )
    assert observed["decoded"]["reference_count"] == 1


@pytest.mark.parametrize(
    "tamper",
    [
        "legacy_repeated_feature",
        "marker_missing",
        "old_shard_schema",
        "overlap",
        "duplicate",
    ],
)
def test_component_transport_keeps_legacy_and_overlap_refusals(tamper: str) -> None:
    logical = _logical()
    if tamper == "legacy_repeated_feature":
        logical.pop("component_time_support")
    if tamper == "overlap":
        logical["time_interval_feature_indexes"][1][0] = 105
    if tamper == "duplicate":
        logical["time_interval_feature_indexes"][1] = deepcopy(
            logical["time_interval_feature_indexes"][0]
        )
    bundle = build_index_bundle(logical)
    if tamper == "marker_missing":
        bundle.pop("component_time_support")
    if tamper == "old_shard_schema":
        bundle["shard_schema"] = "atlas-static-index-shard.v1"
    with pytest.raises(ValueError):
        decode_index_bundle(bundle)
    assert "refusal" in _browser_decode(bundle)


def test_component_static_writer_records_schema_and_preserves_node_support(
    tmp_path: Path,
) -> None:
    feature = _feature() | {
        "country": "Sweden",
        "latitude": 59.0,
        "longitude": 18.0,
        "title": "Owned sample control",
    }
    assets = write_static_atlas_assets(
        tmp_path,
        slug="sample-chronology",
        version="published-export",
        point_layers=[{"key": "human", "features": [feature]}],
        polygon_layers=[],
    )
    assert (
        cast(dict[str, Any], assets.manifest["compatibility"])["index_schema"]
        == "atlas-static-indexes.v5"
    )
    rows = normalize_asset_inventory(assets.manifest["assets"])
    payloads = [
        cast(
            dict[str, Any],
            decode_chunk_script(
                path.read_bytes(),
                expected_asset_key=str(row["asset_key"]),
                expected_payload_sha256=str(row["payload_sha256"]),
                expected_payload_encoding=str(row["payload_encoding"]),
                expected_decoded_byte_count=cast(int, row["decoded_byte_count"]),
            ),
        )
        for row, path in zip(rows, assets.asset_paths, strict=True)
    ]
    index = next(
        payload
        for row, payload in zip(rows, payloads, strict=True)
        if row["domain"] == "indexes"
    )
    assert decode_index_bundle(index)["time_interval_feature_indexes"] == [
        [100, 110, "human", 0],
        [300, 310, "human", 0],
    ]
    node = next(
        payload
        for row, payload in zip(rows, payloads, strict=True)
        if row["domain"] == "nodes"
    )
    assert node["features"][0]["sample_chronologies"] == feature["sample_chronologies"]


def test_index_unions_overlapping_samples_without_filling_disjoint_gap() -> None:
    feature = cast(dict[str, Any], _feature())
    feature["sample_ids"].append("overlap")
    support = deepcopy(feature["sample_chronologies"][0])
    support["sample_id"] = "overlap"
    support["chronology"]["time_start_bp"] = 105
    support["chronology"]["time_end_bp"] = 115
    feature["sample_chronologies"].append(support)
    indexes = build_indexes([{"key": "human", "features": [feature]}])
    assert indexes["time_interval_feature_indexes"] == [
        [100, 115, "human", 0],
        [300, 310, "human", 0],
    ]
