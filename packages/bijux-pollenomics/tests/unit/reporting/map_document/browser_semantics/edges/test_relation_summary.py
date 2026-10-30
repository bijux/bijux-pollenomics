"""Country counts preserve supplied scenario, direction and native identities."""

from __future__ import annotations

from copy import deepcopy
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
    generate_propagation_network,
)
from bijux_pollenomics.analysis.propagation.projection import (
    PropagationSelection,
    project_propagation_network,
)
from bijux_pollenomics.analysis.propagation.projection.relation import (
    candidate_relation_details,
)

from .....analysis.propagation.network.support import event
from ..support import run_node_json, template_block
from .test_edge_focus_url import browser
from .test_edge_focus_url import published as published

SCRIPT = (
    files("bijux_pollenomics.reporting.map_document")
    .joinpath("assets/relation-summary.js")
    .read_text()
)


def edge(
    name: str = "pair",
    *,
    source_country: str = "NO",
    target_country: str = "SE",
    source_bounds: tuple[int, int] = (100, 100),
    target_bounds: tuple[int, int] | None = (0, 0),
    scenario_id: str = "rectangular_100km_100yr_v1",
) -> dict[str, Any]:
    source = event(
        "source-" + name,
        country_code=source_country,
        younger_bp=source_bounds[0],
        older_bp=source_bounds[1],
    )
    target = event(
        "target-" + name,
        country_code=target_country,
        younger_bp=target_bounds[0] if target_bounds else None,
        older_bp=target_bounds[1] if target_bounds else None,
        comparability_status="comparable" if target_bounds else "unresolved",
    )
    scenario = CandidatePropagationScenario(scenario_id, 100, 100)
    candidate = evaluate_propagation_pair(source, target, scenario=scenario)
    assert isinstance(candidate, PropagationCandidate)
    # The common drawable path must consume actual network/projection output.
    if candidate.candidate_status in {
        "definite_candidate",
        "possible_candidate",
        "indeterminate_order",
    }:
        products = project_propagation_network(
            generate_propagation_network((source, target), scenarios=(scenario,)),
            selection=PropagationSelection(scenario_id=scenario.scenario_id),
        )
        layer = (
            "indeterminate_pairs.geojson"
            if candidate.candidate_status == "indeterminate_order"
            else "directed_candidates.geojson"
        )
        features = cast(list[dict[str, Any]], products[layer]["features"])
        return next(
            r["properties"]
            for r in features
            if r["properties"]["source_event_id"] == source.event_id
        )
    return {
        **candidate.as_dict(),
        "source_event": source.as_dict(),
        "target_event": target.as_dict(),
        "relation_details": candidate_relation_details(
            candidate, source, target, scenario
        ),
    }


def summary(
    rows: object, *, callback: str = "null", limit: object = 25
) -> dict[str, Any]:
    script = (
        template_block("function escapeHtml", "function normalizedMediaLinks")
        + SCRIPT
        + "const edges="
        + json.dumps(rows)
        + ";const before=JSON.stringify(edges);"
        + "const data=relationSummaryData(edges);let calls=0;"
        + "const html=renderRelationSummary(data,(id,scenario)=>{calls++;return "
        + callback
        + ";},"
        + json.dumps(limit)
        + ");"
        + "console.log(JSON.stringify({data,html,calls,unchanged:before===JSON.stringify(edges)}));"
    )
    result = cast(dict[str, Any], run_node_json(script))
    assert result["unchanged"] is True
    return result


def test_real_projected_country_counts_preserve_domestic_and_oriented_cells() -> None:
    rows = [
        edge(),
        edge("domestic", source_country="SE"),
        edge("reverse", source_country="SE", target_country="NO"),
    ]
    for row in rows:
        row["source_country"] = row["target_country"] = "Misleading display label"
    before = deepcopy(rows)
    observed = summary(
        rows,
        callback="'#focus_edge='+encodeURIComponent(id)+'&focus_scenario='+encodeURIComponent(scenario)",
    )
    data = observed["data"]
    assert (
        data["status"] == "available"
        and data["edgeCount"] == data["sourceEdgeCount"] == 3
    )
    assert data["countries"] == ["DK", "FI", "NO", "SE"]
    partition = data["partitions"][0]
    assert partition["orientation"] == "directed"
    assert {
        (c["sourceCountry"], c["targetCountry"]): len(c["edgeIds"])
        for c in partition["cells"]
    } == {("NO", "SE"): 1, ("SE", "NO"): 1, ("SE", "SE"): 1}
    document = ET.fromstring(observed["html"])
    table = document.find(".//table")
    assert table is not None and len(table.findall("tbody/tr")) == 4
    assert all(th.get("scope") == "col" for th in table.findall("thead/tr/th"))
    for tr in table.findall("tbody/tr"):
        heading = tr.find("th")
        assert heading is not None and heading.get("scope") == "row"
    assert len(table.findall(".//a")) == 3
    assert "Misleading display label" not in observed["html"]
    assert "zero cell means no supplied relation" in observed["html"]
    assert "before endpoint time, layer and viewport eligibility" in observed["html"]
    assert "displayed lines may be fewer" in observed["html"]
    assert rows == before


