"""Empty displays explain only current supplied selection and population facts."""

from __future__ import annotations

from importlib.resources import files
import json
from typing import Any

import pytest

from ..support import run_node_json, template_block


def evaluate(**changes: Any) -> dict[str, Any]:
    state = {
        "countryCount": 4,
        "selectedLayers": [{"scientific_selection_enabled": False}],
        "scientificSignalCount": 2,
        "selectedScientificSignalCount": 1,
        "pointCount": 0,
        "polygonLayerCount": 0,
        "retainedRelationCount": 0,
        "relationViewportCount": 0,
        "drawnRelationCount": 0,
        "drawNodes": True,
        "drawEdges": True,
        "loadStatus": "ready",
        **changes,
    }
    script = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/selection-empty-state.js")
        .read_text(encoding="utf-8")
    )
    observed: dict[str, Any] = run_node_json(
        template_block("function escapeHtml", "function normalizedMediaLinks")
        + script
        + "const input="
        + json.dumps(state)
        + ";const before=JSON.stringify(input);"
        "const summary=selectionEmptyState(input);"
        "console.log(JSON.stringify({summary,html:renderSelectionEmptyState(summary),"
        "unchanged:JSON.stringify(input)===before}));"
    )
    return observed


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"countryCount": 0}, "empty_countries"),
        ({"selectedLayers": []}, "empty_layers"),
        (
            {
                "selectedLayers": [{"scientific_selection_enabled": True}],
                "selectedScientificSignalCount": 0,
            },
            "empty_scientific_selection",
        ),
    ],
)
def test_explicit_empty_controls_are_selection_facts(
    changes: dict[str, Any], reason: str
) -> None:
    observed = evaluate(**changes)
    assert observed["summary"]["reason"] == reason
    assert not observed["summary"]["hidden"]
    assert observed["unchanged"]
    assert "absen" in observed["html"] or "Retained" in observed["html"]


@pytest.mark.parametrize(
    "changes",
    [
        {"pointCount": 2, "countryCount": 0},
        {
            "retainedRelationCount": 8,
            "relationViewportCount": 3,
            "drawnRelationCount": 1,
        },
    ],
)
def test_existing_population_is_not_reclassified_by_controls_or_drawing_mode(
    changes: dict[str, Any],
) -> None:
    observed = evaluate(**changes)
    assert observed["summary"]["reason"] == "not_empty"
    assert observed["summary"]["hidden"]
    assert observed["html"] == ""
    assert observed["unchanged"]


@pytest.mark.parametrize("draw_edges", [True, False])
def test_edges_only_or_disabled_drawing_preserves_hidden_point_entries(
    draw_edges: bool,
) -> None:
    observed = evaluate(pointCount=5, drawNodes=False, drawEdges=draw_edges)
    summary = observed["summary"]
    assert summary["reason"] == (
        "points_not_drawn" if draw_edges else "drawing_disabled"
    )
    assert not summary["hidden"]
    assert summary["populations"]["pointCount"] == 5
    assert "drawing disabled; not a primitive count" in observed["html"]
    assert "not evidence" in observed["html"]
    assert observed["unchanged"]


def test_nodes_only_explains_undrawn_edges_without_discarding_candidates() -> None:
    observed = evaluate(
        drawEdges=False, retainedRelationCount=8, relationViewportCount=3
    )
    assert observed["summary"]["reason"] == "relations_not_drawn"
    assert observed["summary"]["populations"]["retainedRelationCount"] == 8
    assert observed["summary"]["populations"]["relationViewportCount"] == 3
    assert observed["summary"]["populations"]["drawnRelationCount"] == 0
    assert "Drawing mode" in observed["html"]


@pytest.mark.parametrize("draw_nodes", [True, False])
def test_polygon_layers_do_not_hide_empty_point_relation_explanation(
    draw_nodes: bool,
) -> None:
    observed = evaluate(polygonLayerCount=2, drawNodes=draw_nodes)
    assert observed["summary"]["reason"] == "polygons_only"
    assert observed["summary"]["title"] == "Only polygon layers are displayed"
    assert not observed["summary"]["hidden"]
    assert observed["summary"]["populations"]["polygonLayerCount"] == 2
    assert "presence or absence" in observed["html"]
    assert "does not establish their scientific role" in observed["html"]
    assert observed["unchanged"]


@pytest.mark.parametrize(
    ("viewport", "reason"),
    [(0, "retained_relations_not_display_eligible"), (3, "relations_not_drawn")],
)
def test_retained_display_eligible_and_drawn_relations_stay_separate(
    viewport: int, reason: str
) -> None:
    observed = evaluate(retainedRelationCount=9, relationViewportCount=viewport)
    summary = observed["summary"]
    assert summary["reason"] == reason
    assert summary["populations"]["retainedRelationCount"] == 9
    assert summary["populations"]["relationViewportCount"] == viewport
    assert summary["populations"]["drawnRelationCount"] == 0
    assert "before endpoint time/layer/viewport" in observed["html"]
    assert "refused" not in summary["reason"]
    assert observed["unchanged"]


