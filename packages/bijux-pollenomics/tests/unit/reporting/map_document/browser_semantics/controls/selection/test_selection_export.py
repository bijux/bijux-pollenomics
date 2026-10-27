"""Complete selection exports use authenticated public rows and existing predicates."""

from __future__ import annotations

from copy import deepcopy
from importlib.resources import files
import json
from pathlib import Path
import subprocess
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)

from .....atlas.static_assets.fixtures.layers import build_polygon_layers
from .....atlas.static_assets.fixtures.scientific_evidence import (
    build_edge_records,
    build_scientific_point_layers,
    build_scientific_signals,
)
from ...support import index_transport_helpers, run_node_json, template_block

ASSETS = files("bijux_pollenomics.reporting.map_document").joinpath("assets")
SCRIPT = ASSETS.joinpath("selection-export.js").read_text()


def publish(root: Path, *, duplicate: bool = False) -> dict[str, Any]:
    points = [dict(row) for row in build_scientific_point_layers()[:1]]
    points[0].update(applies_country_filter=True, applies_time_filter=True)
    point_rows = points[0]["features"]
    assert isinstance(point_rows, list)
    point_rows[0].update(
        source_value=0,
        source_unit="NISP",
        source_denominator=None,
        title="Åland <script>literal()</script>",
    )
    point_rows[1].update(source_value=None, source_unit="NISP digitized")
    if duplicate:
        point_rows.append(deepcopy(point_rows[0]))
    edges = [dict(row) for row in build_edge_records()]
    edges[0].update(
        status="indeterminate_order",
        candidate_status="indeterminate_order",
        directional_arrow_allowed=False,
        route_interpretation_allowed=False,
        map_geometry_role="endpoint_connection_only",
        minimum_lag_years=0,
        maximum_lag_years=None,
    )
    assets = write_static_atlas_assets(
        root,
        slug="selection",
        version="controlled",
        point_layers=points,
        polygon_layers=build_polygon_layers(),
        edge_records=[] if duplicate else edges,
        scientific_signals=build_scientific_signals(),
    )
    rows = cast(
        list[dict[str, Any]], normalize_asset_inventory(assets.manifest["assets"])
    )
    payloads = {
        row["domain"]: decode_chunk_script(
            (root / row["path"]).read_bytes(),
            expected_asset_key=row["asset_key"],
            expected_payload_sha256=row["payload_sha256"],
            expected_payload_encoding=row["payload_encoding"],
            expected_decoded_byte_count=row["decoded_byte_count"],
        )
        for row in rows
        if row["domain"] in {"provenance", "edges"}
    }
    return {
        "bootstrap": {
            **assets.manifest,
            "schema_version": "atlas-static-bootstrap.v2",
            "assets": rows,
        },
        "provenance": payloads["provenance"],
        "edges": payloads["edges"]["records"],
        "scripts": {row["asset_key"]: (root / row["path"]).read_text() for row in rows},
    }


@pytest.fixture
def packet(tmp_path: Path) -> dict[str, Any]:
    return publish(tmp_path)


SETUP = r"""
const STATIC_ATLAS_BOOTSTRAP=packet.bootstrap,STATIC_ATLAS_SCHEMAS={nodes:['atlas-node-chunk.v1']};
const STATIC_ATLAS_RAW_CHUNKS=[],STATIC_ATLAS_CHUNKS={nodes:[],details:[]};
const staticAtlasLoadedAssets=new Set(),staticAtlasInFlightAssets=new Map();
const ALL_LAYERS=packet.provenance.layers.map(row=>row.layer),SCOPE_KEY='nordic';
const SCIENTIFIC_SIGNALS=packet.provenance.scientific_signals;
const activeLayerKeys=new Set(ALL_LAYERS.map(row=>row.key)),activeCountries=new Set(['Norway','Sweden']);
const activeScientificSignalIds=new Set(SCIENTIFIC_SIGNALS.map(row=>row.signal_id));
const retainedNeighborRecordCountries=new Map(),nativeLraController=null;
const TIME_HAS_DATA=true;let timeStartBp=0,timeEnd=101;
function timeWindowEndBp(){return timeEnd}
function timeFilterUsesFullExtent(){return true}
function isAnimalLayer(){return false}
function isAnimalSourceChronologyLayer(){return false}
function sourceChronologyFeatureMatches(){return true}
function featureMatchesAnimalFilters(){return true}
function modeledContextFeatureVisible(){return true}
function staticAtlasViewportNeeded(){throw Error('Viewport pruning must not select export assets')}
let state={build_id:STATIC_ATLAS_BOOTSTRAP.build_id,scope_slug:STATIC_ATLAS_BOOTSTRAP.scope_slug,
 version:STATIC_ATLAS_BOOTSTRAP.version,ready:true,generation:1,
 shared_url:'https://localhost/#display_mode=nodes',display:{mode:'nodes',visible_points:1,rendered_relations:0}};
let requests=[],failAsset=null,tamperAsset=null,afterLoad=null;
globalThis.fetch=async path=>{
 const row=STATIC_ATLAS_BOOTSTRAP.assets.find(row=>'./'+row.path===path);requests.push(row.asset_key);
 return {ok:row.asset_key!==failAsset,text:async()=>packet.scripts[row.asset_key]+(row.asset_key===tamperAsset?'tampered':'')};
};
"""


