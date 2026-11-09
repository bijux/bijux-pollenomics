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
            + index_transport_helpers(include_search=False)
            + assets.joinpath("search-index.js").read_text()
            + r"""
(async()=>{try{
 let gramCalls=0;const originalGrams=atlasSearchGrams;
 atlasSearchGrams=(...args)=>{gramCalls++;return originalGrams(...args)};
 const row={asset_key:'indexes:6',domain:'indexes',record_count:13};
 const decoded=await staticAtlasIndexTransport.consume(row,data.bundle,[row]);
 const decodeGramCalls=gramCalls;
 const original=data.expected.text_search_index;
 const expectedKeys=Object.keys(original),actualKeys=Object.keys(decoded.text_search_index);
 const same=JSON.stringify(actualKeys)===JSON.stringify(expectedKeys)&&expectedKeys.every(key=>Array.isArray(original[key])?JSON.stringify(decoded.text_search_index[key])===JSON.stringify(original[key]):Object.keys(original[key]).every(field=>JSON.stringify(decoded.text_search_index[key][field])===JSON.stringify(original[key][field])));
 const metadata=[{layer_kind:'point',layer_index:0,feature_count:13,layer:{key:'pollen'}}];
 let layerRefused=false;try{atlasPublishedSearch(decoded,[{...metadata[0],feature_count:12}])}catch{layerRefused=true}
 const frozen=Object.isFrozen(decoded.text_search_index)&&Object.values(decoded.text_search_index).every(Object.isFrozen);
 // A copied object and a public claim of validation cannot borrow the private cache.
 const foreign=JSON.parse(JSON.stringify(decoded));foreign.validated=true;
 delete foreign.text_search_index[Object.keys(foreign.text_search_index).find(key=>key.startsWith('p:'))];
 const restoredRows=decoded.text_search_index;decoded.text_search_index=foreign.text_search_index;
 let reboundRefused=false;try{atlasPublishedSearch(decoded,metadata)}catch{reboundRefused=true}
 decoded.text_search_index=restoredRows;
 const beforePublishCalls=gramCalls;
 const published=atlasPublishedSearch(decoded,metadata);
 const publishAdditionalGramCalls=gramCalls-beforePublishCalls;
 const afterPublishRefusals=[];
 for(const changed of [
   [{...metadata[0],feature_count:12}],
   [{...metadata[0],feature_count:14}],
   [{...metadata[0],layer:{key:'foreign'}}],
   [metadata[0],metadata[0]],
 ]){try{atlasPublishedSearch(decoded,changed);afterPublishRefusals.push(false)}catch{afterPublishRefusals.push(true)}}
 decoded.search_index_abi='foreign';
 try{atlasPublishedSearch(decoded,metadata);afterPublishRefusals.push(false)}catch{afterPublishRefusals.push(true)}
 decoded.search_index_abi='atlas-substring-postings.v1';
 decoded.text_search_index=foreign.text_search_index;
 try{atlasPublishedSearch(decoded,metadata);afterPublishRefusals.push(false)}catch{afterPublishRefusals.push(true)}
 decoded.text_search_index=restoredRows;
 const beforeReuseCalls=gramCalls;
 const reused=atlasPublishedSearch(decoded,metadata)===published;
 const reuseAdditionalGramCalls=gramCalls-beforeReuseCalls;
 let missingRefused=false;try{atlasPublishedSearch(foreign,metadata)}catch{missingRefused=true}
 const visible=new Map(Object.entries(original).filter(([key])=>key.startsWith('d:')).reverse().map(([key,row],order)=>[key,{order,text:row.text,entry:{key}}]));
 const state={published,visible,fallback:[]};
 const queries=['a','ab','abc','💠','\ud83d','\udc00','a\u0308','.(a)','same','𐐨','absent'];
 const answers=queries.every(query=>JSON.stringify(atlasLookupSearch(state,query).map(row=>row.key))===JSON.stringify([...visible.values()].filter(row=>row.text.includes(query)).slice(0,12).map(row=>row.entry.key)));
 console.log(JSON.stringify({same,answers,decodeGramCalls,publishAdditionalGramCalls,afterPublishRefusals,reused,reuseAdditionalGramCalls,frozen,layerRefused,missingRefused,reboundRefused,keys:actualKeys.filter(key=>key.startsWith('d:')),transportMetadata:Object.hasOwn(decoded,'search_transport_schema')||Object.hasOwn(decoded,'search_transport_counts')}));
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
    assert observed["decodeGramCalls"] == 13
    assert observed["publishAdditionalGramCalls"] == 0
    assert observed["frozen"] is True
    assert observed["layerRefused"] is True
    assert observed["missingRefused"] is True
    assert observed["reboundRefused"] is True
    assert observed["afterPublishRefusals"] == [True] * 6
    assert observed["reused"] is True
    assert observed["reuseAdditionalGramCalls"] == 0
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


def probe_iteration(
    body: str, *, keys: int = 2, references: int = 2, header_bigint: bool = False
) -> dict[str, Any]:
    data = packet()
    data["initialBigIntCap"] = header_bigint
    data["bundle"]["search_transport_counts"].update(
        posting_key_count=keys, posting_reference_count=references
    )
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
            + index_transport_helpers(include_search=False)
            + r"""
