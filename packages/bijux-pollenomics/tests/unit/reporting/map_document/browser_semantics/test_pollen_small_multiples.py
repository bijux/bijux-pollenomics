"""Compatible native variables share display axes without scientific aggregation."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, cast
from xml.etree import ElementTree as ET

import pytest

from bijux_pollenomics.reporting.map_document import template

from .chronology import test_age_depth_diagram as age
from .support import check_javascript_syntax, run_node_json, template_block
from .test_pollen_diagram import add_row, decoded, set_cell


@pytest.fixture
def tabs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    return decoded(
        cast(dict[str, Any], age.decoded(age.projected_tabs(tmp_path, monkeypatch)))
    )


def script() -> str:
    assets = Path(template.__file__).parent / "assets"
    return (
        template_block("function escapeHtml", "function normalizedMediaLinks")
        + template_block(
            "function detailTableShape", "const DETAIL_TABLE_INTERNAL_KEYS"
        )
        + "\n".join(
            (assets / name).read_text()
            for name in (
                "chronology-diagram.js",
                "pollen-diagram.js",
                "pollen-age-axis.js",
                "pollen-small-multiples.js",
            )
        )
    )


def observe(
    tabs: dict[str, Any], selected: str = "null", anchor: str = "key"
) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        run_node_json(
            script()
            + "const tabs="
            + json.dumps(tabs)
            + ";const original=JSON.stringify(tabs);const native=pollenDepthDiagramData(tabs);const key=native.groups.find(g=>g.identity[2]==='neotoma:variable:50')?.key;const options=pollenAgeAxisData(tabs,key).options;const selected="
            + selected
            + ";console.log(JSON.stringify({data:pollenSmallMultiplesData(tabs,"
            + anchor
            + ",selected),html:renderPollenSmallMultiples(tabs,"
            + anchor
            + ",selected),unchanged:original===JSON.stringify(tabs)}));"
        ),
    )


def add_variable(tabs: dict[str, Any], number: int = 51, /, **changes: object) -> None:
    table = tabs["pollen_composition"]
    add_row(
        table["variables"],
        variable_id=f"neotoma:variable:{number}",
        source_taxon_id=number,
        source_reported_name=f"Native taxon {number}",
    )
    add_row(
        table,
        observation_id=f"observation-{number}",
        variable_id=f"neotoma:variable:{number}",
        source_taxon_id=number,
        source_value=9,
        **changes,
    )


def figures(output: dict[str, Any]) -> list[ET.Element]:
    return ET.fromstring(output["html"]).findall("article")


def test_actual_producer_decoder_and_two_native_taxa_share_axes(
    tabs: dict[str, Any],
) -> None:
    add_variable(tabs)
    original = deepcopy(tabs)
    output = observe(tabs)
    assert output["unchanged"] is True and tabs == original
    assert output["data"]["status"] == "depth"
    assert len(output["data"]["panels"]) == 2
    panels = figures(output)
    assert len(panels) == 2
    assert "Selected anchor:" in " ".join(panels[0].itertext())
    assert "Selected anchor:" not in " ".join(panels[1].itertext())
    marks = [panel.find(".//svg/g/circle") for panel in panels]
    assert all(mark is not None for mark in marks)
    assert [mark.get("cx") for mark in marks if mark is not None] == ["85", "585"]
    assert [mark.get("cy") for mark in marks if mark is not None] == ["135", "135"]
    tick_sets = [
        [node.text for node in panel.findall(".//svg/text")] for panel in panels
    ]
    assert tick_sets[0] == tick_sets[1]
    titles = [panel.find(".//svg/title") for panel in panels]
    assert len({title.get("id") for title in titles if title is not None}) == 2
    scroll = panels[0].find(".//div")
    assert scroll is not None and scroll.get("class") == "source-diagram-plot"
    assert scroll.get("tabindex") == "0" and scroll.get("role") == "region"
    assert "No values are summed" in output["html"]
    assert "source depth (unit not supplied)" in output["html"].lower()


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_unit", "percent"),
        ("source_context", "different context"),
        ("source_element", "other element"),
        ("source_element_type", "other type"),
        ("source_denominator", 20),
        ("denominator_status", "different status"),
        ("unit_family", "other family"),
    ],
)
def test_incompatible_native_semantics_are_not_combined(
    tabs: dict[str, Any],
    field: str,
    value: object,
) -> None:
    add_variable(tabs, **{field: value})
    output = observe(tabs)
    assert len(output["data"]["panels"]) == 1
    assert output["data"]["incompatibleGroupCount"] == 1
    assert "1 incompatible source groups are kept separate" in output["html"]


@pytest.mark.parametrize("field", ["collection_unit_id", "dataset_id"])
def test_other_sample_source_partitions_are_kept_separate(
    tabs: dict[str, Any], field: str
) -> None:
    add_row(tabs["samples"]["samples"], sample_id="other-sample", **{field: "other"})
    add_variable(tabs, sample_id="other-sample")
    assert observe(tabs)["data"]["incompatibleGroupCount"] == 1


def test_denominator_literals_of_different_json_types_remain_separate(
    tabs: dict[str, Any],
) -> None:
    set_cell(tabs["pollen_composition"], "source_denominator", 20)
    add_variable(tabs, source_denominator="20")
    assert observe(tabs)["data"]["incompatibleGroupCount"] == 1


def test_explicit_anchor_is_first_highlighted_and_never_inferred(
    tabs: dict[str, Any],
) -> None:
    add_variable(tabs)
    output = observe(
        tabs, anchor="native.groups.find(g=>g.identity[2]==='neotoma:variable:51').key"
    )
    assert output["data"]["panels"][0]["group"]["identity"][2] == "neotoma:variable:51"
    assert "Selected anchor: Native taxon 51" in output["html"]
    stale = observe(tabs, anchor="'unknown'")
    assert stale["data"]["status"] == "unavailable"
    assert not figures(stale)


@pytest.mark.parametrize("posture", ["comparable", "refused", "context_only"])
def test_explicit_age_points_and_intervals_retain_source_posture(
    tabs: dict[str, Any], posture: str
) -> None:
    add_variable(tabs)
    selected = f"options.find(o=>o.identity[6]==='{posture}').key"
    output = observe(tabs, selected)
    assert output["data"]["status"] == "age"
    assert len(figures(output)) == 2
    for panel in figures(output):
        group = panel.find(".//svg/g")
        assert group is not None
        if posture == "context_only":
            assert group.find("circle") is None
            span = group.find("path")
            assert span is not None and span.get("stroke-dasharray") == "7 4"
            assert "-10, 20" in str(group.get("aria-label"))
        else:
            mark = group.find("rect" if posture == "refused" else "path")
            assert mark is not None
            if posture == "refused":
                assert mark.get("stroke-dasharray") == "2 3"
                assert "source refusal <img" in str(group.get("aria-label"))
    assert "not confidence intervals" in output["html"]
    assert output["unchanged"] is True


def test_missing_sample_age_is_omitted_without_zero_or_default_fallback(
    tabs: dict[str, Any],
) -> None:
    add_row(tabs["samples"]["samples"], sample_id="other-sample", source_depth=90)
    add_variable(tabs, sample_id="other-sample")
    set_cell(
        tabs["pollen_composition"]["variables"], "source_reported_name", "Triticum", 1
    )
    output = observe(tabs, "options[0].key")
    panels = output["data"]["panels"]
    assert sum(len(panel["alignment"]["rows"]) for panel in panels) == 1
    assert panels[1]["alignment"]["omitted"] == {"sample_age_assignment_unavailable": 1}
    assert "sample has no assignment" in output["html"]
    assert "1 aligned observations" in output["html"]
    empty_panel = ET.fromstring(output["html"]).findall("article")[1]
    assert "neotoma:variable:51" in " ".join(empty_panel.itertext())


def test_all_ambiguous_assignments_report_no_drawable_observations(
    tabs: dict[str, Any],
) -> None:
    claim = tabs["chronology"]
    add_row(claim, chronology_claim_id="duplicate-assignment")
    output = observe(tabs, "options.find(o=>o.identity[6]==='comparable').key")
    assert not figures(output)
    assert "multiple assignments" in output["html"]
    assert "No observations have an unambiguous assignment" in output["html"]


def test_zero_and_coincident_observations_are_not_summed(tabs: dict[str, Any]) -> None:
    set_cell(tabs["pollen_composition"], "source_value", 0)
    add_row(tabs["pollen_composition"], observation_id="other", source_value=0)
    output = observe(tabs)
    marks = figures(output)[0].findall(".//svg/g")
    assert len(marks) == 2
    assert [
        row["value"] for row in output["data"]["panels"][0]["alignment"]["rows"]
    ] == [0, 0]


def test_mark_and_panel_limits_disclose_full_population_and_keep_full_domain(
    tabs: dict[str, Any],
) -> None:
    table = tabs["pollen_composition"]
    for number in range(51, 60):
        add_variable(tabs, number)
    for number in range(500):
        add_row(table, observation_id=f"anchor-{number:04}", source_value=number)
    set_cell(table, "source_value", 9999, 9)
    output = observe(tabs)
    panels = figures(output)
    assert len(panels) == 8 and len(output["data"]["panels"]) == 10
    assert sum(len(panel.findall(".//svg/g")) for panel in panels) == 507
    assert "8 of 10 compatible panels" in output["html"]
    assert "507 of 510 aligned observations" in output["html"]
    assert all(
        "9999" in [node.text for node in panel.findall(".//svg/text")]
        for panel in panels
    )
    assert output["unchanged"] is True


def test_source_labels_and_refusals_are_escaped(tabs: dict[str, Any]) -> None:
    set_cell(
        tabs["pollen_composition"]["variables"],
        "source_reported_name",
        '<img src="x"/>',
    )
    output = observe(tabs, "options.find(o=>o.identity[6]==='refused').key")
    document = ET.fromstring(output["html"])
    assert not document.findall(".//img")
    assert '<img src="x"/>' in " ".join(document.itertext())
    assert output["unchanged"] is True


def test_unknown_age_selection_does_not_fall_back_to_depth(
    tabs: dict[str, Any],
) -> None:
    output = observe(tabs, "'unknown-age'")
    assert output["data"]["status"] == "unavailable" and not figures(output)


def test_packaged_javascript_syntax(tmp_path: Path) -> None:
    check_javascript_syntax(script(), tmp_path / "pollen-panels.js")


@pytest.mark.parametrize("group_count", [1, 12])
@pytest.mark.parametrize("age_mode", [False, True])
def test_table_qualification_is_constant_with_more_panels_and_alignment_is_unchanged(
    tabs: dict[str, Any], group_count: int, age_mode: bool
) -> None:
    for number in range(51, 50 + group_count):
        add_variable(tabs, number)
    result = run_node_json(
        script()
        + "const tabs="
        + json.dumps(tabs)
        + ";const key=pollenObservationDiagramData(tabs).groups[0].key;const ageKey="
        + ("pollenAgeAxisData(tabs,key).options[0].key" if age_mode else "null")
        + """;
const calls={native:0,ages:0,nativeTables:0,ageTables:0};
const native=pollenObservationDiagramData, ages=sourceAgeAssignmentData;
const nativeTables=pollenDepthTableRows, ageTables=ageDepthTableRows;
pollenObservationDiagramData=(...args)=>{calls.native++;return native(...args);};
sourceAgeAssignmentData=(...args)=>{calls.ages++;return ages(...args);};
pollenDepthTableRows=(...args)=>{calls.nativeTables++;return nativeTables(...args);};
ageDepthTableRows=(...args)=>{calls.ageTables++;return ageTables(...args);};
const result=pollenSmallMultiplesData(tabs,key,ageKey), measured={...calls};
const unchanged=result.panels.every(panel=>JSON.stringify(panel.alignment)===
  JSON.stringify(pollenAgeAxisData(tabs,panel.group.key,ageKey)));
console.log(JSON.stringify({calls:measured,unchanged,count:result.panels.length}));
"""
    )
    assert result == {
        "calls": {"native": 1, "ages": 1, "nativeTables": 3, "ageTables": 2},
        "unchanged": True,
        "count": group_count,
    }
