"""Relation explanations preserve canonical endpoints and evaluator postures."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from typing import Any, cast
from xml.etree import ElementTree as ET

import pytest

from bijux_pollenomics.analysis.propagation.network import (
    evaluate_propagation_pair,
    generate_propagation_network,
)
from bijux_pollenomics.analysis.propagation.projection import (
    project_propagation_network,
)

from ......analysis.propagation.network.support import event
from ...support import run_node_json, template_block
from ..test_scientific_edges import normalize_edges, render_edges


def relation() -> dict[str, Any]:
    source = replace(event("source"), source_record_id="source:record", event_id="")
    target = replace(
        event("target", younger_bp=0, older_bp=0),
        source_record_id="target:record",
        event_id="",
    )
    candidate = evaluate_propagation_pair(source, target)
    row = dict(candidate.as_dict())
    row.update(
        source_record_id=source.source_record_id,
        target_record_id=target.source_record_id,
        source_country="Sweden",
        target_country="Sweden",
        signal_id="taxon:fixture",
        source_event=source.as_dict(),
        target_event=target.as_dict(),
        relation_details={
            "basis": "derived_governed_evaluator_branch_explanation",
            "scenario_id": candidate.scenario_id,
            "maximum_distance_km": 100,
            "maximum_lag_years": 100,
            "predicates": [
                {
                    "predicate_id": name,
                    "label": name.replace("_", " "),
                    "status": status,
                    "observed": value,
                    "threshold": threshold,
                }
                for name, status, value, threshold in [
                    ("spatial_threshold", "pass", 0, 100),
                    ("chronology_available", "pass", None, None),
                    ("positive_lag_possible", "pass", 5600, 0),
                    ("positive_lag_certain", "pass", 5600, 0),
                    ("lag_within_limit_possible", "refuse", 5600, 100),
                    ("lag_within_limit_certain", "not_evaluated", None, 100),
                ]
            ],
        },
    )
    return row


def render(tab: dict[str, Any]) -> tuple[ET.Element, dict[str, Any]]:
    source = (
        template_block("function escapeHtml", "function normalizedMediaLinks")
        + template_block("function renderRelationDetails", "function renderEdgeLayers")
        + "\nconst tab="
        + json.dumps(tab)
        + ";const original=JSON.stringify(tab);"
        + "console.log(JSON.stringify({html:renderRelationDetails(tab),unchanged:original===JSON.stringify(tab)}));"
    )
    observed = cast(dict[str, Any], run_node_json(source))
    assert observed["unchanged"] is True
    return ET.fromstring(observed["html"]), observed


def test_canonical_endpoints_and_all_supplied_statuses_are_accessible() -> None:
    tab = relation()
    tab["target_age_bp"] = 999  # Presentation-node ages cannot replace event ages.
    original = deepcopy(tab)
    document, _ = render(tab)
    tables = document.findall(".//table")
    assert [table.findtext("caption") for table in tables] == [
        "Canonical relation endpoints",
        "Scenario predicates",
    ]
    assert [th.text for th in tables[0].findall("thead/tr/th")] == [
        "Field",
        "Source endpoint",
        "Target endpoint",
    ]
    rows = {
        row.findtext("th"): [td.text for td in row.findall("td")]
        for row in tables[0].findall("tbody/tr")
    }
    assert rows["Event ID"] == [tab["source_event_id"], tab["target_event_id"]]
    assert rows["Younger BP"] == ["5600", "0"]
    assert rows["Older BP"] == ["5600", "0"]
    assert all(
        th.get("scope") == "col"
        for table in tables
        for th in table.findall("thead/tr/th")
    )
    assert all(
        th.get("scope") == "row"
        for table in tables
        for th in table.findall("tbody/tr/th")
    )
    assert [row.findall("td")[0].text for row in tables[1].findall("tbody/tr")] == [
        "pass",
        "pass",
        "pass",
        "pass",
        "refuse",
        "not_evaluated",
    ]
    text = " ".join(document.itertext())
    assert (
        "Derived governed evaluator branch explanation, not recorded execution telemetry"
        in text
    )
    assert "Neither means pass" in text
    assert "not reconstructed movement paths" in text
    assert "do not confer scientific admission" in text
    assert tab == original


@pytest.mark.parametrize(
    "change",
    [
        "absent",
        "scenario",
        "basis",
        "row_missing",
        "row_duplicate",
        "status",
        "bool_observed",
        "nonfinite_limit",
        "event",
        "record",
        "site",
    ],
)
def test_missing_stale_or_malformed_transport_cannot_invent_passes(change: str) -> None:
    tab = relation()
    details = tab["relation_details"]
    if change == "absent":
        del tab["relation_details"]
    elif change in {"scenario", "basis"}:
        details["scenario_id" if change == "scenario" else "basis"] = "other"
    elif change == "row_missing":
        details["predicates"].pop()
    elif change == "row_duplicate":
        details["predicates"][1] = details["predicates"][0]
    elif change == "status":
        details["predicates"][0]["status"] = "accepted"
    elif change == "bool_observed":
        details["predicates"][0]["observed"] = True
    elif change == "nonfinite_limit":
        details["maximum_distance_km"] = None
    else:
        tab["source_event"][
            {"event": "event_id", "record": "source_record_id", "site": "site_id"}[
                change
            ]
        ] = "other"
    document, _ = render(tab)
    assert "Scenario predicate explanation unavailable" in " ".join(document.itertext())
    assert document.find(".//table[caption='Scenario predicates']") is None


def test_all_five_status_tokens_remain_text_not_color_only() -> None:
    tab = relation()
    statuses = ["pass", "qualify", "refuse", "not_evaluated", "unavailable", "pass"]
    for row, status in zip(
        tab["relation_details"]["predicates"], statuses, strict=True
    ):
        row["status"] = status
    document, _ = render(tab)
    table = document.findall(".//table")[1]
    assert [row.findall("td")[0].text for row in table.findall("tbody/tr")] == statuses


def test_source_labels_and_values_are_escaped_without_mutating_records() -> None:
    tab = relation()
    label = "<img src=x onerror=alert(1)>"
    tab["source_event"]["source_family"] = label
    tab["relation_details"]["predicates"][0]["label"] = label
    document, _ = render(tab)
    assert document.find(".//img") is None
    assert " ".join(document.itertext()).count(label) == 2


def test_legacy_flat_edge_keeps_explicit_unavailable_explanation() -> None:
    document, _ = render({"candidate_status": "definite_candidate", "source_age_bp": 0})
    assert not document.findall(".//table")
    text = " ".join(document.itertext())
    assert "Canonical endpoint comparison unavailable" in text
    assert "Legacy or missing checks are not inferred" in text


def test_actual_edge_click_preserves_transport_and_existing_metadata() -> None:
    row = relation()
    rendered = render_edges([row])
    tab = rendered["rows"][0]["focus"]["detailTabs"]["relation"]
    for key in ("source_event", "target_event", "relation_details"):
        assert tab[key] == row[key]
    assert tab["loaded_interval"] == [0, 100]
    document, _ = render(tab)
    assert len(document.findall(".//table")) == 2


def test_actual_producer_projection_bridge_and_mounted_relation_drawer() -> None:
    source = replace(
        event("source", feature_key="taxon:fixture", younger_bp=100, older_bp=100),
        source_record_id="source:record",
        event_id="",
    )
    target = replace(
        event("target", feature_key="taxon:fixture", younger_bp=0, older_bp=0),
        source_record_id="target:record",
        event_id="",
    )
    network = generate_propagation_network((source, target))
    projected: Any = project_propagation_network(network)["directed_candidates.geojson"]
    assert projected["record_count"] == 1
    edge = projected["features"][0]["properties"]
    canonical = dict(network.scenario_results[0].directed_candidates[0].as_dict())
    edge.update(
        signal_id="taxon:fixture",
        source_record_id=source.source_record_id,
        target_record_id=target.source_record_id,
        source_country="Sweden",
        target_country="Sweden",
    )
    normalized = normalize_edges([edge])[0]
    for key, value in canonical.items():
        assert normalized[key] == value
    tabs = render_edges([edge])["rows"][0]["focus"]["detailTabs"]
    assert tabs["overview"]["edge_id"] == canonical["edge_id"]
    tab = tabs["relation"]
    for key in (
        "source_event_id",
        "target_event_id",
        "scenario_id",
        "candidate_status",
        "reason_code",
        "build_id",
        "schema_version",
    ):
        assert tab[key] == canonical[key]
    script = (
        template_block("const DETAIL_TAB_DEFINITIONS", "const DEFAULT_COUNTRIES")
        + template_block("function escapeHtml", "function normalizedMediaLinks")
        + template_block("function detailTableShape", "function renderFocusCard")
        + template_block("function renderRelationDetails", "function renderEdgeLayers")
        + "const tab="
        + json.dumps(tab)
        + ";const original=JSON.stringify(tab);"
        + """
