"""Index-only code remains lazy and consumes each interaction's real limits."""

from __future__ import annotations

from importlib.resources import files

from ..support import run_node_json, template_block


def test_external_index_controller_is_lazy_shared_and_has_transport_identity() -> None:
    helpers = template_block(
        "function indexTransportDescriptor", "function staticAtlasIndexRows"
    )
    factory = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/index-transport.js")
        .read_text()
    )
    observed = run_node_json(
        factory
        + helpers
        + r"""
let staticAtlasIndexTransport=null,staticAtlasIndexTransportRequest=null;
const descriptor={path:'atlas.atlas-index-transport.'+'a'.repeat(16)+'.js',byte_count:20000,integrity:'sha256-'+'A'.repeat(43)+'='};
const STATIC_ATLAS_BOOTSTRAP={runtime:{optional_controllers:{index_transport:descriptor}}};
function staticAtlasFailure(message){throw Error(message)}
function staticAtlasTemporalIdentity(){}
function staticAtlasNonnegativeInteger(value){return value}
async function staticAtlasBoundedGunzip(){}
async function staticAtlasSha256(){}
const window={location:{protocol:'https:'}};
const scripts=[];
const document={createElement(){return {events:{},addEventListener(name,callback){this.events[name]=callback}}},head:{appendChild(script){scripts.push(script)}}};
const before=scripts.length;
const first=loadIndexTransport(),second=loadIndexTransport();
(async()=>{
 await Promise.resolve();
 const pending=scripts.length;
 scripts[0].events.load();
 const controller=await first;
 const shared=controller===await second;
 await loadIndexTransport();
 console.log(JSON.stringify({before,pending,after:scripts.length,shared,samePromise:first===second,
 src:scripts[0].src,integrity:scripts[0].integrity,crossOrigin:scripts[0].crossOrigin,
 methods:Object.keys(controller).sort(),grams:[...controller.searchGrams("AB")].sort()}));
})();
"""
    )
    assert observed == {
        "before": 0,
        "pending": 1,
        "after": 1,
        "shared": True,
        "samePromise": True,
        "src": "./atlas.atlas-index-transport." + "a" * 16 + ".js",
        "integrity": "sha256-" + "A" * 43 + "=",
        "crossOrigin": "anonymous",
        "methods": [
            "acceptPart",
            "consume",
            "mergeShards",
            "planNodeAssets",
            "searchGrams",
            "validatePayload",
        ],
        "grams": ["0041", "00410042", "0042"],
    }


def test_search_and_detail_charge_all_parts_and_helper_before_requests() -> None:
    inventory = template_block(
        "function staticAtlasIndexRows", "function validateStaticAtlasEdgeAssets"
    )
    selection = template_block(
        "function requiredStaticAtlasNodeAssets", "function refreshStaticAtlasLayers"
    )
    detail = template_block(
        "async function ensureStaticAtlasIndexesLoaded",
        "async function detailTabsForRecordId",
    )
    factory = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/index-transport.js")
        .read_text()
    )
    observed = run_node_json(
        factory
        + template_block(
            "function staticAtlasLayerForRow",
            "function animalSourceChronologyCountryFilterBypassed",
        )
        + inventory
        + selection
        + detail
        + template_block(
            "function validateStaticAtlasEdgeAssets",
            "function validateStaticAtlasPayload",
        )
        + template_block("function finiteCoordinateValue", "function coordinateLabel")
        + template_block(
            "function atlasEdgeIntersectsViewport", "function renderEdgeLayers"
        )
        + r"""
const STATIC_ATLAS_INLINE=false, ALL_LAYERS=[];
const rows=[{domain:'indexes',asset_key:'indexes:4',sequence:4,byte_count:100},
 {domain:'indexes',asset_key:'indexes:5',sequence:5,byte_count:200}];
const STATIC_ATLAS_BOOTSTRAP={assets:rows,compatibility:{search_index_abi:'atlas-substring-postings.v1',index_schema:'atlas-static-indexes.v3',index_transport_schema:'atlas-static-index-part.v1'},budgets:{interaction_max_requests:3,interaction_max_bytes:350}};
let staticAtlasIndexTransport=null;
const staticAtlasLoadedAssets=new Set(),STATIC_ATLAS_CHUNKS={edges:{schema_version:"atlas-edges-chunk.v1"}};
function staticAtlasFailure(message){throw Error(message)}
function staticAtlasNonnegativeInteger(value){if(!Number.isSafeInteger(value)||value<0)throw Error('integer');return value}
function indexTransportDescriptor(){return {byte_count:50}}
function visibleGovernedEdges(){return []}const map={_loaded:false};
function staticAtlasNodeSelectionNeeded(){return true}
function staticAtlasViewportNeeded(){return true}
let requests=[];
async function loadIndexTransport(){requests.push('helper');staticAtlasIndexTransport={};}
async function loadStaticAtlasAsset(row){requests.push(row.asset_key);staticAtlasLoadedAssets.add(row.asset_key);if(staticAtlasLoadedAssets.size===rows.length)STATIC_ATLAS_CHUNKS.indexes={detail_record_asset_keys:{}};}
const planner=BijuxPollenomicsIndexTransport.create({bootstrap:STATIC_ATLAS_BOOTSTRAP,failure:staticAtlasFailure,nonnegativeInteger:staticAtlasNonnegativeInteger});
function selected(){const old=staticAtlasIndexTransport;staticAtlasIndexTransport=planner;try{return requiredStaticAtlasNodeAssets({request_count:1,byte_count:50}).map(row=>row.asset_key)}catch(error){return error.message}finally{staticAtlasIndexTransport=old}}
(async()=>{
 const exact=selected();
 STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_requests=2;
 const requestRefusal=selected(),detailRequests=await ensureStaticAtlasIndexesLoaded(),afterRequestRefusal=requests.length;
 STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_requests=3;
 STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_bytes=349;
 const byteRefusal=selected(),detailBytes=await ensureStaticAtlasIndexesLoaded(),afterByteRefusal=requests.length;
 STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_bytes=350;
 const complete=await ensureStaticAtlasIndexesLoaded();
 console.log(JSON.stringify({exact,requestRefusal,byteRefusal,detailRequests,detailBytes,afterRequestRefusal,afterByteRefusal,complete,requests}));
})();
"""
    )
    assert observed["exact"] == ["indexes:4", "indexes:5"]
    assert "3 requests" in observed["requestRefusal"]
    assert "350 bytes" in observed["byteRefusal"]
    assert observed["detailRequests"] is observed["detailBytes"] is False
    assert observed["afterRequestRefusal"] == observed["afterByteRefusal"] == 0
    assert observed["complete"] is True
    assert observed["requests"] == ["helper", "indexes:4", "indexes:5"]


