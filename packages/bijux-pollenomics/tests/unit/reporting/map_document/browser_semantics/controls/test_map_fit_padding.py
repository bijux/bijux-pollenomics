from __future__ import annotations

import json

import pytest

from ..support import run_node_json, template_block


def _fit(
    *,
    operation: str = "fit",
    reduced: bool = False,
    geometry: dict[str, object] | None = None,
) -> dict[str, object]:
    handlers = template_block(
        "document.querySelectorAll('.basemap-button').forEach((button) => button.classList.toggle('is-active', button.dataset.basemap === currentBasemap));",
        "async function restoreDefaults()",
    )
    observed: dict[str, object] = run_node_json(
        "const fixture="
        + json.dumps(geometry or {})
        + f";const reducedMotionQuery={{matches:{json.dumps(reduced)}}};"
        + """
const mapRect={left:0,top:0,right:1280,bottom:800,...fixture.map};
const statusRect={left:350,top:713,right:1264,bottom:776,...fixture.status};
const status={hidden:fixture.hidden??false,
 getBoundingClientRect:()=>statusRect,
 getClientRects:()=>fixture.layout===false?[]:[statusRect]};
const document={querySelectorAll:()=>[],
 getElementById:()=>({getBoundingClientRect:()=>mapRect}),
 querySelector:()=>fixture.absent?null:status};
function getComputedStyle(){return {display:'grid',visibility:'visible',opacity:'1',...fixture.style}}
const currentBasemap='none',INITIAL_BOUNDS=[[54,10],[70,32]],calls=[];
let mapViewReady=true,initialMapFitPending=false;
const selected={isValid:()=>true},original=JSON.stringify(fixture);
function activeBounds(){return selected}
const topbarStatePill={textContent:'',attributes:{},setAttribute(key,value){this.attributes[key]=value}};
const map={fitBounds(bounds,options){calls.push({target:bounds===selected?'active':bounds===INITIAL_BOUNDS?'initial':'unknown',options})}};
"""
        + handlers
        + ("resetView();" if operation == "reset" else "fitToActive();")
        + """
console.log(JSON.stringify({calls,message:topbarStatePill.textContent,
 role:topbarStatePill.attributes.role??null,unchanged:original===JSON.stringify(fixture)}));
"""
    )
    return observed


@pytest.mark.parametrize("operation", ["fit", "reset"])
@pytest.mark.parametrize("reduced", [False, True])
@pytest.mark.parametrize(
    ("geometry", "bottom_padding"),
    [
        ({}, 123),
        (
            {
                "map": {"top": 10.25, "bottom": 810.75},
                "status": {"top": 700.125},
            },
            146.625,
        ),
        (
            {
                "map": {"right": 640, "bottom": 450},
                "status": {"left": 20, "top": 360.5, "right": 620, "bottom": 430},
            },
            125.5,
        ),
    ],
    ids=["bottom-hud", "fractional-css-pixels", "zoomed-css-viewport"],
)
def test_fit_reserves_measured_status_hud_clearance(
    operation: str,
    reduced: bool,
    geometry: dict[str, object],
    bottom_padding: float,
) -> None:
    options: dict[str, object] = {
        "padding": [36, 36],
        "paddingBottomRight": [36, bottom_padding],
    }
    if reduced:
        options["animate"] = False
    assert _fit(operation=operation, reduced=reduced, geometry=geometry) == {
        "calls": [
            {
                "target": "active" if operation == "fit" else "initial",
                "options": options,
            }
        ],
        "message": "",
        "role": None,
        "unchanged": True,
    }


@pytest.mark.parametrize(
    "geometry",
    [
        {"absent": True},
        {"hidden": True},
        {"layout": False},
        {"style": {"display": "none"}},
        {"style": {"visibility": "hidden"}},
        {"style": {"opacity": "0"}},
        {"status": {"left": 1280, "right": 1400}},
        {"status": {"top": 800, "bottom": 840}},
        {"status": {"top": -80, "bottom": 0}},
        {"status": {"top": 713, "bottom": 713}},
    ],
    ids=[
        "absent",
        "hidden",
        "no-layout",
        "display-none",
        "invisible",
        "transparent",
        "right-touch",
        "bottom-touch",
        "top-touch",
        "zero-height",
    ],
)
def test_unobstructed_fit_keeps_original_padding(geometry: dict[str, object]) -> None:
    assert _fit(geometry=geometry) == {
        "calls": [{"target": "active", "options": {"padding": [36, 36]}}],
        "message": "",
        "role": None,
        "unchanged": True,
    }


