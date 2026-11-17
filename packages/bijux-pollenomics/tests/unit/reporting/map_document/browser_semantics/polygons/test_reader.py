"""Actual polygon click handlers retain public metadata in the safe reader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from ..support import run_node_json, template_block


def clicked(rows: object) -> dict[str, Any]:
    source = (
        template_block("function escapeHtml", "function normalizedMediaLinks")
        + template_block("function valueIsAvailable", "function finiteCoordinateValue")
        + template_block("function renderPolygonLayers", "function activeBounds")
        + template_block(
            "function renderFocusCard", "async function focusPointAtVisibleIndex"
        )
        + "const rows="
        + json.dumps(rows)
        + r""";
const properties={name:'generated-native-cell',category:'Conditional registry cell',popup_rows:rows,
 scientific_selection_enabled:false,source_sha256:'a'.repeat(64)};
const layer={key:'generated-context',kind:'context',label:'Generated polygon context',
 applies_country_filter:false,applies_time_filter:false,source_authority_admitted:false,
 geojson:{type:'FeatureCollection',features:[{type:'Feature',properties,geometry:{type:'Polygon',coordinates:[]}}]}};
const before=JSON.stringify(layer),POLYGON_LAYERS=[layer];
const visiblePolygonFeatureEntries=[],renderedPolygonLayers=[],renderedFittablePolygonLayers=[];
function polygonGeometryIsAdmitted(){return true}
function polygonFeatureVisible(){return true}
function polygonPopupHtml(){return ''}
function featureTimeDescriptor(){return {label:'Temporal support',value:'Unsupported'}}
let clicked;
const bounds={isValid(){return true},getSouth(){return 55},getWest(){return 12},getNorth(){return 56},getEast(){return 13}};
const L={geoJSON(data,options){options.onEachFeature(data.features[0],{
 bindPopup(){},on(type,handler){if(type==='click')clicked=handler},getBounds(){return bounds}});
 return {addTo(){}}}};
const map={};let focusState;
function setFocusState(value){focusState=value}
renderPolygonLayers();clicked();
const activeLayerKeys=new Set([layer.key]);
function visiblePointEntryForFocus(){return null}
function renderFocusDetail(){}
const document={activeElement:null};
const focusCard={contains(){return false}},focusSourceLink={},focusPreviousButton={},focusNextButton={};
const focusTitle={},focusSubtitle={},focusMeta={innerHTML:''};
renderFocusCard();
console.log(JSON.stringify({meta:focusState.meta,html:focusMeta.innerHTML,title:focusTitle.textContent,
 subtitle:focusSubtitle.textContent,unchanged:before===JSON.stringify(layer),sourceAuthority:layer.source_authority_admitted,
 scientificSelection:properties.scientific_selection_enabled,bounds:focusState.bounds}));
"""
    )
    return cast(dict[str, Any], run_node_json(source))


@pytest.mark.parametrize("partial", [False, True])
def test_polygon_click_keeps_full_and_partial_native_metadata(partial: bool) -> None:
    rows: list[dict[str, Any]] = [
        {"label": "Registry UUIDs per original 1° cell", "value": 7},
        {"label": "Native cell bounds (EPSG:4619)", "value": "[12, 55, 13, 56]"},
        {
            "label": "Display footprint",
            "value": "Partial; full-cell count retained, not prorated"
            if partial
            else "Full; full-cell count retained",
        },
        {"label": "Source capture (not event time)", "value": "2026-01-01T00:00:00Z"},
        {"label": "Limits", "value": "Country unassigned; chronology unsupported"},
        {
            "label": "Display operation",
            "value": "EPSG:1879 approximate display; native accuracy unknown",
        },
    ]
    result = clicked(rows)
    assert result["meta"] == [
        {"label": "Layer", "value": "Generated polygon context"},
        {"label": "Country", "value": "Unassigned"},
        {"label": "Type", "value": "Conditional registry cell"},
        {"label": "Temporal support", "value": "Unsupported"},
        *rows,
    ]
    assert result["unchanged"] is True
    assert result["sourceAuthority"] is False
    assert result["scientificSelection"] is False
    assert result["bounds"] == [[55, 12], [56, 13]]
    for row in rows:
        assert row["label"] in result["html"]
        assert str(row["value"]) in result["html"]


def test_polygon_reader_preserves_zero_false_and_safe_text() -> None:
    result = clicked(
        [
            {"label": "Zero", "value": 0},
            {"label": "Admission", "value": False},
            {"label": "<b>Source</b>", "value": "<script>untrusted</script>"},
            {"label": "Unknown", "value": None},
            {"label": "Blank", "value": " "},
            None,
        ]
    )
    assert result["meta"][-3:] == [
        {"label": "Zero", "value": 0},
        {"label": "Admission", "value": False},
        {"label": "<b>Source</b>", "value": "<script>untrusted</script>"},
    ]
    assert "&lt;b&gt;Source&lt;/b&gt;" in result["html"]
    assert "&lt;script&gt;untrusted&lt;/script&gt;" in result["html"]
    assert "<script>" not in result["html"]


@pytest.mark.parametrize("rows", [None, {}, "not-an-array", []])
def test_polygon_without_public_rows_keeps_original_reader_fields(rows: object) -> None:
    result = clicked(rows)
    assert [row["label"] for row in result["meta"]] == [
        "Layer",
        "Country",
        "Type",
        "Temporal support",
    ]
    assert result["title"] == "generated-native-cell"


def test_polygon_reader_keeps_four_country_document_runtime_bounded(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.reporting.map_document.render import (
        write_static_map_document,
    )
    from bijux_pollenomics.reporting.map_document.static_assets import (
        write_static_atlas_assets,
    )
    from bijux_pollenomics.reporting.map_publication import resolve_map_scope_policy

    from ....atlas.static_assets.fixtures.layers import (
        build_point_layers,
        build_polygon_layers,
    )

    points, polygons = build_point_layers(), build_polygon_layers()
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="reader",
        point_layers=points,
        polygon_layers=polygons,
    )
    _, runtime = write_static_map_document(
        tmp_path / "index.html",
        "Nordic context",
        "reader",
        "2026-01-01",
        ("Sweden", "Norway", "Denmark", "Finland"),
        resolve_map_scope_policy(None),
        points,
        polygons,
        "./_map_assets",
        static_assets=assets,
    )
    assert runtime.stat().st_size <= 512 * 1024


def test_reader_wraps_complete_cell_identity_at_the_outer_boundary() -> None:
    reader = template_block(
        ".focus-card {\n        grid-area: reader;", ".focus-card[hidden]"
    )
    assert "overflow-wrap: anywhere;" in reader
