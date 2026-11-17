"""Native keyboard and visible source-only entry points preserve scientific zeros."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

DRIVER = r"""
const wait=async(expression)=>{for(let n=0;n<250;n++){if(await evaluate(cdp,expression))return;await new Promise(ok=>setTimeout(ok,20));}throw Error('Browser condition unavailable: '+expression);};
const target=async(selector,click=true)=>{
 let previous,point;
 for(let n=0;n<150;n++){
  const found=await evaluate(cdp,`(()=>{const node=document.querySelector(${JSON.stringify(selector)});if(!node)return null;node.scrollIntoView({block:'center',inline:'center'});const r=node.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,hit=document.elementFromPoint(x,y);return !node.closest('[inert]')&&r.width>0&&r.height>0&&x>=0&&y>=0&&x<innerWidth&&y<innerHeight&&hit&&node.contains(hit)?{x,y}:null;})()`);
  if(found&&previous&&Math.abs(found.x-previous.x)<.5&&Math.abs(found.y-previous.y)<.5){point=found;break;}
  previous=found;await new Promise(ok=>setTimeout(ok,20));
 }
 if(!point)throw Error('No stable visible hit target: '+selector);
 if(click){await cdp.send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...point});await cdp.send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...point});}
};
const key=async(value,code)=>{for(const type of ['keyDown','keyUp'])await cdp.send('Input.dispatchKeyEvent',{type,key:value,code:value,windowsVirtualKeyCode:code,nativeVirtualKeyCode:code,...(value==='Enter'&&type==='keyDown'?{text:'\r',unmodifiedText:'\r'}:{})});};
await wait("document.getElementById('map').getAttribute('aria-busy')!=='true'");
"""


@pytest.mark.parametrize("resource_browser", ["source_only_scoped"], indirect=True)
@pytest.mark.parametrize("width", [390, 1440])
def test_native_escape_restores_source_opener_without_closing_underlying_controls(
    browser_probe: Callable[..., dict[str, Any]], width: int
) -> None:
    observed = browser_probe(
        "",
        width=width,
        driver=DRIVER
        + r"""
if(await evaluate(cdp,"document.getElementById('panel-toggle').getAttribute('aria-expanded')!=='true'"))await target('#panel-toggle');
if(!await evaluate(cdp,"document.getElementById('view-controls').open"))await target('#view-controls>summary');
await target('#source-resources-open',false);
await evaluate(cdp,"document.getElementById('source-resources-open').focus()");
if(await evaluate(cdp,"document.activeElement.id")!=='source-resources-open')throw Error('Visible opener could not take focus');
await key('Enter',13);
await wait("document.querySelector('[data-resource-status]')?.dataset.state==='available'");
await target('[aria-label="Show metadata geometry"]');
await wait("document.querySelector('[data-resource-geometry-status]').textContent.startsWith('Metadata geometry: ')");
const geometry=await evaluate(cdp,"document.querySelectorAll('.neotoma-metadata-geometry').length");
await key('Escape',27);
await wait("!document.getElementById('source-resources-dialog').open");
const first=await evaluate(cdp,"({focus:document.activeElement.id,inert:document.getElementById('sidebar').inert,panel:document.getElementById('panel-toggle').getAttribute('aria-expanded')})");
await key('Escape',27);
const second=await evaluate(cdp,"({focus:document.activeElement.id,inert:document.getElementById('sidebar').inert,panel:document.getElementById('panel-toggle').getAttribute('aria-expanded')})");
return {first,second,geometry};
""",
    )
    result = observed["result"]
    assert result["geometry"] > 0
    assert result["first"] == {
        "focus": "source-resources-open",
        "inert": False,
        "panel": "true",
    }
    if width == 390:
        assert result["second"] == {
            "focus": "panel-toggle",
            "inert": True,
            "panel": "false",
        }
    else:
        assert result["second"]["panel"] == "true"
    assert observed["failures"] == []
    assert not any(path.endswith(".body") for path in observed["calls"])


@pytest.mark.parametrize("resource_browser", ["source_only_scoped"], indirect=True)
@pytest.mark.parametrize("width", [390, 1440])
def test_source_only_empty_state_offers_real_metadata_opener_and_preserves_zero_science(
    browser_probe: Callable[..., dict[str, Any]], width: int
) -> None:
    observed = browser_probe(
        "",
        width=width,
        driver=DRIVER
        + r"""