def test_detail_click_combines_index_helper_parts_and_selected_chunk_limits() -> None:
    helpers = template_block(
        "function staticAtlasIndexRows", "function validateStaticAtlasEdgeAssets"
    )
    details = template_block(
        "async function ensureStaticAtlasIndexesLoaded",
        "async function detailTabsForFeature",
    )
    observed = run_node_json(
        r"""
async function probe(maxRequests,maxBytes,indexesCached=false,recordCached=false){
 const STATIC_ATLAS_INLINE=false,ATLAS_EVIDENCE={details_status:'available'};
 const indexes=[{domain:'indexes',asset_key:'indexes:4',sequence:4,byte_count:100},
  {domain:'indexes',asset_key:'indexes:5',sequence:5,byte_count:200}];
 const detail={domain:'details',asset_key:'details:6',byte_count:90};
 const STATIC_ATLAS_BOOTSTRAP={assets:[...indexes,detail],compatibility:{index_schema:'atlas-static-indexes.v3',index_transport_schema:'atlas-static-index-part.v1'},budgets:{interaction_max_requests:maxRequests,interaction_max_bytes:maxBytes}};
 const lookup={detail_record_asset_keys:{record:'details:6'}};
 const STATIC_ATLAS_CHUNKS={details:[],...(indexesCached?{indexes:lookup}:{})};
 const staticAtlasLoadedAssets=new Set(),DETAIL_RECORDS=new Map();
 if(recordCached)DETAIL_RECORDS.set('record',{tabs:{available:true}});
 let staticAtlasIndexTransport=indexesCached?{}:null;
 const requests=[];
 function staticAtlasFailure(message){throw Error(message)}
 function staticAtlasNonnegativeInteger(value){if(!Number.isSafeInteger(value)||value<0)throw Error('integer');return value}
 function indexTransportDescriptor(){return {byte_count:50}}
 function unavailableDetailTabs(reason){return {reason}}
 async function loadIndexTransport(){requests.push('helper');staticAtlasIndexTransport={}}
 async function loadStaticAtlasAsset(row){
  requests.push(row.asset_key);staticAtlasLoadedAssets.add(row.asset_key);
  if(row.domain==='details')STATIC_ATLAS_CHUNKS.details.push({asset_key:row.asset_key,records:[{record_id:'record',tabs:{available:true}}]});
  else if(indexes.every(row=>staticAtlasLoadedAssets.has(row.asset_key)))STATIC_ATLAS_CHUNKS.indexes=lookup;
 }
"""
        + helpers
        + details
        + r"""
 return {tabs:await detailTabsForRecordId('record'),requests};
}
(async()=>console.log(JSON.stringify({
 exact:await probe(4,440),bytes:await probe(4,439),requests:await probe(3,440),
 cachedIndexes:await probe(1,90,true),cachedRecord:await probe(0,0,false,true)
})))();
"""
    )
    full = ["helper", "indexes:4", "indexes:5", "details:6"]
    assert observed["exact"] == {"tabs": {"available": True}, "requests": full}
    for key in ("bytes", "requests"):
        assert observed[key] == {
            "tabs": {"reason": "detail_chunk_interaction_budget_exceeded"},
            "requests": full[:-1],
        }
    assert observed["cachedIndexes"] == {
        "tabs": {"available": True},
        "requests": ["details:6"],
    }
    assert observed["cachedRecord"] == {"tabs": {"available": True}, "requests": []}


