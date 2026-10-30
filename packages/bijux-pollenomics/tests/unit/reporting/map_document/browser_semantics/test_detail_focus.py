from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import cast
from xml.etree import ElementTree as ET

import pytest

from bijux_pollenomics.reporting.geography import build_published_geography_plan
from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_publication import resolve_map_scope_policy

from ....analysis.classification.test_reviewed_context import _crop_indicator_payload
from ...atlas.static_assets.fixtures.scientific_evidence import (
    build_detail_records,
    build_scientific_point_layers,
    build_scientific_signals,
)
from .support import run_node_json, template_block


def _render_reviewed_context_drawer(payload: dict[str, object]) -> dict[str, object]:
    """Exercise the actual focused classification tab with only DOM sinks stubbed."""
    source = (
        template_block("const DETAIL_TAB_DEFINITIONS", "const DEFAULT_COUNTRIES")
        + template_block("function escapeHtml", "function normalizedMediaLinks")
        + template_block("function detailTableShape", "function renderFocusCard")
    )
    return cast(
        dict[str, object],
        run_node_json(
            source
            + """
const focusTabs={innerHTML:'',contains(){return false;},querySelectorAll(){return [];}};
const focusDetail={innerHTML:'',dataset:{},contains(){return false;},setAttribute(key,value){this[key]=value;},querySelectorAll(){return [];}};
const focusExportButton={},focusCopyLinkButton={},focusExportStatus={};
const document={activeElement:null};
const detailTablePages=new Map();
const DETAIL_TABLE_PAGE_SIZE=25;
let activeFocusTab='classification';
function sourcePollenExportAvailable(){return false;}
function syncHashState(){}
const payload="""
            + json.dumps(payload)
            + """;
const original=JSON.stringify(payload);
const focusState={kind:'point',detailTabs:{classification:payload}};
renderFocusDetail();
console.log(JSON.stringify({html:focusDetail.innerHTML,tabs:focusTabs.innerHTML,labelledBy:focusDetail['aria-labelledby'],status:focusDetail.dataset.detailStatus,payloadUnchanged:original===JSON.stringify(payload)}));
"""
        ),
    )


def test_reviewed_crop_and_indicator_export_renders_distinct_context_counts() -> None:
    payload = _crop_indicator_payload()
    original = deepcopy(payload)
    # This is the real producer's JSON export, not a hand-built browser summary.
    observed = _render_reviewed_context_drawer(json.loads(json.dumps(payload)))
    document = ET.fromstring("<section>" + str(observed["html"]) + "</section>")
    table = document.find(".//table")
    assert table is not None
    assert table.findtext("caption") == "Reviewed crop and indicator context"
    assert [node.get("scope") for node in table.findall("thead/tr/th")] == ["col"] * 3
    rows = table.findall("tbody/tr")
    assert [(row.findtext("th"), row.findtext("td")) for row in rows] == [
        ("Direct crop taxon evidence", "1"),
        ("Qualified crop-type evidence", "1"),
        ("Anthropogenic or land-use indicator", "1"),
        ("Pastoral-associated indicator", "1"),
        ("Ruderal or disturbance-associated indicator", "0"),
    ]
    for row in rows:
        heading = row.find("th")
        assert heading is not None and heading.get("scope") == "row"
    assert [row.findall("td")[1].text for row in rows] == [
        "Pollen alone does not prove local cultivation.",
        "Pollen alone does not prove local cultivation.",
        "Pollen alone does not prove human activity.",
        "Pollen alone does not prove grazing.",
        "Pollen alone does not prove human disturbance.",
    ]
    text = " ".join(document.itertext())
    assert "Unique observations across these categories: 3." in text
    assert "Whole-pollen category observations: 3." in text
    assert "Categories overlap; do not add their counts." in text
    assert "Context review alone does not admit a pollen event or LRA input." in text
    assert "unassessed" in text and "pollen_event_admission" in text
    assert "crop_indicator_totals" not in text
    assert observed["labelledBy"] == "focus-tab-classification"
    assert 'aria-selected="true" aria-controls="focus-detail"' in str(observed["tabs"])
    assert observed["status"] == "available" and observed["payloadUnchanged"] is True
    assert payload == original


def test_reviewed_context_escapes_source_provided_label_and_limit() -> None:
    payload = _crop_indicator_payload()
    row = cast(list[dict[str, object]], payload["crop_indicator_totals"])[0]
    row["label"] = "Direct crop <em>source label</em>"
    row["unproven_claim"] = "<img src=x onerror=alert(1)>"
    document = ET.fromstring(
        "<section>"
        + str(_render_reviewed_context_drawer(payload)["html"])
        + "</section>"
    )
    assert document.find(".//em") is None and document.find(".//img") is None
    assert "Direct crop <em>source label</em>" in " ".join(document.itertext())
    assert "Pollen alone does not prove <img src=x onerror=alert(1)>." in " ".join(
        document.itertext()
    )


