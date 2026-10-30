"""Selection download uses its actual owners and creates no partial browser download."""

from __future__ import annotations

from importlib.resources import files
from typing import Any, cast

import pytest

from ...support import run_node_json, template_block


def observe(action: str) -> dict[str, Any]:
    assets = files("bijux_pollenomics.reporting.map_document").joinpath("assets")
    source = (
        assets.joinpath("selection-export.js").read_text()
        + assets.joinpath("edge-display.js").read_text()
        + template_block(
            "function atlasSelectionExportSnapshot", "const ATLAS_CAPTURE_API_VERSION"
        )
        + r"""
const metadata={key:'points',label:'Literal public layer'},hydrated={...metadata,features:[{record_id:'wrong-viewport-row'}]};
const row={domain:'nodes',asset_key:'node-1',layer_key:'points',layer_kind:'point',layer_index:0,record_count:2,byte_count:400,decoded_byte_count:400};
const STATIC_ATLAS_BOOTSTRAP={schema_version:'atlas-static-bootstrap.v3',build_id:'build',scope_slug:'scope',version:'version',
 assets:[row],budgets:{interaction_max_requests:128,interaction_max_bytes:67108864,chunk_max_bytes:4194304}};
const features=[{record_id:'a',keep:true,latitude:0,longitude:0,value:null,unit:'grains'},
 {record_id:'b',keep:true,latitude:1,longitude:1,value:0,unit:'percent'}];
const chunk={...row,build_id:'build',scope_slug:'scope',version:'version',features,feature_indexes:[0,1]};
const STATIC_ATLAS_CHUNKS={nodes:[],edges:{status:'available',reason_code:null}},staticAtlasLoadedAssets=new Set(),ATLAS_EVIDENCE={layers:[{layer_kind:'point',layer_index:0,layer:metadata}]};
let STATIC_ATLAS_INLINE=false,staticAtlasLoadGeneration=1,filter='initial',diameter=20,busy=false,toolsDelayed=false,assetDelayed=false,releaseTools,releaseAsset;
const emptyState={dataset:{reason:'not_empty'}},slider={get value(){return diameter}},loads=[],predicates=[],blobs=[],downloads=[],revoked=[];
const GOVERNED_EDGE_RECORDS=[{edge_id:'edge',source_record_id:'a',target_record_id:'b'}];
const map={getZoom(){return 0}};
function atlasCaptureSnapshot(){return {build_id:'build',scope_slug:'scope',version:'version',ready:!busy,evidence_display:'both'}}
function atlasSelectionHashParams(){return new URLSearchParams({filter})}
function staticAtlasNodeSelectionNeeded(value){return value===row}
function pointFeatureVisible(layer,feature){predicates.push([layer===metadata,feature.record_id]);return feature.keep===true}
function polygonGeometryIsAdmitted(feature){return feature.validGeometry===true}
function polygonFeatureVisible(layer,properties){return properties.keep===true}
function visibleGovernedEdges(){return GOVERNED_EDGE_RECORDS}
function featureCoordinatePair(feature){return {latitude:feature.latitude,longitude:feature.longitude}}
async function loadStaticAtlasAsset(value,selectionOwned){loads.push([value.asset_key,selectionOwned]);if(assetDelayed)await new Promise(resolve=>{releaseAsset=resolve});STATIC_ATLAS_CHUNKS.nodes.push(chunk);staticAtlasLoadedAssets.add(value.asset_key)}
let toolsCached=true,toolRequests=0;
function currentEvidenceTools(){return toolsCached?{}:null}
function evidenceToolsDescriptor(){return {byte_count:100}}
async function loadEvidenceTools(){if(!toolsCached)toolRequests++;if(toolsDelayed)await new Promise(resolve=>{releaseTools=resolve});return {selectionExport:prepareAtlasSelectionExport}}
const button={disabled:false},status={textContent:''};
const document={getElementById(id){return id==='selection-export'?button:status},createElement(){return {click(){downloads.push({href:this.href,name:this.download})}}}};
class Blob{constructor(parts,options){this.text=parts.join('');this.type=options.type;blobs.push(this)}}
const URL={createObjectURL(){return 'blob:selection'},revokeObjectURL(value){revoked.push(value)}};
const window={setTimeout(callback){callback()}};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function snapshot(){return {status:status.textContent,disabled:button.disabled,loads,predicates,blobs:blobs.map(blob=>JSON.parse(blob.text)),downloads,revoked,toolRequests}}
(async()=>{
"""
        + action
        + "\n})().catch(error=>{console.error(error);process.exitCode=1});"
    )
    return cast(dict[str, Any], run_node_json(source))


def test_actual_download_loads_complete_public_rows_through_shared_owner() -> None:
    actual = observe(
        "await downloadAtlasSelection();console.log(JSON.stringify(snapshot()));"
    )
    assert actual["loads"] == [["node-1", False]]
    assert actual["predicates"] == [[True, "a"], [True, "b"]]
    assert len(actual["blobs"]) == len(actual["downloads"]) == 1
    payload = actual["blobs"][0]
    rows = payload["layers"][0]["records"]
    assert [row["feature"]["record_id"] for row in rows] == ["a", "b"]
    assert [row["feature"]["value"] for row in rows] == [None, 0]
    assert [row["feature"]["unit"] for row in rows] == ["grains", "percent"]
    assert payload["layers"][0]["metadata"] == {
        "key": "points",
        "label": "Literal public layer",
    }
    assert payload["relations"]["endpoint_eligibility"] == [
        {"relation_index": 0, "endpoint_eligible": True}
    ]
    assert payload["snapshot"]["selection_hash"] == "filter=initial"
    assert payload["snapshot"]["acceptance_diameter_km"] == 20
    assert actual["downloads"][0]["name"] == "pollenomics-selection.json"
    assert actual["revoked"] == ["blob:selection"]
    assert not actual["disabled"]


