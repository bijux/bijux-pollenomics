"""Event-definition selection preserves actual source semantics and retained rows."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from importlib.resources import files
import json
from typing import Any, cast
from urllib.parse import urlencode
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

from .....analysis.propagation.network.support import event
from ..support import run_node_json, template_block
from .test_relation_time_summary import edge as status_edge
from .test_scientific_edges import normalize_edges

FIELDS = (
    "event_type",
    "threshold_profile_id",
    "measurement_semantics_id",
    "method_compatibility_key",
)
DEFAULT = (
    "reported_positive_observation",
    "reported_positive_v1",
    "presence.v1",
    "pollen-presence.v1",
)
SCRIPT = (
    files("bijux_pollenomics.reporting.map_document")
    .joinpath("assets/relation-event-definition.js")
    .read_text()
)


def edge(name: str = "first", definition: tuple[str, ...] = DEFAULT) -> dict[str, Any]:
    endpoints = [
        replace(
            event(
                side + name,
                younger_bp=age,
                older_bp=age,
                feature_key="taxon:fixture",
                threshold_profile_id=definition[1],
                measurement_semantics_id=definition[2],
                method_compatibility_key=definition[3],
            ),
            event_type=definition[0],
            event_id="",
        )
        for side, age in (("source", 100), ("target", 0))
    ]
    source, target = endpoints
    scenario = CandidatePropagationScenario("literal-rule", 100, 100)
    candidate = evaluate_propagation_pair(source, target, scenario=scenario)
    assert isinstance(candidate, PropagationCandidate)
    product = candidate_geojson(
        [candidate],
        {item.event_id: item for item in endpoints},
        directional=candidate.directional_arrow_allowed,
        scenario=scenario,
    )
    row = cast(list[dict[str, Any]], product["features"])[0]["properties"]
    assert row["threshold_profile_id"] == definition[1]
    # The projection supplies definitions without changing public event bodies.
    assert row["source_event"] == source.as_dict()
    assert row["target_event"] == target.as_dict()
    assert row["relation_details"]["event_definition"] == dict(
        zip(FIELDS, definition, strict=True)
    )
    row.update(
        source_record_id=source.source_record_id,
        target_record_id=target.source_record_id,
        source_country="Sweden",
        target_country="Sweden",
        signal_id=source.feature_key,
    )
    return dict(normalize_edges([row])[0])


def selected(rows: object, query: str = "", action: str = "") -> dict[str, Any]:
    result = run_node_json(
        template_block("function escapeHtml", "function normalizedMediaLinks")
        + SCRIPT
        + "const edges="
        + json.dumps(rows)
        + ";const original=JSON.stringify(edges);"
        + "let state=relationEventDefinitionFromHash(new URLSearchParams("
        + json.dumps(query)
        + "));"
        + action
        + "const data=relationEventDefinitionSelection(edges,state),params=new URLSearchParams();"
        + "writeRelationEventDefinitionHash(params,state);"
        + "const restored=relationEventDefinitionFromHash(params);"
        + "console.log(JSON.stringify({data:{...data,selected:data.selected.map(row=>row.edge_id)},"
        + "options:renderRelationEventDefinitionOptions(data,state),state,restored,hash:params.toString(),"
        + "unchanged:original===JSON.stringify(edges),references:data.selected.every(row=>edges.includes(row))}));"
    )
    assert result["unchanged"] is True and result["references"] is True
    return cast(dict[str, Any], result)


def query(definition: tuple[str, ...] = DEFAULT) -> str:
    return urlencode({"relation_event_definition": json.dumps(definition)})


def test_actual_native_projection_definitions_are_exact_and_all_retains_every_row() -> (
    None
):
    rows = [
        edge(),
        edge("first-observed", ("derived_first_observed", *DEFAULT[1:])),
        edge("threshold", ("derived_threshold_crossing", *DEFAULT[1:])),
    ]
    before = deepcopy(rows)
    all_rows = selected(rows)
    assert all_rows["data"]["availableCount"] == all_rows["data"]["retainedCount"] == 3
    assert len(all_rows["data"]["catalog"]) == 3
    for row in rows:
        value = tuple(
            row["relation_details"]["event_definition"][key] for key in FIELDS
        )
        observed = selected(rows, query(value))
        assert observed["data"]["selected"] == [row["edge_id"]]
        assert observed["data"]["unavailable"] is False
    assert rows == before


@pytest.mark.parametrize("index", [1, 2, 3])
def test_each_exact_source_definition_dimension_changes_membership(index: int) -> None:
    alternative = list(DEFAULT)
    alternative[index] = "all"
    rows = [edge(), edge("alternative", tuple(alternative))]
    observed = selected(rows, query(tuple(alternative)))
    assert observed["data"]["selected"] == [rows[1]["edge_id"]]
    assert observed["restored"]["value"] is not None
    assert len(observed["data"]["catalog"]) == 2


def test_definition_selection_retains_all_seven_native_statuses_without_reclassification() -> (
    None
):
    inputs = [
        ((100, 100), (0, 0), False),
        ((100, 150), (0, 0), False),
        ((0, 100), (50, 150), False),
        ((100, 100), None, False),
        ((100, 100), (0, 0), True),
        ((0, 0), (100, 100), False),
        ((200, 200), (0, 0), False),
    ]
    rows = [
        status_edge(
            str(index), source_bounds=bounds, target_bounds=target, spatial=spatial
        )
        for index, (bounds, target, spatial) in enumerate(inputs)
    ]
    assert len({row["candidate_status"] for row in rows}) == 7
    observed = selected(rows, query())
    assert observed["data"]["availableCount"] == 7
    assert observed["data"]["selected"] == [row["edge_id"] for row in rows]


@pytest.mark.parametrize(
    "defect", ["definition", "endpoint", "private_field", "legacy"]
)
def test_incomplete_legacy_rows_stay_all_retained_without_specific_fallback(
    defect: str,
) -> None:
    complete, incomplete = edge(), edge("incomplete")
    if defect == "definition":
        del incomplete["relation_details"]["event_definition"]
    elif defect == "endpoint":
        del incomplete["target_event"]
    elif defect == "private_field":
        del incomplete["relation_details"]["event_definition"][
            "method_compatibility_key"
        ]
    else:
        del incomplete["candidate_status"]
    all_rows = selected([complete, incomplete])
    assert all_rows["data"]["missingCount"] == 1
    assert all_rows["data"]["availableCount"] == 1
    assert len(all_rows["data"]["selected"]) == 2
    assert selected([complete, incomplete], query())["data"]["selected"] == [
        complete["edge_id"]
    ]


@pytest.mark.parametrize(
    "defect",
    [
        "event",
        "site",
        "record",
        "feature",
        "type",
        "profile",
        "candidate_profile",
        "measurement",
        "method",
        "basis",
        "scenario",
        "unknown_type",
        "malformed",
    ],
)
def test_conflicting_definitions_are_retained_but_never_selected(defect: str) -> None:
    complete, bad = edge(), edge("bad")
    endpoint = bad["target_event"]
    if defect in {"event", "site", "record", "feature"}:
        endpoint[
            {
                "event": "event_id",
                "site": "site_id",
                "record": "source_record_id",
                "feature": "feature_key",
            }[defect]
        ] = "foreign"
    elif defect == "candidate_profile":
        bad["threshold_profile_id"] = "foreign"
    elif defect in {"type", "profile", "measurement", "method"}:
        endpoint[
            {
                "type": "event_type",
                "profile": "threshold_profile_id",
                "measurement": "measurement_semantics_id",
                "method": "method_compatibility_key",
            }[defect]
        ] = "foreign"
    elif defect == "unknown_type":
        bad["relation_details"]["event_definition"]["event_type"] = "unknown"
    elif defect == "malformed":
        bad["relation_details"]["event_definition"] = []
    else:
        bad["relation_details"]["basis" if defect == "basis" else "scenario_id"] = (
            "foreign"
        )
    all_rows = selected([complete, bad])
    assert all_rows["data"]["conflictingCount"] == 1
    assert len(all_rows["data"]["selected"]) == 2
    assert selected([complete, bad], query())["data"]["selected"] == [
        complete["edge_id"]
    ]


def test_repeated_event_conflicting_definition_makes_both_variants_unselectable() -> (
    None
):
    first = edge()
    second = deepcopy(first)
    second["edge_id"] = "second-relation"
    second["relation_details"]["event_definition"]["measurement_semantics_id"] = (
        "another"
    )
    observed = selected([first, second])
    assert observed["data"]["conflictingCount"] == 2
    assert observed["data"]["catalog"] == []
    assert len(observed["data"]["selected"]) == 2
    assert selected([first, second], query())["data"]["unavailable"] is True


def test_repeated_relation_ids_are_not_a_selectable_definition_population() -> None:
    row = edge()
    observed = selected([row, deepcopy(row)])
    assert observed["data"]["conflictingCount"] == 2
    assert observed["data"]["catalog"] == []


@pytest.mark.parametrize(
    "value",
    [
        "",
        "all",
        "null",
        "[]",
        '["reported_positive_observation",true,"x","y"]',
        '["reported_positive_observation","","x","y"]',
        '["unknown","x","y","z"]',
        '"text"',
    ],
)
def test_invalid_shared_definition_remains_unavailable_when_reshared(
    value: str,
) -> None:
    observed = selected([edge()], urlencode({"relation_event_definition": value}))
    assert observed["data"]["unavailable"] is True
    assert observed["data"]["selected"] == []
    assert observed["state"]["invalid"] is observed["restored"]["invalid"] is True
    assert "Unavailable shared event definition" in observed["options"]


def test_unknown_valid_tuple_and_duplicate_url_never_fall_back_to_all() -> None:
    unknown = selected([edge()], query((DEFAULT[0], "foreign", *DEFAULT[2:])))
    assert unknown["data"]["unavailable"] is True
    assert unknown["data"]["selected"] == []
    duplicate = selected([edge()], query() + "&" + query())
    assert duplicate["state"]["duplicate"] is duplicate["restored"]["duplicate"] is True
    assert duplicate["data"]["selected"] == []


def test_no_parameter_is_all_and_explicit_ui_reset_removes_only_owned_parameter() -> (
    None
):
    observed = selected(
        [edge()], query(), "state={value:null,invalid:false,duplicate:false};"
    )
    assert observed["data"]["selected"]
    assert observed["state"]["value"] is None
    assert observed["hash"] == ""
    assert '<option value="" selected>All retained</option>' in observed["options"]


def test_source_labels_are_escaped_and_membership_is_publication_order_independent() -> (
    None
):
    hostile = '<img src=x onerror="unsafe()">'
    rows = [edge(), edge("other", (DEFAULT[0], hostile, *DEFAULT[2:]))]
    forward, reverse = selected(rows), selected(list(reversed(rows)))
    assert forward["data"]["catalog"] == reverse["data"]["catalog"]
    assert forward["options"] == reverse["options"]
    tree = ET.fromstring(
        "<select>"
        + forward["options"].replace(" selected", ' selected="selected"')
        + "</select>"
    )
    assert tree.find("img") is None
    assert hostile in " ".join(tree.itertext())


@pytest.mark.parametrize("legacy_first", [False, True])
def test_legacy_id_collision_cannot_be_hidden_by_a_native_definition_filter(
    legacy_first: bool,
) -> None:
    native = edge()
    legacy = deepcopy(native)
    del legacy["candidate_status"]
    rows = [legacy, native] if legacy_first else [native, legacy]
    retained = selected(rows)
    assert retained["data"]["conflictingCount"] == 2
    assert len(retained["data"]["selected"]) == 2
    specific = selected(rows, query())
    assert specific["data"]["selected"] == []
    assert specific["data"]["unavailable"] is True