def test_scenarios_and_candidate_statuses_stay_separate() -> None:
    rows = [
        edge("first"),
        edge("second", scenario_id="another-scenario"),
        edge("possible", source_bounds=(100, 150)),
    ]
    data = summary(rows)["data"]
    assert len(data["partitions"]) == 3
    assert {(p["scenarioId"], p["status"]) for p in data["partitions"]} == {
        ("rectangular_100km_100yr_v1", "definite_candidate"),
        ("another-scenario", "definite_candidate"),
        ("rectangular_100km_100yr_v1", "possible_candidate"),
    }
    assert sum(len(c["edgeIds"]) for p in data["partitions"] for c in p["cells"]) == 3


@pytest.mark.parametrize("arrow", [False, None, 0, 1, "true", [], {}, "absent"])
def test_missing_false_or_nonboolean_direction_never_becomes_an_origin(
    arrow: object,
) -> None:
    row = edge()
    if arrow == "absent":
        del row["directional_arrow_allowed"]
    else:
        row["directional_arrow_allowed"] = arrow
    observed = summary([row])
    assert observed["data"]["partitions"][0]["orientation"] == "stored_endpoint_order"
    assert "NON-DIRECTIONAL" in observed["html"]
    assert "neither endpoint is asserted to be older or an origin" in observed["html"]
    assert "Directed source → target country counts" not in observed["html"]


@pytest.mark.parametrize(
    ("source_bounds", "target_bounds", "status"),
    [
        ((0, 100), (50, 150), "indeterminate_order"),
        ((0, 0), (100, 100), "excluded_temporal_nonpositive"),
        ((200, 200), (0, 0), "excluded_temporal_too_large"),
        ((100, 100), None, "unresolved"),
    ],
)
def test_nondirectional_status_keeps_its_identity_even_if_arrow_is_supplied_true(
    source_bounds: tuple[int, int],
    target_bounds: tuple[int, int] | None,
    status: str,
) -> None:
    row = edge(source_bounds=source_bounds, target_bounds=target_bounds)
    assert row["candidate_status"] == status
    row["directional_arrow_allowed"] = True
    observed = summary([row])
    assert observed["data"]["partitions"][0]["status"] == status
    assert observed["data"]["partitions"][0]["orientation"] == "stored_endpoint_order"


@pytest.mark.parametrize(
    "defect",
    [
        "duplicate",
        "conflicting_duplicate",
        "scenario_id",
        "threshold",
        "rule",
        "event_country",
        "endpoint",
        "code",
        "missing_status",
        "feature",
    ],
)
def test_ambiguous_or_invalid_identity_refuses_the_entire_matrix(defect: str) -> None:
    first, second = edge(), edge("second")
    if defect in {"duplicate", "conflicting_duplicate"}:
        second = deepcopy(first)
        if defect == "conflicting_duplicate":
            second["scenario_id"] = "foreign"
    elif defect == "scenario_id":
        second["relation_details"]["scenario_id"] = "foreign"
    elif defect == "threshold":
        second["relation_details"]["maximum_lag_years"] = 200
    elif defect == "rule":
        first["relation_details"]["rule_type"] = "rectangular"
        second["relation_details"]["rule_type"] = "other-rule"
    elif defect == "event_country":
        second["source_event_id"] = first["source_event_id"]
        second["source_country_code"] = "FI"
    elif defect == "endpoint":
        second["source_event"]["event_id"] = "foreign"
    elif defect == "code":
        second["source_country_code"] = "Sweden"
    elif defect == "feature":
        second["source_event_id"] = first["source_event_id"]
        second["feature_key"] = "taxon:foreign"
    else:
        del second["candidate_status"]
    observed = summary([first, second])
    assert observed["data"]["status"] == "refused"
    assert (
        observed["data"]["sourceEdgeCount"] == 2
        and observed["data"]["edgeCount"] is None
    )
    assert observed["data"]["partitions"] == []
    assert (
        "No country matrix is inferred" in observed["html"]
        and "<table" not in observed["html"]
    )


def test_unavailable_empty_and_legacy_metadata_are_distinct() -> None:
    assert summary(None)["data"]["status"] == "unavailable"
    empty = summary([])
    assert empty["data"]["status"] == "available" and empty["data"]["edgeCount"] == 0
    assert "No retained active relation rows were supplied" in empty["html"]
    first, second = edge(), edge("second")
    del first["relation_details"]
    if "rule_type" in second["relation_details"]:
        del second["relation_details"]["rule_type"]
    assert summary([first, second])["data"]["status"] == "available"


