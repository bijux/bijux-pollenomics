"""Native observation values retain exact source joins, units and missingness."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, cast
from xml.etree import ElementTree as ET

import pytest

from bijux_pollenomics.reporting.map_document import template
from bijux_pollenomics.reporting.map_document.evidence_projection import neotoma

from ..evidence_projection.fixtures.neotoma import _neotoma_fixture
from .chronology.test_age_depth_diagram import diagram_script as drawer_script
from .chronology.test_age_depth_diagram import render_drawer
from .support import run_node_json, template_block


@pytest.fixture
def projected_tabs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Build the actual compact transport from the existing native-source fixture."""
    _neotoma_fixture(tmp_path, monkeypatch)
    records, _, _ = neotoma._project_neotoma(
        tmp_path, {"features": [{"evidence_row_id": "10"}]}
    )
    return cast(dict[str, Any], records[0]["tabs"])


def diagram_script() -> str:
    """Run the packaged component with the actual production prefix decoder."""
    return (
        template_block("function escapeHtml", "function normalizedMediaLinks")
        + template_block(
            "function detailTableShape", "const DETAIL_TABLE_INTERNAL_KEYS"
        )
        + (Path(template.__file__).parent / "assets/pollen-diagram.js").read_text()
    )


def observe(tabs: dict[str, Any], key: str | None = None) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        run_node_json(
            diagram_script()
            + "const tabs="
            + json.dumps(tabs)
            + ";const original=JSON.stringify(tabs);const key="
            + json.dumps(key)
            + ";console.log(JSON.stringify({data:pollenDepthDiagramData(tabs),html:renderPollenDepthDiagram(tabs,key),unchanged:original===JSON.stringify(tabs)}));"
        ),
    )


def decoded(tabs: dict[str, Any]) -> dict[str, Any]:
    """Use real transport decoding before controlled semantic mutations."""
    return cast(
        dict[str, Any],
        run_node_json(
            diagram_script()
            + "const tabs="
            + json.dumps(tabs)
            + ";for(const table of [tabs.samples.samples,tabs.pollen_composition,tabs.pollen_composition.variables]){table.records=table.records.map(row=>{const record=decodeDetailTableRow(table,row);return table.fields.map(field=>record[field]);});delete table.identifier_prefixes;delete table.column_dictionaries;}console.log(JSON.stringify(tabs));"
        ),
    )


def set_cell(table: dict[str, Any], field: str, value: object, index: int = 0) -> None:
    table["records"][index][table["fields"].index(field)] = value


def add_row(table: dict[str, Any], **changes: object) -> None:
    row = deepcopy(table["records"][0])
    for field, value in changes.items():
        row[table["fields"].index(field)] = value
    table["records"].append(row)
    table["record_count"] = len(table["records"])


