"""Simultaneous reviewed feature filters retain separate labels and identities."""

from __future__ import annotations

import json

import pytest

from bijux_pollenomics.reporting.map_document.evidence import normalize_atlas_evidence

from ..support import run_node_json, template_block
from .test_scientific_picker import SCRIPT
from .test_scientific_picker_mounting import MOUNT


@pytest.mark.parametrize("_fixture_id", ["MAP-001"])
def test_forest_cereal_and_pastoral_filters_keep_separate_controls_and_records(
    _fixture_id: str,
) -> None:
    selection = template_block(
        "function featureMatchesScientificSelection", "function pointFeatureVisible"
    )
    renderer = template_block(
        "function renderScientificControls", "function visibleGovernedEdges"
    )
    observed = run_node_json(
        SCRIPT
        + MOUNT
        + """
const SCIENTIFIC_SIGNALS=[
  {signal_id:'group:forest',status:'accepted',feature_key:'group:forest',resolution:'group',label:'Forest',color:'#14532d',non_color_cue:'triangle'},
  {signal_id:'group:cereals',status:'accepted',feature_key:'group:cereals',resolution:'group',label:'Cereals',color:'#92400e',non_color_cue:'square'},
  {signal_id:'role:pastoral',status:'accepted',feature_key:'role:pastoral',resolution:'role',label:'Pastoral indicators',color:'#1e40af',non_color_cue:'diamond'},
];
const SCIENTIFIC_RESOLUTION_ORDER=['whole','group','subgroup','role','taxon'];
const activeScientificSignalIds=new Set(SCIENTIFIC_SIGNALS.map(row=>row.signal_id));
const ATLAS_EVIDENCE={classifications_status:'available'};
const scientificActions={},sourceChronologyShortcuts={querySelectorAll(){return []}};
const scientificStatus={},scientificFilters={addEventListener(){}},scientificSummary={};
const document={getElementById(){return {open:true}},querySelectorAll(){return []}};
let scientificPinValues=[],scientificPinnedIds=null,scientificCatalog=null,scientificPickerController=null,scientificPickerStatus='not_loaded';
const evidenceToolsError=null;
function currentEvidenceTools(){return {pickerCatalog:scientificPickerCatalog,pickerInitial:scientificPickerInitialState,pickerHtml:renderScientificPicker,pickerMount:mountScientificPicker}}
function sourceChronologyLayers(){return []}
function escapeHtml(value){return String(value)}
function scientificCueGlyph(cue){return cue}
const features=[
  {record_id:'forest-only',scientific_signal_ids:['group:forest']},
  {record_id:'cereal-only',scientific_signal_ids:['group:cereals']},
  {record_id:'pastoral-only',scientific_signal_ids:['role:pastoral']},
  {record_id:'shared',scientific_signal_ids:['group:forest','role:pastoral']},
];
const layer={scientific_selection_enabled:true};
"""
        + selection
        + renderer
        + """
renderScientificControls();
const allVisible=features.filter(row=>featureMatchesScientificSelection(layer,row)).map(row=>row.record_id);
const controls=SCIENTIFIC_SIGNALS.map(signal=>({
  id:signal.signal_id,
  checked:scientificPinnedIds.includes(signal.signal_id),
  labelled:scientificFilters.innerHTML.includes(`${signal.label} · ${signal.resolution} · ${signal.signal_id}`),
  colored:scientificFilters.innerHTML.includes(`style="color:${signal.color}"`),
  cue:scientificFilters.innerHTML.includes(`data-cue="${signal.non_color_cue}"`),
}));
const separatelyFiltered={};
for(const signal of SCIENTIFIC_SIGNALS){
  activeScientificSignalIds.clear();activeScientificSignalIds.add(signal.signal_id);
  separatelyFiltered[signal.signal_id]=features.filter(row=>featureMatchesScientificSelection(layer,row)).map(row=>row.record_id);
}
console.log(JSON.stringify({allVisible,controls,separatelyFiltered,summary:scientificSummary.textContent}));
"""
    )
    assert observed["allVisible"] == [
        "forest-only",
        "cereal-only",
        "pastoral-only",
        "shared",
    ]
    assert observed["summary"] == "3 of 3 accepted signals selected"
    assert observed["controls"] == [
        {
            "id": identifier,
            "checked": True,
            "labelled": True,
            "colored": True,
            "cue": True,
        }
        for identifier in ("group:forest", "group:cereals", "role:pastoral")
    ]
    assert observed["separatelyFiltered"] == {
        "group:forest": ["forest-only", "shared"],
        "group:cereals": ["cereal-only"],
        "role:pastoral": ["pastoral-only", "shared"],
    }


