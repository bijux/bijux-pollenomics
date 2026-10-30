"""Scientific candidate direction and truthful edge detail presentation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict, cast

from jsonschema import Draft202012Validator
import pytest

from bijux_pollenomics.analysis.propagation.network import (
    PropagationCandidate,
    evaluate_propagation_pair,
)
from bijux_pollenomics.core.geospatial.geojson import JsonObject
from bijux_pollenomics.reporting.map_document.evidence import normalize_atlas_evidence

from .....analysis.propagation.network.support import event
from ..support import run_node_json, template_block


class EdgeFocus(TypedDict):
    subtitle: str
    detailTabs: dict[str, dict[str, object]]


class RenderedEdge(TypedDict):
    options: dict[str, object]
    popup: str
    focus: EdgeFocus


class RenderResult(TypedDict):
    rows: list[RenderedEdge]
    loaded: dict[str, dict[str, object]]


def edge_row(status: str, *, native: bool) -> dict[str, object]:
    row: dict[str, object] = {
        "edge_id": "edge:" + status,
        "signal_id": "taxon:fixture",
        "source_record_id": "source:record",
        "target_record_id": "target:record",
        "source_country": "Norway",
        "target_country": "Sweden",
    }
    if native:
        row.update(
            candidate_status=status,
            directional_arrow_allowed=status
            in ("definite_candidate", "possible_candidate"),
            route_interpretation_allowed=False,
            map_geometry_role="endpoint_connection_only",
        )
    else:
        row["status"] = status
    return row


def normalize_edges(rows: list[JsonObject]) -> list[JsonObject]:
    admitted = normalize_atlas_evidence(
        detail_records=[],
        scientific_signals=[
            {
                "signal_id": "taxon:fixture",
                "feature_key": "taxon:fixture",
                "label": "Synthetic reviewed taxon",
                "resolution": "taxon",
                "status": "accepted",
            }
        ],
        edge_records=rows,
        sequence_records=[],
    )
    return list(admitted.edge_records)


def render_edges(
    rows: list[JsonObject],
    *,
    missing_details: bool = False,
    partial_provenance: bool = False,
) -> RenderResult:
    source = (
        "const edges="
        + json.dumps(normalize_edges(rows))
        + ";\nconst missingDetails="
        + json.dumps(missing_details)
        + ";\nconst partialProvenance="
        + json.dumps(partial_provenance)
        + ";\n"
        + """
const SCIENTIFIC_SIGNALS=[{signal_id:'taxon:fixture',label:'Synthetic reviewed taxon',color:'#123456',non_color_cue:'circle'}];
const STATIC_ATLAS_INLINE=false,STATIC_ATLAS_CHUNKS={edges:{status:'available'}};
let activeEvidenceDisplay=resetEvidenceDisplay();
const visiblePointEntries=[
  {feature:{record_id:'source:record',latitude:60,longitude:18},layer:{key:'points'}},
  {feature:{record_id:'target:record',latitude:61,longitude:19},layer:{key:'points'}},
];
function featureCoordinatePair(row){return row}
function visibleGovernedEdges(){return edges}
function escapeHtml(value){return String(value)}
function scientificCueGlyph(cue){return cue}
const captured=[],renderedEdgeLayers=[],map={};let focus=null;
const L={polyline(coordinates,options){
  const row={coordinates,options,callbacks:{},popup:''};captured.push(row);
  return {bindPopup(html){row.popup=html},on(event,callback){row.callbacks[event]=callback},addTo(){}};
}};
const loaded={overview:{loaded_event:'loaded:event'},relation:{loaded_interval:[0,100]},chronology:{source:{age_bp:0},target:{age_interval_bp:[100,200]}},provenance:{citation:'Original source citation'},samples:{source_rows:['sample:1']}};
if (partialProvenance) loaded.provenance={status:'unavailable',reason_code:'target_source_evidence_not_available',citation:'Original source citation',source_record_id:'source:record',source_provenance:{citation:'Source only'}};
async function detailTabsForRecordId(){return missingDetails ? {overview:{status:'unavailable',reason_code:'detail_record_not_indexed'}} : loaded}
function unavailableDetailTabs(){return Object.fromEntries(['overview','relation','chronology','provenance'].map(key=>[key,{status:'unavailable',reason_code:key+'_evidence_not_available'}]))}
function setFocusState(state){focus=state}
"""
        + template_block(
            "function scientificSignalById", "function renderPolygonLayers"
        )
        + """