def test_exact_ids_and_source_labels_are_escaped_and_unsafe_links_are_not_emitted() -> (
    None
):
    row = edge()
    hostile = '<img src=x onerror="unsafe()">'
    row["edge_id"] = hostile
    row["scenario_id"] = row["relation_details"]["scenario_id"] = hostile
    observed = summary([row], callback="'javascript:unsafe()'")
    document = ET.fromstring(observed["html"])
    assert document.find(".//img") is None and document.find(".//a") is None
    assert hostile in " ".join(document.itertext())
    observed = summary([row], callback="'#edge='+encodeURIComponent(id)")
    document = ET.fromstring(observed["html"])
    link = document.find(".//a")
    assert link is not None
    href = link.get("href")
    assert href is not None and href.startswith("#edge=")
    assert link.text == hostile


def test_full_counts_and_ids_remain_exact_when_only_first_25_links_are_rendered() -> (
    None
):
    base = edge()
    rows = [{**base, "edge_id": f"edge-{index:03}"} for index in range(40)]
    observed = summary(rows, callback="'#edge='+id")
    ids = observed["data"]["partitions"][0]["cells"][0]["edgeIds"]
    assert ids == [r["edge_id"] for r in rows]
    assert observed["data"]["edgeCount"] == 40 and observed["calls"] == 25
    assert "first 25 of 40" in observed["html"]
    assert len(ET.fromstring(observed["html"]).findall(".//a")) == 25
    assert "narrow the scenario, status, country or signal filters" in observed["html"]


def test_projection_order_cannot_change_counts_partitions_or_rendered_first_ids() -> (
    None
):
    rows = [edge("first"), edge("second", source_country="DK", target_country="FI")]
    first, reverse = summary(rows), summary(list(reversed(rows)))
    assert first["data"] == reverse["data"] and first["html"] == reverse["html"]


def test_many_partitions_keep_complete_data_and_bound_total_tables_and_ids() -> None:
    base = edge()
    rows = []
    for index in range(40):
        scenario = f"scenario-{index:03}"
        rows.append(
            {
                **base,
                "edge_id": f"edge-{index:03}",
                "scenario_id": scenario,
                "relation_details": {
                    **base["relation_details"],
                    "scenario_id": scenario,
                },
            }
        )
    observed = summary(rows, callback="'#edge='+id")
    assert len(observed["data"]["partitions"]) == observed["data"]["edgeCount"] == 40
    document = ET.fromstring(observed["html"])
    assert len(document.findall(".//table")) == 25
    assert len(document.findall(".//a")) == observed["calls"] == 25
    assert "first 25 of 40 scenario/status/orientation tables" in observed["html"]
    assert "at most 25 IDs in total" in observed["html"]


@pytest.mark.parametrize(
    "availability", ["loaded", "unloaded", "external_navigation", "pending_restore"]
)
def test_actual_mount_uses_current_filters_and_only_shareable_loaded_identity(
    published: dict[str, Any], availability: str
) -> None:
    observed = browser(
        published,
        "const availability="
        + json.dumps(availability)
        + r""";
const container={innerHTML:''},lookup=document.getElementById;
document.getElementById=id=>id==='relation-country-summary'?container:lookup(id);
const params=new URLSearchParams({relation_scenario:supplied.edge.scenario_id,relation_status:supplied.edge.candidate_status,relation_source_country:'NO',relation_target_country:'SE',focus_layer:'points',focus_feature:'old-point',focus_record:'old-record',focus_tab:'overview',countries:'Norway',cross_border:'only'});
Object.assign(activeRelationFilters,relationFiltersFromHash(params));
setFocusState({kind:'point',layerKey:'points',featureKey:'old-point',recordId:'old-record'});
window.location.hash='#'+params;
if(availability==='unloaded')visiblePointEntries.pop();
if(availability==='external_navigation')atlasURLState.canPublish=()=>false;
if(availability==='pending_restore'){pendingEdgeFocus=request();window.location.hash='#relation_scenario=stale&countries=Sweden&layers=none';}
renderRelationCountrySummary();
console.log(JSON.stringify({html:container.innerHTML,unchanged:original===JSON.stringify(supplied)}));
""",
    )
    assert observed["unchanged"] is True
    document = ET.fromstring(observed["html"])
    link = document.find(".//a")
    if availability in {"unloaded", "external_navigation"}:
        assert link is None
        assert published["edge"]["edge_id"] in " ".join(document.itertext())
        return
    assert link is not None
    from urllib.parse import parse_qs

    state = parse_qs(link.attrib["href"][1:])
    assert not {"focus_layer", "focus_feature", "focus_record"} & state.keys()
    assert state["focus_edge"] == [published["edge"]["edge_id"]]
    assert (
        state["focus_scenario"]
        == state["relation_scenario"]
        == [published["edge"]["scenario_id"]]
    )
    assert state["focus_build"] == [published["manifest"]["build_id"]]
    assert state["focus_tab"] == ["relation"]
    assert state["relation_status"] == [published["edge"]["candidate_status"]]
    assert state["relation_source_country"] == ["NO"]
    assert state["relation_target_country"] == ["SE"]
    assert state["countries"] == ["Norway"] and state["cross_border"] == ["only"]
