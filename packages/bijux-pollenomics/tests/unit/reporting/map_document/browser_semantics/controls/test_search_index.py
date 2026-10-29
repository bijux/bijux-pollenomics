"""Published substring postings feed the real search renderer without changing matches."""

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
from bijux_pollenomics.reporting.map_document.static_assets.search import (
    SEARCH_ABI,
    SEARCH_KIND,
    validate_search_index,
    validate_search_membership,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)
from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from ..support import run_node_json, template_block


def layers() -> list[dict[str, Any]]:
    return [
        {
            "key": f"layer:{i}",
            "label": "Pollen layer Åland",
            "features": [
                {
                    "record_id": f"shared:{j}",
                    "title": f"ÄLG 💠 punctuation.( {j}",
                    "subtitle": "Source-native context",
                    "country": "Sweden",
                    "latitude": 60,
                    "longitude": 18,
                    "time_start_bp": 0,
                    "time_end_bp": 100,
                    "time_label": "source C14 (uncalibrated)",
                }
                for j in range(15)
            ],
        }
        for i in range(2)
    ]


def logical() -> dict[str, Any]:
    return {
        **build_indexes(layers()),
        "detail_record_asset_keys": {},
        "scope_slug": "nordic",
        "version": "controlled-search",
        "build_id": "atlas-" + "a" * 64,
    }