const focusTabs={innerHTML:'',contains(){return false},querySelectorAll(){return []}};
const focusDetail={innerHTML:'',dataset:{},contains(){return false},setAttribute(key,value){this[key]=value},querySelectorAll(){return []}};
const focusExportButton={},focusCopyLinkButton={},focusExportStatus={};
const document={activeElement:null},detailTablePages=new Map(),DETAIL_TABLE_PAGE_SIZE=25;
let activeFocusTab='relation';const focusState={kind:'edge',detailTabs:{relation:tab}};
function sourcePollenExportAvailable(){return false}function syncHashState(){}
renderFocusDetail();
console.log(JSON.stringify({html:focusDetail.innerHTML,unchanged:original===JSON.stringify(tab),label:focusDetail['aria-labelledby']}));
"""
    )
    observed = run_node_json(script)
    document = ET.fromstring("<div>" + observed["html"] + "</div>")
    tables = document.findall(".//table")
    assert [table.findtext("caption") for table in tables[:2]] == [
        "Canonical relation endpoints",
        "Scenario predicates",
    ]
    assert [row.findall("td")[0].text for row in tables[1].findall("tbody/tr")] == [
        "pass"
    ] * 6
    assert observed["unchanged"] is True and observed["label"] == "focus-tab-relation"
    assert "loaded interval" in " ".join(document.itertext())
