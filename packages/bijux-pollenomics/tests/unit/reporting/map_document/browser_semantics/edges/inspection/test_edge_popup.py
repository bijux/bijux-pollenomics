"""Canonical event evidence and one accessible drawer action in edge popups."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from typing import Any, cast
from xml.etree import ElementTree as ET

import pytest

from bijux_pollenomics.analysis.propagation.network import generate_propagation_network
from bijux_pollenomics.analysis.propagation.projection import (
    project_propagation_network,
)

from ......analysis.propagation.network.support import event
from ...support import run_node_json, template_block
from ..test_scientific_edges import edge_row, normalize_edges


def projected_edge(
    *, indeterminate: bool = False, domestic: bool = False
) -> dict[str, Any]:
    source = replace(
        event(
            "source",
            country_code="SE" if domestic else "NO",
            feature_key="taxon:fixture",
            younger_bp=0 if indeterminate else 100,
            older_bp=100,
        ),
        source_record_id="source:record",
        event_id="",
    )
    target = replace(
        event(
            "target",
            feature_key="taxon:fixture",
            younger_bp=50 if indeterminate else 0,
            older_bp=150 if indeterminate else 0,
        ),
        source_record_id="target:record",
        event_id="",
    )
    products = project_propagation_network(
        generate_propagation_network((source, target))
    )
    layer: Any = products[
        "indeterminate_pairs.geojson"
        if indeterminate
        else "directed_candidates.geojson"
    ]
    row = next(
        feature["properties"]
        for feature in layer["features"]
        if feature["properties"]["source_event_id"] == source.event_id
    )
    row.update(
        signal_id="taxon:fixture",
        source_record_id=source.source_record_id,
        target_record_id=target.source_record_id,
        source_country="Sweden" if domestic else "Norway",
        target_country="Sweden",
    )
    return cast(dict[str, Any], row)


def popup(
    row: dict[str, Any], *, action: str = "none", foreign_button: bool = False
) -> dict[str, Any]:
    source = (
        "const edges="
        + json.dumps(normalize_edges([row]))
        + ";const action="
        + json.dumps(action)
        + ";const foreignButton="
        + json.dumps(foreign_button)
        + ";"
        + template_block("function escapeHtml", "function normalizedMediaLinks")
        + """
const original=JSON.stringify(edges);
const SCIENTIFIC_SIGNALS=[{signal_id:'taxon:fixture',label:'Source taxon',color:'#123456',non_color_cue:'circle'}];
const STATIC_ATLAS_INLINE=false,STATIC_ATLAS_CHUNKS={edges:{status:'available'}};
let activeEvidenceDisplay=resetEvidenceDisplay();
const visiblePointEntries=[
{feature:{record_id:'source:record',latitude:60,longitude:18},layer:{key:'points'}},
{feature:{record_id:'target:record',latitude:61,longitude:19},layer:{key:'points'}}];
function featureCoordinatePair(row){return row}function visibleGovernedEdges(){return edges}
function scientificCueGlyph(cue){return cue}
let focus=null,activeFocusTab='overview',requests=0,renders=0,focusCalls=0,prevented=false,stopped=false;
const document={getElementById(id){if(id!=='focus-tab-relation')throw Error('Wrong focus target');return {focus(){focusCalls++}}}};
function renderFocusDetail(){renders++}
const captured=[],renderedEdgeLayers=[],map={};
const L={polyline(coordinates,options){const row={coordinates,options,callbacks:{},popup:''};captured.push(row);
return {bindPopup(html){row.popup=html},on(name,callback){row.callbacks[name]=callback},addTo(){}}}};
async function detailTabsForRecordId(id){requests++;return {overview:{record_id:id},relation:{retained:'original evidence'},provenance:{source:'original source'}}}
function unavailableDetailTabs(){throw Error('Unexpected missing fixture')}
function setFocusState(state){focus=state;activeFocusTab='overview'}
"""
        + template_block(
            "function scientificSignalById", "function renderPolygonLayers"
        )
        + """