def test_actual_producer_decoder_and_native_svg_keep_source_ids_and_limits(
    projected_tabs: dict[str, Any],
) -> None:
    original = deepcopy(projected_tabs)
    output = observe(projected_tabs)
    data = output["data"]
    assert output["unchanged"] is True and projected_tabs == original
    assert data["status"] == "available" and data["total"] == 1
    assert len(data["groups"]) == 1 and data["omitted"] == {}
    group = data["groups"][0]
    assert group["identity"][:5] == [
        "neotoma:collection-unit:20",
        "neotoma:dataset:30",
        "neotoma:variable:50",
        50,
        "NISP",
    ]
    row = group["rows"][0]
    assert row["observation"]["observation_id"] == "neotoma:observation:40:50:1"
    assert row["sample"] == "neotoma:sample:40" and row["depth"] == 12
    assert row["value"] == 3 and group["identity"][8:10] == [
        None,
        "not_provided_by_source",
    ]
    document = ET.fromstring(output["html"])
    svg = document.find(".//svg")
    assert svg is not None and svg.get("role") == "img"
    assert svg.find("title") is not None and svg.find("desc") is not None
    assert len(svg.findall("g")) == 1
    mark = svg.find("g")
    assert mark is not None and mark.get("tabindex") == "0"
    assert "neotoma:observation:40:50:1" in str(mark.get("aria-label"))
    label = document.find("label")
    select = document.find("select")
    assert label is not None and select is not None
    assert (
        label.get("for") == select.get("id")
        and select.get("data-pollen-depth-group") == "true"
    )
    text = " ".join(document.itertext())
    assert "Reported value (NISP)" in text
    assert "Source depth (unit not supplied)" in text and "12 cm" not in text
    assert "No counts are summed or converted to percentages" in text
    assert "no ecological classification is accepted here" in text
    assert "1 of 1 individual source observations drawn" in text


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("source_value", None, "source_value_not_numeric"),
        ("source_value", "0", "source_value_not_numeric"),
        ("source_value", True, "source_value_not_numeric"),
        ("source_value", float("nan"), "source_value_not_numeric"),
        ("source_value", float("inf"), "source_value_not_numeric"),
        ("source_value", -1, "source_count_not_nonnegative_exact_integer"),
        ("source_value", 1.5, "source_count_not_nonnegative_exact_integer"),
        ("source_value", 2**53, "source_count_not_nonnegative_exact_integer"),
        ("source_unit", None, "source_unit_unavailable"),
        ("source_unit", " ", "source_unit_unavailable"),
        ("detection_status", "source_null", "source_value_not_reported"),
        ("detection_status", "not_provided_by_source", "source_value_not_reported"),
        ("detection_status", "refused", "source_value_not_reported"),
        ("source_taxon_id", 999, "source_taxon_identity_mismatch"),
        ("sample_id", "unknown", "sample_identity_unavailable"),
        ("variable_id", "unknown", "variable_identity_unavailable"),
    ],
)
def test_missing_refused_or_invalid_values_are_not_zero(
    projected_tabs: dict[str, Any], field: str, value: object, reason: str
) -> None:
    tabs = decoded(projected_tabs)
    set_cell(tabs["pollen_composition"], field, value)
    output = observe(tabs)
    assert output["data"]["total"] == 1 and output["data"]["groups"] == []
    assert output["data"]["omitted"] == {reason: 1}
    assert output["unchanged"] is True and "<svg" not in output["html"]
    assert reason not in output["html"] and "Not charted:" in output["html"]


def test_zero_and_distinct_coincident_observations_are_not_summed(
    projected_tabs: dict[str, Any],
) -> None:
    tabs = decoded(projected_tabs)
    table = tabs["pollen_composition"]
    set_cell(table, "source_value", 0)
    add_row(table, observation_id="neotoma:observation:40:50:2")
    set_cell(tabs["samples"]["samples"], "source_depth", 0)
    output = observe(tabs)
    rows = output["data"]["groups"][0]["rows"]
    assert len(rows) == 2 and [row["value"] for row in rows] == [0, 0]
    assert [row["depth"] for row in rows] == [0, 0]
    svg = ET.fromstring(output["html"]).find(".//svg")
    assert svg is not None and len(svg.findall("g")) == 2
    marks = svg.findall("g/circle")
    assert marks[0].attrib == marks[1].attrib
    assert output["unchanged"] is True


@pytest.mark.parametrize("table_name", ["observations", "samples", "variables"])
def test_duplicate_native_identities_are_ambiguous(
    projected_tabs: dict[str, Any], table_name: str
) -> None:
    tabs = decoded(projected_tabs)
    table = {
        "observations": tabs["pollen_composition"],
        "samples": tabs["samples"]["samples"],
        "variables": tabs["pollen_composition"]["variables"],
    }[table_name]
    changes = {"source_value": 999} if table_name == "observations" else {}
    add_row(table, **changes)
    result = observe(tabs)["data"]
    assert result["groups"] == []
    reason = {
        "observations": "ambiguous_observation_identity",
        "samples": "sample_identity_unavailable",
        "variables": "variable_identity_unavailable",
    }[table_name]
    assert result["omitted"] == {reason: 2 if table_name == "observations" else 1}


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_unit", "%"),
        ("source_context", {"preparation": "native"}),
        ("source_element", "spore"),
        ("source_element_type", "fragment"),
        ("source_denominator", 20),
        ("denominator_status", "native_other"),
        ("unit_family", "native_other"),
    ],
)
def test_literal_units_context_and_denominators_never_merge(
    projected_tabs: dict[str, Any], field: str, value: object
) -> None:
    tabs = decoded(projected_tabs)
    add_row(
        tabs["pollen_composition"],
        observation_id="neotoma:observation:40:50:2",
        **{field: value},
    )
    output = observe(tabs)
    assert len(output["data"]["groups"]) == 2
    assert [group["rows"][0]["value"] for group in output["data"]["groups"]] == [3, 3]
    labels = [
        option.text for option in ET.fromstring(output["html"]).findall("select/option")
    ]
    assert len(set(labels)) == 2
    selected = output["data"]["groups"][1]["key"]
    option = ET.fromstring(observe(tabs, selected)["html"]).find(
        "select/option[@selected]"
    )
    assert option is not None and option.get("value") == selected
    assert (
        "the selected native source group is unavailable"
        in observe(tabs, "foreign")["html"]
    )