const initial=await evaluate(cdp,"({cta:!!document.getElementById('source-metadata-browse'),reason:document.getElementById('empty-state').dataset.reason,text:document.querySelector('.empty-state:not([hidden])')?.textContent,genericHidden:document.getElementById('empty-state').hidden,science:document.getElementById('topbar-state-pill').textContent})");
if(!initial.cta)return {initial};
await target('#source-metadata-browse');
await wait("document.querySelector('[data-resource-status]')?.dataset.state==='available'");
await target('[aria-label="Show metadata geometry"]');
await wait("document.querySelector('[data-resource-geometry-status]').textContent.startsWith('Metadata geometry: ')");
const geometry=await evaluate(cdp,"document.querySelectorAll('.neotoma-metadata-geometry').length");
await key('Escape',27);
await wait("!document.getElementById('source-resources-dialog').open");
return {initial,geometry,focus:await evaluate(cdp,"document.activeElement.id"),science:await evaluate(cdp,"document.getElementById('topbar-state-pill').textContent")};
""",
    )
    result = observed["result"]
    assert result["initial"]["cta"] is True
    assert result["initial"]["reason"] == "source_metadata_only"
    assert result["initial"]["genericHidden"] is True
    assert "Select a country" not in result["initial"]["text"]
    assert "0 scientific countries, layers and points" in result["initial"]["text"]
    assert "separate" in result["initial"]["text"]
    assert result["geometry"] > 0 and result["focus"] == "source-metadata-browse"
    assert result["science"] == result["initial"]["science"]
    assert "0 countries" in result["science"] and "0 layers" in result["science"]
    assert "0 visible points" in result["science"]
    assert observed["failures"] == []
    assert not any(path.endswith(".body") for path in observed["calls"])


@pytest.mark.parametrize("resource_browser", ["source_only_scoped"], indirect=True)
@pytest.mark.parametrize("width", [390, 1440])
def test_native_source_search_question_mark_does_not_open_background_help(
    browser_probe: Callable[..., dict[str, Any]], width: int
) -> None:
    observed = browser_probe(
        "",
        width=width,
        driver=DRIVER
        + r"""
if(await evaluate(cdp,"document.getElementById('panel-toggle').getAttribute('aria-expanded')!=='true'"))await target('#panel-toggle');
if(!await evaluate(cdp,"document.getElementById('view-controls').open"))await target('#view-controls>summary');
await target('#source-resources-open',false);
await evaluate(cdp,"document.getElementById('source-resources-open').focus()");
await key('Enter',13);
await wait("document.querySelector('[data-resource-status]')?.dataset.state==='available'");
await target('[aria-label="Search source metadata"]');
await cdp.send('Input.dispatchKeyEvent',{type:'keyDown',key:'?',code:'Slash',text:'?',unmodifiedText:'/',windowsVirtualKeyCode:191,nativeVirtualKeyCode:191,modifiers:8});
await cdp.send('Input.dispatchKeyEvent',{type:'keyUp',key:'?',code:'Slash',windowsVirtualKeyCode:191,nativeVirtualKeyCode:191,modifiers:8});
return await evaluate(cdp,"({query:document.querySelector('[aria-label=\"Search source metadata\"]').value,helpHidden:document.getElementById('help-dialog').hidden,sourceOpen:document.getElementById('source-resources-dialog').open})");
""",
    )
    assert observed["result"] == {"query": "?", "helpHidden": True, "sourceOpen": True}
    assert observed["failures"] == []


@pytest.mark.parametrize("resource_browser", ["scoped"], indirect=True)
@pytest.mark.parametrize("width", [390, 1440])
def test_hidden_scientific_countries_keep_the_country_selection_entry(
    browser_probe: Callable[..., dict[str, Any]], width: int
) -> None:
    observed = browser_probe(
        "",
        width=width,
        driver=DRIVER
        + r"""
if(await evaluate(cdp,"document.getElementById('panel-toggle').getAttribute('aria-expanded')!=='true'"))await target('#panel-toggle');
if(!await evaluate(cdp,"document.getElementById('countries-none').closest('details').open"))await target('details:has(#countries-none)>summary');
await target('#countries-none');
await wait("document.getElementById('map').getAttribute('aria-busy')!=='true'");
return await evaluate(cdp,"({metadataHidden:document.getElementById('source-metadata-state').hidden,reason:document.getElementById('empty-state').dataset.reason,text:document.getElementById('empty-state').textContent,countries:[...document.querySelectorAll('.country-checkbox')].map(node=>node.checked)})");
""",
    )
    assert observed["result"]["metadataHidden"] is True
    assert observed["result"]["reason"] == "empty_countries"
    assert "Select a country" in observed["result"]["text"]
    assert observed["result"]["countries"] == [False] * 4
    assert observed["failures"] == []