def test_download_waits_for_complete_assets_before_creating_one_blob() -> None:
    actual = observe(
        "assetDelayed=true;const request=downloadAtlasSelection();await tick();"
        "const before={blobs:blobs.length,downloads:downloads.length,disabled:button.disabled};"
        "releaseAsset();await request;console.log(JSON.stringify({before,after:snapshot()}));"
    )
    assert actual["before"] == {"blobs": 0, "downloads": 0, "disabled": True}
    assert len(actual["after"]["blobs"]) == 1
    assert not actual["after"]["disabled"]


def test_unavailable_relation_reason_is_preserved_with_zero_relation_rows() -> None:
    actual = observe(
        "GOVERNED_EDGE_RECORDS.length=0;STATIC_ATLAS_CHUNKS.edges={status:'unavailable',reason_code:'governed_events_unavailable'};"
        "await downloadAtlasSelection();console.log(JSON.stringify(snapshot()));"
    )
    payload = actual["blobs"][0]
    assert payload["snapshot"]["relation_availability"] == {
        "status": "unavailable",
        "reason_code": "governed_events_unavailable",
    }
    assert payload["counts"]["selected_relation_rows"] == 0


@pytest.mark.parametrize("limit", ["requests", "bytes"])
def test_optional_tools_alone_cannot_exceed_download_interaction_budget(
    limit: str,
) -> None:
    actual = observe(
        "toolsCached=false;"
        + (
            "STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_requests=0;"
            if limit == "requests"
            else "STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_bytes=99;"
        )
        + "await downloadAtlasSelection();console.log(JSON.stringify(snapshot()));"
    )
    assert actual["toolRequests"] == 0 and actual["loads"] == []
    assert actual["blobs"] == actual["downloads"] == []
    assert "budget" in actual["status"]


def test_first_download_reserves_tools_request_within_total_request_limit() -> None:
    actual = observe(
        "toolsCached=false;STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_requests=1;"
        "await downloadAtlasSelection();console.log(JSON.stringify(snapshot()));"
    )
    assert actual["toolRequests"] == 1 and actual["loads"] == []
    assert actual["blobs"] == actual["downloads"] == []
    assert "budget" in actual["status"]


@pytest.mark.parametrize("when", ["tools", "assets"])
@pytest.mark.parametrize(
    "change", ["filter='changed'", "staticAtlasLoadGeneration++", "diameter=30"]
)
def test_changes_during_preparation_refuse_without_creating_a_blob(
    when: str, change: str
) -> None:
    actual = observe(
        f"{when == 'tools' and 'toolsDelayed' or 'assetDelayed'}=true;"
        "const request=downloadAtlasSelection();await tick();"
        + change
        + f";{'releaseTools' if when == 'tools' else 'releaseAsset'}();await request;"
        "console.log(JSON.stringify(snapshot()));"
    )
    assert actual["blobs"] == actual["downloads"] == []
    assert "changed" in actual["status"].lower()
    assert not actual["disabled"]


@pytest.mark.parametrize(
    "action",
    [
        "busy=true",
        "emptyState.dataset.reason='loading_unavailable'",
        "STATIC_ATLAS_INLINE=true",
        "ATLAS_EVIDENCE.layers.push(ATLAS_EVIDENCE.layers[0])",
        "loadStaticAtlasAsset=async()=>{throw Error('authenticated transport refused')}",
    ],
)
def test_unready_missing_ambiguous_or_failed_data_never_produces_partial_download(
    action: str,
) -> None:
    actual = observe(
        action
        + ";await downloadAtlasSelection();console.log(JSON.stringify(snapshot()));"
    )
    assert actual["blobs"] == actual["downloads"] == []
    assert not actual["disabled"]
    assert actual["status"] != "Preparing the complete selection…"


def test_owner_uses_original_layer_metadata_and_existing_geometry_predicates() -> None:
    actual = observe(
        "const owner=atlasSelectionExportOwner();"
        "console.log(JSON.stringify({same:owner.layerForAsset(row)===metadata,"
        "point:owner.featureSelected(metadata,features[0],'point'),"
        "polygon:owner.featureSelected(metadata,{validGeometry:true,properties:{keep:true}},'polygon'),"
        "refused:owner.featureSelected(metadata,{validGeometry:false,properties:{keep:true}},'polygon')}));"
    )
    assert actual == {"same": True, "point": True, "polygon": True, "refused": False}


def test_download_control_and_handler_are_present_without_eager_optional_loading() -> (
    None
):
    controls = template_block(
        '<details id="view-controls"', '<details id="scientific-controls"'
    )
    assert 'id="selection-export"' in controls
    assert 'id="selection-export-status"' in controls
    assert 'aria-describedby="selection-export-status"' in controls
    assert (
        "document.getElementById('selection-export').addEventListener('click', downloadAtlasSelection)"
        in template_block(
            "modeledContextDownload.addEventListener", "focusTabs.addEventListener"
        )
    )
