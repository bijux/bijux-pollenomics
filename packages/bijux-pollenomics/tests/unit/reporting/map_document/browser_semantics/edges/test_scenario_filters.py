"""Retained native relation filters are literal, shared and distinct from display admission."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from typing import Any, cast
from xml.etree import ElementTree as ET

import pytest

from bijux_pollenomics.analysis.propagation.candidates import (
    CandidatePropagationScenario,
)
from bijux_pollenomics.analysis.propagation.network import (
    PropagationCandidate,
    evaluate_propagation_pair,
)
from bijux_pollenomics.analysis.propagation.projection.geojson import candidate_geojson
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from .....analysis.propagation.network.support import event
from ....atlas.static_assets.fixtures.scientific_evidence import (
    build_scientific_point_layers,
)
from ..support import template_block
from .test_edge_focus_url import browser
from .test_scientific_edges import normalize_edges


@pytest.fixture(scope="module")
def packet(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    source = replace(
        event(
            "source",
            country_code="NO",
            feature_key="taxon:fixture",
            younger_bp=100,
            older_bp=100,
        ),
        source_record_id="source:record",
        event_id="",
    )
    target = replace(
        event("target", feature_key="taxon:fixture", younger_bp=0, older_bp=0),
        source_record_id="target:record",
        event_id="",
    )
    rows = []
    for name, distance, lag in (
        ("wide", 100, 100),
        ("short", 200, 50),
        ("all", 50, 100),
    ):
        scenario = CandidatePropagationScenario(
            scenario_id=name, maximum_distance_km=distance, maximum_lag_years=lag
        )
        candidate = evaluate_propagation_pair(source, target, scenario=scenario)
        assert isinstance(candidate, PropagationCandidate)
        geojson = candidate_geojson(
            [candidate],
            {source.event_id: source, target.event_id: target},
            directional=candidate.directional_arrow_allowed,
            scenario=scenario,
        )
        row = cast(list[dict[str, Any]], geojson["features"])[0]["properties"]
        row.update(
            source_record_id=source.source_record_id,
            target_record_id=target.source_record_id,
            signal_id="taxon:fixture",
            source_country="Norway",
            target_country="Sweden",
        )
        rows.append(row)
    rows = normalize_edges(rows)
    layers = [dict(row) for row in build_scientific_point_layers()[:1]]
    features = cast(list[dict[str, Any]], layers[0]["features"])[:2]
    for feature, identity in zip(
        features, ("source:record", "target:record"), strict=True
    ):
        feature.update(record_id=identity, scientific_signal_ids=["taxon:fixture"])
    layers[0]["features"] = features
    assets = write_static_atlas_assets(
        tmp_path_factory.mktemp("scenario-selection"),
        slug="scenario",
        version="scenario-selection",
        point_layers=layers,
        polygon_layers=[],
        edge_records=rows,
        scientific_signals=[
            {
                "signal_id": "taxon:fixture",
                "feature_key": "taxon:fixture",
                "resolution": "taxon",
                "label": "Native fixture",
                "status": "accepted",
            }
        ],
    )
    return {
        "edge": next(row for row in rows if row["scenario_id"] == "wide"),
        "manual": next(row for row in rows if row["scenario_id"] == "short"),
        "literalAll": next(row for row in rows if row["scenario_id"] == "all"),
        "features": features,
        "manifest": assets.manifest,
    }


def selected(packet: dict[str, Any], action: str) -> dict[str, Any]:
    return browser(packet, "GOVERNED_EDGE_RECORDS.push(supplied.manual);\n" + action)


def test_actual_scenarios_filter_native_status_without_reclassification(
    packet: dict[str, Any],
) -> None:
    before = deepcopy(packet)
    observed = selected(
        packet,
        r"""
const all=visibleGovernedEdges().map(row=>row.edge_id);
activeRelationFilters.scenario='short';const scenario=visibleGovernedEdges();
activeRelationFilters.status='definite_candidate';const contradictory=visibleGovernedEdges();
activeRelationFilters.status='excluded_temporal_too_large';const refused=visibleGovernedEdges();
console.log(JSON.stringify({all,scenario:scenario.map(row=>row.candidate_status),contradictory:contradictory.length,refused:refused.map(row=>row.edge_id),unchanged:original===JSON.stringify(supplied)}));
""",
    )
    assert len(observed["all"]) == 2
    assert observed["scenario"] == ["excluded_temporal_too_large"]
    assert observed["contradictory"] == 0
    assert observed["refused"] == [packet["manual"]["edge_id"]]
    assert observed["unchanged"] is True and packet == before


@pytest.mark.parametrize(
    "key,value", [("sourceCountry", "NO"), ("targetCountry", "SE")]
)
def test_stored_country_filters_use_native_codes_and_do_not_match_legacy_labels(
    packet: dict[str, Any], key: str, value: str
) -> None:
    observed = selected(
        packet,
        "const key="
        + json.dumps(key)
        + ";const value="
        + json.dumps(value)
        + r""";