renderEdgeLayers();
async function inspect(){
  const rows=[];
  for(const row of captured){
    await row.callbacks.click();
    rows.push({options:row.options,popup:row.popup,focus});
  }
  console.log(JSON.stringify({rows,loaded}));
}
inspect();
"""
    )
    return cast(RenderResult, run_node_json(source))


@pytest.mark.parametrize("native", [False, True], ids=["legacy", "native"])
@pytest.mark.parametrize(
    ("status", "dash", "separator"),
    [
        ("definite_candidate", None, " → "),
        ("possible_candidate", "10 7", " → "),
        ("indeterminate_order", "2 7", " — "),
    ],
    ids=["MAP-004-definite", "MAP-004-possible", "MAP-004-indeterminate"],
)
def test_candidate_styles_distinguish_uncertainty_without_color(
    native: bool, status: str, dash: str | None, separator: str
) -> None:
    result = render_edges([edge_row(status, native=native)])
    row = result["rows"][0]
    assert row["options"]["color"] == "#123456"
    assert row["options"]["dashArray"] == dash
    assert separator in row["popup"]
    assert separator in row["focus"]["subtitle"]
    assert row["focus"]["detailTabs"]["relation"]["status"] == status
    if status == "indeterminate_order":
        assert " → " not in row["popup"]
        assert " → " not in row["focus"]["subtitle"]
        assert "Indeterminate order (no direction)" in row["popup"]
        assert "has no direction" in row["popup"]


@pytest.mark.parametrize(
    ("key", "value", "reason"),
    [
        ("directional_arrow_allowed", True, "directional arrow"),
        ("directional_arrow_allowed", 0, "directional arrow"),
        ("route_interpretation_allowed", True, "route interpretation"),
        ("map_geometry_role", "migration_route", "geometry role"),
        ("status", "definite_candidate", "statuses conflict"),
        ("candidate_status", "unknown", "candidate status"),
    ],
)
def test_native_candidate_contract_conflicts_are_refused(
    key: str, value: object, reason: str
) -> None:
    row = edge_row("indeterminate_order", native=True)
    row[key] = value
    with pytest.raises(ValueError, match=reason):
        normalize_edges([row])


@pytest.mark.parametrize(
    "status",
    [
        "unresolved",
        "excluded_spatial",
        "excluded_temporal_nonpositive",
        "excluded_temporal_too_large",
    ],
)
def test_non_candidate_status_never_acquires_direction(status: str) -> None:
    row = edge_row(status, native=True)
    result = render_edges([row])["rows"][0]
    assert " → " not in result["popup"]
    assert " → " not in result["focus"]["subtitle"]
    assert "No candidate succession is admitted for " + status in result["popup"]
    assert "Candidate succession under the governed rule" not in result["popup"]
    assert "Endpoint connection" in result["popup"]
    assert "candidate relation" not in result["focus"]["subtitle"]
    assert (
        result["focus"]["detailTabs"]["relation"]["directional_arrow_allowed"] is False
    )


@pytest.mark.parametrize("_fixture_id", ["MAP-006"])
def test_edge_detail_retains_loaded_evidence_and_all_provided_scientific_fields(
    _fixture_id: str,
) -> None:
    row = edge_row("possible_candidate", native=True)
    row.update(
        source_event_id="source:event",
        target_event_id="target:event",
        source_site_id="source:site",
        target_site_id="target:site",
        feature_key="taxon:fixture",
        resolution="taxon",
        source_age_bp=0,
        target_age_bp=None,
        source_age_interval_bp=[0, 100],
        target_age_interval_bp=[200, 300],
        distance_km_unrounded=10.123456,
        distance_km_display=10.123,
        minimum_lag_years=-100,
        maximum_lag_years=200,
        reason_code="positive_lag_possible",
        scenario_id="scenario:fixture",
        threshold_profile_id="threshold:fixture",
        temporal_contract_version="temporal:fixture",
        classification_contract_version="classification:fixture",
        propagation_contract_version="propagation:fixture",
        schema_version="1.0.0",
        build_id="build:fixture",
        source_provenance={"source_id": "source:dataset", "citation": "Source A"},
        target_provenance={"source_id": "target:dataset", "citation": "Source B"},
        event_manifest_digest="events:digest",
        config_digest="config:digest",
        producer_version="producer:fixture",
    )
    result = render_edges([row])
    tabs = result["rows"][0]["focus"]["detailTabs"]
    relation = tabs["relation"]
    for key in (
        "source_event_id",
        "target_event_id",
        "source_site_id",
        "target_site_id",
        "feature_key",
        "resolution",
        "source_age_bp",
        "target_age_bp",
        "source_age_interval_bp",
        "target_age_interval_bp",
        "distance_km_unrounded",
        "distance_km_display",
        "minimum_lag_years",
        "maximum_lag_years",
        "candidate_status",
        "reason_code",
        "scenario_id",
        "threshold_profile_id",
        "temporal_contract_version",
        "classification_contract_version",
        "propagation_contract_version",
        "schema_version",
        "build_id",
    ):
        assert relation[key] == row[key]
    for key in (
        "source_provenance",
        "target_provenance",
        "event_manifest_digest",
        "config_digest",
        "producer_version",
        "build_id",
    ):
        assert tabs["provenance"][key] == row[key]
    assert tabs["overview"]["loaded_event"] == "loaded:event"
    assert relation["loaded_interval"] == [0, 100]
    assert tabs["chronology"] == result["loaded"]["chronology"]
    assert tabs["samples"] == result["loaded"]["samples"]
    assert tabs["provenance"]["citation"] == "Original source citation"
    assert result["loaded"]["relation"] == {"loaded_interval": [0, 100]}


def test_missing_edge_details_remain_missing_without_inferred_event_ids() -> None:
    result = render_edges([edge_row("definite_candidate", native=False)])
    tabs = result["rows"][0]["focus"]["detailTabs"]
    for key in (
        "source_event_id",
        "target_event_id",
        "minimum_lag_years",
        "maximum_lag_years",
        "scenario_id",
        "source_age_bp",
        "target_age_bp",
        "build_id",
    ):
        assert key not in tabs["relation"]
    assert "source_provenance" not in tabs["provenance"]
    assert tabs["chronology"] == result["loaded"]["chronology"]


@pytest.mark.parametrize(
    "status",
    [
        "definite_candidate",
        "possible_candidate",
        "indeterminate_order",
        "unresolved",
        "excluded_spatial",
        "excluded_temporal_nonpositive",
        "excluded_temporal_too_large",
    ],
)
def test_native_arrow_flag_cannot_be_missing_or_inverted(status: str) -> None:
    row = edge_row(status, native=True)
    row["directional_arrow_allowed"] = not row["directional_arrow_allowed"]
    with pytest.raises(ValueError, match="directional arrow"):
        normalize_edges([row])
    del row["directional_arrow_allowed"]
    with pytest.raises(ValueError, match="directional arrow"):
        normalize_edges([row])


def test_missing_record_endpoint_cannot_be_inferred_from_canonical_event_id() -> None:
    row = edge_row("definite_candidate", native=True)
    row["source_event_id"] = "source:event"
    del row["source_record_id"]
    with pytest.raises(ValueError, match="source_record_id is missing"):
        normalize_edges([row])


def test_provided_edge_evidence_marks_partial_tabs_without_claiming_completeness() -> (
    None
):
    row = edge_row("definite_candidate", native=True)
    row["source_provenance"] = {"citation": "Provided citation"}
    result = render_edges([row], missing_details=True)
    tabs = result["rows"][0]["focus"]["detailTabs"]
    assert tabs["overview"]["edge_id"] == row["edge_id"]
    assert tabs["overview"]["status"] == "partial"
    assert tabs["overview"]["evidence_availability"] == "partial"
    assert (
        tabs["overview"]["availability_reason_code"]
        == "overview_evidence_not_available"
    )
    assert tabs["provenance"]["source_provenance"] == row["source_provenance"]
    assert tabs["provenance"]["status"] == "partial"
    assert (
        tabs["provenance"]["availability_reason_code"]
        == "provenance_evidence_not_available"
    )
    assert tabs["chronology"]["status"] == "unavailable"
    assert tabs["relation"]["status"] == "definite_candidate"
    absent = render_edges(
        [edge_row("definite_candidate", native=False)], missing_details=True
    )
    assert (
        absent["rows"][0]["focus"]["detailTabs"]["provenance"]["status"]
        == "unavailable"
    )


def test_actual_native_candidate_fields_survive_the_explicit_atlas_bridge() -> None:
    source = event("source", feature_key="taxon:fixture")
    target = event(
        "target", feature_key="taxon:fixture", younger_bp=5500, older_bp=5500
    )
    candidate = evaluate_propagation_pair(source, target)
    assert isinstance(candidate, PropagationCandidate)
    canonical = dict(candidate.as_dict())
    schema = json.loads(
        Path(
            "configs/scientific-contracts/propagation-candidate.schema.json"
        ).read_text()
    )
    Draft202012Validator(schema).validate(canonical)
    row = {
        **canonical,
        "signal_id": "taxon:fixture",
        "source_record_id": source.source_record_id,
        "target_record_id": target.source_record_id,
        "source_country": "Sweden",
        "target_country": "Sweden",
    }
    normalized = normalize_edges([row])[0]
    for key, value in canonical.items():
        assert normalized[key] == value
    assert normalized["status"] == canonical["candidate_status"]
    assert normalized["source_record_id"] != normalized["source_event_id"]
    assert normalized["target_record_id"] != normalized["target_event_id"]


@pytest.mark.parametrize(
    ("key", "value", "reason"),
    [
        ("route_interpretation_allowed", True, "route interpretation"),
        ("map_geometry_role", "migration_route", "geometry role"),
    ],
)
@pytest.mark.parametrize(
    "status", ["definite_candidate", "possible_candidate", "indeterminate_order"]
)
def test_explicit_legacy_route_semantics_are_refused(
    key: str, value: object, reason: str, status: str
) -> None:
    row = edge_row(status, native=False)
    row[key] = value
    with pytest.raises(ValueError, match=reason):
        normalize_edges([row])
    row[key] = (
        False if key == "route_interpretation_allowed" else "endpoint_connection_only"
    )
    assert normalize_edges([row])[0][key] == row[key]


def test_partial_loaded_provenance_survives_a_supplied_config_digest() -> None:
    row = edge_row("indeterminate_order", native=False)
    row["config_digest"] = "config:provided"
    result = render_edges([row], partial_provenance=True)
    provenance = result["rows"][0]["focus"]["detailTabs"]["provenance"]
    original = result["loaded"]["provenance"]
    for key in ("citation", "source_record_id", "source_provenance", "reason_code"):
        assert provenance[key] == original[key]
    assert provenance["config_digest"] == "config:provided"
    assert provenance["status"] == "partial"
    assert provenance["evidence_availability"] == "partial"
    assert (
        provenance["availability_reason_code"] == "target_source_evidence_not_available"
    )
    assert "target_provenance" not in provenance
    assert original["status"] == "unavailable"
    assert "config_digest" not in original
