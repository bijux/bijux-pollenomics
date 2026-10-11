// Reconcile actual downloads and record URL restoration with retained source tables.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir, readdir, rm } from 'node:fs/promises';
import { resolve, relative, join, extname } from 'node:path';
import { gunzipSync } from 'node:zlib';

const [candidateDirectory, outputDirectory, browserBinary] = process.argv.slice(2);
if (!candidateDirectory || !outputDirectory || !browserBinary) throw Error('usage: node source-export.mjs CANDIDATE_DIRECTORY OUTPUT_DIRECTORY BROWSER_BINARY');
const candidate = resolve(candidateDirectory), output = resolve(outputDirectory);
await mkdir(output, { recursive: true });
const generation = JSON.parse(await readFile(join(candidate, 'generation.json'), 'utf8'));
const sourceDetails = new Map();
for (const name of await readdir(candidate)) {
  if (!name.includes('.atlas-details.')) continue;
  const script = await readFile(join(candidate, name), 'utf8');
  const marker = 'globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push(';
  const envelope = JSON.parse(script.slice(script.indexOf(marker) + marker.length, -3));
  const text = envelope.payload_encoding === 'gzip_base64' ? gunzipSync(Buffer.from(envelope.payload_gzip_base64, 'base64')).toString('utf8') : envelope.payload_json;
  assert.equal(createHash('sha256').update(text).digest('hex'), envelope.payload_sha256);
  for (const record of JSON.parse(text).records) sourceDetails.set(record.record_id, record);
}
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
const receipt = {schema_version:'atlas-source-pollen-export-verification.v1',status:'FAIL',downloads:[],url_replays:[],runtime_errors:[]};
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
    const initialUrl=`http://127.0.0.1:${server.address().port}/index.html?viewport=${width}#basemap=none`;
    await navigate(initialUrl);
    await waitFor(`location.search === '?viewport=${width}' && document.getElementById('map')?.getAttribute('aria-busy') === 'false'`);
    await evaluate("document.getElementById('search-toggle').click()");
    await cdp.send('Input.insertText',{text:'Ageröds Mosse'});
    await waitFor("document.querySelector('[data-search-index]') !== null");
    await key('Enter',13);
    await waitFor("document.getElementById('focus-export').disabled === false");
    await evaluate("document.getElementById('focus-tab-chronology').focus()");
    await key('Enter',13);
    const first=await download(width,'selected','neotoma:site:12');
    const sharedUrl=first.selection.shared_url;
    const params=new URL(sharedUrl).hash.slice(1);
    assert.equal(new URLSearchParams(params).get('focus_record'),'neotoma:site:12');
    assert.equal(new URLSearchParams(params).get('focus_tab'),'chronology');
    await navigate(sharedUrl);
    await waitFor("document.getElementById('focus-export')?.disabled === false && document.getElementById('focus-tab-chronology')?.getAttribute('aria-selected') === 'true'");
    const restored=await download(width,'restored','neotoma:site:12');
    assert.deepEqual(restored,first,'download changes after exact shared URL replay');
    receipt.url_replays.push({width,record_id:first.record_id,feature_identity:first.feature_identity,tab:'chronology',download_equal:true});
    await evaluate("document.getElementById('focus-next').focus()");
    await key('Enter',13);
    await waitFor("document.getElementById('focus-title').textContent === 'Bergakyllen' && document.getElementById('focus-export').disabled === false");
    await download(width,'next','neotoma:site:3009');
    const stale=new URL(sharedUrl);stale.searchParams.set('refused','filtered-record');stale.hash=`${new URL(sharedUrl).hash}&countries=none`;
    await navigate(stale.href);
    await waitFor("location.search.includes('refused=filtered-record') && document.getElementById('map')?.getAttribute('aria-busy') === 'false'");
    await waitFor("document.getElementById('topbar-state-pill').textContent.includes('Shared record is unavailable')");
    assert.equal(await evaluate("document.getElementById('focus-card').hidden"),true);
    receipt.url_replays.push({width,record_id:'neotoma:site:12',excluded_by_filters:true,drawer_hidden:true});
  }
  assert.equal(receipt.runtime_errors.length,0);
  receipt.status='PASS';
} catch(error) { receipt.error=String(error.stack||error);process.exitCode=1; }
finally {
  clearTimeout(budget);if(cdp)cdp.close();browser.kill('SIGTERM');const kill=setTimeout(()=>browser.kill('SIGKILL'),4000);await closed;clearTimeout(kill);
  await new Promise(accept=>server.close(accept));
  receipt.served_files_sha256=Object.fromEntries([...requests].sort());
  receipt.verifier_sha256=createHash('sha256').update(await readFile(new URL(import.meta.url))).digest('hex');
  await writeFile(join(output,'receipt.json'),`${JSON.stringify(receipt,null,2)}\n`);
  await writeFile(join(output,'browser.log'),log);
  await rm(join(output,'browser-profile'),{recursive:true,force:true});
}