const legacy={...supplied.edge,edge_id:'legacy'};delete legacy.candidate_status;delete legacy.source_country_code;delete legacy.target_country_code;
GOVERNED_EDGE_RECORDS.push(legacy);const retained=visibleGovernedEdges().length;
activeRelationFilters[key]=value;const native=visibleGovernedEdges().map(row=>row.edge_id);
activeRelationFilters[key]=key==='sourceCountry'?'Norway':'Sweden';const displayName=visibleGovernedEdges().length;
console.log(JSON.stringify({retained,native,displayName,metadata:relationFilterMetadata(GOVERNED_EDGE_RECORDS,activeRelationFilters)}));
""",
    )
    assert observed["retained"] == 3 and len(observed["native"]) == 2
    assert "legacy" not in observed["native"] and observed["displayName"] == 0
    assert observed["metadata"]["unavailable_fields"] == [key]


@pytest.mark.parametrize(
    "parameter",
    [
        "relation_scenario",
        "relation_status",
        "relation_source_country",
        "relation_target_country",
    ],
)
@pytest.mark.parametrize("defect", ["unknown", "empty", "duplicate"])
def test_invalid_shared_filter_stays_unavailable_when_reshared(
    packet: dict[str, Any], parameter: str, defect: str
) -> None:
    observed = selected(
        packet,
        "const parameter="
        + json.dumps(parameter)
        + ";const defect="
        + json.dumps(defect)
        + r""";
const values={relation_scenario:'wide',relation_status:'definite_candidate',relation_source_country:'NO',relation_target_country:'SE'};
const p=new URLSearchParams();p.set(parameter,defect==='empty'?'':defect==='unknown'?'<img src=x>':values[parameter]);
if(defect==='duplicate')p.append(parameter,values[parameter]);
Object.assign(activeRelationFilters,relationFiltersFromHash(p));syncHashState();
const restored=relationFiltersFromHash(new URLSearchParams(savedHash.slice(1)));
const first=relationFilterSelection(GOVERNED_EDGE_RECORDS,activeRelationFilters),second=relationFilterSelection(GOVERNED_EDGE_RECORDS,restored);
console.log(JSON.stringify({selected:visibleGovernedEdges().length,first:first.unavailable,second:second.unavailable,reshared:savedHash}));
""",
    )
    assert observed["selected"] == 0 and len(observed["first"]) == 1
    assert observed["first"] == observed["second"] and parameter in observed["reshared"]


def test_exact_filter_link_export_metadata_and_reset_keep_all_four_fields(
    packet: dict[str, Any],
) -> None:
    observed = selected(
        packet,
        r"""
Object.assign(activeRelationFilters,relationFiltersFromHash(new URLSearchParams('relation_scenario=short&relation_status=excluded_temporal_too_large&relation_source_country=NO&relation_target_country=SE')));
syncHashState();window.location.hash=savedHash;const parsed=parseHashState();
const metadata=relationFilterMetadata(GOVERNED_EDGE_RECORDS,activeRelationFilters);
const p=new URLSearchParams('relation_scenario=wide&relation_scenario=wide');Object.assign(activeRelationFilters,relationFiltersFromHash(p));
resetRelationFilters();const reset=structuredClone(activeRelationFilters);
console.log(JSON.stringify({parsed:parsed.relationFilters,metadata,reset,after:visibleGovernedEdges().length}));
""",
    )
    fields = {
        "scenario": "short",
        "status": "excluded_temporal_too_large",
        "sourceCountry": "NO",
        "targetCountry": "SE",
    }
    assert observed["parsed"] == {**fields, "invalid": []}
    assert observed["metadata"] == {**fields, "unavailable_fields": []}
    assert observed["reset"] == dict.fromkeys(fields) | {"invalid": []}
    assert observed["after"] == 2
    assert "resetRelationFilters();" in template_block(
        "async function restoreDefaults", "document.getElementById('countries-all')"
    )
    assert (
        "relation_filters: relationFilterMetadata(GOVERNED_EDGE_RECORDS, activeRelationFilters)"
        in template_block(
            "focusExportButton.addEventListener", "focusTabs.addEventListener"
        )
    )
    assert (
        "relation_filters: relationFilterMetadata(GOVERNED_EDGE_RECORDS, activeRelationFilters)"
        in template_block(
            "function atlasCaptureSnapshot", "function atlasCaptureOrientationKeys"
        )
    )


def test_controls_and_rule_breakdown_are_accessible_exact_and_escaped(
    packet: dict[str, Any],
) -> None:
    observed = selected(
        packet,
        r"""