def test_real_writer_codec_and_search_renderer_preserve_visible_substrings(
    tmp_path: Path,
) -> None:
    points = layers()
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="controlled-search",
        point_layers=points,
        polygon_layers=[],
    )
    payloads: dict[str, dict[str, object]] = {}
    for raw_row, path in zip(
        normalize_asset_inventory(assets.manifest["assets"]),
        assets.asset_paths,
        strict=True,
    ):
        row = cast(dict[str, Any], raw_row)
        payloads[row["asset_key"]] = decode_chunk_script(
            path.read_bytes(),
            expected_asset_key=row["asset_key"],
            expected_payload_sha256=row["payload_sha256"],
            expected_payload_encoding=row["payload_encoding"],
            expected_decoded_byte_count=row.get("decoded_byte_count"),
        )
    bundle = next(
        value
        for value in payloads.values()
        if str(value["schema_version"]).startswith("atlas-static-indexes.")
    )
    decoded = decode_index_bundle(bundle)
    validate_search_membership(payloads, decoded, None)
    for mutation in (
        "missing",
        "duplicate",
        "out_of_range",
        "foreign_layer",
        "wrong_text",
        "foreign_record",
    ):
        changed = deepcopy(decoded)
        search = changed[SEARCH_KIND]
        assert isinstance(search, dict)
        doc = search["d:0:0"]
        assert isinstance(doc, dict)
        if mutation == "missing":
            del search["d:0:0"]
        elif mutation == "duplicate":
            search["d:0:999"] = dict(doc)
        elif mutation == "out_of_range":
            doc["feature_index"] = 999
        elif mutation == "foreign_layer":
            doc["layer_key"] = "foreign"
        elif mutation == "wrong_text":
            doc["text"] = "wrong source text"
        else:
            doc["record_id"] = "foreign-record"
        with pytest.raises(ValueError, match="actual published representations"):
            validate_search_membership(payloads, changed, None)
    helper = template_block(
        "// Published UTF-16 postings", "function buildSearchResults"
    )
    start = MAP_DOCUMENT_TEMPLATE.index("function buildSearchResults")
    decoder = template_block(
        "function staticAtlasFailure", "function normalizeStaticAtlasBootstrap"
    )
    decoder += template_block(
        "async function staticAtlasSha256", "function validateStaticAtlasPayload"
    )
    selection = template_block(
        "function staticAtlasLayerForRow", "function refreshStaticAtlasLayers"
    )
    renderer = MAP_DOCUMENT_TEMPLATE[
        start : MAP_DOCUMENT_TEMPLATE.index("async function renderMapState", start)
    ]
    # Search is adjacent to renderMapState; no replacement implementation is used.
    js = (
        "const data="
        + json.dumps(
            {
                "points": points,
                "index": decoded,
                "bundle": bundle,
                "indexRow": next(
                    row
                    for row in normalize_asset_inventory(assets.manifest["assets"])
                    if row["domain"] == "indexes"
                ),
                "edges": next(
                    value
                    for value in payloads.values()
                    if str(value["schema_version"]).startswith("atlas-edges-chunk.")
                ),
                "bootstrap": assets.manifest,
                "assetRows": normalize_asset_inventory(assets.manifest["assets"]),
            }
        )
        + ";\n"
        + r"""
const assert=require('node:assert/strict');
function staticAtlasFailure(message){throw new Error(message)}
const STATIC_ATLAS_INLINE=false, STATIC_ATLAS_BOOTSTRAP=data.bootstrap;
const STATIC_ATLAS_CHUNKS={indexes:data.index,edges:data.edges,provenance:{layers:data.points.map((layer,layer_index)=>({layer_kind:'point',layer_index,layer,feature_count:layer.features.length}))}};
function visibleGovernedEdges(){return STATIC_ATLAS_CHUNKS.edges.records;}
const staticAtlasSearchFeatureKeys=new WeakMap(),staticAtlasLoadedAssets=new Set(),ALL_LAYERS=data.points,activeLayerKeys=new Set();
let visiblePointEntries=data.points.flatMap((layer,i)=>layer.features.map((feature,j)=>{staticAtlasSearchFeatureKeys.set(feature,`d:${i}:${j}`);return {layer,feature,neighborContext:j===1}}));
let buttons=[],focused=-1;const searchInput={value:''},searchClearButton={},searchCount={dataset:{}},searchResults={hidden:true,innerHTML:'',querySelectorAll(){buttons=[];return Array.from({length:(this.innerHTML.match(/data-search-index=/g)||[]).length},()=>({addEventListener(event,fn){buttons.push(fn)}}))}};
function featureTimeLabel(feature){return feature.time_label||''}
function featureTimeDescriptor(feature){return {label:'Chronology context',value:featureTimeLabel(feature)}}
function escapeHtml(value){return String(value)}
function featureCoordinatePair(feature){return feature}
function focusPointAtVisibleIndex(index){focused=index};function setSearchOpen(){};
const map={flyTo(){},getZoom(){return 5}},window={setTimeout(){}};
"""
        + decoder
        + selection
        + helper
        + renderer
        + r"""
(async()=>{
STATIC_ATLAS_CHUNKS.indexes=await staticAtlasMergeIndexShards(data.indexRow,data.bundle);
assert.deepEqual({...STATIC_ATLAS_CHUNKS.indexes.text_search_index},data.index.text_search_index);
function oracle(q){return visiblePointEntries.filter(({layer,feature})=>`${feature.title||''} ${feature.subtitle||''} ${feature.country||''} ${layer.label||''} ${featureTimeLabel(feature)}`.toLowerCase().includes(q)).slice(0,12)}
const originalAssets=STATIC_ATLAS_BOOTSTRAP.assets;STATIC_ATLAS_BOOTSTRAP.assets=data.assetRows;
assert.deepEqual(requiredStaticAtlasNodeAssets().map(row=>row.asset_key),[data.indexRow.asset_key]);
staticAtlasLoadedAssets.add(data.indexRow.asset_key);assert.equal(requiredStaticAtlasNodeAssets().length,0);staticAtlasLoadedAssets.clear();
STATIC_ATLAS_BOOTSTRAP.assets=data.assetRows.filter(row=>row.domain!=='indexes');assert.throws(()=>requiredStaticAtlasNodeAssets(),/missing or duplicated/);
STATIC_ATLAS_BOOTSTRAP.assets=[...data.assetRows,data.indexRow];assert.throws(()=>requiredStaticAtlasNodeAssets(),/missing or duplicated/);
STATIC_ATLAS_BOOTSTRAP.assets=data.assetRows;const budget=STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_bytes;STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_bytes=0;assert.throws(()=>requiredStaticAtlasNodeAssets(),/interaction budget/);STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_bytes=budget;
STATIC_ATLAS_BOOTSTRAP.assets=originalAssets;
const completeVisible=visiblePointEntries;visiblePointEntries=[];assert.deepEqual(publishedSearchCounts(),{focalCount:0,neighborCount:0});assert.deepEqual(publishedSearchResults('early'),[]);visiblePointEntries=completeVisible;
let cases=0;
for(const subset of [visiblePointEntries,visiblePointEntries.filter((_,i)=>i%2===1),[...visiblePointEntries].reverse()]){
 visiblePointEntries=subset;preparePublishedSearch();
 for(const raw of ['ÄLG','ä','💠','\ud83d','.(','source c14','SWEDEN','pollen layer','missing','x','a']){
  const query=raw.trim().toLowerCase();assert.deepEqual(publishedSearchResults(query),oracle(query));
  searchInput.value=raw;buildSearchResults();assert.equal(searchResults.hidden,false);if(buttons.length){buttons[0]();assert.equal(focused,visiblePointEntries.indexOf(oracle(query)[0]))}cases++;
 }
 searchInput.value='   ';buildSearchResults();assert.equal(searchResults.hidden,true);cases++;
}
assert.equal(Number(searchCount.dataset.normalizationFallbackCount),0);
let browserRefusals=0;
for(const mutation of ['missing','duplicate','range','layer','posting','shape']){
 const bad=JSON.parse(JSON.stringify(data.index)),rows=bad.text_search_index;
 if(mutation==='missing')delete rows['d:0:0'];
 else if(mutation==='duplicate')rows['d:0:999']={...rows['d:0:0']};
 else if(mutation==='range')rows['d:0:0'].feature_index=999;
 else if(mutation==='layer')rows['d:0:0'].layer_key='foreign';
 else if(mutation==='posting')rows[Object.keys(rows).find(key=>key.startsWith('p:'))]=['d:999:999'];
 else rows['d:0:0'].text=null;
 assert.throws(()=>atlasPublishedSearch(bad,STATIC_ATLAS_CHUNKS.provenance.layers),/search/);browserRefusals++;
}
for(const metadata of [null,[{...STATIC_ATLAS_CHUNKS.provenance.layers[0],feature_count:-1}], [...STATIC_ATLAS_CHUNKS.provenance.layers,STATIC_ATLAS_CHUNKS.provenance.layers[0]]])assert.throws(()=>atlasPublishedSearch(JSON.parse(JSON.stringify(data.index)),metadata),/search/);
STATIC_ATLAS_BOOTSTRAP.compatibility.search_index_abi='';assert.throws(()=>preparePublishedSearch(),/search ABI/);
delete STATIC_ATLAS_BOOTSTRAP.compatibility.search_index_abi;preparePublishedSearch();assert.deepEqual(publishedSearchResults('älg'),oracle('älg'));
STATIC_ATLAS_BOOTSTRAP.compatibility.search_index_abi='atlas-substring-postings.v1';preparePublishedSearch();
// A real coercion-format difference is kept explicit rather than losing a match.
const numeric={...data.points[0].features[0],title:1e-7};
const numericLayer={...data.points[0],features:[numeric]};
const fallbackDoc={...data.index.text_search_index['d:0:0'],text:'1e-07 source-native context sweden pollen layer åland source c14 (uncalibrated)'};
const published=atlasPublishedSearch(data.index,STATIC_ATLAS_CHUNKS.provenance.layers);
const changed={docs:new Map(published.docs),postings:published.postings};changed.docs.set('d:0:0',fallbackDoc);
const state=atlasPrepareVisibleSearch(changed,[{layer:numericLayer,feature:numeric}],()=> 'd:0:0',featureTimeLabel);
assert.equal(state.normalizationFallbackCount,1);assert.equal(atlasLookupSearch(state,'1e-7').length,1);
assert.throws(()=>atlasPrepareVisibleSearch(published,[{layer:data.points[0],feature:{...data.points[0].features[0],record_id:'foreign'}}],()=> 'd:0:0',featureTimeLabel),/representation differs/);
const runtime=atlasPrepareVisibleSearch(published,[{layer:numericLayer,feature:numeric}],()=>undefined,featureTimeLabel);assert.equal(runtime.runtimeRepresentationCount,1);assert.equal(atlasLookupSearch(runtime,'1e-7').length,1);
console.log(JSON.stringify({cases,first12:12,normalizationFallback:state.normalizationFallbackCount,browserRefusals}));
})().catch(error=>{console.error(error);process.exitCode=1});
"""
    )
    observed = run_node_json(js)
    assert observed["cases"] == 36 and observed["normalizationFallback"] == 1
    assert observed["browserRefusals"] == 6
    assert (
        cast(dict[str, Any], assets.manifest["compatibility"])["search_index_abi"]
        == SEARCH_ABI
    )


