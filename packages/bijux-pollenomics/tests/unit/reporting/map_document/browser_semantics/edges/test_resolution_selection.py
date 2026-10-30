"""Scientific resolution filters select distinct unchanged candidate evidence."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import TypedDict, cast

import pytest

from bijux_pollenomics.analysis.propagation.network import (
    PhenomenonEvent,
    generate_propagation_network,
)
from bijux_pollenomics.core.geospatial.geojson import JsonObject
from bijux_pollenomics.reporting.map_document.evidence import normalize_atlas_evidence

from .....analysis.propagation.network.support import event
from ..support import run_node_json, template_block


class RenderedCandidate(TypedDict):
    title: str
    popup: str
    relation: dict[str, object]


class SelectionState(TypedDict):
    selected: list[str]
    edges: list[dict[str, object]]
    rendered: list[RenderedCandidate]
    points: list[str]
    summary: str


class ObservedSelection(TypedDict):
    states: list[SelectionState]
    unchanged: bool
    eligibility_count: int


def governed_edges() -> tuple[list[JsonObject], list[JsonObject]]:
    candidates: list[PhenomenonEvent] = []
    for resolution, feature in (
        ("ecological_group", "group:cereals"),
        ("taxon", "taxon:secale_cereale"),
    ):
        candidates.extend(
            (
                event("source", resolution=resolution, feature_key=feature),
                event(
                    "target",
                    resolution=resolution,
                    feature_key=feature,
                    younger_bp=5500,
                    older_bp=5500,
                ),
            )
        )
    network = generate_propagation_network(candidates)
    scenario = network.scenario_results[0]
    assert scenario.reconciliation.eligible_event_count == 4
    assert len(scenario.directed_candidates) == 2
    rows: list[JsonObject] = []
    for candidate in scenario.directed_candidates:
        rows.append(
            {
                **candidate.as_dict(),
                "signal_id": candidate.feature_key,
                "source_record_id": "record-source",
                "target_record_id": "record-target",
                "source_country": "Sweden",
                "target_country": "Sweden",
                "status": candidate.candidate_status,
            }
        )
    signals: list[JsonObject] = [
        {
            "signal_id": "group:cereals",
            "feature_key": "group:cereals",
            "resolution": "group",
            "label": "Cereals",
            "status": "accepted",
        },
        {
            "signal_id": "taxon:secale_cereale",
            "feature_key": "taxon:secale_cereale",
            "resolution": "taxon",
            "label": "Secale cereale",
            "status": "accepted",
        },
    ]
    original = deepcopy((rows, signals))
    admitted = normalize_atlas_evidence(
        detail_records=[],
        scientific_signals=signals,
        edge_records=rows,
        sequence_records=[],
    )
    assert (rows, signals) == original
    return list(admitted.edge_records), list(admitted.scientific_signals)


@pytest.mark.parametrize(
    "initial",
    ["group:cereals", "taxon:secale_cereale"],
    ids=["MAP-002-group-first", "MAP-002-taxon-first"],
)
def test_group_taxon_switch_preserves_candidate_identity_and_eligibility_counts(
    initial: str,
) -> None:
    edges, signals = governed_edges()
    source = (
        "const GOVERNED_EDGE_RECORDS="
        + json.dumps(edges)
        + ";\nconst SCIENTIFIC_SIGNALS="
        + json.dumps(signals)
        + ";\nconst initial="
        + json.dumps(initial)
        + ";\n"
        + """