def observe(packet: dict[str, Any], action: str) -> dict[str, Any]:
    source = (
        "const packet="
        + json.dumps(packet)
        + ";const original=JSON.stringify(packet);\n"
        + SETUP
        + template_block(
            "function staticAtlasFailure", "function normalizeStaticAtlasBootstrap"
        )
        + template_block(
            "async function staticAtlasSha256", "function indexTransportDescriptor"
        )
        + index_transport_helpers(common=False)
        + template_block(
            "function indexTransportDescriptor",
            "function validateStaticAtlasEdgeAssets",
        )
        + template_block(
            "function validateStaticAtlasPayload", "function loadStaticAtlasAsset"
        )
        + ASSETS.joinpath("selection-loading.js").read_text()
        + template_block(
            "function staticAtlasLayerForRow", "function staticAtlasViewportNeeded"
        )
        + template_block(
            "function staticAtlasNodeSelectionNeeded",
            "function requiredStaticAtlasEdgeNodeKeys",
        )
        + template_block("function finiteTimeValue", "function valueIsAvailable")
        + template_block("function finiteCoordinateValue", "function coordinateLabel")
        + template_block(
            "function featureTimeAdmission", "function polygonFeatureVisible"
        )
        + template_block(
            "function polygonFeatureVisible", "function removeRenderedLayers"
        )
        + template_block(
            "function isRetainedNeighborContext", "function renderRelationControls"
        )
        + template_block(
            "function atlasEdgeIntersectsViewport", "function edgeEvidencePopupHtml"
        )
        + SCRIPT
        + r"""
const owner={bootstrap:STATIC_ATLAS_BOOTSTRAP,
 snapshot:()=>({...state,filters:{countries:[...activeCountries],layers:[...activeLayerKeys],signals:[...activeScientificSignalIds],time:[timeStartBp,timeEnd]}}),
 assetNeeded:staticAtlasNodeSelectionNeeded,isLoaded:row=>staticAtlasLoadedAssets.has(row.asset_key),
 loadAsset:async row=>{await fetchStaticAtlasNodeAsset(row,new AbortController().signal);if(afterLoad)afterLoad()},
 readAsset:row=>STATIC_ATLAS_CHUNKS.nodes.find(part=>part.asset_key===row.asset_key),
 layerForAsset:row=>packet.provenance.layers.find(layer=>layer.layer_index===row.layer_index&&layer.layer_kind===row.layer_kind)?.layer,
 featureSelected:(layer,feature,kind)=>kind==='point'?pointFeatureVisible(layer,feature):polygonFeatureVisible(layer,feature.properties)&&polygonGeometryIsAdmitted(feature),
 relations:()=>({retained_count:packet.edges.length,records:packet.edges}),
 endpointEligible:(edge,entries)=>atlasEdgeRenderSelection([edge],new Map(entries.map(row=>[String(row.feature.record_id),row])),0,featureCoordinatePair,null).rows.length===1};
async function exportResult(){const result=await prepareAtlasSelectionExport(owner);return {...result,payload:JSON.parse(result.text)}}
(async()=>{
"""
        + action
        + "\n})().catch(error=>{console.error(error);process.exitCode=1});"
    )
    try:
        return cast(dict[str, Any], run_node_json(source))
    except subprocess.CalledProcessError as error:
        raise AssertionError(error.stderr) from error


