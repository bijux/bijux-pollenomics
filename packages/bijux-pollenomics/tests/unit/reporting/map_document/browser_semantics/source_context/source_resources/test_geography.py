"""Metadata geometry has separate visibility and never borrows scientific admission."""

from collections.abc import Callable
from typing import Any

import pytest


def test_metadata_overlay_starts_off_and_has_explicit_unassigned_control(
    browser_probe: Callable[..., dict[str, Any]],
) -> None:
    observed = browser_probe("""(async()=>{const button=document.getElementById('source-resources-open');if(!button)return {supported:false};button.click();
for(let i=0;i<150&&!document.querySelector('[data-resource-list]')?.children.length;i++)await new Promise(ok=>setTimeout(ok,20));
const show=document.querySelector('[aria-label="Show metadata geometry"]'),unassigned=document.querySelector('[aria-label="Include unassigned metadata geometry"]');
const before=document.querySelector('[data-resource-geometry-status]')?.textContent,wasOff=show?.checked===false;
show.checked=true;unassigned.checked=true;unassigned.dispatchEvent(new Event('change'));await new Promise(ok=>setTimeout(ok,100));
return {supported:true,wasOff,before,after:document.querySelector('[data-resource-geometry-status]')?.textContent,paths:document.querySelectorAll('.neotoma-metadata-geometry').length};})()""")
    result = observed["result"]
    assert result["supported"] is True and result["wasOff"] is True
    assert "off" in result["before"].lower()
    assert "Metadata geometry:" in result["after"]
    assert "scientific" in result["after"].lower()
    assert observed["failures"] == []


def test_late_extent_failure_after_disable_cannot_replace_newer_geometry_posture() -> (
    None
):
    from importlib.resources import files

    from ...support import run_node_json

    source = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/source-resources/geography.js")
        .read_text()
    )
    observed = run_node_json(
        source
        + """
(async()=>{let rejectSite;const pending=new Promise((_,reject)=>rejectSite=reject),status={textContent:''};
const group={clearLayers(){},addLayer(){},addTo(){}};const map={hasLayer:()=>false,removeLayer(){}};
const geography=createSourceResourceGeography({browser:{site:()=>pending},map,leaflet:{layerGroup:()=>group,svg:()=>({})},countries:()=>['SE'],status});
const old=geography.update({enabled:true,includeUnassigned:false,rows:[{site_id:'12'}],sites:[{record_id:'12',country_code:'SE',native_extent_variant_ids:['extent:one']}]});
await Promise.resolve();await geography.update({enabled:false,rows:[],sites:[]});const latest=status.textContent;
rejectSite(Error('Old extent lookup failed'));let rejected=false;try{await old}catch{rejected=true}console.log(JSON.stringify({rejected,latest,current:status.textContent}));})();
"""
    )
    assert observed["rejected"] is False
    assert (
        observed["current"] == observed["latest"]
        and "off" in observed["current"].lower()
    )


def test_explicit_metadata_zoom_uses_only_latest_navigation() -> None:
    from importlib.resources import files

    from ...support import run_node_json

    source = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/source-resources/geography.js")
        .read_text()
    )
    observed = run_node_json(
        source
        + """
(async()=>{let resolveFirst;const pending=new Promise(resolve=>resolveFirst=resolve),fits=[];
const site=(id,x)=>({site_id:id,geometry_status:'native_point_consensus',marker_geometry:{type:'Point',coordinates:[x,61]},native_extent_variant_ids:[]});
const layer=geometry=>({geometry,bindTooltip(){},on(){}}),group={clearLayers(){}};
const map={fitBounds:bounds=>fits.push(bounds.x)};
const leaflet={layerGroup:()=>group,svg:()=>({}),geoJSON:layer,featureGroup:values=>({getBounds:()=>({isValid:()=>true,x:values[0].geometry.coordinates[0]})})};
const geography=createSourceResourceGeography({browser:{site:id=>id==='12'?pending:Promise.resolve(site('13',13))},map,leaflet,countries:()=>['SE'],status:{}});
const old=geography.zoom('12');await geography.zoom('13');resolveFirst(site('12',12));await old;console.log(JSON.stringify({fits}));})();
"""
    )
    assert observed["fits"] == [13]


@pytest.mark.parametrize("resource_browser", ["wide"], indirect=True)
def test_actual_native_multipolygon_holes_render_without_a_site_centroid(
    browser_probe: Callable[..., dict[str, Any]],
) -> None:
    observed = browser_probe("""(async()=>{document.getElementById('source-resources-open').click();
for(let i=0;i<150&&!document.querySelectorAll('[data-resource-dataset]').length;i++)await new Promise(ok=>setTimeout(ok,20));
const show=document.querySelector('[aria-label="Show metadata geometry"]'),unassigned=document.querySelector('[aria-label="Include unassigned metadata geometry"]');show.checked=true;unassigned.checked=true;unassigned.dispatchEvent(new Event('change'));
for(let i=0;i<150&&!document.querySelector('.neotoma-metadata-geometry');i++)await new Promise(ok=>setTimeout(ok,20));
const paths=[...document.querySelectorAll('.neotoma-metadata-geometry')].map(node=>({tag:node.tagName,d:node.getAttribute('d'),fill:node.getAttribute('fill-rule')}));return {paths,status:document.querySelector('[data-resource-geometry-status]')?.textContent};})()""")
    result = observed["result"]
    assert "0 consensus points; 1 native extent variants" in result["status"]
    assert len(result["paths"]) == 1
    assert result["paths"][0]["fill"] == "evenodd"
    assert result["paths"][0]["d"].count("M") == 3
    assert not any(path.endswith(".body") for path in observed["calls"])
    assert observed["failures"] == []


def test_cancelled_zoom_failure_does_not_escape_into_new_reader_state() -> None:
    from importlib.resources import files

    from ...support import run_node_json

    source = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/source-resources/geography.js")
        .read_text()
    )
    observed = run_node_json(
        source
        + """
(async()=>{let rejectFirst;const pending=new Promise((_,reject)=>rejectFirst=reject),status={textContent:'New metadata selection'};
const geography=createSourceResourceGeography({browser:{site:()=>pending},map:{},leaflet:{layerGroup:()=>({}),svg:()=>({})},countries:()=>['SE'],status});
const old=geography.zoom('12');geography.cancel();rejectFirst(Error('Old site failed'));let rejected=false;try{await old}catch{rejected=true}console.log(JSON.stringify({rejected,status:status.textContent}));})();
"""
    )
    assert observed == {"rejected": False, "status": "New metadata selection"}


def test_new_metadata_navigation_invalidates_pending_extent_failure() -> None:
    from importlib.resources import files

    from ...support import run_node_json

    source = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/source-resources/geography.js")
        .read_text()
    )
    observed = run_node_json(
        source
        + """
(async()=>{let rejectSite;const pending=new Promise((_,reject)=>rejectSite=reject),status={textContent:''};
const geography=createSourceResourceGeography({browser:{site:()=>pending},map:{hasLayer:()=>false},leaflet:{layerGroup:()=>({clearLayers(){}}),svg:()=>({})},countries:()=>['SE'],status});
const old=geography.update({enabled:true,rows:[{site_id:'12'}],sites:[{record_id:'12',country_code:'SE',native_extent_variant_ids:['one']}]});
geography.cancel();status.textContent='New native site selection';rejectSite(Error('Superseded extent failure'));await old;console.log(JSON.stringify({status:status.textContent}));})();
"""
    )
    assert observed["status"] == "New native site selection"