def test_datasets_and_collections_with_same_native_variable_stay_separate(
    projected_tabs: dict[str, Any],
) -> None:
    tabs = decoded(projected_tabs)
    add_row(
        tabs["samples"]["samples"],
        sample_id="neotoma:sample:41",
        collection_unit_id="neotoma:collection-unit:21",
        dataset_id="neotoma:dataset:31",
    )
    add_row(
        tabs["pollen_composition"],
        observation_id="neotoma:observation:41:50:1",
        sample_id="neotoma:sample:41",
    )
    groups = observe(tabs)["data"]["groups"]
    assert len(groups) == 2
    assert {tuple(group["identity"][:2]) for group in groups} == {
        ("neotoma:collection-unit:20", "neotoma:dataset:30"),
        ("neotoma:collection-unit:21", "neotoma:dataset:31"),
    }


def test_nonpollen_semantics_escape_and_other_native_units_keep_signed_values(
    projected_tabs: dict[str, Any],
) -> None:
    tabs = decoded(projected_tabs)
    table = tabs["pollen_composition"]
    set_cell(table, "source_value", -1.25)
    set_cell(table, "source_unit", "native laboratory unit")
    set_cell(table, "unit_family", "other")
    set_cell(table, "source_element", "spore")
    set_cell(table["variables"], "source_reported_name", '<img src=x onerror="bad()">')
    set_cell(table["variables"], "source_semantics", [{"source_element": "spore"}])
    result = observe(tabs)
    assert result["data"]["groups"][0]["rows"][0]["value"] == -1.25
    document = ET.fromstring(result["html"])
    assert document.find(".//img") is None
    assert "spore" in " ".join(document.itertext())
    assert "&lt;img" in result["html"] and result["unchanged"] is True


@pytest.mark.parametrize("value", [None, "12", True])
def test_depth_is_not_parsed_or_imputed(
    projected_tabs: dict[str, Any], value: object
) -> None:
    tabs = decoded(projected_tabs)
    set_cell(tabs["samples"]["samples"], "source_depth", value)
    result = observe(tabs)["data"]
    assert result["omitted"] == {"source_depth_not_numeric": 1} and not result["groups"]


def test_mark_limit_keeps_full_accounting_and_extrema(
    projected_tabs: dict[str, Any],
) -> None:
    tabs = decoded(projected_tabs)
    table = tabs["pollen_composition"]
    for index in range(1, 501):
        add_row(
            table,
            observation_id=f"neotoma:observation:40:50:{index + 1}",
            source_value=index,
        )
    output = observe(tabs)
    assert len(output["data"]["groups"][0]["rows"]) == output["data"]["total"] == 501
    svg = ET.fromstring(output["html"]).find(".//svg")
    assert svg is not None and len(svg.findall("g")) == 500
    assert "500 of 501 individual source observations drawn" in output["html"]
    assert ">500</text>" in output["html"] and output["unchanged"] is True


@pytest.mark.parametrize("kind", ["source", "malformed", "duplicate_fields"])
def test_unavailable_tables_refuse_without_changing_source(
    projected_tabs: dict[str, Any], kind: str
) -> None:
    tabs = deepcopy(projected_tabs)
    if kind == "source":
        tabs["overview"]["source_family"] = "sead"
    elif kind == "malformed":
        tabs["pollen_composition"]["records"][0].pop()
    else:
        tabs["pollen_composition"]["fields"].append("sample_id")
    output = observe(tabs)
    assert output["data"]["status"] == "unavailable" and "<svg" not in output["html"]
    assert output["unchanged"] is True
    assert output["data"]["reason"] not in output["html"]