const sourceSnapshot=JSON.stringify(GOVERNED_EDGE_RECORDS);
const GOVERNED_EDGE_ELIGIBILITY_COUNT=GOVERNED_EDGE_RECORDS.length;
const STATIC_ATLAS_INLINE=false,STATIC_ATLAS_CHUNKS={edges:{status:'available'},sequences:{status:'unavailable',reason_code:'synthetic_sequences_not_supplied'}};
const GOVERNED_SEQUENCE_RECORDS=[],COUNTRY_PAIR_KEYS=['Sweden|Sweden'];
const activeCountries=new Set(['Sweden']),activeCountryPair='all',crossBorderOnly=false;
const activeScientificSignalIds=new Set();
let activeEvidenceDisplay=resetEvidenceDisplay(),pendingEdgeFocus=null;
const countryPairFilter={},crossBorderOnlyCheckbox={},relationSummary={dataset:{}};
const relationFilterStatus={},relationFilterControls=Object.fromEntries(relationFilterFields().map(([key])=>[key,{}]));
const relationEventDefinitionControl={},relationEventDefinitionStatus={};
const visiblePointEntries=[
 {feature:{record_id:'record-source',latitude:55.605,longitude:13.0038,scientific_signal_ids:['group:cereals','taxon:secale_cereale']},layer:{key:'points',scientific_selection_enabled:true}},
 {feature:{record_id:'record-target',latitude:55.605,longitude:13.0038,scientific_signal_ids:['group:cereals','taxon:secale_cereale']},layer:{key:'points',scientific_selection_enabled:true}},
];
function featureCoordinatePair(row){return row}
function escapeHtml(value){return String(value)}
function scientificCueGlyph(value){return value}
const map={},renderedEdgeLayers=[];let captured=[],focus=null;
const L={polyline(coordinates,options){
 const row={popup:'',callbacks:{}};captured.push(row);
 return {bindPopup(value){row.popup=value},on(event,callback){row.callbacks[event]=callback},addTo(){}};
}};
async function detailTabsForRecordId(){return {overview:{},relation:{},provenance:{}}}
function unavailableDetailTabs(){return {}}
function setFocusState(state){focus=state}
"""
        + template_block(
            "function atlasCountryPairKey",
            "function atlasRetainedNeighborRecordCountries",
        )
        + template_block(
            "function featureMatchesScientificSelection", "function pointFeatureVisible"
        )
        + template_block(
            "function visibleGovernedEdges", "function isRetainedNeighborContext"
        )
        + template_block(
            "function renderRelationControls", "function selectSourceChronologyLevel"
        )
        + template_block(
            "function scientificSignalById", "function renderPolygonLayers"
        )
        + """
async function inspect(){
 const opposite=initial==='group:cereals'?'taxon:secale_cereale':'group:cereals';
 const selections=[[initial],[opposite],['group:cereals','taxon:secale_cereale'],[],[initial]];
 const states=[];
 for(const selected of selections){
   activeScientificSignalIds.clear();selected.forEach(id=>activeScientificSignalIds.add(id));
   captured=[];renderedEdgeLayers.length=0;
   renderRelationControls();renderEdgeLayers();
   const rendered=[];
   for(const row of captured){await row.callbacks.click();rendered.push({title:focus.title,popup:row.popup,relation:focus.detailTabs.relation});}
   states.push({selected,edges:visibleGovernedEdges(),rendered,
     points:visiblePointEntries.filter(entry=>featureMatchesScientificSelection(entry.layer,entry.feature)).map(entry=>entry.feature.record_id),
     summary:relationSummary.textContent});
 }
 console.log(JSON.stringify({states,eligibility_count:GOVERNED_EDGE_ELIGIBILITY_COUNT,unchanged:JSON.stringify(GOVERNED_EDGE_RECORDS)===sourceSnapshot}));
}
inspect();
"""
    )
    observed = cast(ObservedSelection, run_node_json(source))
    by_signal = {str(edge["signal_id"]): edge for edge in edges}
    labels = {str(signal["signal_id"]): str(signal["label"]) for signal in signals}
    assert observed["eligibility_count"] == 2 and observed["unchanged"]
    assert observed["states"][0] == observed["states"][-1]
    for state in observed["states"]:
        expected = [edge for edge in edges if edge["signal_id"] in state["selected"]]
        assert state["edges"] == expected
        assert len(state["rendered"]) == len(expected)
        assert state["summary"].startswith(
            f"{len(expected)} of 2 retained rows matched by country/signal/relation filters"
        )
        assert (
            "before endpoint time/layer/viewport display eligibility"
            in state["summary"]
        )
        assert state["points"] == (
            ["record-source", "record-target"] if expected else []
        )
        for row, edge in zip(state["rendered"], expected, strict=True):
            assert row["title"] == labels[str(edge["signal_id"])]
            assert str(edge["edge_id"]) in row["popup"]
            assert row["title"] in row["popup"]
            for field in (
                "feature_key",
                "resolution",
                "source_event_id",
                "target_event_id",
            ):
                assert row["relation"][field] == edge[field]
    group = by_signal["group:cereals"]
    taxon = by_signal["taxon:secale_cereale"]
    assert (
        group["resolution"] == "ecological_group"
        and group["feature_key"] == "group:cereals"
    )
    assert (
        taxon["resolution"] == "taxon"
        and taxon["feature_key"] == "taxon:secale_cereale"
    )
    assert group["edge_id"] != taxon["edge_id"]
    assert group["source_event_id"] != taxon["source_event_id"]
    assert group["target_event_id"] != taxon["target_event_id"]