@pytest.mark.parametrize("operation", ["fit", "reset"])
@pytest.mark.parametrize(
    "geometry",
    [
        {"absent": True, "map": {"right": 72}},
        {"absent": True, "map": {"bottom": 72}},
        {"status": {"top": 40}},
        {"status": {"top": -20}},
        {"map": {"right": None}},
        {"status": {"right": None}},
    ],
    ids=[
        "narrow",
        "short",
        "no-height-after-padding",
        "covered",
        "invalid-map",
        "invalid-status",
    ],
)
def test_unusable_fit_preserves_camera_and_reports_unavailability(
    operation: str, geometry: dict[str, object]
) -> None:
    assert _fit(operation=operation, geometry=geometry) == {
        "calls": [],
        "message": "Fit unavailable: the map has no usable area.",
        "role": "status",
        "unchanged": True,
    }


@pytest.mark.parametrize("resize_route", ["observer", "window"])
def test_initial_hidden_map_gets_valid_view_then_one_measured_reset(
    resize_route: str,
) -> None:
    readiness = template_block(
        "let initialMapFitPending = false;", "// Attribution owns"
    )
    observer = template_block("if (window.ResizeObserver)", "const basemaps =")
    resize_handler = template_block(
        "window.addEventListener('resize', () => window.setTimeout(() => {",
        "Object.assign(activeRelationFilters",
    )
    handlers = template_block(
        "function fitMapBounds(bounds)", "async function restoreDefaults"
    )
    observed = run_node_json(
        """
let visible=false,readyCallback,observerCallback,windowCallback,frame,viewCenter;
const calls=[],snapshots=[],INITIAL_BOUNDS=[[54,10],[70,32]],center={lat:62,lng:21};
const map={whenReady(fn){readyCallback=fn},
 setView(actualCenter,zoom,options){viewCenter=actualCenter;calls.push(['initialize',actualCenter===center,zoom,options]);readyCallback()},
 getCenter(){if(!viewCenter)throw Error('Uninitialized view');return viewCenter},
 fitBounds(bounds,options){calls.push(['fit',bounds===INITIAL_BOUNDS,options])},
 invalidateSize(options){calls.push(['invalidate',options??null])}};
const L={latLngBounds(bounds){if(bounds!==INITIAL_BOUNDS)throw Error('Changed initial bounds');return {getCenter:()=>center}}};
const mapElement={getBoundingClientRect:()=>({left:0,top:0,right:visible?1280:0,bottom:visible?800:0})};
const document={getElementById:()=>mapElement,querySelector:()=>null};
const topbarStatePill={textContent:'',setAttribute(){}},reducedMotionQuery={matches:false};
const window={ResizeObserver:true,setTimeout(fn){fn()},addEventListener(type,fn){windowCallback=fn}};
class ResizeObserver{constructor(fn){observerCallback=fn}observe(){}}
function requestAnimationFrame(fn){frame=fn;return 1}
function observerResize(){observerCallback();const pending=frame;frame=null;if(pending)pending()}
"""
        + readiness
        + observer
        + resize_handler
        + handlers
        + """
resetView();snapshots.push({calls:calls.slice(),pending:initialMapFitPending,ready:mapViewReady,centerReady:map.getCenter()===center});
"""
        + ("observerResize();" if resize_route == "observer" else "windowCallback();")
        + """
snapshots.push({calls:calls.slice(),pending:initialMapFitPending});visible=true;
"""
        + ("observerResize();" if resize_route == "observer" else "windowCallback();")
        + "snapshots.push({calls:calls.slice(),pending:initialMapFitPending});"
        + ("observerResize();" if resize_route == "observer" else "windowCallback();")
        + "console.log(JSON.stringify({snapshots,calls,message:topbarStatePill.textContent}));"
    )
    initialize = ["initialize", True, 0, {"animate": False}]
    invalidate = [
        "invalidate",
        {"animate": False, "pan": False} if resize_route == "observer" else None,
    ]
    fit = ["fit", True, {"padding": [36, 36]}]
    assert observed == {
        "snapshots": [
            {
                "calls": [initialize],
                "pending": True,
                "ready": True,
                "centerReady": True,
            },
            {"calls": [initialize, invalidate], "pending": True},
            {"calls": [initialize, invalidate, invalidate, fit], "pending": False},
        ],
        "calls": [initialize, invalidate, invalidate, fit, invalidate],
        "message": "Map view fitted.",
    }
