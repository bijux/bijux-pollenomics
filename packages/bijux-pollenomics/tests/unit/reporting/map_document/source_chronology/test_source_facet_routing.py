"""Exact source facets route to bounded transport without changing native membership."""

from __future__ import annotations

from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.static_assets import nodes


def source_layer(features: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "key": "neotoma-source-exact-taxon",
        "semantic_role": "source_chronology_context",
        "node_level": "source_taxon",
        "features": features,
    }


def test_facet_first_partition_preserves_original_feature_indexes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    features = [
        {
            "node_id": f"source-node-{index}",
            "country": "Sweden",
            "latitude": 61.0,
            "longitude": 15.0,
            "source_taxon_id": 1 if index % 40 == 0 else 2,
            "native_payload": "x" * 900,
        }
        for index in range(278)
    ]
    monkeypatch.setattr(nodes, "ATLAS_COMPRESSED_CHUNK_TARGET_BYTES", 2200)
    _, payloads = nodes.build_node_payloads(
        slug="nordic",
        version="v66",
        point_layers=[source_layer(features)],
        polygon_layers=[],
    )
    assert len(payloads) == 139
    parts = cast(list[dict[str, Any]], payloads)
    selected = [
        row
        for row in parts
        if any(feature["source_taxon_id"] == 1 for feature in row["features"])
    ]
    assert len(selected) <= 4
    restored = {
        index: feature
        for row in parts
        for index, feature in zip(row["feature_indexes"], row["features"], strict=True)
    }
    assert len(restored) == len(features)
    assert [restored[index] for index in sorted(restored)] == features