const trace={calls:0,pushed:[],regex:[],capReads:[],sizeReads:0,coercions:0,remember:0};
const counts=data.bundle.search_transport_counts;
let cap=data.initialBigIntCap?BigInt(counts.posting_reference_count):counts.posting_reference_count,active=false;
Object.defineProperty(counts,'posting_reference_count',{
 enumerable:true,get(){if(active)trace.capReads.push(typeof cap==='bigint'?`${cap}n`:cap);return cap},set(value){cap=value}
});
const originalPush=Array.prototype.push,originalTest=RegExp.prototype.test;
Array.prototype.push=function(...values){
 if(values.length===1&&typeof values[0]==='string'&&values[0].startsWith('d:'))originalPush.call(trace.pushed,values[0]);
 return originalPush.apply(this,values);
};
RegExp.prototype.test=function(value){
 if(this.source==='^(?:[a-f0-9]{4}){1,3}$')trace.regex.push(value);
 return originalTest.call(this,value);
};
const transport=globalThis.BijuxPollenomicsIndexTransport.create({
 bootstrap:STATIC_ATLAS_BOOTSTRAP,failure:staticAtlasFailure,
 temporalIdentity:staticAtlasTemporalIdentity,nonnegativeInteger:staticAtlasNonnegativeInteger,
 nativeCalendarNumber,boundedGunzip:staticAtlasBoundedGunzip,sha256:staticAtlasSha256,
 rememberRestoredSearch(){trace.remember++},
 searchGrams(){
  trace.calls++;if(trace.calls>1)return new Set();active=true;
  const set=new Set();
  Object.defineProperty(set,'size',{get(){trace.sizeReads++;throw Error('untrusted size read')}});
"""
            + body
            + r"""
 }
});
(async()=>{let result;
 try{
  const row={asset_key:'indexes:6',domain:'indexes',record_count:13};
  const decoded=await transport.consume(row,data.bundle,[row]);
  result={postings:Object.fromEntries(Object.entries(decoded.text_search_index).filter(([key])=>key.startsWith('p:')))};
 }catch(error){result={refusal:error.message}}
 finally{Array.prototype.push=originalPush;RegExp.prototype.test=originalTest}
 console.log(JSON.stringify({...result,...trace}));
})();
""",
        ),
    )


def test_live_reference_budget_refuses_before_the_second_posting_append() -> None:
    observed = probe_iteration(
        "set[Symbol.iterator]=function*(){yield '0061';"
        "counts.posting_reference_count=1;yield '0062';"
        "counts.posting_reference_count=2};return set;"
    )
    assert "posting_reference_count exceeds its declared count" in observed["refusal"]
    assert observed["pushed"] == ["d:0:0"]
    assert observed["capReads"] == [2, 1]
    assert observed["remember"] == observed["sizeReads"] == 0


@pytest.mark.parametrize("cap", [1, 2])
def test_temporary_bigint_cap_retains_relational_comparison_semantics(cap: int) -> None:
    observed = probe_iteration(
        "set[Symbol.iterator]=function*(){yield '0061';"
        f"counts.posting_reference_count={cap}n;yield '0062';"
        "counts.posting_reference_count=2};return set;"
    )
    if cap == 2:
        assert "refusal" not in observed
        assert observed["postings"] == {
            "p:0061": ["d:0:0"],
            "p:0062": ["d:0:0"],
        }
        assert observed["pushed"] == ["d:0:0"] * 2
        assert observed["capReads"] == [2, "2n", 2]
        assert observed["remember"] == 1
    else:
        assert (
            "posting_reference_count exceeds its declared count" in observed["refusal"]
        )
        assert observed["pushed"] == ["d:0:0"]
        assert observed["capReads"] == [2, "1n"] and observed["remember"] == 0
    assert observed["sizeReads"] == 0


def test_initial_bigint_header_remains_refused_before_calling_the_helper() -> None:
    observed = probe_iteration("throw Error('helper called');", header_bigint=True)
    assert "search posting_reference_count is invalid" in observed["refusal"]
    assert observed["calls"] == observed["remember"] == 0
    assert observed["pushed"] == []


def test_iterator_final_count_change_keeps_the_global_mismatch_refusal() -> None:
    observed = probe_iteration(
        "set[Symbol.iterator]=function*(){yield '0061';yield '0062';"
        "counts.posting_reference_count=1};return set;"
    )
    assert "derived search counts differ from their declaration" in observed["refusal"]
    assert observed["pushed"] == ["d:0:0"] * 2
    assert observed["capReads"] == [2, 2, 1]
    assert observed["remember"] == observed["sizeReads"] == 0


def test_actual_yielded_references_are_counted_without_reading_set_size() -> None:
    observed = probe_iteration(
        "set[Symbol.iterator]=function*(){yield '0061';yield '0062';yield '0061'};"
        "return set;",
        references=3,
    )
    assert "refusal" not in observed
    assert observed["postings"] == {
        "p:0061": ["d:0:0", "d:0:0"],
        "p:0062": ["d:0:0"],
    }
    assert observed["regex"] == ["0061", "0062"]
    assert observed["pushed"] == ["d:0:0"] * 3
    assert observed["remember"] == 1 and observed["sizeReads"] == 0


@pytest.mark.parametrize(
    "value",
    [
        "null",
        "42",
        "Symbol('0061')",
        "new String('0061')",
        "{toString(){trace.coercions++;throw Error('coercion')}}",
    ],
)
def test_nonstring_gram_is_never_coerced_even_after_a_valid_key(value: str) -> None:
    observed = probe_iteration(
        "set[Symbol.iterator]=function*(){yield '0061';yield " + value + "};return set;"
    )
    assert "search UTF-16 gram identity is invalid" in observed["refusal"]
    assert observed["pushed"] == ["d:0:0"] and observed["regex"] == ["0061"]
    assert observed["coercions"] == observed["remember"] == 0


@pytest.mark.parametrize(
    ("gram", "keys", "references", "message"),
    [
        ("zzzz", 0, 0, "search UTF-16 gram identity is invalid"),
        ("0061", 0, 0, "posting_key_count exceeds its declared count"),
        ("0061", 1, 0, "posting_reference_count exceeds its declared count"),
    ],
)
def test_new_gram_format_and_key_budget_precede_reference_budget(
    gram: str, keys: int, references: int, message: str
) -> None:
    observed = probe_iteration(
        "set[Symbol.iterator]=function*(){yield " + json.dumps(gram) + "};return set;",
        keys=keys,
        references=references,
    )
    assert message in observed["refusal"]
    assert observed["pushed"] == [] and observed["remember"] == 0
    assert observed["capReads"] == ([0] if keys else [])


def test_custom_iterator_failure_is_not_replaced_by_a_count_error() -> None:
    observed = probe_iteration(
        "set[Symbol.iterator]=function*(){yield '0061';throw Error('gram iterator failed')};"
        "return set;"
    )
    assert observed["refusal"] == "gram iterator failed"
    assert observed["pushed"] == ["d:0:0"] and observed["remember"] == 0


def test_non_set_iterable_remains_refused_before_iteration() -> None:
    observed = probe_iteration(
        "return {[Symbol.iterator]:function*(){trace.coercions++;yield '0061'}};"
    )
    assert "did not return unique grams" in observed["refusal"]
    assert observed["pushed"] == [] and observed["coercions"] == 0


def test_unsafe_reference_declaration_refuses_before_calling_the_helper() -> None:
    observed = probe_iteration("throw Error('helper called');", references=2**53)
    assert "search posting_reference_count is invalid" in observed["refusal"]
    assert observed["calls"] == observed["remember"] == 0
    assert observed["pushed"] == []


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


@pytest.mark.parametrize("completion", ("success", "scheduler_error", "live_cap"))
def test_scheduled_restoration_keeps_shared_assembly_private_until_complete(
    completion: str,
) -> None:
    data = packet()
    expected = data["expected"]
    count = 1025
    expected["country_feature_indexes"] = {"Sweden": {"pollen": list(range(count))}}
    expected["text_search_index"] = build_search_index(
        [
            {
                "key": "pollen",
                "features": [{"record_id": i, "title": "Åa💠"} for i in range(count)],
            }
        ]
    )
    bundle = build_index_bundle(expected, search_transport_schema=CODEC)
    data["manifest"]["domains"]["indexes"]["record_count"] = count
    data["manifest"]["compatibility"]["index_transport_schema"] = (
        "atlas-static-index-part.v1"
    )
    shards = cast(list[dict[str, Any]], bundle["shards"])
    middle = len(shards) // 2
    data["parts"] = []
    for number, (first, stop) in enumerate(((0, middle), (middle, len(shards))), 1):
        data["parts"].append(
            {
                **{key: value for key, value in bundle.items() if key != "shards"},
                "schema_version": "atlas-static-index-part.v1",
                "bundle_schema": bundle["schema_version"],
                "bundle_sha256": sha256(
                    json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
                "part_number": number,
                "part_count": 2,
                "first_shard_number": first + 1,
                "last_shard_number": stop,
                "shards": shards[first:stop],
                "asset_key": f"indexes:{5 + number}",
            }
        )
    data["completion"] = completion
    observed = run_node_json(
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
        + files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/search-index.js")
        .read_text()
        + index_transport_helpers(include_search=False)
        + r"""
