"""Actual relation controls select source definitions without changing retained evidence."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

import pytest

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from ..support import template_block
from .inspection.focus_support import browser
from .test_event_definition_filters import DEFAULT, edge
from .test_scenario_filters import packet as packet

CONTROLS = r"""
GOVERNED_EDGE_RECORDS.push(supplied.manual);
STATIC_ATLAS_CHUNKS.sequences={status:'unavailable',reason_code:'not_supplied'};
const GOVERNED_SEQUENCE_RECORDS=[],GOVERNED_EDGE_ELIGIBILITY_COUNT=GOVERNED_EDGE_RECORDS.length;
const COUNTRY_PAIR_KEYS=['Norway|Sweden'];
const countryPairFilter={},crossBorderOnlyCheckbox={},relationSummary={dataset:{}},relationFilterStatus={};
const relationFilterControls={scenario:{},status:{},sourceCountry:{},targetCountry:{}};
let eventChanged;
const relationEventDefinitionControl={value:'',addEventListener(type,callback){eventChanged=callback}};
const relationEventDefinitionStatus={};
function snapshot(){
 renderRelationControls();
 return {options:relationEventDefinitionControl.innerHTML,status:relationEventDefinitionStatus.textContent,
 summary:relationFilterStatus.innerHTML,counts:relationSummary.dataset,
 selected:visibleGovernedEdges().map(row=>row.edge_id),metadata:relationEventDefinitionMetadata(GOVERNED_EDGE_RECORDS,activeRelationEventDefinition),
 filters:relationFilterMetadata(GOVERNED_EDGE_RECORDS,activeRelationFilters)};
}
"""


def ui(packet: dict[str, Any], action: str) -> dict[str, Any]:
    return browser(
        packet,
        CONTROLS
        + template_block(
            "function renderRelationControls", "function selectSourceChronologyLevel"
        )
        + template_block(
            "relationEventDefinitionControl.addEventListener",
            "countryPairFilter.addEventListener",
        )
        + action,
    )


def test_mounted_real_control_keeps_global_catalog_and_all_filter_counts(
    packet: dict[str, Any],
) -> None:
    before = deepcopy(packet)
    observed = ui(
        packet,
        r"""
const before=snapshot();
activeRelationFilters.scenario=supplied.edge.scenario_id;
activeRelationFilters.status=supplied.edge.candidate_status;
activeRelationFilters.sourceCountry=supplied.edge.source_country_code;
activeRelationFilters.targetCountry=supplied.edge.target_country_code;
const tuple=Object.values(supplied.edge.relation_details.event_definition);
relationEventDefinitionControl.value=JSON.stringify(tuple);eventChanged();
await new Promise(resolve=>setImmediate(resolve));
const after=snapshot();
console.log(JSON.stringify({before,after,hash:savedHash,unchanged:original===JSON.stringify(supplied)}));
""",
    )
    assert len(observed["before"]["selected"]) == 2
    assert observed["after"]["selected"] == [packet["edge"]["edge_id"]]
    assert observed["after"]["counts"]["filterMatchedCandidateCount"] == "1"
    assert "1 of 2 retained relations" in observed["after"]["summary"]
    assert observed["after"]["filters"]["scenario"] == packet["edge"]["scenario_id"]
    assert "2 rows with supplied definitions" in observed["after"]["status"]
    assert "Rule: rectangular" in observed["after"]["summary"]
    assert (
        "maximum distance 100 km; maximum lag 100 years" in observed["after"]["summary"]
    )
    assert "relation_event_definition=" in observed["hash"]
    assert "relation_scenario=wide" in observed["hash"]
    assert observed["unchanged"] is True and packet == before


def test_global_event_conflict_cannot_disappear_under_other_filters(
    packet: dict[str, Any],
) -> None:
    observed = ui(
        packet,
        r"""
const conflict=structuredClone(supplied.edge);conflict.edge_id+='-conflict';
conflict.scenario_id=conflict.relation_details.scenario_id='other';
conflict.relation_details.event_definition.measurement_semantics_id='different';
GOVERNED_EDGE_RECORDS.push(conflict);
activeRelationFilters.scenario=supplied.edge.scenario_id;
const retained=snapshot();
activeRelationEventDefinition.value=JSON.stringify(Object.values(supplied.edge.relation_details.event_definition));
const specific=snapshot();
console.log(JSON.stringify({retained,specific,unchanged:original===JSON.stringify(supplied)}));
""",
    )
    assert observed["retained"]["selected"] == [packet["edge"]["edge_id"]]
    assert observed["specific"]["selected"] == []
    assert "conflicting of 3 retained rows" in observed["specific"]["status"]
    assert observed["specific"]["metadata"]["unavailable"] is True
    assert "no fallback" in observed["specific"]["status"]
    assert observed["unchanged"] is True


@pytest.mark.parametrize("defect", ["missing", "legacy", "conflicting"])
def test_all_retained_preserves_unavailable_rows_and_specific_excludes_them(
    packet: dict[str, Any], defect: str
) -> None:
    observed = ui(
        packet,
        "const defect="
        + json.dumps(defect)
        + r""";
