// Observe controlled country outlines and north-up projection without network tiles.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { resolve, relative, join, extname } from 'node:path';

const [candidateDirectory, outputDirectory, browserBinary] = process.argv.slice(2);
if (!candidateDirectory || !outputDirectory || !browserBinary) throw Error('usage: node boundary-orientation.mjs CANDIDATE_DIRECTORY OUTPUT_DIRECTORY BROWSER_BINARY');
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
const receipt={schema_version:'atlas-boundary-orientation-browser.v1',status:'FAIL',candidate:{schema_version:generation.schema_version,status:generation.status,scientific_admission:generation.scientific_admission,geometry_sha256:generation.geometry_sha256,generation_sha256:sha(generationBytes),renderer_sha256:generation.inputs_sha256[rendererPath],outputs_sha256:generation.outputs_sha256},scenarios:[],runtime_errors:[]};
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
  for (const width of [1440,390]) {
    await cdp.send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
    const origin=`http://127.0.0.1:${server.address().port}/index.html?viewport=${width}`;
    for (const mode of ['provider-failure','tile-free']) {
      const firstTile=tileRequests.length;
      await navigate(`${origin}&scenario=${mode}#basemap=${mode==='provider-failure'?'street':'none'}`);
      await waitFor("globalThis.BijuxPollenomicsAtlasCapture?.snapshot().ready === true && BijuxPollenomicsAtlasCapture.snapshot().basemap === 'none'");
      if(mode==='provider-failure')await waitFor("document.getElementById('basemap-readout').textContent.includes('terrain unavailable')");
      await waitFor("document.querySelectorAll('.leaflet-boundary-pane path').length === 4");
      const tiles=tileRequests.slice(firstTile);
      if(mode==='tile-free')assert.equal(tiles.length,0,'direct No basemap requested provider tiles');
      else {
        assert.ok(tiles.filter(url=>new URL(url).hostname==='tile.openstreetmap.org').length>=3);
        assert.ok(tiles.filter(url=>new URL(url).hostname==='tile.opentopomap.org').length>=3);
        assert.ok(tiles.every(url=>new URL(url).search===''));
      }
      const facts=await evaluate(`(()=>{
        const cues=[...document.querySelectorAll('[data-legend-country]')].map(row=>({country:row.dataset.legendCountry,stroke:getComputedStyle(row.querySelector('.legend-boundary-cue')).color}));
        const paths=[...document.querySelectorAll('.leaflet-boundary-pane path')].map(path=>{const rect=path.getBoundingClientRect(),style=getComputedStyle(path);return {country:cues.find(cue=>cue.stroke===style.stroke)?.country||null,left:rect.left,top:rect.top,right:rect.right,bottom:rect.bottom,width:rect.width,height:rect.height,stroke:style.stroke,stroke_width:style.strokeWidth,opacity:Number(style.opacity),fill_opacity:Number(style.fillOpacity)}});
        const scale=document.querySelector('.leaflet-control-scale-line'),scaleRect=scale.getBoundingClientRect(),scaleHit=document.elementFromPoint(scaleRect.left+scaleRect.width/2,scaleRect.top+scaleRect.height/2);
        return {basemap:BijuxPollenomicsAtlasCapture.snapshot().basemap,paths,scale:scale.textContent,scale_visible:scale.contains(scaleHit),coordinates:document.getElementById('center-readout').textContent,coordinates_visible:document.getElementById('center-readout').getClientRects().length>0,readout:document.getElementById('basemap-readout').textContent,north_indicator_present:Boolean(document.querySelector('[aria-label="North"], [aria-label="North arrow"], .north-arrow, .compass'))};
      })()`);
      assert.equal(facts.basemap,'none');
      assert.equal(facts.paths.length,4);
      assert.ok(facts.paths.every(row=>row.width>0&&row.height>0&&row.stroke!=='none'&&Number.parseFloat(row.stroke_width)>0&&row.opacity>0));
      assert.deepEqual(facts.paths.map(row=>row.country).sort(),['Denmark','Finland','Norway','Sweden'],'rendered outline colors did not bind to country cues');
      const outlines=Object.fromEntries(facts.paths.map(row=>[row.country,row]));
      assert.ok(outlines.Norway.top<outlines.Sweden.top&&outlines.Sweden.top<outlines.Denmark.top,'northward controlled outlines did not render higher on screen');
      assert.ok(outlines.Norway.left<outlines.Sweden.left&&outlines.Sweden.left<outlines.Finland.left,'eastward controlled outlines did not render farther right');
      assert.ok(facts.scale.includes('km')||facts.scale.includes('m'));
      assert.equal(facts.scale_visible,true);assert.ok(facts.coordinates.includes(','));
      assert.equal(facts.coordinates_visible,width>900,'coordinate status visibility differs from observed responsive layout');
      await evaluate("document.getElementById('legend-toggle').click()");
      const legend=await evaluate("[...document.querySelectorAll('[data-legend-country]')].filter(row=>row.getClientRects().length).map(row=>row.dataset.legendCountry).sort()");
      assert.deepEqual(legend,['Denmark','Finland','Norway','Sweden']);
      await evaluate("document.getElementById('legend-toggle').click()");
      const shot=await screenshot(width,mode);
      receipt.scenarios.push({width,mode,tile_requests:tiles.length,street_tile_failures:tiles.filter(url=>new URL(url).hostname==='tile.openstreetmap.org').length,terrain_tile_failures:tiles.filter(url=>new URL(url).hostname==='tile.opentopomap.org').length,legend_countries:legend,...facts,screenshot:shot});
    }
  }
  assert.equal(receipt.runtime_errors.length,0);
  receipt.status='PASS';
} catch(error) {receipt.error=String(error.stack||error);if(cdp)receipt.diagnostic=await evaluate("({hash:location.hash,readout:document.getElementById('basemap-readout')?.textContent,paths:document.querySelectorAll('.leaflet-boundary-pane path').length,snapshot:globalThis.BijuxPollenomicsAtlasCapture?.snapshot()})");process.exitCode=1;}
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
