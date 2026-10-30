"""Declared document transport restores the complete existing search representation."""

from __future__ import annotations

import base64
from collections.abc import Callable
from copy import deepcopy
import gzip
from hashlib import sha256
from importlib.resources import files
import json
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (
    build_index_bundle,
)
from bijux_pollenomics.reporting.map_document.static_assets.search import (
    build_search_index,
)
from bijux_pollenomics.reporting.map_document.template import NATIVE_LRA_CONTROLLER

from ..support import index_transport_helpers, run_node_json, template_block

CODEC = "atlas-search-documents.v1"


def logical(mode: str) -> dict[str, Any]:
    texts = [
        "",
        "a",
        "ab",
        "abc",
        "Åa",
        "💠",
        "\ud83d",
        "\udc00",
        "a\u0308",
        ".(a)",
        "same",
        "same",
        "𐐀a",
    ]
    features = [{"record_id": "repeated", "title": text} for text in texts]
    search = cast(
        dict[str, Any], build_search_index([{"key": "pollen", "features": features}])
    )
    search["d:0:0"]["text"] = ""
    for key in list(search):
        if key.startswith("p:"):
            search[key] = [value for value in search[key] if value != "d:0:0"]
            if not search[key]:
                del search[key]
    return {
        "schema_version": "atlas-static-signed-indexes.v1"
        if mode == "signed"
        else "atlas-static-indexes.v2",
        "scope_slug": "fixture",
        "version": "v66",
        "build_id": "atlas-" + "a" * 64,
        **(
            {"temporal_profile": "calendar-bp1950-signed.v1", "temporal_axis": "BP1950"}
            if mode == "signed"
            else {}
        ),
        **({"component_time_support": True} if mode == "components" else {}),
        "country_feature_indexes": {"Sweden": {"pollen": list(range(len(features)))}},
        "spatial_degree_feature_indexes": {},
        "time_interval_feature_indexes": [
            [-5 if mode == "signed" else 1, 5, "pollen", 0]
        ],
        "signal_layer_indexes": {"pollen": ["pollen"]},
        "detail_record_asset_keys": {},
        "search_index_abi": "atlas-substring-postings.v1",
        "text_search_index": search,
    }


def packet(mode: str = "legacy") -> dict[str, Any]:
    expected = logical(mode)
    bundle = build_index_bundle(expected, search_transport_schema=CODEC)
    return {
        "bundle": {**bundle, "asset_key": "indexes:6"},
        "expected": expected,
        "manifest": {
            "schema_version": "atlas-static-bootstrap.v3"
            if mode == "signed"
            else "atlas-static-bootstrap.v2",
            **{key: expected[key] for key in ("scope_slug", "version", "build_id")},
            **(
                {key: expected[key] for key in ("temporal_profile", "temporal_axis")}
                if mode == "signed"
                else {}
            ),
            "compatibility": {
                "index_schema": bundle["schema_version"],
                "search_index_abi": expected["search_index_abi"],
                "search_transport_schema": CODEC,
            },
            "domains": {"indexes": {"record_count": 13}},
            "budgets": {"chunk_max_bytes": 4194304},
        },
    }


def observe(data: dict[str, Any]) -> dict[str, Any]:
    assets = files("bijux_pollenomics.reporting.map_document").joinpath("assets")
    native = NATIVE_LRA_CONTROLLER[
        NATIVE_LRA_CONTROLLER.index(
            "function nativeCalendarNumber"
        ) : NATIVE_LRA_CONTROLLER.index("function nativeCalendarSame")
    ]
    return cast(
        dict[str, Any],
        run_node_json(
            "const data="
            + json.dumps(data)
            + ";const STATIC_ATLAS_BOOTSTRAP=data.manifest;"
            + template_block(
                "function staticAtlasFailure", "function normalizeStaticAtlasBootstrap"
            )
            + template_block(
                "async function staticAtlasSha256",
                "async function staticAtlasBoundedGunzip",
            )
            + native
            + index_transport_helpers()
            + assets.joinpath("search-index.js").read_text()
            + r"""
(async()=>{try{
 const row={asset_key:'indexes:6',domain:'indexes',record_count:13};
 const decoded=await staticAtlasIndexTransport.consume(row,data.bundle,[row]);
 const original=data.expected.text_search_index;
 const expectedKeys=Object.keys(original),actualKeys=Object.keys(decoded.text_search_index);
 const same=JSON.stringify(actualKeys)===JSON.stringify(expectedKeys)&&expectedKeys.every(key=>Array.isArray(original[key])?JSON.stringify(decoded.text_search_index[key])===JSON.stringify(original[key]):Object.keys(original[key]).every(field=>JSON.stringify(decoded.text_search_index[key][field])===JSON.stringify(original[key][field])));
 const published=atlasPublishedSearch(decoded,[{layer_kind:'point',layer_index:0,feature_count:13,layer:{key:'pollen'}}]);
 const visible=new Map(Object.entries(original).filter(([key])=>key.startsWith('d:')).reverse().map(([key,row],order)=>[key,{order,text:row.text,entry:{key}}]));
 const state={published,visible,fallback:[]};
 const queries=['a','ab','abc','💠','\ud83d','\udc00','a\u0308','.(a)','same','𐐨','absent'];
 const answers=queries.every(query=>JSON.stringify(atlasLookupSearch(state,query).map(row=>row.key))===JSON.stringify([...visible.values()].filter(row=>row.text.includes(query)).slice(0,12).map(row=>row.entry.key)));
 console.log(JSON.stringify({same,answers,keys:actualKeys.filter(key=>key.startsWith('d:')),transportMetadata:Object.hasOwn(decoded,'search_transport_schema')||Object.hasOwn(decoded,'search_transport_counts')}));
}catch(error){console.log(JSON.stringify({refusal:error.message}))}})();
"""
        ),
    )