def test_mounted_pollen_drawer_keeps_complete_tables_and_other_tabs_separate(
    projected_tabs: dict[str, Any],
) -> None:
    output = render_drawer(projected_tabs, active="pollen_composition")
    assert 'id="native-value-depth-title"' in str(output["html"])
    assert "Showing 1–1 of 1" in str(output["html"])
    assert "neotoma:observation:40:50:1" in str(output["html"])
    assert (
        output["label"] == "focus-tab-pollen_composition"
        and output["unchanged"] is True
    )
    for active in ("overview", "samples", "chronology"):
        other = render_drawer(projected_tabs, active=active)
        assert 'id="native-value-depth-title"' not in str(other["html"])
        assert other["unchanged"] is True


def test_actual_drawer_group_change_survives_pagination_tabs_and_resets_per_record(
    projected_tabs: dict[str, Any],
) -> None:
    tabs = decoded(projected_tabs)
    for index in range(1, 27):
        add_row(
            tabs["pollen_composition"],
            observation_id=f"neotoma:observation:40:50:{index + 1}",
            source_context="alternative" if index == 1 else None,
        )
    output = run_node_json(
        drawer_script()
        + "const tabs="
        + json.dumps(tabs)
        + """;
const before=JSON.stringify(tabs), callbacks={}, detailTablePages=new Map(), DETAIL_TABLE_PAGE_SIZE=25;
let focusedSelect=0, currentSelect;
const focusTabs={innerHTML:'',contains(){return false;},querySelectorAll(){return ['overview','pollen_composition'].map(key=>({dataset:{focusTab:key},addEventListener(event,callback){callbacks[key]=callback;}}));}};
const focusDetail={innerHTML:'',dataset:{},contains(){return false;},setAttribute(k,v){this[k]=v;},querySelectorAll(selector){
  if(selector==='[data-pollen-depth-group]'){
    if(activeFocusTab!=='pollen_composition')return [];
    currentSelect={value:'',focus(){focusedSelect++;},addEventListener(event,callback){callbacks.change=callback;}};
    return [currentSelect];
  }
  return [{dataset:{detailTablePage:'pollen_composition',pageDirection:'next'},disabled:false,addEventListener(event,callback){callbacks.next=callback;}}];
}};
const focusExportButton={},focusCopyLinkButton={},focusExportStatus={},document={activeElement:null};
function sourcePollenExportAvailable(){return false;}
function syncHashState(){}
let activeFocusTab='pollen_composition',focusState={kind:'point',detailTabs:tabs};
const keys=pollenDepthDiagramData(tabs).groups.map(group=>group.key);
renderFocusDetail();const initial=focusDetail.innerHTML;
currentSelect.value=keys[1];callbacks.change();const changed=focusDetail.innerHTML;
renderFocusDetail();const rerendered=focusDetail.innerHTML;
callbacks.next();const paginated=focusDetail.innerHTML;
callbacks.overview();const overview=focusDetail.innerHTML;
callbacks.pollen_composition();const returned=focusDetail.innerHTML;
focusState={kind:'point',detailTabs:JSON.parse(JSON.stringify(tabs))};
renderFocusDetail();const newRecord=focusDetail.innerHTML;
currentSelect.value='foreign';callbacks.change();const invalidChoice=focusDetail.innerHTML;
console.log(JSON.stringify({keys,initial,changed,rerendered,paginated,overview,returned,newRecord,invalidChoice,focusedSelect,unchanged:before===JSON.stringify(tabs)}));
"""
    )
    from html import unescape
    import re

    def selected(html: str) -> str:
        match = re.search(r'<option value="([^"]*)" selected="selected">', html)
        assert match is not None
        return unescape(match.group(1))

    assert selected(output["initial"]) == output["keys"][0]
    for state in ("changed", "rerendered", "paginated", "returned"):
        assert selected(output[state]) == output["keys"][1]
    assert "Showing 26–27 of 27" in output["paginated"]
    assert 'id="native-value-depth-title"' not in output["overview"]
    assert (
        selected(output["newRecord"])
        == selected(output["invalidChoice"])
        == output["keys"][0]
    )
    assert output["focusedSelect"] == 2 and output["unchanged"] is True