const thresholds=relationScenarioThresholds(GOVERNED_EDGE_RECORDS,null);
const options=relationFilterOptions(['wide','<script>hostile</script>'],'missing',true,'scenario');
console.log(JSON.stringify({thresholds,options}));
""",
    )
    tree = ET.fromstring("<div>" + observed["thresholds"] + "</div>")
    text = " ".join(tree.itertext())
    assert "wide" in text and "maximum distance 100 km; maximum lag 100 years" in text
    assert "short" in text and "maximum distance 200 km; maximum lag 50 years" in text
    assert text.count("Rule: rectangular") == 2
    options = ET.fromstring(
        "<select>"
        + observed["options"]
        .replace(" selected", ' selected="selected"')
        .replace(" disabled", ' disabled="disabled"')
        + "</select>"
    )
    assert options.find("script") is None
    assert "Unavailable shared scenario" in " ".join(options.itertext())
    for identity in ("scenario", "status", "source-country", "target-country"):
        assert f'for="relation-{identity}-filter"' in MAP_DOCUMENT_TEMPLATE
    assert "Stored endpoints do not establish direction" in MAP_DOCUMENT_TEMPLATE
    assert "Candidate status is not scientific admission" in MAP_DOCUMENT_TEMPLATE
    assert (
        "before endpoint time/layer/viewport display eligibility"
        in MAP_DOCUMENT_TEMPLATE
    )


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "conflict",
        "wrong_scenario",
        "bool",
        "missing_rule",
        "conflicting_rule",
    ],
)
def test_scenario_metadata_is_never_inferred_from_ids_or_conflicting_rows(
    packet: dict[str, Any], defect: str
) -> None:
    observed = selected(
        packet,
        "const defect="
        + json.dumps(defect)
        + r""";
const first={...supplied.edge,relation_details:{...supplied.edge.relation_details}},second={...first,edge_id:'second',relation_details:{...first.relation_details}};
if(defect==='missing')delete second.relation_details;
if(defect==='conflict')second.relation_details.maximum_distance_km=999;
if(defect==='wrong_scenario')second.relation_details.scenario_id='other';
if(defect==='bool')second.relation_details.maximum_lag_years=true;
if(defect==='missing_rule')delete second.relation_details.rule_type;
if(defect==='conflicting_rule')second.relation_details.rule_type='other';
console.log(JSON.stringify({html:relationScenarioThresholds([first,second],first.scenario_id)}));
""",
    )
    text = " ".join(ET.fromstring("<div>" + observed["html"] + "</div>").itertext())
    if defect in {"missing_rule", "conflicting_rule"}:
        assert "Rule: unavailable" in text and "maximum distance 100 km" in text
    else:
        assert "Thresholds unavailable" in text and "maximum distance 999" not in text


def test_selected_retained_edge_does_not_bypass_missing_time_filtered_endpoint(
    packet: dict[str, Any],
) -> None:
    observed = selected(
        packet,
        r"""
activeRelationFilters.scenario='wide';const retained=visibleGovernedEdges().length;
visiblePointEntries.pop();renderEdgeLayers();const restored=await restoreEdgeFocus(request());
console.log(JSON.stringify({retained,rendered:callbacks.length,restored,focus:focusState}));
""",
    )
    assert observed == {"retained": 1, "rendered": 0, "restored": False, "focus": None}


def test_actual_control_mount_and_change_handlers_use_one_selected_set(
    packet: dict[str, Any],
) -> None:
    setup = r"""