@pytest.mark.parametrize("mode", ["legacy", "signed", "components"])
def test_document_codec_preserves_exact_map_and_literal_query_order(mode: str) -> None:
    observed = observe(packet(mode))
    assert "refusal" not in observed
    assert observed["same"] is True
    assert observed["answers"] is True
    assert observed["transportMetadata"] is False
    assert observed["keys"].index("d:0:10") < observed["keys"].index("d:0:2")


def repack(shard: dict[str, Any], transform: Callable[[dict[str, Any]], None]) -> None:
    raw = json.loads(gzip.decompress(base64.b64decode(shard["payload_gzip_base64"])))
    transform(raw)
    body = json.dumps(
        raw, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode()
    shard.update(
        payload_gzip_base64=base64.b64encode(gzip.compress(body, mtime=0)).decode(),
        decoded_byte_count=len(body),
        payload_sha256=sha256(body).hexdigest(),
        record_count=len(raw["entries"]),
    )


@pytest.mark.parametrize(
    "defect",
    [
        "compat_missing",
        "compat_null",
        "bundle_null",
        "counts_missing",
        "counts_extra",
        "counts_bool",
        "counts_negative",
        "counts_fraction",
        "shard_missing",
        "shard_unknown",
        "nonsearch_marker",
        "document_identity",
        "posting_smuggled",
    ],
)
def test_document_codec_refuses_mixed_tags_counts_and_non_document_rows(
    defect: str,
) -> None:
    data = packet()
    bundle, compat = data["bundle"], data["manifest"]["compatibility"]
    counts = bundle["search_transport_counts"]
    if defect == "compat_missing":
        del compat["search_transport_schema"]
    elif defect == "compat_null":
        compat["search_transport_schema"] = None
    elif defect == "bundle_null":
        bundle["search_transport_schema"] = None
    elif defect == "counts_missing":
        del bundle["search_transport_counts"]
    elif defect == "counts_extra":
        counts["foreign"] = 0
    elif defect in {"counts_bool", "counts_negative", "counts_fraction"}:
        counts["document_count"] = {
            "counts_bool": True,
            "counts_negative": -1,
            "counts_fraction": 0.5,
        }[defect]
    else:
        shard = next(
            item
            for item in bundle["shards"]
            if (item["index_kind"] != "text_search_index")
            == (defect == "nonsearch_marker")
        )

        def change(raw: dict[str, Any]) -> None:
            if defect == "shard_missing":
                del raw["search_transport_schema"]
            elif defect in {"shard_unknown", "nonsearch_marker"}:
                raw["search_transport_schema"] = (
                    "unknown" if defect == "shard_unknown" else CODEC
                )
            elif defect == "document_identity":
                raw["entries"][0][1]["feature_index"] = 99
            else:
                raw["entries"].append(["p:ffff", []])

        repack(shard, change)
    assert "refusal" in observe(data)


@pytest.mark.parametrize(
    "field",
    [
        "document_count",
        "utf16_unit_count",
        "posting_key_count",
        "posting_reference_count",
    ],
)
@pytest.mark.parametrize("delta", [-1, 1])
def test_document_codec_refuses_under_and_over_declared_expansion(
    field: str, delta: int
) -> None:
    data = deepcopy(packet())
    data["bundle"]["search_transport_counts"][field] += delta
    assert "refusal" in observe(data)


def test_document_bound_refuses_before_decoding_a_later_frame() -> None:
    data = packet()
    bundle = data["bundle"]
    shard = next(
        item for item in bundle["shards"] if item["index_kind"] == "text_search_index"
    )
    later = deepcopy(shard)
    repack(shard, lambda raw: raw.update(entries=raw["entries"][:1]))
    repack(later, lambda raw: raw.update(entries=raw["entries"][1:]))
    later["shard_number"] = len(bundle["shards"]) + 1
    later["payload_sha256"] = "0" * 64
    bundle["shards"].append(later)
    bundle["shard_count"] += 1
    bundle["search_transport_counts"]["document_count"] = 0
    observed = observe(data)
    assert "merged search documents exceed" in observed["refusal"]
