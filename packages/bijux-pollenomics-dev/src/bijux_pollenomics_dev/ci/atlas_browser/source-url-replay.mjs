// Verify complete shared state through external hash navigation and browser history.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir, readdir, rm } from 'node:fs/promises';
import { resolve, relative, join, extname } from 'node:path';

const [candidateDirectory, outputDirectory, browserBinary] = process.argv.slice(2);
if (!candidateDirectory || !outputDirectory || !browserBinary) throw Error('usage: node source-url-replay.mjs CANDIDATE_DIRECTORY OUTPUT_DIRECTORY BROWSER_BINARY');
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
const receipt = {schema_version:'atlas-source-url-replay-verification.v1',status:'FAIL',baseline_states:[],hash_replays:[],history_replays:[],internal_writes:[],stale_writers:[],runtime_errors:[]};
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
  cdp.listen(event=>{if(event.method==='Runtime.exceptionThrown')receipt.runtime_errors.push(event.params.exceptionDetails);});
  await cdp.send('Network.enable');
  await cdp.send('Network.setBlockedURLs',{urls:['*://tile.openstreetmap.org/*','*://*.tile.openstreetmap.org/*','*://tile.opentopomap.org/*','*://*.tile.opentopomap.org/*']});
  receipt.browser=await cdp.send('Browser.getVersion');
  for (const width of [1440,390]) {
    await cdp.send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
    const origin=`http://127.0.0.1:${server.address().port}/index.html?viewport=${width}`;
    const baselines=[];
    for(const [index,record] of generation.source_records.entries()) {
      const hash=new URLSearchParams({basemap:'none',countries:record.country,layers:'neotoma-pollen,sead-sites',scientific_signals:'none',cross_border:'only',density:String(30+index*10),diameter:String(65+index*5),panel:'collapsed',legend:'expanded',animal_scope:'comparator',animal_nordic:'only',time_start:'0',time_interval:'12000',focus_layer:record.layer_key,focus_feature:record.feature_identity,focus_record:record.record_id,focus_tab:'chronology'});
      if(record.record_id==='sead:site:6468'){hash.delete('time_start');hash.delete('time_interval');}
      await navigate(`${origin}&baseline=${index}#${hash}`);
      await ready(record);
      const state=await captureState();
      assert.deepEqual(state.countries,[record.country]);assert.equal(state.focus_title,record.title);assert.equal(state.focus_tab,'chronology');
      assert.equal(new URLSearchParams(state.hash.slice(1)).get('focus_record'),record.record_id);
      assert.equal(state.density,String(30+index*10));assert.equal(state.diameter,String(65+index*5));assert.equal(state.cross_border,true);
      assert.equal(state.candidate_count,0);assert.equal(state.propagation,false);
      baselines.push({record,state});
      receipt.baseline_states.push({width,record_id:record.record_id,hash:state.hash,state_sha256:hashJSON(state)});
    }
    await navigate(`${origin}#basemap=none`);
    await waitFor("globalThis.BijuxPollenomicsAtlasCapture?.snapshot().ready === true");
    await cdp.send('Page.resetNavigationHistory');
    let currentTimeOrigin=await evaluate('performance.timeOrigin');
    for(const {record,state} of baselines) {
      const response=await cdp.send('Page.navigate',{url:`${origin}${state.hash}`});
      await ready(record);
      await waitFor(`performance.timeOrigin !== ${currentTimeOrigin}`);
      const actual=await captureState();assert.deepEqual(actual,state,'direct external hash replay lost complete state');
      const timeOrigin=await stableDocument();
      receipt.hash_replays.push({width,record_id:record.record_id,country:record.country,cdp_same_document_navigation:!response.loaderId,complete_state_equal:true,incoming_hash_preserved:true,document_reinitialized:timeOrigin!==currentTimeOrigin,no_reload_loop:true});
      currentTimeOrigin=timeOrigin;
    }
    const history=await cdp.send('Page.getNavigationHistory');
    assert.equal(history.currentIndex,baselines.length);
    const entries=history.entries.slice(1);
    for(const [direction,indexes] of [['back',[6,5,4,3,2,1,0]],['forward',[1,2,3,4,5,6,7]]]) {
      for(const index of indexes) {
        const {record,state}=baselines[index];
        await cdp.send('Page.navigateToHistoryEntry',{entryId:entries[index].id});
        await ready(record);
        const actual=await captureState();assert.deepEqual(actual,state,'history replay lost shared state');
        const timeOrigin=await stableDocument();
        receipt.history_replays.push({width,direction,record_id:record.record_id,country:record.country,complete_state_equal:true,incoming_hash_preserved:true,no_reload_loop:true});
        currentTimeOrigin=timeOrigin;
      }
    }
    const before=await evaluate('performance.timeOrigin');
    await evaluate("document.getElementById('focus-tab-provenance').click()");
    await waitFor("new URLSearchParams(location.hash.slice(1)).get('focus_tab') === 'provenance'");
    assert.equal(await stableDocument(),before,'internal tab publication reloaded the document');
    await evaluate("document.getElementById('density-opacity-slider').value='50';document.getElementById('density-opacity-slider').dispatchEvent(new Event('input',{bubbles:true}))");
    await waitFor("new URLSearchParams(location.hash.slice(1)).get('density') === '50'");
    assert.equal(await stableDocument(),before,'internal control publication reloaded the document');
    receipt.internal_writes.push({width,tab:'provenance',density:50,same_document:true});
    const incoming=baselines[0];
    await evaluate(`location.hash=${JSON.stringify(incoming.state.hash)};document.getElementById('focus-tab-overview').click();true`);
    await ready(incoming.record);
    assert.deepEqual(await captureState(),incoming.state,'old drawer writer replaced incoming external state');
    await stableDocument();
    receipt.stale_writers.push({width,incoming_record_id:incoming.record.record_id,incoming_country:incoming.record.country,old_tab_writer:'overview',incoming_hash_and_complete_state_preserved:true,no_reload_loop:true});
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

function hashJSON(value){return createHash('sha256').update(JSON.stringify(value)).digest('hex');}
async function ready(record){await waitFor(`globalThis.BijuxPollenomicsAtlasCapture?.snapshot().ready === true && document.getElementById('focus-title')?.textContent === ${JSON.stringify(record.title)} && document.getElementById('focus-tab-chronology')?.getAttribute('aria-selected') === 'true' && !document.getElementById('focus-detail').textContent.includes('Loading')`);}
async function captureState(){return evaluate(`(()=>{const snapshot=BijuxPollenomicsAtlasCapture.snapshot();return {hash:location.hash,countries:snapshot.countries,time:snapshot.time_window_bp,layers:snapshot.capture_layers.active_keys,point_count:snapshot.visible_point_count,candidate_count:snapshot.visible_governed_candidate_count,source_chronology:snapshot.source_chronology,modeled_context:snapshot.modeled_context,propagation:snapshot.scientific_posture.observation_chronology_is_propagation,classification_status:snapshot.scientific_posture.classifications_status,focus_title:document.getElementById('focus-title').textContent,focus_tab:document.querySelector('#focus-tabs [aria-selected=true]').getAttribute('data-focus-tab'),detail:document.getElementById('focus-detail').textContent,density:document.getElementById('density-opacity-slider').value,diameter:document.getElementById('diameter-slider').value,cross_border:document.getElementById('cross-border-only').checked,panel_collapsed:document.getElementById('sidebar').classList.contains('is-collapsed')};})()`);}
async function stableDocument(){const before=await evaluate('performance.timeOrigin');await new Promise(accept=>setTimeout(accept,150));assert.equal(await evaluate('performance.timeOrigin'),before,'URL replay caused a document reload loop');return before;}
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
