// Verify production map keyboard focus in local tile-free browser modes.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { resolve, relative, join, extname } from 'node:path';

const [candidateDirectory, outputDirectory, browserBinary] = process.argv.slice(2);
if (!candidateDirectory || !outputDirectory || !browserBinary) throw Error('usage: node map-keyboard-navigation.mjs CANDIDATE_DIRECTORY OUTPUT_DIRECTORY BROWSER_BINARY');
const candidate = resolve(candidateDirectory), output = resolve(outputDirectory);
await mkdir(output, { recursive: true });
const generationBytes = await readFile(join(candidate, 'generation.json'));
const generation = JSON.parse(generationBytes);
assert.equal(generation.status, 'controlled_synthetic_geometry_only');
assert.equal(generation.scientific_admission, 'not_evaluated');
assert.deepEqual(generation.countries, ['Denmark','Finland','Norway','Sweden']);
assert.equal(generation.polygon_count, 4);
for (const [path, expected] of Object.entries(generation.outputs_sha256)) {
  assert.equal(sha(await readFile(join(candidate, path))), expected, `candidate output ${path}`);
}
const rendererPath='packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/document.html';
assert.equal(sha(await readFile(rendererPath)), generation.inputs_sha256[rendererPath], 'renderer changed after candidate generation');
const requests = new Map(), tileRequests=[];
const server = createServer(async (request, response) => {
  const path = resolve(candidate, `.${decodeURIComponent(new URL(request.url, 'http://localhost').pathname)}`);
  if (relative(candidate, path).startsWith('..')) { response.writeHead(403).end(); return; }
  try {
    const bytes = await readFile(path);
    requests.set(relative(candidate,path),sha(bytes));
    const type = {'.html':'text/html','.js':'application/javascript','.css':'text/css','.png':'image/png'}[extname(path)] || 'application/octet-stream';
    response.writeHead(200, {'Content-Type':type,'Cache-Control':'no-store'}).end(bytes);
  } catch { response.writeHead(404).end(); }
});
await new Promise(accept => server.listen(0, '127.0.0.1', accept));
const browser = spawn(browserBinary, ['--headless=new','--disable-gpu','--disable-background-networking','--no-first-run','--no-default-browser-check','--remote-debugging-port=0',`--user-data-dir=${join(output,'browser-profile')}`,'about:blank'], {stdio:['ignore','pipe','pipe']});
const closed = new Promise(accept => browser.once('close',accept));
const receipt={schema_version:'atlas-map-keyboard-navigation-browser.v1',status:'FAIL',candidate:{schema_version:generation.schema_version,status:generation.status,scientific_admission:generation.scientific_admission,geometry_sha256:generation.geometry_sha256,generation_sha256:sha(generationBytes),renderer_sha256:generation.inputs_sha256[rendererPath],outputs_sha256:generation.outputs_sha256},scenarios:[],runtime_errors:[]};
let log='',cdp;
const budget=setTimeout(()=>browser.kill('SIGKILL'),120000);
try {
  const endpoint=await new Promise((accept,reject)=>{
    const timer=setTimeout(()=>reject(Error('debugger readiness timed out')),20000);
    browser.once('error',reject);
    browser.stderr.on('data',bytes=>{log+=bytes.toString();const match=log.match(/DevTools listening on (ws:\/\/[^\s]+)/);if(match){clearTimeout(timer);accept(match[1]);}});
  });
  const debuggerOrigin=new URL(endpoint);debuggerOrigin.protocol='http:';debuggerOrigin.pathname='';
  const target=await(await fetch(`${debuggerOrigin.origin}/json/new?about:blank`,{method:'PUT'})).json();
  cdp=await connect(target.webSocketDebuggerUrl);
  await cdp.send('Page.enable');await cdp.send('Runtime.enable');await cdp.send('Network.enable');
  cdp.listen(event=>{if(event.method==='Runtime.exceptionThrown')receipt.runtime_errors.push(event.params.exceptionDetails);if(event.method==='Network.requestWillBeSent'&&/https:\/\/(tile\.openstreetmap\.org|tile\.opentopomap\.org)\//.test(event.params.request.url))tileRequests.push(event.params.request.url);});
  await cdp.send('Network.setBlockedURLs',{urls:['*://tile.openstreetmap.org/*','*://*.tile.openstreetmap.org/*','*://tile.opentopomap.org/*','*://*.tile.opentopomap.org/*']});
  receipt.browser=await cdp.send('Browser.getVersion');
  for (const width of [320,1440]) {
    await cdp.send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
    const origin=`http://127.0.0.1:${server.address().port}/index.html?viewport=${width}`;
    for (const mode of ['provider-failure','tile-free']) {
      const firstTile=tileRequests.length;
      await navigate(`${origin}&scenario=${mode}#basemap=${mode==='provider-failure'?'street':'none'}`);
      await waitFor("globalThis.BijuxPollenomicsAtlasCapture?.snapshot().ready === true && BijuxPollenomicsAtlasCapture.snapshot().basemap === 'none'");
      if(mode==='provider-failure')await waitFor("document.getElementById('basemap-readout').textContent.includes('terrain unavailable')");
      const route=[];
      for(let step=0;step<180;step++){
        await key('Tab',9);
        const focus=await focusSnapshot();
        route.push(focus);
        if(step>3&&focus.id===route[0].id&&focus.class_name===route[0].class_name)break;
      }
      const north=await evaluate("(()=>{const element=document.getElementById('north-orientation'),style=getComputedStyle(element);return {tab_index:element.tabIndex,role:element.getAttribute('role'),label:element.getAttribute('aria-label'),focusable:element.matches('a,button,input,select,textarea,[tabindex]'),visible:element.getClientRects().length>0&&style.visibility==='visible'}})()");
      const playback=await evaluate("(()=>{const button=document.getElementById('time-playback-toggle'),status=document.getElementById('time-stepper-status');return {disabled:button.disabled,visible:button.getClientRects().length>0,status_disabled:status.disabled,status_text:status.textContent.trim()}})()");
      await evaluate("document.getElementById('fit-active').focus()");
      await key('Tab',9);
      const forward=await focusSnapshot();
      await key('Tab',9,true);
      const backward=await focusSnapshot();
      await evaluate("document.getElementById('legend-toggle').focus()");
      const legendBefore=await focusSnapshot();
      await key('Enter',13);
      const legendEnter={expanded:await evaluate("document.getElementById('legend-toggle').getAttribute('aria-expanded')"),focus:await focusSnapshot()};
      await key(' ',32);
      const legendSpace={expanded:await evaluate("document.getElementById('legend-toggle').getAttribute('aria-expanded')"),focus:await focusSnapshot()};
      await evaluate("document.querySelector('.leaflet-control-zoom-in').focus()");
      const zoomBefore=await focusSnapshot();
      const zoomStart=await evaluate("BijuxPollenomicsAtlasCapture.snapshot().view.zoom");
      await key('Enter',13);
      await waitFor(`BijuxPollenomicsAtlasCapture.snapshot().view.zoom > ${zoomStart}`);
      const zoomIn=await focusSnapshot();
      const zoomInLevel=await evaluate("BijuxPollenomicsAtlasCapture.snapshot().view.zoom");
      await new Promise(accept=>setTimeout(accept,500));
      await evaluate("document.querySelector('.leaflet-control-zoom-out').focus()");
      await key('Enter',13);
      await new Promise(accept=>setTimeout(accept,500));
      const zoomOut=await focusSnapshot();
      const zoomOutLevel=await evaluate("BijuxPollenomicsAtlasCapture.snapshot().view.zoom");
      await evaluate("document.querySelector('.leaflet-control-attribution a').focus()");
      const attributionFocus=await focusSnapshot();
      const attributionScreenshot=await screenshot(width,`${mode}-attribution-focus`);
      await evaluate("document.getElementById('basemap-readout').focus()");
      const basemapBefore=await focusSnapshot();
      await key('Enter',13);
      const basemapImmediate=await focusSnapshot();
      await new Promise(accept=>setTimeout(accept,300));
      const basemapSettled=await focusSnapshot();
      const panelOpen=await evaluate("!document.getElementById('sidebar').classList.contains('is-collapsed') && !document.getElementById('sidebar').inert");
      const scrimHiddenFromAccessibility=await evaluate("document.getElementById('mobile-scrim').getAttribute('aria-hidden') === 'true' && document.getElementById('mobile-scrim').tabIndex === -1");
      await key('Tab',9);
      const basemapNext=await focusSnapshot();
      await key('Tab',9,true);
      const basemapPrevious=await focusSnapshot();
      await evaluate("document.getElementById('help-toggle').focus()");
      await key('Enter',13);
      const helpOpen=await focusSnapshot();
      const helpModal=await evaluate("!document.getElementById('help-dialog').hidden && document.querySelector('#help-dialog [role=dialog]').getAttribute('aria-modal') === 'true' && document.querySelector('.app-shell').inert");
      const helpScreenshot=await screenshot(width,`${mode}-help-dialog`);
      await key('Tab',9);
      const helpNext=await focusSnapshot();
      await key('Tab',9);
      const helpWrap=await focusSnapshot();
      await key('Tab',9,true);
      const helpReverseWrap=await focusSnapshot();
      await key('Escape',27);
      const helpReturn=await focusSnapshot();
      const helpClosed=await evaluate("document.getElementById('help-dialog').hidden && !document.querySelector('.app-shell').inert");
      const mobileExit=width<=900?await (async()=>{await key('Escape',27);await new Promise(accept=>setTimeout(accept,300));return {focus:await focusSnapshot(),panel_closed:await evaluate("document.getElementById('sidebar').classList.contains('is-collapsed') && document.getElementById('sidebar').inert")};})():null;
      await evaluate("document.getElementById('basemap-readout').focus()");
      await key(' ',32);
      await new Promise(accept=>setTimeout(accept,300));
      const basemapSpace={panel_open:await evaluate("!document.getElementById('sidebar').classList.contains('is-collapsed') && !document.getElementById('sidebar').inert"),focus:await focusSnapshot()};
      assert.deepEqual([north.role,north.label,north.focusable,north.visible],['img','North is up',false,true]);
      assert.ok(!route.some(focus=>focus.id==='north-orientation'||focus.id==='mobile-scrim'));
      assert.equal(route[0].id,'fit-active');
      assert.ok(route.length<=15,'hidden controls enlarged the Tab route');
      const tabStops=route.filter(focus=>focus.tag!=='body');
      assert.ok(tabStops.every(focus=>focus.focus_visible&&focus.inside_viewport&&focus.center_hit&&focus.outline_style!=='none'&&Number.parseFloat(focus.outline_width)>0),'Tab reached a hidden or unoutlined control');
      for(const id of ['fit-active','search-toggle','panel-toggle','legend-toggle','basemap-readout'])assert.ok(route.some(focus=>focus.id===id),`Tab did not reach ${id}`);
      for(const className of ['leaflet-control-zoom-in','leaflet-control-zoom-out'])assert.ok(route.some(focus=>focus.class_name===className),`Tab did not reach ${className}`);
      assert.ok(route.some(focus=>focus.href?.startsWith('https://leafletjs.com')),'Tab did not reach the attribution link');
      assert.ok(playback.visible&&playback.disabled&&playback.status_disabled&&playback.status_text.includes('No BP chronology'),'playback unavailable state was not explicit');
      assert.ok(!route.some(focus=>focus.id==='time-playback-toggle'||focus.id==='time-stepper-status'));
      assert.equal(forward.id,'search-toggle');assert.equal(backward.id,'fit-active');
      assert.deepEqual([legendBefore.id,legendEnter.expanded,legendEnter.focus.id,legendSpace.expanded,legendSpace.focus.id],['legend-toggle','true','legend-toggle','false','legend-toggle']);
      assert.ok([legendBefore,legendEnter.focus,legendSpace.focus].every(focus=>focus.focus_visible&&focus.inside_viewport&&focus.center_hit));
      assert.equal(zoomInLevel,zoomStart+1);assert.equal(zoomOutLevel,zoomStart);
      assert.ok([zoomBefore,zoomIn,zoomOut].every(focus=>focus.focus_visible&&focus.inside_viewport&&focus.center_hit&&focus.outline_style!=='none'));
      assert.ok(attributionFocus.href?.startsWith('https://leafletjs.com'));
      assert.ok(attributionFocus.focus_visible&&attributionFocus.inside_viewport&&attributionFocus.center_hit&&attributionFocus.outline_style!=='none');
      assert.equal(basemapBefore.id,'basemap-readout');assert.ok(basemapBefore.focus_visible&&basemapBefore.inside_viewport);
      assert.ok(panelOpen&&basemapSettled.class_name.includes('basemap-button is-active')&&basemapSettled.inside_viewport&&basemapSettled.center_hit&&basemapSettled.focus_visible);
      assert.ok(scrimHiddenFromAccessibility,'pointer scrim entered the accessibility or Tab route');
      assert.equal(basemapNext.id,'reset-view');assert.ok(basemapPrevious.class_name.includes('basemap-button is-active'));
      assert.ok(helpModal&&helpClosed&&helpOpen.id==='help-close'&&helpNext.id==='help-return'&&helpWrap.id==='help-close'&&helpReverseWrap.id==='help-return'&&helpReturn.id==='help-toggle');
      assert.ok([helpOpen,helpNext,helpWrap,helpReverseWrap].every(focus=>focus.help&&focus.focus_visible&&focus.inside_viewport&&focus.center_hit));
      if(width<=900)assert.ok(mobileExit?.panel_closed&&mobileExit.focus.id==='basemap-readout','mobile Escape did not restore the Basemap opener');
      assert.ok(basemapSpace.panel_open&&basemapSpace.focus.class_name.includes('basemap-button is-active')&&basemapSpace.focus.inside_viewport,'Space did not open Basemap selection');
      const tiles=tileRequests.slice(firstTile);
      if(mode==='tile-free')assert.equal(tiles.length,0,'direct No basemap requested provider tiles');
      else {assert.ok(tiles.filter(url=>new URL(url).hostname==='tile.openstreetmap.org').length>=3);assert.ok(tiles.filter(url=>new URL(url).hostname==='tile.opentopomap.org').length>=3);}
      const shot=await screenshot(width,mode);
      receipt.scenarios.push({width,mode,tile_requests:tiles.length,street_tile_failures:tiles.filter(url=>new URL(url).hostname==='tile.openstreetmap.org').length,terrain_tile_failures:tiles.filter(url=>new URL(url).hostname==='tile.opentopomap.org').length,north,playback,route,direction:{forward,backward},legend:{before:legendBefore,enter:legendEnter,space:legendSpace},zoom:{before:zoomBefore,in:zoomIn,out:zoomOut,start:zoomStart,in_level:zoomInLevel,out_level:zoomOutLevel},attribution:{focus:attributionFocus,screenshot:attributionScreenshot},basemap:{before:basemapBefore,immediate:basemapImmediate,settled:basemapSettled,panel_open:panelOpen,scrim_hidden_from_accessibility:scrimHiddenFromAccessibility,next:basemapNext,previous:basemapPrevious,space:basemapSpace},help:{open:helpOpen,modal:helpModal,next:helpNext,wrap:helpWrap,reverse_wrap:helpReverseWrap,return:helpReturn,closed:helpClosed,screenshot:helpScreenshot},mobile_exit:mobileExit,screenshot:shot});
    }
  }
  assert.equal(receipt.runtime_errors.length,0);
  receipt.status='PASS';
} catch(error) {receipt.error=String(error.stack||error);if(cdp)receipt.diagnostic=await evaluate("(()=>{const attribution=document.querySelector('.leaflet-control-attribution'),rect=attribution.getBoundingClientRect(),hit=document.elementFromPoint(rect.left+rect.width/2,rect.top+rect.height/2);const zoom=document.querySelector('.leaflet-control-zoom'),zoomRect=zoom.getBoundingClientRect(),plus=zoom.querySelector('.leaflet-control-zoom-in'),minus=zoom.querySelector('.leaflet-control-zoom-out'),centerHit=element=>{const box=element.getBoundingClientRect(),target=document.elementFromPoint(box.left+box.width/2,box.top+box.height/2);return {visible:element.contains(target),hit_class:String(target?.className||''),hit_id:target?.id||null};};return {hash:location.hash,attribution:rect.toJSON(),attribution_text:attribution.textContent,hit_class:String(hit?.className||''),hit_id:hit?.id||null,zoom:zoomRect.toJSON(),zoom_plus:centerHit(plus),zoom_minus:centerHit(minus),status:document.querySelector('.map-status').getBoundingClientRect().toJSON(),topbar:document.querySelector('.map-topbar').getBoundingClientRect().toJSON(),document_width:document.documentElement.scrollWidth,topbar_buttons:Object.fromEntries(['fit-active','search-toggle','panel-toggle','time-step-older','time-stepper-status','time-step-newer','time-playback-toggle'].map(id=>{const element=document.getElementById(id),box=element.getBoundingClientRect(),target=document.elementFromPoint(box.left+box.width/2,box.top+box.height/2);return [id,{rect:box.toJSON(),hit:element.contains(target),hit_class:String(target?.className||''),hit_id:target?.id||null}]})),scale:document.querySelector('.leaflet-control-scale-line').getBoundingClientRect().toJSON(),legend:document.getElementById('floating-legend').getBoundingClientRect().toJSON(),north:document.getElementById('north-orientation').getBoundingClientRect().toJSON(),snapshot:globalThis.BijuxPollenomicsAtlasCapture?.snapshot()}})()");receipt.diagnostic_screenshot=await screenshot(await evaluate('innerWidth'),'diagnostic');process.exitCode=1;}
finally {
  clearTimeout(budget);if(cdp)cdp.close();browser.kill('SIGTERM');const kill=setTimeout(()=>browser.kill('SIGKILL'),4000);await closed;clearTimeout(kill);
  await new Promise(accept=>server.close(accept));
  receipt.served_files_sha256=Object.fromEntries([...requests].sort());
  receipt.verifier_sha256=sha(await readFile(new URL(import.meta.url)));
  await writeFile(join(output,'receipt.json'),`${JSON.stringify(receipt,null,2)}\n`);
  await writeFile(join(output,'browser.log'),log);
  await rm(join(output,'browser-profile'),{recursive:true,force:true});
}

function sha(bytes){return createHash('sha256').update(bytes).digest('hex');}
async function screenshot(width,mode){const result=await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});const bytes=Buffer.from(result.data,'base64'),path=join(output,`${width}-${mode}.png`);await writeFile(path,bytes);return {path:relative(output,path),sha256:sha(bytes)};}
async function navigate(url){let waiting=true;const loaded=new Promise((accept,reject)=>{const timeout=setTimeout(()=>{waiting=false;reject(Error('page load timed out'));},20000);cdp.listen(event=>{if(waiting&&event.method==='Page.loadEventFired'){waiting=false;clearTimeout(timeout);accept();}});});const navigation=await cdp.send('Page.navigate',{url});if(!navigation.loaderId)await cdp.send('Page.reload',{ignoreCache:true});await loaded;}
async function evaluate(expression){const value=await cdp.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(value.exceptionDetails)throw Error(JSON.stringify(value.exceptionDetails));return value.result.value;}
async function waitFor(expression){const deadline=Date.now()+20000;while(Date.now()<deadline){if(await evaluate(expression))return;await new Promise(accept=>setTimeout(accept,50));}throw Error(`timed out: ${expression}`);}
async function connect(url){return new Promise((accept,reject)=>{const socket=new WebSocket(url),pending=new Map(),listeners=new Set();let id=0;socket.addEventListener('error',reject);socket.addEventListener('open',()=>{socket.addEventListener('message',event=>{const value=JSON.parse(event.data);if(!value.id){listeners.forEach(listener=>listener(value));return;}const request=pending.get(value.id);if(!request)return;pending.delete(value.id);clearTimeout(request.timeout);if(value.error)request.reject(Error(JSON.stringify(value.error)));else request.accept(value.result);});accept({send(method,params={}){const requestId=++id;return new Promise((acceptRequest,rejectRequest)=>{const timeout=setTimeout(()=>{pending.delete(requestId);rejectRequest(Error(`CDP timeout: ${method}`));},20000);pending.set(requestId,{accept:acceptRequest,reject:rejectRequest,timeout});socket.send(JSON.stringify({id:requestId,method,params}));});},listen(callback){listeners.add(callback);},close(){socket.close();}});});});}

async function key(name,code,shift=false){const params={type:'keyDown',key:name,code:name===' '?'Space':name,windowsVirtualKeyCode:code,modifiers:shift?8:0,...(name==='Enter'?{text:'\r'}:name===' '?{text:' '}: {})};await cdp.send('Input.dispatchKeyEvent',params);await cdp.send('Input.dispatchKeyEvent',{type:'keyUp',key:name,code:params.code,windowsVirtualKeyCode:code,modifiers:shift?8:0});}
async function focusSnapshot(){return evaluate(`(()=>{const element=document.activeElement,rect=element.getBoundingClientRect(),style=getComputedStyle(element),hit=document.elementFromPoint(rect.left+rect.width/2,rect.top+rect.height/2);return {id:element.id||null,tag:element.tagName.toLowerCase(),class_name:String(element.className||''),text:element.textContent?.trim().slice(0,80)||'',href:element.getAttribute('href'),rect:{left:rect.left,top:rect.top,right:rect.right,bottom:rect.bottom,width:rect.width,height:rect.height},focus_visible:element.matches(':focus-visible'),outline_width:style.outlineWidth,outline_style:style.outlineStyle,outline_color:style.outlineColor,center_hit:element.contains(hit),inside_viewport:rect.left>=0&&rect.right<=innerWidth&&rect.top>=0&&rect.bottom<=innerHeight,sidebar:!!element.closest('#sidebar'),help:!!element.closest('#help-dialog')};})()`);}