function decoded(table) {
  return table.records.map(row=>Object.fromEntries(table.fields.map((field,index)=>[field,row[index]===null?null:table.identifier_prefixes?.[field]?`${table.identifier_prefixes[field]}${row[index]}`:row[index]])));
}
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
async function download(width,stage,recordId) {
  const directory=join(output,`${width}-${stage}`);await mkdir(directory,{recursive:true});
  await cdp.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:directory});
  await evaluate("document.getElementById('focus-export').focus()");await key('Enter',13);
  const filename=`${recordId.replace(/[^A-Za-z0-9._-]+/g,'-')}.pollen-series.json`;
  const file=join(directory,filename),deadline=Date.now()+20000;
  let bytes;
  while(Date.now()<deadline){try{bytes=await readFile(file);JSON.parse(bytes.toString('utf8'));break;}catch{await new Promise(accept=>setTimeout(accept,50));}}
  if(!bytes)throw Error(`download timed out: ${filename}`);
  const payload=JSON.parse(bytes.toString('utf8')),source=sourceDetails.get(recordId),summary=generation.source_records.find(record=>record.record_id===recordId);
  assert.equal(payload.schema_version,'source-pollen-record-export.v1');assert.equal(payload.record_id,recordId);
  for(const [key,table] of [['samples',source.tabs.samples.samples],['chronology_claims',source.tabs.chronology],['pollen_observations',source.tabs.pollen_composition],['source_variables',source.tabs.pollen_composition.variables],['collection_units',source.tabs.samples.collection_units],['datasets',source.tabs.samples.datasets]]) {
    assert.equal(payload[key].record_count,table.record_count,key);assert.deepEqual(payload[key].records,decoded(table),key);
  }
  assert.deepEqual(payload.source_provenance,source.tabs.provenance);
  assert.equal(payload.temporal_support.interpolation_allowed,false);
  assert.equal(payload.temporal_support.site_range_is_continuous_support,false);
  const statuses=new Map();for(const row of payload.chronology_claims.records){const key=JSON.stringify([row.calibration_status,row.comparability_status]);statuses.set(key,(statuses.get(key)||0)+1);}
  for(const status of summary.chronology_status_counts)assert.equal(statuses.get(JSON.stringify([status.calibration,status.comparability])),status.count);
  receipt.downloads.push({width,stage,record_id:recordId,path:relative(output,file),sha256:createHash('sha256').update(bytes).digest('hex'),sample_count:payload.samples.record_count,chronology_claim_count:payload.chronology_claims.record_count,observation_count:payload.pollen_observations.record_count,complete_source_tables_equal:true,chronology_status_counts:summary.chronology_status_counts});
  return payload;
}
async function evaluate(expression){const value=await cdp.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(value.exceptionDetails)throw Error(JSON.stringify(value.exceptionDetails));return value.result.value;}
async function waitFor(expression){const deadline=Date.now()+20000;while(Date.now()<deadline){if(await evaluate(expression))return;await new Promise(accept=>setTimeout(accept,50));}throw Error(`timed out: ${expression}`);}
async function key(name,code){await cdp.send('Input.dispatchKeyEvent',{type:'keyDown',key:name,code:name,windowsVirtualKeyCode:code,...(name==='Enter'?{text:'\r'}:{})});await cdp.send('Input.dispatchKeyEvent',{type:'keyUp',key:name,windowsVirtualKeyCode:code});}
async function connect(url){return new Promise((accept,reject)=>{const socket=new WebSocket(url),pending=new Map(),listeners=new Set();let id=0;socket.addEventListener('error',reject);socket.addEventListener('open',()=>{socket.addEventListener('message',event=>{const value=JSON.parse(event.data);if(!value.id){listeners.forEach(listener=>listener(value));return;}const request=pending.get(value.id);if(!request)return;pending.delete(value.id);clearTimeout(request.timeout);if(value.error)request.reject(Error(JSON.stringify(value.error)));else request.accept(value.result);});accept({send(method,params={}){const requestId=++id;return new Promise((acceptRequest,rejectRequest)=>{const timeout=setTimeout(()=>{pending.delete(requestId);rejectRequest(Error(`CDP timeout: ${method}`));},20000);pending.set(requestId,{accept:acceptRequest,reject:rejectRequest,timeout});socket.send(JSON.stringify({id:requestId,method,params}));});},listen(callback){listeners.add(callback);},close(){socket.close();}});});});}
