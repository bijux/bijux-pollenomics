"""Literal temporal envelopes retain native joins and missing-age distinctions."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from importlib.resources import files
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

from ......analysis.propagation.network.support import event
from ...support import run_node_json, template_block
from ..test_scientific_edges import normalize_edges

SCRIPT = (
    files("bijux_pollenomics.reporting.map_document")
    .joinpath("assets/relation-time-summary.js")
    .read_text()
)


def edge(
    name: str = "first",
    *,
    source_bounds: tuple[int, int] = (100, 100),
    target_bounds: tuple[int, int] | None = (0, 0),
    spatial: bool = False,
) -> dict[str, Any]:
    source = event(
        "source-" + name,
        younger_bp=source_bounds[0],
        older_bp=source_bounds[1],
        feature_key="taxon:fixture",
    )
    target = event(
        "target-" + name,
        younger_bp=target_bounds[0] if target_bounds else None,
        older_bp=target_bounds[1] if target_bounds else None,
        comparability_status="comparable" if target_bounds else "unresolved",
        feature_key="taxon:fixture",
    )
    if spatial:
        target = replace(target, longitude=20, event_id="")
    scenario = CandidatePropagationScenario("literal-rule", 100, 100)
    candidate = evaluate_propagation_pair(source, target, scenario=scenario)
    assert isinstance(candidate, PropagationCandidate)
    product = candidate_geojson(
        [candidate],
        {source.event_id: source, target.event_id: target},
        directional=candidate.directional_arrow_allowed,
        scenario=scenario,
    )
    row = cast(list[dict[str, Any]], product["features"])[0]["properties"]
    row.update(
        source_record_id=source.source_record_id,
        target_record_id=target.source_record_id,
        source_country="Sweden",
        target_country="Sweden",
        signal_id=source.feature_key,
    )
    return dict(normalize_edges([row])[0])


def summary(rows: object) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        run_node_json(
            template_block("function escapeHtml", "function normalizedMediaLinks")
            + SCRIPT
            + "const rows="
            + json.dumps(rows)
            + ";const before=JSON.stringify(rows);const data=relationTimeSummaryData(rows);"
            + "console.log(JSON.stringify({data,html:renderRelationTimeSummary(data),unchanged:before===JSON.stringify(rows)}));"
        ),
    )


def test_actual_projection_preserves_zero_intervals_and_descriptive_gaps() -> None:
    rows = [edge(), edge("older", source_bounds=(500, 550), target_bounds=(450, 450))]
    before = deepcopy(rows)
    # Keep a single exact status group without changing endpoint source facts.
    assert rows[0]["candidate_status"] == rows[1]["candidate_status"]
    observed = summary(rows)
    group = observed["data"]["groups"][0]
    assert observed["data"]["status"] == "available"
    assert group["edgeCount"] == 2 and group["distinctEventCount"] == 4
    assert group["source"] == {
        "distinctEventCount": 2,
        "comparableEventCount": 2,
        "unresolvedEventCount": 0,
        "missingEndpointCount": 0,
        "youngerBp": 100,
        "olderBp": 550,
    }
    assert group["target"]["youngerBp"] == 0
    assert group["target"]["olderBp"] == 450
    tree = ET.fromstring(observed["html"])
    assert len(tree.findall(".//tbody/tr")) == 2
    assert all(th.get("scope") == "col" for th in tree.findall(".//thead/tr/th"))
    assert (
        "not continuous coverage through gaps or a confidence interval"
        in observed["html"]
    )
    assert "before endpoint time, layer and viewport eligibility" in observed["html"]
    assert "No midpoint, time bin, calibration or interpolation" in observed["html"]
    assert observed["unchanged"] is True and rows == before


@pytest.mark.parametrize(
    "field",
    ["scenario_id", "signal_id", "resolution", "feature_key", "candidate_status"],
)
def test_exact_group_dimensions_cannot_silently_merge(field: str) -> None:
    first, second = edge(), edge("second")
    second[field] = "another" if field != "candidate_status" else "possible_candidate"
    if field in {"resolution", "feature_key"}:
        for side in ("source", "target"):
            second[f"{side}_event"][field] = second[field]
    observed = summary([first, second])
    assert observed["data"]["status"] == "available"
    assert len(observed["data"]["groups"]) == 2
    assert sum(row["edgeCount"] for row in observed["data"]["groups"]) == 2


@pytest.mark.parametrize(
    ("bounds", "target", "spatial", "status"),
    [
        ((100, 100), (0, 0), False, "definite_candidate"),
        ((100, 150), (0, 0), False, "possible_candidate"),
        ((0, 100), (50, 150), False, "indeterminate_order"),
        ((100, 100), None, False, "unresolved"),
        ((100, 100), (0, 0), True, "excluded_spatial"),
        ((0, 0), (100, 100), False, "excluded_temporal_nonpositive"),
        ((200, 200), (0, 0), False, "excluded_temporal_too_large"),
    ],
)
def test_all_native_statuses_remain_literal_without_origin_inference(
    bounds: tuple[int, int],
    target: tuple[int, int] | None,
    spatial: bool,
    status: str,
) -> None:
    row = edge(source_bounds=bounds, target_bounds=target, spatial=spatial)
    assert row["candidate_status"] == status
    observed = summary([row])
    group = observed["data"]["groups"][0]
    assert group["candidate_status"] == status
    assert "Stored source endpoint" in observed["html"]
    assert "Stored target endpoint" in observed["html"]
    assert "do not establish age order for indeterminate relations" in observed["html"]
    if target is None:
        assert group["target"]["unresolvedEventCount"] == 1
        assert group["target"]["missingEndpointCount"] == 0
        assert group["target"]["youngerBp"] is None


def test_reused_event_is_distinct_once_but_missing_endpoint_occurrences_stay_visible() -> (
    None
):
    first = edge()
    second = deepcopy(first)
    second["edge_id"] = "second-native-relation"
    del second["target_event"]
    observed = summary([first, second])
    group = observed["data"]["groups"][0]
    assert group["distinctEventCount"] == 2
    assert group["target"]["distinctEventCount"] == 1
    assert group["target"]["comparableEventCount"] == 1
    assert group["target"]["missingEndpointCount"] == 1
    assert (
        "Missing endpoint counts count relation endpoint occurrences"
        in observed["html"]
    )


@pytest.mark.parametrize(
    "defect",
    [
        "duplicate",
        "missing_record",
        "wrong_record",
        "wrong_site",
        "wrong_event",
        "wrong_feature",
        "conflicting_event",
        "conflicting_age",
        "bool",
        "string",
        "negative",
        "partial",
        "reversed",
        "refused",
        "unresolved_numeric",
        "unknown_contract",
        "missing_contract",
        "mixed_contract",
        "endpoint_contract",
    ],
)
def test_ambiguous_identity_or_invalid_age_refuses_numeric_aggregation(
    defect: str,
) -> None:
    first, second = edge(), edge("second")
    event_row = second["source_event"]
    if defect == "duplicate":
        second["edge_id"] = first["edge_id"]
    elif defect == "missing_record":
        del second["source_record_id"]
    elif defect in {"wrong_record", "wrong_site", "wrong_event", "wrong_feature"}:
        key = {
            "wrong_record": "source_record_id",
            "wrong_site": "site_id",
            "wrong_event": "event_id",
            "wrong_feature": "feature_key",
        }[defect]
        event_row[key] = "foreign"
    elif defect in {"conflicting_event", "conflicting_age"}:
        second["source_event_id"] = first["source_event_id"]
        if defect == "conflicting_age":
            second["source_site_id"] = first["source_site_id"]
            second["source_record_id"] = first["source_record_id"]
            second["source_event"] = deepcopy(first["source_event"])
            second["source_event"]["older_bp"] = 101
    elif defect in {"unknown_contract", "mixed_contract"}:
        second["temporal_contract_version"] = "future"
    elif defect == "missing_contract":
        del second["temporal_contract_version"]
    elif defect == "endpoint_contract":
        event_row["temporal_contract_version"] = "foreign"
    elif defect == "refused":
        event_row["comparability_status"] = "refused"
    elif defect == "unresolved_numeric":
        event_row["comparability_status"] = "unresolved"
    else:
        event_row["younger_bp"] = {
            "bool": True,
            "string": "100",
            "negative": -1,
            "partial": None,
            "reversed": 101,
        }[defect]
    observed = summary([first, second])
    assert observed["data"]["status"] == "refused"
    assert observed["data"]["sourceEdgeCount"] == 2
    assert observed["data"]["groups"] == []
    assert "No numeric envelope is inferred" in observed["html"]
    assert "<table" not in observed["html"]
    assert observed["unchanged"] is True


def test_unavailable_empty_and_missing_endpoints_are_not_zero_ages() -> None:
    assert summary(None)["data"]["status"] == "unavailable"
    empty = summary([])
    assert empty["data"]["status"] == "available"
    assert "No retained active relation rows" in empty["html"]
    row = edge()
    row["source_event"] = None
    del row["target_event"]
    observed = summary([row])
    assert observed["data"]["groups"][0]["source"]["youngerBp"] is None
    assert "Unavailable (no comparable supplied endpoint ages)" in observed["html"]


@pytest.mark.parametrize(
    "field", ["country_code", "source_snapshot_id", "chronology_claim_id"]
)
def test_reused_event_source_identity_cannot_change_between_relations(
    field: str,
) -> None:
    first = edge()
    second = deepcopy(first)
    second["edge_id"] = "another-relation"
    second["source_event"][field] = "foreign"
    assert summary([first, second])["data"]["status"] == "refused"


def test_source_ids_are_escaped_and_publication_order_does_not_change_summary() -> None:
    rows = [edge(), edge("second")]
    hostile = '<img src=x onerror="unsafe()">'
    rows[0]["scenario_id"] = rows[0]["signal_id"] = hostile
    observed, reverse = summary(rows), summary(list(reversed(rows)))
    assert observed["data"] == reverse["data"]
    assert observed["html"] == reverse["html"]
    tree = ET.fromstring(observed["html"])
    assert tree.find(".//img") is None
    assert hostile in " ".join(tree.itertext())


def test_many_exact_groups_keep_complete_data_and_bound_displayed_rows() -> None:
    base = edge()
    rows = [
        {**base, "edge_id": f"edge-{index:03}", "scenario_id": f"scenario-{index:03}"}
        for index in range(40)
    ]
    observed = summary(rows)
    assert len(observed["data"]["groups"]) == observed["data"]["sourceEdgeCount"] == 40
    assert len(ET.fromstring(observed["html"]).findall(".//tbody/tr")) == 50
    assert "first 25 of 40 exact groups" in observed["html"]
    assert "All groups remain in the retained selection" in observed["html"]