(async()=>{
 const assert=require('node:assert/strict'),original=JSON.stringify(data);
 let calls=0,remember=0,yields=0,release,entered,accepted=null,settled=false;
 const pause=new Promise(resolve=>release=resolve),atYield=new Promise(resolve=>entered=resolve),sentinel=new Error('scheduler failed');
 const dependencies={bootstrap:STATIC_ATLAS_BOOTSTRAP,failure:staticAtlasFailure,
  temporalIdentity:staticAtlasTemporalIdentity,nonnegativeInteger:staticAtlasNonnegativeInteger,
  nativeCalendarNumber:()=>false,boundedGunzip:staticAtlasBoundedGunzip,sha256:staticAtlasSha256,
  searchGrams(text){calls++;return atlasSearchGrams(text)},
  rememberRestoredSearch(index,postings){remember++;atlasRememberRestoredSearch(index,postings)},
  yieldTask(){yields++;entered();return pause.then(()=>{if(data.completion==='scheduler_error')throw sentinel;})}};
 const controller=BijuxPollenomicsIndexTransport.create(dependencies);
 dependencies.yieldTask=()=>{throw Error('scheduler dependency was reread')};
 const rows=data.parts.map((part,i)=>({asset_key:part.asset_key,domain:'indexes',sequence:6+i,record_count:part.shards.length}));
 assert.equal(await controller.consume(rows[0],data.parts[0],rows),null);
 const consume=controller.consume(rows[1],data.parts[1],rows);
 const observed=consume.then(value=>{accepted=value;settled=true},error=>{settled=true;return error});
 await atYield;
 let heartbeat=false;await new Promise(resolve=>setTimeout(()=>{heartbeat=true;resolve()},0));
 assert.equal(calls,1024);assert.equal(remember,0);assert.equal(settled,false);assert.equal(accepted,null);
 const repeated=controller.consume(rows[1],data.parts[1],rows);
 const repeatedObserved=repeated.then(value=>value,error=>error);
 if(data.completion==='live_cap')for(const part of data.parts)part.search_transport_counts.posting_reference_count=0;
 release();const error=await observed,again=await repeatedObserved;
 if(data.completion==='success'){
  assert.equal(accepted,again);assert.equal(calls,1025);assert.equal(remember,1);
  assert.deepEqual({...accepted.text_search_index},data.expected.text_search_index);
  assert.equal(Object.isFrozen(accepted.text_search_index),true);
  const metadata=[{layer_kind:'point',layer_index:0,feature_count:1025,layer:{key:'pollen'}}];
  assert.equal(atlasPublishedSearch(accepted,metadata),atlasPublishedSearch(again,metadata));
  assert.equal(JSON.stringify(data),original);
 }else{
  assert.equal(accepted,null);assert.equal(remember,0);assert.equal(error,again);
  if(data.completion==='scheduler_error')assert.equal(error,sentinel);
  else assert.match(error.message,/posting_reference_count exceeds its declared count/);
 }
 console.log(JSON.stringify({heartbeat,yields,calls,remember,accepted:accepted!==null}));
})().catch(error=>{console.error(error);process.exitCode=1});
"""
    )
    assert observed["heartbeat"] is True
    assert observed["yields"] == 1
    assert observed["remember"] == (1 if completion == "success" else 0)
    assert observed["accepted"] is (completion == "success")