def routed_payload(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    from bijux_pollenomics.reporting.map_document.static_assets.source_facets.routing import (
        bind_source_facet_routes,
    )

    features = [
        {
            "node_id": str(index),
            "country": "Sweden",
            "source_taxon_id": 1 if index % 40 == 0 else 2,
            "native_payload": "x" * 900,
        }
        for index in range(278)
    ]
    layer = source_layer(features)
    layer["facet_metadata"] = {
        "source_taxa": [
            {
                "value": f"source:neotoma:taxon:{identity}",
                "source_taxon_id": identity,
                "node_count": sum(
                    row["source_taxon_id"] == identity for row in features
                ),
            }
            for identity in [1, 2, 99]
        ]
    }
    monkeypatch.setattr(nodes, "ATLAS_COMPRESSED_CHUNK_TARGET_BYTES", 2200)
    metadata, parts = nodes.build_node_payloads(
        slug="nordic", version="v66", point_layers=[layer], polygon_layers=[]
    )
    payloads = {f"nodes:{index}": part for index, part in enumerate(parts, 1)}
    bind_source_facet_routes(metadata, payloads)
    return {"metadata": metadata, "payloads": payloads}


@pytest.mark.parametrize(
    "mutation", ["facet", "omitted_all", "asset", "duplicate", "count", "schema"]
)
def test_routing_is_rederived_from_every_actual_native_buffer(
    monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    from bijux_pollenomics.reporting.map_document.static_assets.source_facets.routing import (
        validate_source_facet_routes,
    )

    data = routed_payload(monkeypatch)
    metadata, payloads = data["metadata"], data["payloads"]
    validate_source_facet_routes(metadata, payloads, required=True)
    layer = metadata[0]["layer"]
    route = layer["static_source_facets"]
    if mutation == "facet":
        del route["facets"]["1"]
    elif mutation == "omitted_all":
        del layer["static_source_facets"]
    elif mutation == "asset":
        route["facets"]["1"]["asset_keys"][0] = "nodes:foreign"
    elif mutation == "duplicate":
        route["facets"]["1"]["asset_keys"].append(route["facets"]["1"]["asset_keys"][0])
    elif mutation == "count":
        route["facets"]["1"]["record_count"] = True
    else:
        route["schema_version"] = "unsupported"
    with pytest.raises(ValueError, match="routing"):
        validate_source_facet_routes(metadata, payloads, required=True)


def test_selective_routing_reserves_whole_query_and_preserves_legacy_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from importlib.resources import files
    import json

    from ..browser_semantics.support import run_node_json

    data = routed_payload(monkeypatch)
    layer = data["metadata"][0]["layer"]
    assets = [
        {
            "asset_key": key,
            "domain": "nodes",
            "layer_key": layer["key"],
            "layer_kind": "point",
            "byte_count": 200,
        }
        for key in data["payloads"]
    ]
    factory = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/index-transport.js")
        .read_text()
    )
    result = run_node_json(
        factory
        + "\nconst data="
        + json.dumps({"layer": layer, "assets": assets})
        + r""";
const ordinary={key:'ordinary'}, extra=Array.from({length:42},(_,i)=>({asset_key:'other:'+i,domain:'nodes',layer_key:'ordinary',layer_kind:'point',byte_count:100}));
const indexes=[{asset_key:'indexes:1',domain:'indexes',byte_count:200},{asset_key:'indexes:2',domain:'indexes',byte_count:200}];
const bootstrap={assets:[...data.assets,...extra,...indexes],compatibility:{source_facet_routing_schema:'atlas-source-facet-routing.v1',search_index_abi:'atlas-substring-postings.v1'},budgets:{interaction_max_requests:128,interaction_max_bytes:67108864}};
const controller=BijuxPollenomicsIndexTransport.create({bootstrap,failure(message){throw Error(message)},nonnegativeInteger(value){if(!Number.isSafeInteger(value)||value<0)throw Error('integer');return value}});
let selection={code:'all',taxon:'source:neotoma:taxon:1',preset:null};
const input={endpointKeys:new Set(),nodeNeeded:()=>true,viewportNeeded:()=>true,layerForRow:row=>row.layer_key==='ordinary'?ordinary:data.layer,isLoaded:()=>false,indexes:()=>indexes,overhead:{request_count:1,byte_count:20000},sourceSelection:()=>selection};
const chosen=controller.planNodeAssets(input), source=chosen.filter(row=>row.layer_key===data.layer.key);
if(source.length!==data.layer.static_source_facets.facets['1'].asset_keys.length)throw Error('selected native route differs');
if(chosen.length!==source.length+44)throw Error('whole query or indexes omitted');
selection={code:'all',taxon:'all',preset:{member_taxon_ids:[1]}};
if(JSON.stringify(controller.planNodeAssets(input))!==JSON.stringify(chosen))throw Error('preset union differs');
selection={code:'all',taxon:'source:neotoma:taxon:99',preset:null};
if(controller.planNodeAssets(input).some(row=>row.layer_key===data.layer.key))throw Error('valid zero facet fetched source nodes');
selection={code:'all',taxon:'source:neotoma:taxon:1',preset:null};
const expectedRequests=chosen.length+1, expectedBytes=chosen.reduce((sum,row)=>sum+row.byte_count,20000);
bootstrap.budgets.interaction_max_requests=expectedRequests;bootstrap.budgets.interaction_max_bytes=expectedBytes;controller.planNodeAssets(input);
bootstrap.budgets.interaction_max_requests--;let requestRefused=false;try{controller.planNodeAssets(input)}catch(error){requestRefused=/interaction budget/.test(error.message)};
bootstrap.budgets.interaction_max_requests=expectedRequests;bootstrap.budgets.interaction_max_bytes--;let byteRefused=false;try{controller.planNodeAssets(input)}catch(error){byteRefused=/interaction budget/.test(error.message)};
bootstrap.budgets.interaction_max_requests=128;bootstrap.budgets.interaction_max_bytes=67108864;
delete bootstrap.compatibility.source_facet_routing_schema;delete data.layer.static_source_facets;
let legacyRefused=false;try{controller.planNodeAssets(input)}catch(error){legacyRefused=/interaction budget/.test(error.message)};
console.log(JSON.stringify({source:source.length,whole:chosen.length,requestRefused,byteRefused,legacyRefused}));
"""
    )
    assert result == {
        "source": 4,
        "whole": 48,
        "requestRefused": True,
        "byteRefused": True,
        "legacyRefused": True,
    }


def test_routing_singleton_counts_do_not_accept_boolean_equivalence() -> None:
    from bijux_pollenomics.reporting.map_document.static_assets.source_facets.routing import (
        bind_source_facet_routes,
        validate_source_facet_routes,
    )

    feature = {"node_id": "original", "source_taxon_id": 1, "country": "Sweden"}
    layer = source_layer([feature])
    layer["facet_metadata"] = {"source_taxa": [{"source_taxon_id": 1, "node_count": 1}]}
    metadata, parts = nodes.build_node_payloads(
        slug="nordic", version="v66", point_layers=[layer], polygon_layers=[]
    )
    payloads = {"nodes:1": parts[0]}
    bind_source_facet_routes(metadata, payloads)
    bound = cast(dict[str, Any], metadata[0]["layer"])
    bound["static_source_facets"]["facets"]["1"]["record_count"] = True
    with pytest.raises(ValueError, match="routing"):
        validate_source_facet_routes(metadata, payloads, required=True)