def test_lazy_planner_preflights_code_and_parts_and_restores_only_latest_selection() -> (
    None
):
    factory = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/index-transport.js")
        .read_text()
    )
    loading = template_block(
        "function indexTransportDescriptor", "function validateStaticAtlasEdgeAssets"
    )
    planning = template_block(
        "function requiredStaticAtlasNodeAssets", "function refreshStaticAtlasLayers"
    )
    selection = template_block(
        "async function ensureStaticAtlasSelectionLoaded", "const countryColors"
    )
    ownership = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/selection-loading.js")
        .read_text()
        .split("async function fetchStaticAtlasNodeAsset")[0]
    )
    observed = run_node_json(
        factory
        + template_block(
            "function validateStaticAtlasEdgeAssets",
            "function validateStaticAtlasPayload",
        )
        + template_block("function finiteCoordinateValue", "function coordinateLabel")
        + template_block(
            "function atlasEdgeIntersectsViewport", "function renderEdgeLayers"
        )
        + r"""
const assert=require('node:assert/strict');
async function probe(maxRequests,failOnce=false){
 const STATIC_ATLAS_INLINE=false,STATIC_ATLAS_BOOTSTRAP={
 assets:[{asset_key:'nodes:a',domain:'nodes',layer_key:'point',layer_kind:'point',byte_count:100},
 {asset_key:'nodes:b',domain:'nodes',layer_key:'point',layer_kind:'point',byte_count:100},
 {asset_key:'indexes:1',domain:'indexes',byte_count:100},{asset_key:'indexes:2',domain:'indexes',byte_count:200}],
 compatibility:{search_index_abi:'atlas-substring-postings.v1',index_schema:'atlas-static-indexes.v3',index_transport_schema:'atlas-static-index-part.v1'},
 budgets:{interaction_max_requests:maxRequests,interaction_max_bytes:450},
 runtime:{optional_controllers:{index_transport:{path:'atlas.atlas-index-transport.'+'a'.repeat(16)+'.js',byte_count:50,integrity:'sha256-'+'A'.repeat(43)+'='}}}};
 let staticAtlasIndexTransport=null,staticAtlasIndexTransportRequest=null,active='nodes:a';
 const staticAtlasLoadedAssets=new Set(),staticAtlasInFlightAssets=new Map(),scripts=[],requested=[],layer={key:'point'};
 const document={createElement(){return {events:{},addEventListener(name,callback){this.events[name]=callback}}},head:{appendChild(script){scripts.push(script)}}},window={location:{protocol:'https:'}};
 function staticAtlasFailure(message){throw Error(message)}
 function staticAtlasNonnegativeInteger(value){if(!Number.isSafeInteger(value)||value<0)throw Error('integer');return value}
 function staticAtlasTemporalIdentity(){}async function staticAtlasBoundedGunzip(){}async function staticAtlasSha256(){}
 function visibleGovernedEdges(){return []}const map={_loaded:false},STATIC_ATLAS_CHUNKS={edges:{schema_version:"atlas-edges-chunk.v1"}};
 function staticAtlasNodeSelectionNeeded(row){return row.asset_key===active}
 function staticAtlasViewportNeeded(){return true}function staticAtlasLayerForRow(){return layer}
 async function loadStaticAtlasAsset(row){requested.push(row.asset_key);staticAtlasLoadedAssets.add(row.asset_key)}
 function validateLoadedStaticAtlasEdgeAssets(){}function refreshStaticAtlasLayers(){}
"""
        + loading
        + planning
        + ownership
        + selection
        + r"""
 if(maxRequests<3){let error;try{await ensureStaticAtlasSelectionLoaded()}catch(value){error=value.message}return {error,scripts:scripts.length,requested}}
 const old=ensureStaticAtlasSelectionLoaded(),cancelled=assert.rejects(old,{name:'AbortError'});
 await Promise.resolve();active='nodes:b';const current=ensureStaticAtlasSelectionLoaded();await cancelled;
 assert.equal(scripts.length,1);scripts[0].events[failOnce?'error':'load']();
 if(failOnce){await assert.rejects(current,/could not be loaded/);const retry=ensureStaticAtlasSelectionLoaded();await Promise.resolve();assert.equal(scripts.length,2);scripts[1].events.load();await retry}else await current;
 return {scripts:scripts.length,requested};
}
(async()=>{console.log(JSON.stringify({refused:await probe(2),latest:await probe(4),retry:await probe(4,true)}))})();
"""
    )
    assert observed["refused"]["scripts"] == 0
    assert observed["refused"]["requested"] == []
    assert "interaction budget" in observed["refused"]["error"]
    assert observed["latest"] == {
        "scripts": 1,
        "requested": ["nodes:b", "indexes:1", "indexes:2"],
    }
    assert observed["retry"] == {
        "scripts": 2,
        "requested": ["nodes:b", "indexes:1", "indexes:2"],
    }