def test_complete_export_loads_off_viewport_rows_and_preserves_literal_fields(
    packet: dict[str, Any],
) -> None:
    result = observe(
        packet,
        "const result=await exportResult();console.log(JSON.stringify({result,requests,unchanged:original===JSON.stringify(packet)}));",
    )
    data = result["result"]["payload"]
    counts = data["counts"]
    assert counts["selected_public_rows"] == 3
    assert counts["point_rows"] == 2 and counts["polygon_rows"] == 1
    assert counts["selected_node_assets"] == counts["newly_loaded_node_assets"] == 3
    assert (
        counts["selected_relation_rows"]
        == counts["endpoint_eligible_relation_rows"]
        == 2
    )
    assert data["snapshot"]["display"]["visible_points"] == 1
    assert data["snapshot"]["display"]["rendered_relations"] == 0
    points = data["layers"][0]["records"]
    assert [row["feature_index"] for row in points] == [0, 1]
    assert points[0]["feature"]["source_value"] == 0
    assert points[0]["feature"]["source_unit"] == "NISP"
    assert points[0]["feature"]["source_denominator"] is None
    assert points[0]["feature"]["title"] == "Åland <script>literal()</script>"
    assert points[1]["feature"]["source_value"] is None
    assert points[1]["feature"]["source_unit"] == "NISP digitized"
    native = next(
        row for row in data["relations"]["records"] if "candidate_status" in row
    )
    assert native["candidate_status"] == "indeterminate_order"
    assert native["directional_arrow_allowed"] is False
    assert native["minimum_lag_years"] == 0 and native["maximum_lag_years"] is None
    assert data["scope"]["source_series_included"] is False
    assert data["scope"]["scientific_admission"] == "not_asserted"
    assert result["result"]["byte_count"] == len(result["result"]["text"].encode())
    assert len(result["requests"]) == 3 and result["unchanged"] is True


def test_cached_assets_are_authenticated_and_not_requested_again(
    packet: dict[str, Any],
) -> None:
    actual = observe(
        packet,
        "const first=STATIC_ATLAS_BOOTSTRAP.assets.find(row=>row.domain==='nodes');await owner.loadAsset(first);const before=JSON.stringify(STATIC_ATLAS_CHUNKS.nodes[0]);requests=[];const result=await exportResult();console.log(JSON.stringify({counts:result.counts,requests,unchanged:before===JSON.stringify(STATIC_ATLAS_CHUNKS.nodes[0])}));",
    )
    assert actual["counts"]["authenticated_cached_node_assets"] == 1
    assert actual["counts"]["newly_loaded_node_assets"] == len(actual["requests"]) == 2
    assert actual["unchanged"] is True


def test_time_excluded_endpoints_do_not_drop_retained_relations(
    packet: dict[str, Any],
) -> None:
    actual = observe(
        packet,
        "timeEnd=0;const result=await exportResult();console.log(JSON.stringify(result.payload));",
    )
    assert actual["counts"]["point_rows"] == 1
    assert actual["counts"]["selected_relation_rows"] == 2
    assert actual["counts"]["endpoint_eligible_relation_rows"] == 1
    assert [
        row["endpoint_eligible"] for row in actual["relations"]["endpoint_eligibility"]
    ] == [False, True]
    assert len(actual["relations"]["records"]) == 2


def test_repeated_native_record_ids_remain_distinct_public_rows(tmp_path: Path) -> None:
    actual = observe(
        publish(tmp_path, duplicate=True),
        "console.log(JSON.stringify((await exportResult()).counts));",
    )
    assert actual["point_rows"] == actual["rows_with_literal_record_id"] == 3
    assert actual["unique_literal_record_ids"] == 2
    assert actual["selected_public_rows"] == 4


def test_repeated_relation_ids_preserve_each_retained_row(
    packet: dict[str, Any],
) -> None:
    actual = observe(
        packet,
        "owner.relations=()=>({retained_count:3,records:[...packet.edges,packet.edges[0]]});"
        "console.log(JSON.stringify((await exportResult()).payload));",
    )
    assert actual["counts"]["selected_relation_rows"] == 3
    assert actual["counts"]["unique_literal_edge_ids"] == 2
    assert len(actual["relations"]["records"]) == 3
    assert len(actual["relations"]["endpoint_eligibility"]) == 3


@pytest.mark.parametrize(
    "field", ["generation", "build_id", "shared_url", "display", "filters"]
)
def test_intervening_snapshot_change_refuses_whole_result(
    packet: dict[str, Any], field: str
) -> None:
    actual = observe(
        packet,
        f"afterLoad=()=>{{if({json.dumps(field)}==='filters')activeCountries.clear();else state[{json.dumps(field)}]='changed'}};let error;try{{await exportResult()}}catch(value){{error=value.message}}console.log(JSON.stringify({{error,requests}}));",
    )
    assert "build, filters or display changed" in actual["error"]


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "tampered",
        "unaccepted",
        "missing_payload",
        "wrong_build",
        "wrong_count",
    ],
)
def test_missing_or_inconsistent_selected_asset_never_yields_partial_export(
    packet: dict[str, Any], defect: str
) -> None:
    actual = observe(
        packet,
        "const row=STATIC_ATLAS_BOOTSTRAP.assets.find(row=>row.domain==='nodes');const defect="
        + json.dumps(defect)
        + ";if(defect==='missing')failAsset=row.asset_key;if(defect==='tampered')tamperAsset=row.asset_key;"
        "if(defect==='unaccepted')owner.loadAsset=async()=>{};"
        "if(defect==='missing_payload')owner.readAsset=()=>null;"
        "if(defect==='wrong_build'||defect==='wrong_count'){const read=owner.readAsset;owner.readAsset=row=>({...read(row),...(defect==='wrong_build'?{build_id:'wrong'}:{features:[]})})}"
        "let error;try{await exportResult()}catch(value){error=value.message}console.log(JSON.stringify({error}));",
    )
    assert "Current selection export unavailable" in actual["error"]


