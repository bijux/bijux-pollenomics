// Verify disconnected authentic sample supports through the real static map and controls.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { resolve, relative, join, extname } from 'node:path';

const [candidateDirectory, outputDirectory, browserBinary] = process.argv.slice(2);
if (!candidateDirectory || !outputDirectory || !browserBinary) throw Error('usage: node components.mjs CANDIDATE OUTPUT BROWSER');
const candidate=resolve(candidateDirectory), output=resolve(outputDirectory);
await mkdir(output,{recursive:true});
const generation=JSON.parse(await readFile(join(candidate,'generation.json'),'utf8'));
assert.equal(generation.schema_version,'atlas-sample-owned-chronology-candidate.v1');
assert.equal(generation.component_index_schema,'atlas-static-indexes.v5');
const requests=new Map();
const server=createServer(async(request,response)=>{
  const path=resolve(candidate,`.${decodeURIComponent(new URL(request.url,'http://localhost').pathname)}`);
  if(relative(candidate,path).startsWith('..')){response.writeHead(403).end();return;}
  try{const bytes=await readFile(path);requests.set(relative(candidate,path),hash(bytes));const type={'.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json','.png':'image/png'}[extname(path)]||'application/octet-stream';response.writeHead(200,{'Content-Type':type,'Cache-Control':'no-store'}).end(bytes);}catch{response.writeHead(404).end();}
});
await new Promise(accept=>server.listen(0,'127.0.0.1',accept));
const browser=spawn(browserBinary,['--headless=new','--disable-gpu','--disable-background-networking','--no-first-run','--no-default-browser-check','--remote-debugging-port=0',`--user-data-dir=${join(output,'browser-profile')}`,'about:blank'],{stdio:['ignore','pipe','pipe']});
const closed=new Promise(accept=>browser.once('close',accept));
let log='',cdp;
const receipt={schema_version:'atlas-sample-owned-chronology-browser.v1',status:'FAIL',source_cases:[],control_replays:[],screenshots:[],runtime_errors:[],source_review_or_event_admission:false};
const budget=setTimeout(()=>browser.kill('SIGKILL'),120000);
try{
  const endpoint=await new Promise((accept,reject)=>{const timer=setTimeout(()=>reject(Error('debugger readiness timed out')),20000);browser.once('error',reject);browser.stderr.on('data',bytes=>{log+=bytes.toString();const match=log.match(/DevTools listening on (ws:\/\/[^\s]+)/);if(match){clearTimeout(timer);accept(match[1]);}});});
  const origin=new URL(endpoint);origin.protocol='http:';origin.pathname='';
  const target=await(await fetch(`${origin.origin}/json/new?about:blank`,{method:'PUT'})).json();
  cdp=await connect(target.webSocketDebuggerUrl);
  await cdp.send('Page.enable');await cdp.send('Runtime.enable');await cdp.send('Network.enable');
  cdp.listen(event=>{if(event.method==='Runtime.exceptionThrown')receipt.runtime_errors.push(event.params.exceptionDetails);});
  receipt.browser=await cdp.send('Browser.getVersion');
  const base=`http://127.0.0.1:${server.address().port}/index.html`;
  for(const width of [1440,390]){
    await cdp.send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
    for(const query of generation.queries){
      const params=new URLSearchParams({basemap:'none',countries:'Sweden,Denmark',layers:'sample-owned-chronology',time_start:String(query.start_bp),time_interval:String(query.end_bp-query.start_bp),panel:'collapsed'});
      await navigate(`${base}?width=${width}&case=${encodeURIComponent(query.label)}#${params}`);
      await waitFor('globalThis.BijuxPollenomicsAtlasCapture?.snapshot().ready===true');
      const snapshot=await evaluate('BijuxPollenomicsAtlasCapture.snapshot()');
      assert.deepEqual(snapshot.time_window_bp,{younger_bp:query.start_bp,older_bp:query.end_bp});
      assert.equal(snapshot.visible_point_count,query.expected_visible_features,'Authentic source components must determine visible features');
      assert.equal(snapshot.visible_governed_candidate_count,0);
      assert.equal(snapshot.scientific_posture.observation_chronology_is_propagation,false);
      receipt.source_cases.push({width,...query,actual_visible_features:snapshot.visible_point_count,time_window_bp:snapshot.time_window_bp,missing_source_sample_contributes_no_dated_feature:true});
      if(query.label==='disjoint-source-gap'||query===generation.queries[1]){
        const path=`${width}-${query.label}.png`;const capture=await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});const bytes=Buffer.from(capture.data,'base64');await writeFile(join(output,path),bytes);receipt.screenshots.push({path,sha256:hash(bytes),bytes:bytes.length,width});
      }
    }
    // Real DOM input events must restore the gap without relying on URL initialization.
    await evaluate("document.getElementById('time-interval-slider').value='1';document.getElementById('time-interval-slider').dispatchEvent(new Event('input',{bubbles:true}));");
    await evaluate("document.getElementById('time-start-slider').value='4141';document.getElementById('time-start-slider').dispatchEvent(new Event('input',{bubbles:true}));");
    await waitFor('BijuxPollenomicsAtlasCapture.snapshot().time_window_bp.younger_bp===4141 && BijuxPollenomicsAtlasCapture.snapshot().ready===true');
    const restored=await evaluate('BijuxPollenomicsAtlasCapture.snapshot()');assert.equal(restored.visible_point_count,0);receipt.control_replays.push({width,input_events:'window span and younger BP',gap_bp:4141,visible_points:0});
  }
  const download=await(await fetch(`${base.replace('/index.html','')}/sample-support.json`)).json();
  assert.deepEqual(download.records,generation.source_records,'Static source-support download must preserve every exact selected source field');
  assert.equal(download.records[1].feature.time_start_bp,null);assert.equal(download.records[1].feature.time_end_bp,null);
  receipt.source_support_download={source_records:download.records.length,selected_sample_rows:download.records.reduce((sum,row)=>sum+row.selected_rows.length,0),all_selected_fields_exact:true,undated_original_sample_id:download.records[1].selected_rows[0].genetic_id,undated_is_null_not_zero:true,sha256:hash(await readFile(join(candidate,'sample-support.json')))};
  assert.equal(receipt.runtime_errors.length,0);receipt.status='PASS';
}catch(error){receipt.error=String(error.stack||error);if(cdp)receipt.diagnostic=await evaluate('({snapshot:globalThis.BijuxPollenomicsAtlasCapture?.snapshot(),state:document.getElementById("topbar-state-pill")?.textContent,hash:location.hash})');process.exitCode=1;}
finally{
  clearTimeout(budget);if(cdp)cdp.close();browser.kill('SIGTERM');const kill=setTimeout(()=>browser.kill('SIGKILL'),4000);await closed;clearTimeout(kill);await new Promise(accept=>server.close(accept));receipt.served_files_sha256=Object.fromEntries([...requests].sort());receipt.verifier_sha256=hash(await readFile(new URL(import.meta.url)));await writeFile(join(output,'receipt.json'),`${JSON.stringify(receipt,null,2)}\n`);await writeFile(join(output,'browser.log'),log);await rm(join(output,'browser-profile'),{recursive:true,force:true});
}
function hash(bytes){return createHash('sha256').update(bytes).digest('hex');}
async function navigate(url){let waiting=true;const loaded=new Promise((accept,reject)=>{const timeout=setTimeout(()=>{waiting=false;reject(Error('page load timed out'));},20000);cdp.listen(event=>{if(waiting&&event.method==='Page.loadEventFired'){waiting=false;clearTimeout(timeout);accept();}});});const navigation=await cdp.send('Page.navigate',{url});if(!navigation.loaderId)await cdp.send('Page.reload',{ignoreCache:true});await loaded;}
async function evaluate(expression){const value=await cdp.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(value.exceptionDetails)throw Error(JSON.stringify(value.exceptionDetails));return value.result.value;}
async function waitFor(expression){const deadline=Date.now()+20000;while(Date.now()<deadline){if(await evaluate(expression))return;await new Promise(accept=>setTimeout(accept,50));}throw Error(`timed out: ${expression}`);}
async function connect(url){return new Promise((accept,reject)=>{const socket=new WebSocket(url),pending=new Map(),listeners=new Set();let id=0;socket.addEventListener('error',reject);socket.addEventListener('open',()=>{socket.addEventListener('message',event=>{const value=JSON.parse(event.data);if(!value.id){listeners.forEach(listener=>listener(value));return;}const request=pending.get(value.id);if(!request)return;pending.delete(value.id);clearTimeout(request.timeout);if(value.error)request.reject(Error(JSON.stringify(value.error)));else request.accept(value.result);});accept({send(method,params={}){const requestId=++id;return new Promise((acceptRequest,rejectRequest)=>{const timeout=setTimeout(()=>{pending.delete(requestId);rejectRequest(Error(`CDP timeout: ${method}`));},20000);pending.set(requestId,{accept:acceptRequest,reject:rejectRequest,timeout});socket.send(JSON.stringify({id:requestId,method,params}));});},listen(callback){listeners.add(callback);},close(){socket.close();}});});});}