@pytest.mark.parametrize("_fixture_id", ["MAP-003"])
def test_reviewed_pinus_and_secale_keep_stable_distinct_colors_and_labels(
    _fixture_id: str,
) -> None:
    signals = [
        {
            "signal_id": "taxon:pinus-sylvestris",
            "feature_key": "taxon:pinus-sylvestris",
            "resolution": "taxon",
            "label": "Pinus sylvestris",
            "status": "accepted",
        },
        {
            "signal_id": "taxon:secale-cereale",
            "feature_key": "taxon:secale-cereale",
            "resolution": "taxon",
            "label": "Secale cereale",
            "status": "accepted",
        },
    ]
    normalized = normalize_atlas_evidence(
        detail_records=[],
        scientific_signals=signals,
        edge_records=[],
        sequence_records=[],
    ).scientific_signals
    reverse = normalize_atlas_evidence(
        detail_records=[],
        scientific_signals=list(reversed(signals)),
        edge_records=[],
        sequence_records=[],
    ).scientific_signals
    assert normalized == reverse
    assert len({row["color"] for row in normalized}) == 2
    assert all(row["non_color_cue"] for row in normalized)
    renderer = template_block(
        "function renderScientificControls", "function visibleGovernedEdges"
    )
    observed = run_node_json(
        SCRIPT
        + MOUNT
        + "const SCIENTIFIC_SIGNALS="
        + json.dumps(normalized)
        + ";\n"
        + """
const SCIENTIFIC_RESOLUTION_ORDER=['whole','group','subgroup','role','taxon'];
const activeScientificSignalIds=new Set(SCIENTIFIC_SIGNALS.map(row=>row.signal_id));
const ATLAS_EVIDENCE={classifications_status:'available'};
const scientificActions={},sourceChronologyShortcuts={querySelectorAll(){return []}};
const scientificStatus={},scientificFilters={addEventListener(){}},scientificSummary={};
const document={getElementById(){return {open:true}},querySelectorAll(){return []}};
let scientificPinValues=[],scientificPinnedIds=null,scientificCatalog=null,scientificPickerController=null,scientificPickerStatus='not_loaded';
const evidenceToolsError=null;
function currentEvidenceTools(){return {pickerCatalog:scientificPickerCatalog,pickerInitial:scientificPickerInitialState,pickerHtml:renderScientificPicker,pickerMount:mountScientificPicker}}
function sourceChronologyLayers(){return []}
function escapeHtml(value){return String(value)}
function scientificCueGlyph(cue){return cue}
"""
        + renderer
        + """
renderScientificControls();
console.log(JSON.stringify(SCIENTIFIC_SIGNALS.map(signal=>({
  id:signal.signal_id,labelled:scientificFilters.innerHTML.includes(`${signal.label} · ${signal.resolution} · ${signal.signal_id}`),
  colored:scientificFilters.innerHTML.includes(`style="color:${signal.color}"`),
  cue:scientificFilters.innerHTML.includes(`data-cue="${signal.non_color_cue}"`),
}))));
"""
    )
    assert observed == [
        {"id": row["signal_id"], "labelled": True, "colored": True, "cue": True}
        for row in normalized
    ]
