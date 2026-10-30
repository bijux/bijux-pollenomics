"""Map focus highlights exact source observations without changing their meaning."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, cast
from xml.etree import ElementTree as ET

import pytest

from ..support import check_javascript_syntax, run_node_json
from .test_pollen_diagram import add_row, set_cell
from .test_pollen_small_multiples import add_variable, script
from .test_pollen_small_multiples import tabs as tabs


def evaluate(tabs: dict[str, Any], expression: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        run_node_json(
            script()
            + "const tabs="
            + json.dumps(tabs)
            + ";const original=JSON.stringify(tabs);const native=pollenDepthDiagramData(tabs);"
            + "const group=native.groups.find(g=>g.identity[2]==='neotoma:variable:50'),key=group.key;"
            + "const id=group.rows[0].observation.observation_id;const options=pollenAgeAxisData(tabs,key).options;const value="
            + expression
            + ";console.log(JSON.stringify({value,unchanged:original===JSON.stringify(tabs)}));"
        ),
    )


def selected_marks(html: str) -> list[ET.Element]:
    return ET.fromstring(html).findall('.//g[@data-selected-observation="true"]')


def test_depth_highlight_is_exact_identity_and_keeps_original_circle(
    tabs: dict[str, Any],
) -> None:
    add_row(tabs["pollen_composition"], observation_id="another-at-same-sample")
    original = deepcopy(tabs)
    output = evaluate(
        tabs,
        "renderPollenDepthDiagram(tabs,key,undefined,{selectedObservationIds:[id,id+'-other']})",
    )
    assert output["unchanged"] and tabs == original
    marks = selected_marks(output["value"])
    assert len(marks) == 1
    assert "Selected map-signal observation;" in str(marks[0].get("aria-label"))
    assert marks[0].find("title").text == marks[0].get("aria-label")  # type: ignore[union-attr]
    assert marks[0].find("circle").get("r") == "4"  # type: ignore[union-attr]
    box = marks[0].find("rect")
    assert box is not None and box.get("fill") == "none"
    assert box.get("stroke-dasharray") == "3 2"
    assert len(ET.fromstring(output["value"]).findall(".//svg/g/circle")) == 2
    assert "1 of 1 aligned selected map-signal observations drawn" in output["value"]


@pytest.mark.parametrize("posture", ["comparable", "context_only", "refused"])
def test_age_highlight_preserves_point_interval_and_refusal_glyphs(
    tabs: dict[str, Any], posture: str
) -> None:
    expression = (
        "(()=>{const age=options.find(o=>o.identity[6]==="
        + json.dumps(posture)
        + ").key;return {plain:renderPollenAgeDiagram(tabs,key,age),selected:renderPollenAgeDiagram(tabs,key,age,true,[id])};})()"
    )
    output = evaluate(tabs, expression)
    plain = ET.fromstring(output["value"]["plain"]).find(".//svg/g")
    selected = selected_marks(output["value"]["selected"])
    assert plain is not None and len(selected) == 1
    original_glyphs = [ET.tostring(child) for child in plain if child.tag != "title"]
    # The selection outline surrounds the unchanged raw point/span marks.
    highlighted_glyphs = list(selected[0])[2:]
    assert [ET.tostring(child) for child in highlighted_glyphs] == original_glyphs
    assert output["unchanged"]
    if posture == "context_only":
        assert selected[0].find("circle") is None
        assert "reported age point not supplied" in str(selected[0].get("aria-label"))
    if posture == "refused":
        assert "source-refused" in output["value"]["selected"]
        assert "source posture refused" in str(selected[0].get("aria-label"))


@pytest.mark.parametrize("age_mode", [False, True])
def test_compatible_panels_highlight_only_passed_observation_ids(
    tabs: dict[str, Any], age_mode: bool
) -> None:
    add_variable(tabs)
    selected_age = "options[0].key" if age_mode else "null"
    output = evaluate(
        tabs,
        "renderPollenSmallMultiples(tabs,key," + selected_age + ",[id])",
    )
    assert len(ET.fromstring(output["value"]).findall("article")) == 2
    assert len(selected_marks(output["value"])) == 1
    assert output["unchanged"]


def test_explicit_anchor_has_placeholder_and_no_lexical_first_figure(
    tabs: dict[str, Any],
) -> None:
    add_variable(tabs)
    output = evaluate(
        tabs,
        "(()=>{let called=0;const html=renderPollenDepthDiagram(tabs,null,()=>{called++;return 'unexpected';},{requireExplicitAnchor:true,selectedObservationIds:[id]});return {html,called};})()",
    )
    html = output["value"]["html"]
    assert output["value"]["called"] == 0 and not ET.fromstring(html).findall(".//svg")
    options = ET.fromstring(html).findall("select/option")
    assert len(options) == 3
    assert options[0].get("value") == "" and options[0].get("selected") == "selected"
    assert all(option.get("selected") is None for option in options[1:])
    assert "No display anchor is inferred" in html and output["unchanged"]
    chosen = evaluate(
        tabs,
        "renderPollenDepthDiagram(tabs,key,undefined,{requireExplicitAnchor:true,selectedObservationIds:[id]})",
    )
    assert len(selected_marks(chosen["value"])) == 1


def test_custom_composer_receives_exact_ids_and_legacy_defaults_match(
    tabs: dict[str, Any],
) -> None:
    output = evaluate(
        tabs,
        "(()=>{let received;renderPollenDepthDiagram(tabs,key,(g,ids)=>{received={key:g.key,ids};return '';},{selectedObservationIds:[id]});return {received,key,id,same:renderPollenDepthDiagram(tabs,key)===renderPollenDepthDiagram(tabs,key,undefined,{requireExplicitAnchor:false,selectedObservationIds:[]})};})()",
    )["value"]
    assert output["same"]
    assert output["received"] == {"key": output["key"], "ids": [output["id"]]}


def test_selected_ids_cannot_rescue_ambiguous_age_assignment(
    tabs: dict[str, Any],
) -> None:
    claim = tabs["chronology"]["records"][0]
    add_row(tabs["chronology"], chronology_claim_id="duplicate-claim")
    # add_row copies the first source assignment, retaining its same group/sample.
    assert claim != tabs["chronology"]["records"][-1]
    output = evaluate(
        tabs,
        "renderPollenAgeDiagram(tabs,key,options.find(o=>o.identity[6]==='comparable').key,true,[id])",
    )
    assert not selected_marks(output["value"])
    assert "No observations have one usable source age assignment" in output["value"]
    assert output["unchanged"]


def test_selection_beyond_display_cap_is_counted_without_a_fabricated_mark(
    tabs: dict[str, Any],
) -> None:
    table = tabs["pollen_composition"]
    for index in range(500):
        add_row(table, observation_id=f"z-{index:04}")
    output = evaluate(
        tabs,
        "renderPollenDepthDiagram(tabs,key,undefined,{selectedObservationIds:['z-0499']})",
    )
    assert not selected_marks(output["value"])
    assert "500 of 501 individual source observations drawn" in output["value"]
    assert "0 of 1 aligned selected map-signal observations drawn" in output["value"]
    assert output["unchanged"]


def test_selected_source_identity_is_escaped_and_javascript_parses(
    tabs: dict[str, Any], tmp_path: Path
) -> None:
    set_cell(tabs["pollen_composition"], "observation_id", '<img src="x"/>')
    output = evaluate(
        tabs,
        "renderPollenDepthDiagram(tabs,key,undefined,{selectedObservationIds:[id]})",
    )
    assert not ET.fromstring(output["value"]).findall(".//img")
    assert '<img src="x"/>' in str(selected_marks(output["value"])[0].get("aria-label"))
    assert output["unchanged"]
    check_javascript_syntax(script(), tmp_path / "selected-observations.js")