@pytest.mark.parametrize(
    "defect", ["requests", "transport", "decoded", "legacy_upper_bound", "json"]
)
def test_resource_limits_refuse_without_truncation(
    packet: dict[str, Any], defect: str
) -> None:
    actual = observe(
        packet,
        "const defect="
        + json.dumps(defect)
        + ";const budgets=STATIC_ATLAS_BOOTSTRAP.budgets;"
        "if(defect==='requests')budgets.interaction_max_requests=0;"
        "if(defect==='transport'){const row=STATIC_ATLAS_BOOTSTRAP.assets.find(row=>row.domain==='nodes');row.byte_count=budgets.interaction_max_bytes+1}"
        "if(defect==='decoded')budgets.interaction_max_bytes=1;"
        "if(defect==='legacy_upper_bound'){STATIC_ATLAS_BOOTSTRAP.assets.forEach(row=>delete row.decoded_byte_count);budgets.interaction_max_bytes=budgets.chunk_max_bytes}"
        "if(defect==='json'){state.context='x'.repeat(100000);budgets.interaction_max_bytes=50000}"
        "let error;try{await exportResult()}catch(value){error=value.message}console.log(JSON.stringify({error,requests}));",
    )
    assert "budget" in actual["error"]
    if defect != "json":
        assert actual["requests"] == []


def test_nonfinite_values_refuse_instead_of_becoming_null(
    packet: dict[str, Any],
) -> None:
    actual = observe(
        packet,
        "state.unavailable=NaN;let error;try{await exportResult()}catch(value){error=value.message}console.log(JSON.stringify({error,requests}));",
    )
    assert "JSON cannot preserve" in actual["error"]
    assert actual["requests"] == []


def test_true_empty_selection_has_zero_counts_without_loading(
    packet: dict[str, Any],
) -> None:
    actual = observe(
        packet,
        "activeLayerKeys.clear();const result=await exportResult();console.log(JSON.stringify({payload:result.payload,requests}));",
    )
    assert actual["payload"]["layers"] == []
    assert actual["payload"]["counts"]["selected_public_rows"] == 0
    assert actual["payload"]["counts"]["selected_relation_rows"] == 2
    assert actual["payload"]["counts"]["endpoint_eligible_relation_rows"] == 0
    assert actual["requests"] == []


@pytest.mark.parametrize("budget", ["requests", "bytes"])
@pytest.mark.parametrize("one_over", [False, True])
def test_transport_overhead_and_missing_nodes_share_one_budget(
    packet: dict[str, Any], budget: str, one_over: bool
) -> None:
    actual = observe(
        packet,
        "const budget="
        + json.dumps(budget)
        + ";const oneOver="
        + json.dumps(one_over)
        + ";const nodes=STATIC_ATLAS_BOOTSTRAP.assets.filter(row=>row.domain==='nodes');"
        "const limits=STATIC_ATLAS_BOOTSTRAP.budgets;"
        "if(budget==='requests'){limits.interaction_max_requests=nodes.length+1;"
        "owner.transportOverhead={request_count:oneOver?2:1,byte_count:0}}"
        "else{limits.interaction_max_bytes=nodes.reduce((sum,row)=>sum+row.byte_count,0)+100000;"
        "owner.transportOverhead={request_count:0,byte_count:oneOver?100001:100000}}"
        "let counts,error;try{counts=(await exportResult()).counts}catch(value){error=value.message}"
        "console.log(JSON.stringify({counts,error,requests}));",
    )
    if one_over:
        assert "interaction request or byte budget" in actual["error"]
        assert actual["requests"] == []
    else:
        assert actual["counts"]["newly_loaded_node_assets"] == 3
        assert len(actual["requests"]) == 3


@pytest.mark.parametrize(
    "overhead",
    [
        None,
        [],
        {},
        {"request_count": True, "byte_count": 0},
        {"request_count": -1, "byte_count": 0},
        {"request_count": 0, "byte_count": None},
        {"request_count": 0, "byte_count": 0.5},
        {"request_count": 0, "byte_count": 2**53},
    ],
)
def test_malformed_transport_overhead_refuses_before_node_requests(
    packet: dict[str, Any], overhead: object
) -> None:
    actual = observe(
        packet,
        "owner.transportOverhead="
        + json.dumps(overhead)
        + ";let error;try{await exportResult()}catch(value){error=value.message}"
        "console.log(JSON.stringify({error,requests}));",
    )
    assert "transport overhead" in actual["error"]
    assert actual["requests"] == []