const relationSummary={dataset:{}},countryPairFilter={},crossBorderOnlyCheckbox={};
const relationFilterStatus={innerHTML:''},handlers={};
const relationFilterControls=Object.fromEntries(relationFilterFields().map(([key])=>[key,{value:'',addEventListener(type,callback){handlers[key]=callback}}]));
const COUNTRY_PAIR_KEYS=['Norway|Sweden'],GOVERNED_EDGE_ELIGIBILITY_COUNT=GOVERNED_EDGE_RECORDS.length,GOVERNED_SEQUENCE_RECORDS=[];
STATIC_ATLAS_CHUNKS.sequences={status:'unavailable',reason_code:'fixture_no_sequence'};
"""
    observed = selected(
        packet,
        setup
        + template_block(
            "function renderRelationControls", "function selectSourceChronologyLevel"
        )
        + template_block(
            "relationFilterFields().forEach(([key]) => {",
            "countryPairFilter.addEventListener",
        )
        + r"""
renderRelationControls();const initial=relationFilterStatus.innerHTML;
activeRelationFilters.invalid=['scenario'];renderRelationControls();const unavailable=relationFilterStatus.innerHTML;
renderLoadedMapState=()=>{renderRelationControls();syncHashState()};
for(const [key,value] of Object.entries({scenario:'short',status:'excluded_temporal_too_large',sourceCountry:'NO',targetCountry:'SE'})){
 relationFilterControls[key].value=value;handlers[key]();
}
await Promise.resolve();await Promise.resolve();await Promise.resolve();
console.log(JSON.stringify({initial,unavailable,final:relationFilterStatus.innerHTML,selected:visibleGovernedEdges().map(row=>row.edge_id),summary:relationSummary.textContent,matched:relationSummary.dataset.filterMatchedCandidateCount,hash:savedHash,invalid:activeRelationFilters.invalid}));
""",
    )
    assert "2 of 2 retained relations" in observed["initial"]
    assert "Shared relation filter unavailable" in observed["unavailable"]
    assert "1 of 2 retained relations" in observed["final"]
    assert (
        "Nonselected records, including any refusal context, remain retained"
        in observed["final"]
    )
    assert observed["selected"] == [packet["manual"]["edge_id"]]
    assert observed["matched"] == "1" and observed["invalid"] == []
    assert (
        "before endpoint time/layer/viewport display eligibility" in observed["summary"]
    )
    for parameter in (
        "relation_scenario=short",
        "relation_status=excluded_temporal_too_large",
        "relation_source_country=NO",
        "relation_target_country=SE",
    ):
        assert parameter in observed["hash"]


def test_literal_all_is_one_native_scenario_and_absence_is_unrestricted(
    packet: dict[str, Any],
) -> None:
    observed = selected(
        packet,
        r"""
GOVERNED_EDGE_RECORDS.push(supplied.literalAll);const unrestricted=visibleGovernedEdges().length;
Object.assign(activeRelationFilters,relationFiltersFromHash(new URLSearchParams('relation_scenario=all')));syncHashState();
const selected=visibleGovernedEdges().map(row=>row.edge_id),options=relationFilterOptions(relationFilterSelection(GOVERNED_EDGE_RECORDS,activeRelationFilters).catalog.scenario,'all',false,'scenario');
window.location.hash=savedHash;const restored=parseHashState().relationFilters;
resetRelationFilters();syncHashState();
console.log(JSON.stringify({unrestricted,selected,options,restored,after:visibleGovernedEdges().length,resetHash:savedHash}));
""",
    )
    assert observed["unrestricted"] == observed["after"] == 3
    assert observed["selected"] == [packet["literalAll"]["edge_id"]]
    assert observed["restored"]["scenario"] == "all"
    assert '<option value="all" selected>all</option>' in observed["options"]
    assert '<option value="" >All retained</option>' in observed["options"]
    assert "relation_scenario" not in observed["resetHash"]


def test_malformed_native_country_value_is_retained_but_not_a_selectable_code(
    packet: dict[str, Any],
) -> None:
    observed = selected(
        packet,
        r"""
const bad={...supplied.edge,source_country_code:'Norway'};GOVERNED_EDGE_RECORDS=[bad];
const all=visibleGovernedEdges().length,catalog=relationFilterSelection(GOVERNED_EDGE_RECORDS,activeRelationFilters).catalog;
activeRelationFilters.sourceCountry='Norway';
console.log(JSON.stringify({all,catalog,selected:visibleGovernedEdges().length,unavailable:relationFilterMetadata(GOVERNED_EDGE_RECORDS,activeRelationFilters).unavailable_fields}));
""",
    )
    assert observed["all"] == 1 and observed["selected"] == 0
    assert observed["catalog"]["sourceCountry"] == []
    assert observed["unavailable"] == ["sourceCountry"]