const extra=structuredClone(supplied.edge);extra.edge_id+='-'+defect;
if(defect==='missing')delete extra.relation_details.event_definition;
if(defect==='legacy')delete extra.candidate_status;
if(defect==='conflicting')extra.threshold_profile_id='wrong';
GOVERNED_EDGE_RECORDS.push(extra);const retained=snapshot();
activeRelationEventDefinition.value=JSON.stringify(Object.values(supplied.edge.relation_details.event_definition));
const specific=snapshot();
console.log(JSON.stringify({retained,specific,unchanged:original===JSON.stringify(supplied)}));
""",
    )
    assert len(observed["retained"]["selected"]) == 3
    assert len(observed["specific"]["selected"]) == 2
    assert observed["specific"]["metadata"]["unavailable"] is False
    assert observed["unchanged"] is True


@pytest.mark.parametrize("selection", ["unknown", "malformed", "duplicate"])
def test_shared_selection_is_restored_literally_and_never_defaults_to_all(
    packet: dict[str, Any], selection: str
) -> None:
    value = json.dumps((DEFAULT[0], "unknown", *DEFAULT[2:]))
    if selection == "malformed":
        value = "<script>unsafe()</script>"
    query = urlencode({"relation_event_definition": value})
    if selection == "duplicate":
        query += "&" + query
    observed = ui(
        packet,
        "window.location.hash="
        + json.dumps("#" + query)
        + ";const initialState=parseHashState();"
        + template_block(
            "Object.assign(activeRelationFilters, initialState.relationFilters)",
            "if (NATIVE_LRA_BINDING",
        )
        + r"""
const refused=snapshot();syncHashState();window.location.hash=savedHash;
const parsed=parseHashState();resetRelationEventDefinition();const reset=snapshot();syncHashState();
console.log(JSON.stringify({refused,parsed:parsed.relationEventDefinition,reset,hash:savedHash,unchanged:original===JSON.stringify(supplied)}));
""",
    )
    assert observed["refused"]["selected"] == []
    assert "Unavailable shared event definition" in observed["refused"]["options"]
    assert observed["parsed"]["value"] == value
    assert observed["parsed"]["duplicate"] is (selection == "duplicate")
    assert len(observed["reset"]["selected"]) == 2
    assert "relation_event_definition" not in observed["hash"]
    assert observed["unchanged"] is True


def test_literal_profile_all_and_escaped_source_metadata_remain_exact_choices(
    packet: dict[str, Any],
) -> None:
    alternative = edge(
        "alternative", (DEFAULT[0], "all", '<source "value">', DEFAULT[3])
    )
    observed = ui(
        packet,
        "const alternative="
        + json.dumps(alternative)
        + r""";
GOVERNED_EDGE_RECORDS.push(alternative);activeCountries.add(alternative.source_country);
activeScientificSignalIds.add(alternative.signal_id);crossBorderOnly=false;
activeRelationEventDefinition.value=JSON.stringify(Object.values(alternative.relation_details.event_definition));
const selected=snapshot();console.log(JSON.stringify({selected,unchanged:original===JSON.stringify(supplied)}));
""",
    )
    assert observed["selected"]["selected"] == [alternative["edge_id"]]
    options = observed["selected"]["options"].replace(
        " selected", ' selected="selected"'
    )
    tree = ET.fromstring("<select>" + options + "</select>")
    assert tree.find("source") is None
    assert '<source "value">' in " ".join(tree.itertext())
    assert observed["unchanged"] is True


def test_capture_export_and_reset_use_same_actual_event_state() -> None:
    for start, end in (
        ("function atlasCaptureSnapshot", "function atlasCaptureOrientationKeys"),
        ("focusExportButton.addEventListener", "focusTabs.addEventListener"),
    ):
        assert (
            "relation_event_definition: relationEventDefinitionMetadata(GOVERNED_EDGE_RECORDS, activeRelationEventDefinition)"
            in template_block(start, end)
        )
    assert "resetRelationEventDefinition();" in template_block(
        "async function restoreDefaults", "document.getElementById('countries-all')"
    )
    assert 'for="relation-event-definition-filter"' in MAP_DOCUMENT_TEMPLATE
    assert (
        'aria-describedby="relation-event-definition-status"' in MAP_DOCUMENT_TEMPLATE
    )
    assert "__RELATION_EVENT_DEFINITION_CONTROLLER__" not in MAP_DOCUMENT_TEMPLATE
