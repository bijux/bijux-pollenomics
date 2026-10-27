"""Independent physical-packet/browser parity on manually declared logical fields."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
import json
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (
    build_index_bundle,
)
from bijux_pollenomics.reporting.map_document.static_assets.index_transport import (
    decode_index_payloads,
)
from bijux_pollenomics.reporting.map_document.template import NATIVE_LRA_CONTROLLER

from ..support import run_node_json, template_block

PART_SCHEMA = "atlas-static-index-part.v1"


def logical_fields(mode: str = "legacy") -> dict[str, Any]:
    intervals = [[100, 110, "pollen", 0], [300, 310, "pollen", 1]]
    if mode == "components":
        intervals = [
            [100, 110, "pollen", 0],
            [300, 310, "pollen", 0],
            [500, 510, "pollen", 1],
        ]
    if mode == "signed":
        intervals = [[-55, -50, "pollen", 0], [100, 110, "pollen", 1]]
    return {
        "schema_version": "atlas-static-signed-indexes.v1"
        if mode == "signed"
        else "atlas-static-indexes.v2",
        "scope_slug": "fixture",
        "version": "v66",
        "build_id": "atlas-" + "a" * 64,
        **({"component_time_support": True} if mode == "components" else {}),
        **(
            {"temporal_profile": "calendar-bp1950-signed.v1", "temporal_axis": "BP1950"}
            if mode == "signed"
            else {}
        ),
        "country_feature_indexes": {"Sweden": {"pollen": [0, 1]}},
        "spatial_degree_feature_indexes": {"55:13": {"pollen": [0, 1]}},
        "time_interval_feature_indexes": intervals,
        "signal_layer_indexes": {"pollen-signal": ["pollen"]},
        "detail_record_asset_keys": {"site:1": "details:4", "site:2": "details:4"},
        "search_index_abi": "atlas-substring-postings.v1",
        "text_search_index": {
            "d:0:0": {
                "layer_index": 0,
                "feature_index": 0,
                "layer_key": "pollen",
                "record_id": "site:1",
                "text": "a",
            },
            "d:0:1": {
                "layer_index": 0,
                "feature_index": 1,
                "layer_key": "pollen",
                "record_id": "site:2",
                "text": "b",
            },
            "p:0061": ["d:0:0"],
            "p:0062": ["d:0:1"],
        },
    }


def literal_digest(value: object) -> str:
    return sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def packets(
    mode: str = "legacy", *, split: bool = True, unicode_identity: bool = False
) -> dict[str, Any]:
    expected = logical_fields(mode)
    if unicode_identity:
        expected["version"] = "Åland-💠-\x7f"
    bundle = build_index_bundle(expected)
    manifest: dict[str, Any] = {
        "schema_version": "atlas-static-bootstrap.v3"
        if mode == "signed"
        else "atlas-static-bootstrap.v2",
        **{
            key: value
            for key, value in expected.items()
            if key
            in {
                "scope_slug",
                "version",
                "build_id",
                "temporal_profile",
                "temporal_axis",
            }
        },
        "compatibility": {
            "index_schema": bundle["schema_version"],
            "search_index_abi": expected["search_index_abi"],
            **({"index_transport_schema": PART_SCHEMA} if split else {}),
        },
        "domains": {"indexes": {"record_count": 4}},
        "budgets": {"chunk_max_bytes": 4194304},
    }
    rows: list[dict[str, Any]] = []
    payloads: dict[str, dict[str, Any]] = {}
    if split:
        shards = cast(list[dict[str, Any]], bundle["shards"])
        middle = len(shards) // 2
        assert 0 < middle < len(shards)
        header = {key: value for key, value in bundle.items() if key != "shards"}
        for number, (first, stop) in enumerate(((0, middle), (middle, len(shards))), 1):
            key = f"indexes:{11 + number}"
            rows.append(
                {
                    "asset_key": key,
                    "sequence": 11 + number,
                    "domain": "indexes",
                    "record_count": stop - first,
                }
            )
            payloads[key] = {
                **header,
                "schema_version": PART_SCHEMA,
                "bundle_schema": bundle["schema_version"],
                "bundle_sha256": literal_digest(bundle),
                "part_number": number,
                "part_count": 2,
                "first_shard_number": first + 1,
                "last_shard_number": stop,
                "shards": deepcopy(shards[first:stop]),
                "asset_key": key,
            }
    else:
        rows.append(
            {
                "asset_key": "indexes:12",
                "sequence": 12,
                "domain": "indexes",
                "record_count": 4,
            }
        )
        payloads["indexes:12"] = {**bundle, "asset_key": "indexes:12"}
    manifest["assets"] = rows
    return {
        "rows": rows,
        "payloads": payloads,
        "manifest": manifest,
        "expected": expected,
    }


def browser(
    packet: dict[str, Any], *, action: str = "serial", reverse: bool = False
) -> dict[str, Any]:
    assets = files("bijux_pollenomics.reporting.map_document").joinpath("assets")
    native_number = NATIVE_LRA_CONTROLLER[
        NATIVE_LRA_CONTROLLER.index(
            "function nativeCalendarNumber"
        ) : NATIVE_LRA_CONTROLLER.index("function nativeCalendarSame")
    ]
    source = (
        "globalThis.crypto=require('node:crypto').webcrypto;"
        "const data="
        + json.dumps({**packet, "action": action, "reverse": reverse})
        + ";"
        + "const STATIC_ATLAS_BOOTSTRAP=data.manifest;"
        + template_block(
            "function staticAtlasFailure", "function staticAtlasNonnegativeInteger"
        )
        + template_block(
            "function staticAtlasNonnegativeInteger",
            "function staticAtlasNullableFiniteNumber",
        )
        + template_block(
            "function staticAtlasTemporalIdentity",
            "function normalizeStaticAtlasBootstrap",
        )
        + template_block(
            "async function staticAtlasSha256",
            "async function staticAtlasBoundedGunzip",
        )
        + template_block(
            "async function staticAtlasBoundedGunzip",
            "function indexTransportDescriptor",
        )
        + native_number
        + assets.joinpath("index-transport.js").read_text()
        + assets.joinpath("search-index.js").read_text()
        + r"""
