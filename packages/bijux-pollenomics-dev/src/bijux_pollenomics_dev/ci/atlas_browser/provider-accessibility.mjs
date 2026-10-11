// Exercise keyless provider fallback and keyboard source inspection with tiles blocked.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir, readdir, rm } from 'node:fs/promises';
import { resolve, relative, join, extname } from 'node:path';

const [candidateDirectory, outputDirectory, browserBinary] = process.argv.slice(2);
if (!candidateDirectory || !outputDirectory || !browserBinary) throw Error('usage: node provider-accessibility.mjs CANDIDATE_DIRECTORY OUTPUT_DIRECTORY BROWSER_BINARY');
const candidate = resolve(candidateDirectory), output = resolve(outputDirectory);
await mkdir(output, { recursive: true });
const generation = JSON.parse(await readFile(join(candidate, 'generation.json'), 'utf8'));
const requests = new Map();
const server = createServer(async (request, response) => {
  const path = resolve(candidate, `.${decodeURIComponent(new URL(request.url, 'http://localhost').pathname)}`);
  if (relative(candidate, path).startsWith('..')) { response.writeHead(403).end(); return; }
  try {
    const bytes = await readFile(path);
    requests.set(relative(candidate, path), createHash('sha256').update(bytes).digest('hex'));
    const type = {'.html':'text/html','.js':'application/javascript','.css':'text/css','.png':'image/png'}[extname(path)] || 'application/octet-stream';
    response.writeHead(200, {'Content-Type':type,'Cache-Control':'no-store'}).end(bytes);
  } catch { response.writeHead(404).end(); }
});
await new Promise(accept => server.listen(0, '127.0.0.1', accept));
const browser = spawn(browserBinary, ['--headless=new','--disable-gpu','--disable-background-networking','--no-first-run','--no-default-browser-check','--remote-debugging-port=0',`--user-data-dir=${join(output,'browser-profile')}`,'about:blank'], {stdio:['ignore','pipe','pipe']});
const closed = new Promise(accept => browser.once('close',accept));
let log = '', cdp;
const receipt = {schema_version:'atlas-provider-accessibility-verification.v1',status:'FAIL',provider_fallbacks:[],tile_free_modes:[],keyboard_routes:[],downloads:[],runtime_errors:[]};
const tileRequests=[];
const budget = setTimeout(()=>browser.kill('SIGKILL'),120000);
try {
  const endpoint = await new Promise((accept,reject)=>{
    const timer=setTimeout(()=>reject(Error('debugger readiness timed out')),20000);
    browser.once('error',reject);
    browser.stderr.on('data',bytes=>{log+=bytes.toString();const match=log.match(/DevTools listening on (ws:\/\/[^\s]+)/);if(match){clearTimeout(timer);accept(match[1]);}});
  });
  const debuggerOrigin=new URL(endpoint);debuggerOrigin.protocol='http:';debuggerOrigin.pathname='';
  const target=await(await fetch(`${debuggerOrigin.origin}/json/new?about:blank`,{method:'PUT'})).json();
  cdp=await connect(target.webSocketDebuggerUrl);
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  cdp.listen(event=>{if(event.method==='Runtime.exceptionThrown')receipt.runtime_errors.push(event.params.exceptionDetails);if(event.method==='Network.requestWillBeSent' && /https:\/\/(tile\.openstreetmap\.org|tile\.opentopomap\.org)\//.test(event.params.request.url))tileRequests.push({url:event.params.request.url,headers:event.params.request.headers});});
  await cdp.send('Network.enable');
  await cdp.send('Network.setBlockedURLs',{urls:['*://tile.openstreetmap.org/*','*://*.tile.openstreetmap.org/*','*://tile.opentopomap.org/*','*://*.tile.opentopomap.org/*']});
  receipt.browser=await cdp.send('Browser.getVersion');
  const expectedSource=JSON.parse(await readFile('docs/report/atlas/source-export/downloads/neotoma-site-12.pollen-series.json','utf8'));
  for(const width of [1440,390]) {
    await cdp.send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
    const origin=`http://127.0.0.1:${server.address().port}/index.html?viewport=${width}`;
    const firstTile=tileRequests.length;
    await navigate(`${origin}&scenario=provider-failure#basemap=street`);
    await waitFor("globalThis.BijuxPollenomicsAtlasCapture?.snapshot().ready === true && BijuxPollenomicsAtlasCapture.snapshot().basemap === 'none'");
    await waitFor("document.getElementById('basemap-readout').textContent.includes('terrain unavailable')");
    const fallback=await capture();
    const providerTiles=tileRequests.slice(firstTile);
    const street=providerTiles.filter(row=>new URL(row.url).hostname==='tile.openstreetmap.org');
    const terrain=providerTiles.filter(row=>new URL(row.url).hostname==='tile.opentopomap.org');
    assert.ok(street.length>=3);assert.ok(terrain.length>=3);
    for(const request of providerTiles){assert.equal(new URL(request.url).search,'');assert.equal(Object.keys(request.headers).some(key=>key.toLowerCase()==='authorization'),false);}
    assert.equal(fallback.visible_points,8);assert.equal(fallback.basemap,'none');assert.equal(fallback.readout_live,'polite');
    const fallbackLegend=await legendTarget();
    const fallbackScale=await scaleControl();
    assert.equal(fallbackLegend.center_hit,true,'Fallback legend toggle is obscured at touch center');
    if(width<=640)assert.ok(fallbackLegend.rect.height>=44,'Fallback legend toggle is below mobile touch target height');
    assert.ok(fallbackScale.line.includes('km')||fallbackScale.line.includes('m'));
    assert.equal(fallbackScale.center_hit,true,'Fallback scale is obscured at its center');
    if(width<=640)assert.ok(fallbackScale.rect.bottom<fallbackScale.status_top,'Fallback scale is below the mobile status panel');
    const failedShot=await screenshot(width,'provider-failure');
    receipt.provider_fallbacks.push({width,street_tile_failures:street.length,terrain_tile_failures:terrain.length,keyless_requests:true,final_basemap:fallback.basemap,visible_source_sites:fallback.visible_points,readout:fallback.readout,legend_touch_target:fallbackLegend,scale_control:fallbackScale,screenshot:failedShot});
    await inspectSource(width,'provider-failure',expectedSource);
    const tileFreeStart=tileRequests.length;
    await navigate(`${origin}&scenario=tile-free#basemap=none`);
    await waitFor("globalThis.BijuxPollenomicsAtlasCapture?.snapshot().ready === true && BijuxPollenomicsAtlasCapture.snapshot().basemap === 'none'");
    await new Promise(accept=>setTimeout(accept,350));
    const tileFree=await capture();
    assert.equal(tileRequests.length,tileFreeStart,'No basemap requested network tiles');
    assert.equal(tileFree.visible_points,8);assert.equal(tileFree.basemap,'none');
    assert.ok(tileFree.scale.includes('km')||tileFree.scale.includes('m'));
    assert.ok(tileFree.readout.includes('no basemap'));
    const legend=await legendTarget();
    const scale=await scaleControl();
    assert.equal(scale.center_hit,true,'No-basemap scale is obscured at its center');
    if(width<=640)assert.ok(scale.rect.bottom<scale.status_top,'No-basemap scale is below the mobile status panel');
    const tileFreeShot=await screenshot(width,'tile-free');
    receipt.tile_free_modes.push({width,tile_requests:0,visible_source_sites:8,scale:tileFree.scale,coordinates:tileFree.coordinates,readout:tileFree.readout,legend_touch_target:legend,scale_control:scale,screenshot:tileFreeShot});
    assert.equal(legend.center_hit,true,'No-basemap legend toggle is obscured at touch center');
    if(width<=640)assert.ok(legend.rect.height>=44,'No-basemap legend toggle is below mobile touch target height');
    await inspectSource(width,'tile-free',expectedSource);
  }
  assert.equal(receipt.runtime_errors.length,0);
  receipt.status='PASS';
} catch(error) { receipt.error=String(error.stack||error);if(cdp)receipt.diagnostic=await evaluate("({hash:location.hash,title:document.getElementById('focus-title')?.textContent,detail:document.getElementById('focus-detail')?.textContent,snapshot:globalThis.BijuxPollenomicsAtlasCapture?.snapshot(),state:document.getElementById('topbar-state-pill')?.textContent})");process.exitCode=1; }
finally {
  clearTimeout(budget);if(cdp)cdp.close();browser.kill('SIGTERM');const kill=setTimeout(()=>browser.kill('SIGKILL'),4000);await closed;clearTimeout(kill);
  await new Promise(accept=>server.close(accept));
  receipt.served_files_sha256=Object.fromEntries([...requests].sort());
  receipt.verifier_sha256=createHash('sha256').update(await readFile(new URL(import.meta.url))).digest('hex');
  await writeFile(join(output,'receipt.json'),`${JSON.stringify(receipt,null,2)}\n`);
  await writeFile(join(output,'browser.log'),log);
  await rm(join(output,'browser-profile'),{recursive:true,force:true});
}

async function capture(){return evaluate(`(()=>{const snapshot=BijuxPollenomicsAtlasCapture.snapshot();return {basemap:snapshot.basemap,visible_points:snapshot.visible_point_count,countries:snapshot.countries,scale:document.querySelector('.leaflet-control-scale-line')?.textContent||'',coordinates:document.getElementById('center-readout').textContent,readout:document.getElementById('basemap-readout').textContent,readout_live:document.getElementById('basemap-readout').getAttribute('aria-live')}})()`);}
async function legendTarget(){return evaluate(`(()=>{const button=document.getElementById('legend-toggle'),rect=button.getBoundingClientRect(),center=[rect.left+rect.width/2,rect.top+rect.height/2],hit=document.elementFromPoint(...center);return {rect:{left:rect.left,top:rect.top,right:rect.right,bottom:rect.bottom,height:rect.height},center_hit:button.contains(hit),hit_id:hit?.id||null,hit_class:String(hit?.className||'')}})()`);}
async function scaleControl(){return evaluate(`(()=>{const line=document.querySelector('.leaflet-control-scale-line'),rect=line.getBoundingClientRect(),status=document.querySelector('.map-status').getBoundingClientRect(),center=[rect.left+rect.width/2,rect.top+rect.height/2],hit=document.elementFromPoint(...center);return {line:line.textContent,rect:{left:rect.left,top:rect.top,right:rect.right,bottom:rect.bottom},status_top:status.top,center_hit:line.contains(hit),hit_class:String(hit?.className||'')}})()`);}
async function screenshot(width,scenario){const result=await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});const bytes=Buffer.from(result.data,'base64');const path=join(output,`${width}-${scenario}.png`);await writeFile(path,bytes);return {path:relative(output,path),sha256:createHash('sha256').update(bytes).digest('hex')};}
async function inspectSource(width,scenario,expected){
  await evaluate("document.getElementById('search-toggle').focus()");await key('Enter',13);
  await waitFor("document.getElementById('search-toggle').getAttribute('aria-expanded') === 'true'");
  await cdp.send('Input.insertText',{text:'Ageröds Mosse'});
  await waitFor("document.querySelector('[data-search-index]') !== null");
  const search=await evaluate("({count:document.getElementById('search-count').textContent,live:document.getElementById('search-count').getAttribute('aria-live')})");assert.equal(search.live,'polite');
  await key('Enter',13);
  await waitFor("document.getElementById('focus-title').textContent === 'Ageröds Mosse' && document.getElementById('focus-export').disabled === false");
  assert.equal(await evaluate("document.activeElement.id"),'focus-tab-overview');
  const labels=await evaluate("({card:document.getElementById('focus-card').getAttribute('aria-live'),tabs:document.getElementById('focus-tabs').getAttribute('role'),panel:document.getElementById('focus-detail').getAttribute('role'),selected:document.getElementById('focus-tab-overview').getAttribute('aria-selected')})");
  assert.deepEqual(labels,{card:'polite',tabs:'tablist',panel:'tabpanel',selected:'true'});
  await key('ArrowRight',39);assert.equal(await evaluate("document.activeElement.id"),'focus-tab-samples');
  await key('End',35);assert.equal(await evaluate("document.activeElement.id"),'focus-tab-provenance');
  await key('Home',36);assert.equal(await evaluate("document.activeElement.id"),'focus-tab-overview');
  await evaluate("document.getElementById('focus-tab-chronology').focus()");await key('Enter',13);
  await waitFor("document.getElementById('focus-tab-chronology').getAttribute('aria-selected') === 'true'");
  let chronology=await evaluate("document.getElementById('focus-detail').textContent"),page=0;
  assert.ok(chronology.includes('context_only'));
  while(!chronology.includes('refused') && page<11){
    const next=await evaluate("document.querySelector('#focus-detail [data-page-direction=next]')?.disabled === false");
    if(!next)break;
    await evaluate("document.querySelector('#focus-detail [data-page-direction=next]').focus()");await key('Enter',13);
    chronology=await evaluate("document.getElementById('focus-detail').textContent");page+=1;
  }
  assert.ok(chronology.includes('refused'),'source refusal was not visible on any paged chronology');
  const download=await sourceDownload(width,scenario,expected);
  await evaluate("document.getElementById('focus-close').focus()");await key('Enter',13);
  await waitFor("document.getElementById('focus-card').hidden === true");
  assert.equal(await evaluate("document.activeElement.id"),'search-toggle');
  await evaluate("document.getElementById('basemap-readout').focus()");await key('Enter',13);
  await waitFor("document.getElementById('view-controls').open === true && !document.getElementById('sidebar').classList.contains('is-collapsed')");
  assert.equal(await evaluate("document.getElementById('help-toggle').getClientRects().length > 0"),true);
  await evaluate("document.getElementById('help-toggle').focus()");await key('Enter',13);
  await waitFor("document.getElementById('help-dialog').hidden === false");
  const help=await evaluate("({role:document.querySelector('#help-dialog [role=dialog]').getAttribute('role'),modal:document.querySelector('#help-dialog [role=dialog]').getAttribute('aria-modal'),active:document.activeElement.id})");
  assert.equal(help.role,'dialog');assert.equal(help.modal,'true');assert.notEqual(help.active,'help-toggle');
  await key('Escape',27);await waitFor("document.getElementById('help-dialog').hidden === true");assert.equal(await evaluate("document.activeElement.id"),'help-toggle');
  receipt.keyboard_routes.push({width,scenario,search_announcement:search.count,drawer_roles:labels,arrow_home_end_tabs:true,clear_returns_to_search:true,help_modal_escape_returns_to_help:true,source_chronology_context_refusal_visible:true,refusal_table_page:page});
  receipt.downloads.push(download);
}
async function sourceDownload(width,scenario,expected){const directory=join(output,`${width}-${scenario}-source`);await mkdir(directory,{recursive:true});await cdp.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:directory});await evaluate("document.getElementById('focus-export').click()");const file=join(directory,'neotoma-site-12.pollen-series.json'),deadline=Date.now()+20000;let bytes;while(Date.now()<deadline){try{bytes=await readFile(file);JSON.parse(bytes);break;}catch{await new Promise(accept=>setTimeout(accept,50));}}if(!bytes)throw Error('source record download timed out');const actual=JSON.parse(bytes);for(const key of ['samples','chronology_claims','pollen_observations','source_variables','collection_units','datasets','source_provenance','source_semantics','temporal_support'])assert.deepEqual(actual[key],expected[key],`source-owned ${key} changed in ${scenario}`);assert.equal(actual.temporal_support.interpolation_allowed,false);return {width,scenario,record_id:actual.record_id,path:relative(output,file),sha256:createHash('sha256').update(bytes).digest('hex'),source_tables_equal:true,chronology_claims:actual.chronology_claims.record_count,pollen_observations:actual.pollen_observations.record_count};}
async function navigate(url) {
  let waiting=true;
  const loaded=new Promise((accept,reject)=>{
    const timeout=setTimeout(()=>{waiting=false;reject(Error('page load timed out'));},20000);
    cdp.listen(event=>{if(waiting&&event.method==='Page.loadEventFired'){waiting=false;clearTimeout(timeout);accept();}});
  });
  const navigation=await cdp.send('Page.navigate',{url});
  if (!navigation.loaderId) await cdp.send('Page.reload',{ignoreCache:true});
  await loaded;
}
async function evaluate(expression){const value=await cdp.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(value.exceptionDetails)throw Error(JSON.stringify(value.exceptionDetails));return value.result.value;}
async function waitFor(expression){const deadline=Date.now()+20000;while(Date.now()<deadline){if(await evaluate(expression))return;await new Promise(accept=>setTimeout(accept,50));}throw Error(`timed out: ${expression}`);}
async function key(name,code){await cdp.send('Input.dispatchKeyEvent',{type:'keyDown',key:name,code:name,windowsVirtualKeyCode:code,...(name==='Enter'?{text:'\r'}:{})});await cdp.send('Input.dispatchKeyEvent',{type:'keyUp',key:name,windowsVirtualKeyCode:code});}
async function connect(url){return new Promise((accept,reject)=>{const socket=new WebSocket(url),pending=new Map(),listeners=new Set();let id=0;socket.addEventListener('error',reject);socket.addEventListener('open',()=>{socket.addEventListener('message',event=>{const value=JSON.parse(event.data);if(!value.id){listeners.forEach(listener=>listener(value));return;}const request=pending.get(value.id);if(!request)return;pending.delete(value.id);clearTimeout(request.timeout);if(value.error)request.reject(Error(JSON.stringify(value.error)));else request.accept(value.result);});accept({send(method,params={}){const requestId=++id;return new Promise((acceptRequest,rejectRequest)=>{const timeout=setTimeout(()=>{pending.delete(requestId);rejectRequest(Error(`CDP timeout: ${method}`));},20000);pending.set(requestId,{accept:acceptRequest,reject:rejectRequest,timeout});socket.send(JSON.stringify({id:requestId,method,params}));});},listen(callback){listeners.add(callback);},close(){socket.close();}});});});}