@pytest.mark.parametrize(
    "change",
    [
        "schema",
        "scope",
        "missing_role",
        "duplicate_role",
        "negative",
        "boolean",
        "proof",
        "union_too_small",
        "union_too_large",
        "whole_category",
        "whole_too_small",
    ],
)
def test_malformed_reviewed_context_has_no_apparent_classification_summary(
    change: str,
) -> None:
    payload = _crop_indicator_payload()
    totals = cast(list[dict[str, object]], payload["crop_indicator_totals"])
    if change == "schema":
        payload["schema_version"] = "classification-reviewed-context.v99"
    elif change == "scope":
        payload["scope"] = "admitted_pollen_event"
    elif change == "missing_role":
        totals.pop()
    elif change == "duplicate_role":
        totals[0]["role_id"] = totals[1]["role_id"]
    elif change == "negative":
        totals[0]["unique_observation_count"] = -1
    elif change == "boolean":
        totals[0]["unique_observation_count"] = True
    elif change == "proof":
        totals[0]["pollen_alone_proves"] = True
    elif change == "union_too_small":
        payload["crop_indicator_union_observation_count"] = 0
    elif change == "union_too_large":
        payload["crop_indicator_union_observation_count"] = 5
    elif change == "whole_too_small":
        payload["whole_pollen_category_observation_count"] = 0
    else:
        payload["whole_pollen_category_observation_count"] = None
    observed = _render_reviewed_context_drawer(payload)
    assert "reviewed_classification_context_invalid" in str(observed["html"])
    assert "<table" not in str(observed["html"])


def build_detail_focus_candidate(directory: Path) -> Path:
    """Materialize a synthetic golden record using the production atlas producer."""
    directory.mkdir(parents=True, exist_ok=True)
    layers = build_scientific_point_layers()
    details = build_detail_records()
    tabs = details[0]["tabs"]
    assert isinstance(tabs, dict)
    tabs["samples"] = {
        "record_count": 26,
        "fields": ["sample_id", "depth_cm"],
        "records": [[f"sample:{index}", index] for index in range(26)],
    }
    assets = write_static_atlas_assets(
        directory,
        slug="detail-focus",
        version="keyboard-contract",
        point_layers=layers,
        polygon_layers=[],
        detail_records=details,
        scientific_signals=build_scientific_signals(),
    )
    policy = resolve_map_scope_policy(
        next(
            scope
            for scope in build_published_geography_plan(
                ("Sweden", "Norway")
            ).regional_scopes
            if scope.key == "nordic"
        )
    )
    document = directory / "index.html"
    document.write_text(
        render_multi_country_map_html(
            "Synthetic detail keyboard contract",
            "keyboard-contract",
            "2026-09-27",
            ("Sweden", "Norway"),
            policy,
            layers,
            [],
            "./_map_assets",
            static_assets=assets,
        ),
        encoding="utf-8",
    )
    return document


def test_detail_tabs_keyboard_wrap_home_end_and_leave_tab_to_browser() -> None:
    handler = template_block(
        "focusTabs.addEventListener('keydown'", "focusPreviousButton.addEventListener"
    )
    observed = run_node_json(
        """
const DETAIL_TAB_DEFINITIONS=[['overview','Overview'],['samples','Samples'],['provenance','Provenance']];
let activeFocusTab='overview',renderCount=0,listener;
const focusTabs={addEventListener(type,callback){listener=callback;}};
function renderFocusDetail(){renderCount++;}
"""
        + handler
        + """
const moves=[];
for (const key of ['ArrowLeft','ArrowRight','End','Home','Tab']) {
  let prevented=false;
  listener({key,target:{matches(){return true;},dataset:{focusTab:activeFocusTab}},preventDefault(){prevented=true;}});
  moves.push({key,selected:activeFocusTab,prevented});
}
console.log(JSON.stringify({moves,renderCount}));
"""
    )
    assert observed == {
        "moves": [
            {"key": "ArrowLeft", "selected": "provenance", "prevented": True},
            {"key": "ArrowRight", "selected": "overview", "prevented": True},
            {"key": "End", "selected": "provenance", "prevented": True},
            {"key": "Home", "selected": "overview", "prevented": True},
            {"key": "Tab", "selected": "overview", "prevented": False},
        ],
        "renderCount": 4,
    }


def test_detail_focus_candidate_exposes_labelled_panel_and_loaded_sample_pages(
    tmp_path: Path,
) -> None:
    document = build_detail_focus_candidate(tmp_path)
    html = document.read_text(encoding="utf-8")
    assert 'role="tabpanel" tabindex="0"' in html
    assert 'aria-controls="focus-detail" tabindex="${activeFocusTab === key' in html
    assert (
        "focusDetail.setAttribute('aria-labelledby', `focus-tab-${activeFocusTab}`)"
        in html
    )
    assert "focusedTable" in html
    assert "restoreFocusFromCard()" in html
    assert "./_map_assets/leaflet/leaflet.js" in html


def test_detail_paging_controls_keep_sequential_focus_and_boundary_disabling() -> None:
    import re

    renderer = template_block(
        "function renderDetailTable", "function renderDetailValue"
    )
    observed = run_node_json(
        """
const DETAIL_TABLE_PAGE_SIZE=2;
const detailTablePages=new Map();
const DETAIL_TABLE_INTERNAL_KEYS=new Set();
function detailTableShape(table){return Array.isArray(table.records);}
function decodeDetailTableRow(table,row){return {sample_id:row[0]};}
function escapeHtml(value){return String(value);}
function detailTableText(value){return String(value);}
function renderDetailObjectEntries(){return '';}
"""
        + renderer
        + """
const table={record_count:5,fields:['sample_id'],records:[['a'],['b'],['c'],['d'],['e']]};
const pages=[0,1,2].map(page=>{detailTablePages.set('samples',page);return renderDetailTable(table,'samples');});
console.log(JSON.stringify(pages));
"""
    )
    for page, html in enumerate(observed):
        buttons = re.findall(r"<button\b[^>]*>", html)
        assert len(buttons) == 2
        for button in buttons:
            assert 'tabindex="0"' in button
            assert 'data-detail-table-page="samples"' in button
        assert ("disabled" in buttons[0]) is (page == 0)
        assert ("disabled" in buttons[1]) is (page == 2)
