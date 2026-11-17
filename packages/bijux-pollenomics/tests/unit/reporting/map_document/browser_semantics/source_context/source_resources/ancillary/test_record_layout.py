"""Long ancillary identities remain readable without widening the metadata dialog."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from .test_interactions import DRIVER


@pytest.mark.parametrize("resource_browser", ["supporting"], indirect=True)
@pytest.mark.parametrize("width", [390, 1440])
def test_supporting_metadata_actions_contain_their_complete_identity(
    browser_probe: Callable[..., dict[str, Any]], width: int
) -> None:
    observed = browser_probe(
        "",
        width=width,
        height=1100 if width == 1440 else 844,
        driver=DRIVER
        + r"""
if(await evaluate(cdp,"document.getElementById('panel-toggle').getAttribute('aria-expanded')!=='true'"))await target('#panel-toggle');
if(!await evaluate(cdp,"document.getElementById('view-controls').open"))await target('#view-controls>summary');
await target('#source-resources-open');
await wait("document.querySelector('[data-resource-status]')?.dataset.state==='available'");
await target('[aria-label="Search source metadata"]');
for(const type of ['keyDown','keyUp'])await cdp.send('Input.dispatchKeyEvent',{type,key:'Tab',code:'Tab',windowsVirtualKeyCode:9,modifiers:8});
await wait("document.activeElement?.getAttribute('aria-label')==='Metadata population'");
for(const letter of 'Supporting metadata entries'){
 const data={key:letter,code:letter===' '?'Space':'Key'+letter.toUpperCase(),windowsVirtualKeyCode:letter.toUpperCase().charCodeAt(0),text:letter,unmodifiedText:letter};
 await cdp.send('Input.dispatchKeyEvent',{type:'keyDown',...data});delete data.text;delete data.unmodifiedText;await cdp.send('Input.dispatchKeyEvent',{type:'keyUp',...data});
}
await wait("document.querySelector('[aria-label=\"Metadata population\"]').value==='supporting_entries'&&!!document.querySelector('[data-ancillary-record]')");
const layout=await evaluate(cdp,`(()=>{const dialog=document.getElementById('source-resources-dialog');return{dialog_client:dialog.clientWidth,dialog_scroll:dialog.scrollWidth,rows:[...dialog.querySelectorAll('[data-ancillary-record]')].map(row=>{const button=row.querySelector('button'),p=row.getBoundingClientRect(),r=button.getBoundingClientRect(),style=getComputedStyle(row),left=p.left+parseFloat(style.borderLeftWidth)+parseFloat(style.paddingLeft),right=p.right-parseFloat(style.borderRightWidth)-parseFloat(style.paddingRight);return{id:row.dataset.ancillaryRecord,text:button.textContent,button_width:r.width,parent_inner_width:right-left,contained:r.left>=left-.5&&r.right<=right+.5};})};})()`);
if(layout.rows.some(row=>!row.contained)||layout.dialog_scroll>layout.dialog_client+1)return{layout,readable:[],pre:null};
const readable=[];
for(const row of layout.rows){
 const selector='[data-ancillary-record='+JSON.stringify(row.id)+'] button';await target(selector,false);
 readable.push(await evaluate(cdp,`(()=>{const button=document.querySelector(${JSON.stringify(selector)}),b=button.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(button);return{id:${JSON.stringify(row.id)},text:button.textContent,full_text_in_button:[...range.getClientRects()].every(r=>r.left>=b.left-.5&&r.right<=b.right+.5&&r.top>=b.top-.5&&r.bottom<=b.bottom+.5)};})()`));
}
await target('[data-ancillary-record='+JSON.stringify(layout.rows[0].id)+'] button');
await wait("!!document.querySelector('[data-resource-detail] pre')");await target('[data-resource-detail] details>summary');
const pre=await evaluate(cdp,"(()=>{const pre=document.querySelector('[data-resource-detail] pre'),dialog=document.getElementById('source-resources-dialog');return{overflow_x:getComputedStyle(pre).overflowX,client:pre.clientWidth,scroll:pre.scrollWidth,dialog_client:dialog.clientWidth,dialog_scroll:dialog.scrollWidth};})()");
return{layout,readable,pre};
""",
    )
    result = observed["result"]
    layout = result["layout"]
    assert layout["rows"]
    assert all(row["contained"] for row in layout["rows"]), layout["rows"]
    assert layout["dialog_scroll"] <= layout["dialog_client"] + 1
    assert len(result["readable"]) == len(layout["rows"])
    for row in result["readable"]:
        assert row["id"] in row["text"]
        assert row["full_text_in_button"] is True
    assert result["pre"]["overflow_x"] == "auto"
    assert result["pre"]["scroll"] >= result["pre"]["client"]
    assert result["pre"]["dialog_scroll"] <= result["pre"]["dialog_client"] + 1
    assert observed["failures"] == []
    assert not any(path.endswith(".body") for path in observed["calls"])