@pytest.mark.parametrize(
    "changes",
    [
        {"selectedScientificSignalCount": 0},
        {
            "selectedScientificSignalCount": 0,
            "selectedLayers": [
                {"scientific_selection_enabled": True},
                {"scientific_selection_enabled": False},
            ],
        },
        {
            "scientificSignalCount": 0,
            "selectedScientificSignalCount": 0,
            "selectedLayers": [{"scientific_selection_enabled": True}],
        },
        {"selectedLayers": [{"status": "unavailable"}, {}]},
        {"sourceStatus": "not_collected", "declaredReason": "all_refused"},
        {"classifications_status": "unavailable", "candidate_status": "refused"},
    ],
)
def test_partial_or_missing_scientific_metadata_cannot_explain_whole_selection(
    changes: dict[str, Any],
) -> None:
    observed = evaluate(**changes)
    assert observed["summary"]["reason"] == "unknown"
    assert "does not distinguish" in observed["html"]
    assert "not evidence" in observed["html"]


@pytest.mark.parametrize(
    ("status", "reason"),
    [("loading", "loading"), ("unavailable", "loading_unavailable")],
)
def test_whole_selection_load_state_does_not_use_previous_population(
    status: str, reason: str
) -> None:
    observed = evaluate(loadStatus=status, pointCount=4)
    assert observed["summary"]["reason"] == reason
    assert not observed["summary"]["hidden"]
    assert observed["summary"]["populations"] is None
    assert observed["summary"]["facts"] == []


@pytest.mark.parametrize("status", ["loading", "unavailable"])
@pytest.mark.parametrize(
    "changes",
    [
        {"retainedRelationCount": 0, "relationViewportCount": 12},
        {"pointCount": None, "selectedLayers": None},
        {"drawNodes": "previous-generation", "drawnRelationCount": -1},
    ],
)
def test_whole_selection_load_status_withholds_stale_or_incomplete_populations(
    status: str, changes: dict[str, Any]
) -> None:
    observed = evaluate(loadStatus=status, **changes)
    assert observed["summary"]["reason"] == (
        "loading" if status == "loading" else "loading_unavailable"
    )
    assert observed["summary"]["populations"] is None
    assert observed["summary"]["facts"] == []
    assert not observed["summary"]["hidden"]
    assert observed["unchanged"]


def test_separate_untimed_exclusions_never_become_whole_selection_cause() -> None:
    observed = evaluate(
        timeFilterActive=True,
        untimedExclusion={
            "status": "available",
            "count": 8,
            "split_status": "available",
            "absent_count": 2,
            "refused_count": 5,
            "contextual_count": 1,
        },
    )
    assert observed["summary"]["reason"] == "unknown"
    assert "8 records" in observed["html"]
    assert "2 absent, 5 refused, 1 contextual" in observed["html"]
    assert "separate count does not explain" in observed["html"]


@pytest.mark.parametrize(
    "untimed",
    [
        {"status": "unavailable", "count": 9},
        {"status": "available", "count": True},
        {"status": "available", "count": -1},
        {"status": "available", "count": "9"},
    ],
)
def test_unavailable_or_invalid_untimed_counts_are_not_reported(
    untimed: dict[str, Any],
) -> None:
    observed = evaluate(timeFilterActive=True, untimedExclusion=untimed)
    assert len(observed["summary"]["facts"]) == 1
    assert observed["summary"]["reason"] == "unknown"


@pytest.mark.parametrize("active", [False, None])
def test_untimed_exclusions_require_active_time_filter(active: bool | None) -> None:
    observed = evaluate(
        timeFilterActive=active,
        untimedExclusion={"status": "available", "count": 7},
    )
    assert len(observed["summary"]["facts"]) == 1


def test_incomplete_or_conflicting_untimed_split_is_labeled_unavailable() -> None:
    observed = evaluate(
        timeFilterActive=True,
        untimedExclusion={
            "status": "available",
            "count": 7,
            "split_status": "available",
            "absent_count": 1,
            "refused_count": 1,
            "contextual_count": 1,
        },
    )
    assert "7 records" in observed["html"]
    assert "split is unavailable" in observed["html"]
    assert "1 absent" not in observed["html"]


@pytest.mark.parametrize(
    "changes",
    [
        {"pointCount": True},
        {"countryCount": -1},
        {"retainedRelationCount": "0"},
        {"polygonLayerCount": 0.5},
        {"drawnRelationCount": 1},
        {"relationViewportCount": 1},
        {"selectedScientificSignalCount": 3},
        {"selectedLayers": [None]},
        {"selectedLayers": [{}, []]},
        {"loadStatus": "ready-ish"},
        {"pointCount": 2**53},
        {"drawNodes": "false"},
        {"drawEdges": None},
        {"drawNodes": 0},
        {
            "drawEdges": False,
            "retainedRelationCount": 1,
            "relationViewportCount": 1,
            "drawnRelationCount": 1,
        },
    ],
)
def test_invalid_population_is_unknown_without_coercion(
    changes: dict[str, Any],
) -> None:
    observed = evaluate(**changes)
    assert observed["summary"]["reason"] == "unknown"
    assert observed["summary"]["populations"] is None
    assert "unavailable" in observed["html"]
    assert observed["unchanged"]