(async()=>{
  try {
    const controller=globalThis.BijuxPollenomicsIndexTransport.create({
      bootstrap:STATIC_ATLAS_BOOTSTRAP,failure:staticAtlasFailure,
      temporalIdentity:staticAtlasTemporalIdentity,nonnegativeInteger:staticAtlasNonnegativeInteger,
      nativeCalendarNumber,boundedGunzip:staticAtlasBoundedGunzip,sha256:staticAtlasSha256});
    const rows=data.rows, ordered=data.reverse?[...rows].reverse():rows;
    const consume=row=>controller.consume(row,data.payloads[row.asset_key],rows);
    let results;
    if(data.action==='concurrent') results=await Promise.all(ordered.map(consume));
    else if(data.action==='repeat') {
      results=[await consume(rows[0]),await consume(rows[0])];
      for(const row of rows.slice(1))results.push(await consume(row));
      results.push(await consume(rows[rows.length-1]));
    } else if(data.action==='conflict') {
      await consume(rows[0]);
      const changed=structuredClone(data.payloads[rows[0].asset_key]);
      changed.bundle_sha256='b'.repeat(64);
      await controller.consume(rows[0],changed,rows);
      console.log(JSON.stringify({accepted_conflicting_repeat:true}));
      return;
    } else if(data.action==='partial') results=[await consume(rows[0])];
    else {results=[];for(const row of ordered)results.push(await consume(row));}
    const completed=results.filter(value=>value!==null);
    const decoded=completed[completed.length-1]||null;
    let searches=null;
    if(decoded) {
      const published=atlasPublishedSearch(decoded,[{layer_kind:'point',layer_index:0,feature_count:2,layer:{key:'pollen'}}]);
      const visible=new Map(['a','b'].map((text,index)=>[`d:0:${index}`,{order:index,text,entry:{record_id:`site:${index+1}`}}]));
      const state={published,visible,fallback:[]};
      searches=Object.fromEntries(['a','b','absent'].map(query=>[query,atlasLookupSearch(state,query).map(row=>row.record_id)]));
    }
    console.log(JSON.stringify({decoded,published:results.map(value=>value!==null),searches}));
  } catch(error) {console.log(JSON.stringify({refusal:error.message}));}
})();
"""
    )
    return cast(dict[str, Any], run_node_json(source))


@pytest.mark.parametrize("mode", ["legacy", "signed", "components"])
@pytest.mark.parametrize("reverse", [False, True])
def test_manual_packets_preserve_logical_fields_and_queries(
    mode: str, reverse: bool
) -> None:
    packet = packets(mode)
    assert (
        decode_index_payloads(
            packet["rows"], packet["payloads"], manifest=packet["manifest"]
        )
        == packet["expected"]
    )
    observed = browser(packet, action="concurrent", reverse=reverse)
    assert "refusal" not in observed
    assert sum(observed["published"]) == 1
    assert {key: observed["decoded"][key] for key in packet["expected"]} == packet[
        "expected"
    ]
    assert observed["decoded"]["reference_count"] == 4
    assert observed["searches"] == {"a": ["site:1"], "b": ["site:2"], "absent": []}


def test_partial_and_authenticated_repeat_do_not_publish_incomplete_or_duplicate_indexes() -> (
    None
):
    packet = packets()
    partial = browser(packet, action="partial")
    assert partial == {"decoded": None, "published": [False], "searches": None}
    repeated = browser(packet, action="repeat")
    assert repeated["published"] == [False, False, True, True]
    assert repeated["decoded"]["country_feature_indexes"] == {
        "Sweden": {"pollen": [0, 1]}
    }
    assert repeated["decoded"]["reference_count"] == 4
    assert "refusal" in browser(packet, action="conflict")


@pytest.mark.parametrize("mode", ["legacy", "signed", "components"])
def test_singleton_path_keeps_legacy_logical_semantics(mode: str) -> None:
    packet = packets(mode, split=False)
    observed = browser(packet)
    assert "refusal" not in observed
    assert observed["published"] == [True]
    assert {key: observed["decoded"][key] for key in packet["expected"]} == packet[
        "expected"
    ]
    assert "index_transport_schema" not in packet["manifest"]["compatibility"]


def test_python_ascii_escaping_matches_actual_browser_bundle_hash() -> None:
    packet = packets(unicode_identity=True)
    observed = browser(packet)
    assert "refusal" not in observed
    assert observed["decoded"]["version"] == "Åland-💠-\x7f"


@pytest.mark.parametrize(
    "corruption",
    [
        "missing",
        "duplicate_part",
        "manifest_reorder",
        "mixed_build",
        "mixed_abi",
        "mixed_profile",
        "bundle_digest",
        "local_count",
        "global_count",
        "null_transport",
        "gapped_sequence",
        "duplicate_shard",
    ],
)
def test_python_and_actual_browser_refuse_invalid_complete_transport(
    corruption: str,
) -> None:
    packet = packets()
    rows, payloads, manifest = packet["rows"], packet["payloads"], packet["manifest"]
    first, second = (payloads[row["asset_key"]] for row in rows)
    if corruption == "missing":
        del payloads[rows.pop()["asset_key"]]
    elif corruption == "duplicate_part":
        second["part_number"] = first["part_number"]
    elif corruption == "manifest_reorder":
        rows.reverse()
    elif corruption == "mixed_build":
        second["build_id"] = "atlas-" + "b" * 64
    elif corruption == "mixed_abi":
        second["search_index_abi"] = "another-abi"
    elif corruption == "mixed_profile":
        second.update(
            temporal_profile="calendar-bp1950-signed.v1", temporal_axis="BP1950"
        )
    elif corruption == "bundle_digest":
        first["bundle_sha256"] = second["bundle_sha256"] = "b" * 64
    elif corruption == "local_count":
        rows[0]["record_count"] = 4
    elif corruption == "global_count":
        manifest["domains"]["indexes"]["record_count"] = first["shard_count"]
    elif corruption == "null_transport":
        manifest["compatibility"]["index_transport_schema"] = None
    elif corruption == "gapped_sequence":
        old = rows[1]["asset_key"]
        rows[1].update(sequence=14, asset_key="indexes:14")
        payloads["indexes:14"] = payloads.pop(old)
        payloads["indexes:14"]["asset_key"] = "indexes:14"
    else:
        copied = deepcopy(first["shards"][0])
        copied["shard_number"] = second["first_shard_number"]
        second["shards"][0] = copied
    with pytest.raises(ValueError):
        decode_index_payloads(rows, payloads, manifest=manifest)
    assert "refusal" in browser(packet)