renderEdgeLayers();
(async()=>{
const row=captured[0];let nativeAction=false;
if(action==='line')await row.callbacks.click();
if(action==='button'){
  const button={dataset:{compareEdge:foreignButton?'foreign':edges[0].edge_id}};
  const event={popup:{getElement:()=>({querySelector:()=>button})}};
  row.callbacks.popupopen(event);row.callbacks.popupopen(event);
  if(button.onclick){nativeAction=true;await button.onclick({detail:0,preventDefault(){prevented=true},stopPropagation(){stopped=true}})}
}
console.log(JSON.stringify({html:row.popup,focus,requests,renders,focusCalls,activeFocusTab,nativeAction,prevented,stopped,unchanged:original===JSON.stringify(edges)}));
})().catch(error=>{console.error(error);process.exit(1)});
"""
    )
    return cast(dict[str, Any], run_node_json(source))


def text(result: dict[str, Any]) -> str:
    return " ".join(" ".join(ET.fromstring(result["html"]).itertext()).split())


def test_actual_projection_bridge_popup_preserves_zero_and_canonical_event_ages() -> (
    None
):
    row = projected_edge()
    row["source_age_bp"], row["target_age_bp"] = 9999, 9999
    before = deepcopy(row)
    observed = popup(row)
    rendered = text(observed)
    assert "Older endpoint site-source · 100 BP" in rendered
    assert "Younger endpoint site-target · 0 BP" in rendered
    assert "9999" not in rendered
    assert "Distance 0 km" in rendered
    assert "Directional lag bounds 100 to 100 years" in rendered
    assert "rectangular_100km_100yr_v1" in rendered
    assert "maximum distance 100 km; maximum lag 100 years" in rendered
    assert "Norway → Sweden" in rendered
    assert "definite_candidate" in rendered and "taxon" in rendered
    assert "not demonstrate a migration route" in rendered
    assert row == before and observed["unchanged"] is True


def test_indeterminate_order_never_gains_older_younger_labels_or_arrows() -> None:
    observed = popup(projected_edge(indeterminate=True))
    rendered = text(observed)
    assert "Source endpoint site-source · 0–100 BP" in rendered
    assert "Target endpoint site-target · 50–150 BP" in rendered
    assert "Directional lag bounds -150 to 50 years" in rendered
    assert "Norway — Sweden" in rendered
    assert "Older endpoint" not in rendered and "Younger endpoint" not in rendered
    assert "→" not in rendered and "Indeterminate order (no direction)" in rendered


@pytest.mark.parametrize(
    "posture", ["cross_border", "domestic", "missing", "wrong_type"]
)
def test_country_pair_posture_uses_only_the_supplied_native_boolean(
    posture: str,
) -> None:
    row = projected_edge(domestic=posture == "domestic")
    # Display labels need not be an authority for national membership.
    row["source_country"], row["target_country"] = "Source label", "Target label"
    if posture == "missing":
        del row["cross_border"]
    elif posture == "wrong_type":
        row["cross_border"] = 0
    rendered = text(popup(row))
    expected = (
        "Cross-border"
        if posture == "cross_border"
        else "Domestic"
        if posture == "domestic"
        else "Country-pair posture unavailable"
    )
    assert f"Countries {expected} · Source label → Target label" in rendered


@pytest.mark.parametrize("value", [True, False, None, 1, "false", [], {}, "absent"])
def test_native_country_transport_and_filters_never_admit_truthy_unknowns(
    value: object,
) -> None:
    raw = projected_edge()
    raw["source_country"], raw["target_country"] = "Source label", "Target label"
    if value == "absent":
        del raw["cross_border"]
    else:
        raw["cross_border"] = value
    before = deepcopy(raw)
    edge = normalize_edges([raw])[0]
    if value == "absent":
        assert "cross_border" not in edge
    else:
        assert edge["cross_border"] == value and type(edge["cross_border"]) is type(
            value
        )
    observed = run_node_json(
        template_block(
            "function atlasCountryPairKey", "function atlasFilterStateSnapshot"
        )
        + "const edge="
        + json.dumps(edge)
        + ";const countries=new Set(['Source label']);"
        + "console.log(JSON.stringify({visible:atlasEdgeVisible(edge,countries,'all',true,new Set(['taxon:fixture'])),neighbors:atlasRetainedNeighborRecordCountries([edge],countries).size}));"
    )
    assert observed == {
        "visible": value is True,
        "neighbors": 1 if value is True else 0,
    }
    assert raw == before


def test_flat_legacy_country_filter_compatibility_is_not_native_posture_evidence() -> (
    None
):
    raw = edge_row("definite_candidate", native=False)
    edge = normalize_edges([raw])[0]
    assert edge["cross_border"] is True and "cross_border" not in raw
    assert "Country-pair posture unavailable" in text(popup(raw))


@pytest.mark.parametrize("change", ["missing", "null", "bool", "reversed", "foreign"])
def test_unavailable_canonical_age_never_falls_back_to_node_age(change: str) -> None:
    row = projected_edge()
    row["source_age_bp"] = 12345
    if change == "missing":
        del row["source_event"]
    elif change == "foreign":
        row["source_event"]["event_id"] = "foreign-event"
    elif change == "null":
        row["source_event"]["younger_bp"] = None
    elif change == "bool":
        row["source_event"]["younger_bp"] = False
    else:
        row["source_event"]["younger_bp"], row["source_event"]["older_bp"] = 101, 100
    rendered = text(popup(row))
    assert "12345" not in rendered
    assert "Unavailable" in rendered
    assert (
        "0 BP" in rendered
        if change not in {"missing", "foreign"}
        else "Unavailable (no comparable canonical event age)" in rendered
    )


@pytest.mark.parametrize("change", ["distance", "lag", "scenario"])
def test_legacy_missing_numbers_and_scenario_are_not_defaulted(change: str) -> None:
    row = edge_row("definite_candidate", native=False)
    row.update(
        distance_km_unrounded=0,
        minimum_lag_years=0,
        maximum_lag_years=0,
        scenario_id="provided-only",
    )
    if change == "distance":
        row["distance_km_unrounded"] = None
    elif change == "lag":
        row["minimum_lag_years"] = None
    else:
        del row["scenario_id"]
    rendered = text(popup(row))
    assert "Unavailable (no comparable canonical event age)" in rendered
    assert {
        "distance": "Distance Unavailable",
        "lag": "Directional lag bounds Unavailable",
        "scenario": "Scenario Unavailable",
    }[change] in rendered
    if change != "distance":
        assert "Distance 0 km" in rendered
    if change != "lag":
        assert "Directional lag bounds 0 to 0 years" in rendered


def test_source_fields_and_action_identity_are_escaped() -> None:
    row = projected_edge()
    hostile = '<img src=x onerror="alert(1)">'
    row["source_event"]["site_id"] = row["source_site_id"] = hostile
    row["scenario_id"] = hostile
    row["edge_id"] = "edge:<script>unsafe</script>"
    result = popup(row)
    document = ET.fromstring(result["html"])
    assert document.find(".//img") is None and document.find(".//script") is None
    assert hostile in text(result)
    button = document.find("button")
    assert button is not None and button.get("data-compare-edge") == row["edge_id"]


@pytest.mark.parametrize("action", ["line", "button"])
def test_accessible_compare_action_reuses_canonical_drawer_callback(
    action: str,
) -> None:
    row = projected_edge()
    observed = popup(row, action=action)
    button = ET.fromstring(observed["html"]).find("button")
    assert (
        button is not None and button.tag == "button" and button.get("type") == "button"
    )
    assert (
        button.text == "Compare evidence"
        and button.get("data-compare-edge") == row["edge_id"]
    )
    assert observed["requests"] == 1  # Reopening a popup does not accumulate handlers.
    assert observed["focus"]["edgeId"] == row["edge_id"]
    assert (
        observed["focus"]["detailTabs"]["relation"]["source_event_id"]
        == row["source_event_id"]
    )
    assert (
        observed["focus"]["detailTabs"]["relation"]["retained"] == "original evidence"
    )
    assert observed["activeFocusTab"] == (
        "relation" if action == "button" else "overview"
    )
    assert observed["focusCalls"] == (1 if action == "button" else 0)
    assert observed["renders"] == (1 if action == "button" else 0)
    assert observed["prevented"] is observed["stopped"] is (action == "button")
    assert observed["unchanged"] is True


def test_foreign_popup_button_cannot_open_another_edge() -> None:
    observed = popup(projected_edge(), action="button", foreign_button=True)
    assert observed["requests"] == 0 and observed["focus"] is None
    assert observed["nativeAction"] is False