def test_search_codec_keeps_legacy_and_postings_exact() -> None:
    incoming = logical()
    assert decode_index_bundle(build_index_bundle(incoming)) == incoming
    legacy = {
        key: value
        for key, value in incoming.items()
        if key not in {SEARCH_KIND, "search_index_abi"}
    }
    assert decode_index_bundle(build_index_bundle(legacy)) == legacy
    assert decode_index_bundle(legacy) == legacy
    assert all(key.isascii() for key in incoming[SEARCH_KIND] if key.startswith("p:"))


@pytest.mark.parametrize(
    "change",
    ["missing_posting", "duplicate_reference", "foreign_reference", "unknown_abi"],
)
def test_corrupt_declared_search_never_becomes_legacy(change: str) -> None:
    incoming = deepcopy(logical())
    postings = incoming[SEARCH_KIND]
    key = next(key for key in postings if key.startswith("p:"))
    if change == "missing_posting":
        del postings[key]
    elif change == "duplicate_reference":
        postings[key].append(postings[key][0])
    elif change == "foreign_reference":
        postings[key].append("d:999:999")
    else:
        incoming["search_index_abi"] = "unsupported"
    with pytest.raises(ValueError):
        decode_index_bundle(build_index_bundle(incoming))


def test_missing_or_changed_document_payload_refuses() -> None:
    index = logical()[SEARCH_KIND]
    cases: list[dict[str, Any]] = [{}, {"foreign": {}}, {**index, "p:0078": ["d:0:0"]}]
    for value in cases:
        if value == {}:
            validate_search_index(
                value
            )  # Empty corpus itself is legitimate; membership adjudicates size.
        else:
            with pytest.raises(ValueError):
                validate_search_index(value)
