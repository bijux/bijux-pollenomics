// Replay populated modeled frames and signed native selections through actual downloads.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir, readdir, rm } from 'node:fs/promises';
import { resolve, relative, join, extname } from 'node:path';
import { gunzipSync } from 'node:zlib';
import { selectionAgreement } from './native-lra.mjs';

const [candidateDirectory, outputDirectory, browserBinary] = process.argv.slice(2);
if (!candidateDirectory || !outputDirectory || !browserBinary) throw Error('usage: node frame-url-replay.mjs CANDIDATE_DIRECTORY OUTPUT_DIRECTORY BROWSER_BINARY');
const candidate = resolve(candidateDirectory), output = resolve(outputDirectory);
await mkdir(output, { recursive: true });
const generation = JSON.parse(await readFile(join(candidate, 'generation.json'), 'utf8'));
const sourceFeatures=[];
for(const name of await readdir(join(candidate,'modeled'))) {
  if(!name.includes('.atlas-nodes.'))continue;
  const script=await readFile(join(candidate,'modeled',name),'utf8'),marker='globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push(';
  const envelope=JSON.parse(script.slice(script.indexOf(marker)+marker.length,-3));
  const bytes=envelope.payload_encoding==='gzip_base64'?gunzipSync(Buffer.from(envelope.payload_gzip_base64,'base64')):Buffer.from(envelope.payload_json);
  assert.equal(createHash('sha256').update(bytes).digest('hex'),envelope.payload_sha256);
  for(const feature of JSON.parse(bytes).features)if(!sourceFeatures.some(existing=>existing.properties.record_id===feature.properties.record_id))sourceFeatures.push(feature);
}
const nativeView=JSON.parse(await readFile(join(candidate,'native','native-view.json'),'utf8'));
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
const receipt = {schema_version:'atlas-populated-frame-url-replay-verification.v1',status:'FAIL',modeled_frames:[],native_selections:[],hash_replays:[],history_replays:[],native_refusals:[],runtime_errors:[]};
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
    for(const kind of ['modeled','native']) {
      const origin=`http://127.0.0.1:${server.address().port}/${kind}/${kind==='native'?'map':'index'}.html?viewport=${width}`;
      const cases=kind==='modeled'?modeledCases():nativeCases();
      const baselines=[];
      for(const [index,item] of cases.entries()) {
        await navigate(`${origin}&baseline=${index}#${item.hash}`);
        await ready(kind);
        const state=await observe(kind,width,`baseline-${index}`);
        baselines.push(state);
      }
      await navigate(`${origin}#basemap=none&density=55`);await ready(kind);await cdp.send('Page.resetNavigationHistory');
      for(const [index,baseline] of baselines.entries()) {
        const before=await evaluate('performance.timeOrigin');
        const navigation=await cdp.send('Page.navigate',{url:`${origin}${baseline.hash}`});
        await waitFor(`performance.timeOrigin !== ${before}`);await ready(kind);
        const state=await observe(kind,width,`hash-${index}`);assert.deepEqual(state,baseline);
        await stableDocument();
        receipt.hash_replays.push({width,kind,index,same_document_command:!navigation.loaderId,complete_state_and_download_equal:true,no_reload_loop:true});
      }
      const history=await cdp.send('Page.getNavigationHistory');assert.equal(history.currentIndex,cases.length);const entries=history.entries.slice(1);
      for(const [direction,indexes] of [['back',[2,1,0]],['forward',[1,2,3]]])for(const index of indexes) {
        const before=await evaluate('performance.timeOrigin');
        await cdp.send('Page.navigateToHistoryEntry',{entryId:entries[index].id});await waitFor(`performance.timeOrigin !== ${before}`);await ready(kind);
        const state=await observe(kind,width,`${direction}-${index}`);assert.deepEqual(state,baselines[index]);await stableDocument();
        receipt.history_replays.push({width,kind,direction,index,complete_state_and_download_equal:true,no_reload_loop:true});
      }
      if(kind==='native') {
        const invalid=new URL(`${origin}${baselines[0].hash}`),params=new URLSearchParams(invalid.hash.slice(1));params.set('calendar_profile','calendar-bp1950-incompatible');invalid.hash=params.toString();
        const before=await evaluate('performance.timeOrigin');await cdp.send('Page.navigate',{url:invalid.href});await waitFor(`performance.timeOrigin !== ${before}`);await ready(kind);
        const refused=await evaluate(`(async()=>{let export_refused=false;try{await __BIJUX_LRA_VIEW__.exportSelection();}catch{export_refused=true;}return {snapshot:__BIJUX_LRA_VIEW__.snapshot(),status:document.getElementById('lra-selection-status').textContent,download_disabled:document.getElementById('lra-download').disabled,export_refused,profile:new URLSearchParams(location.hash.slice(1)).get('calendar_profile')}})()`);
        assert.ok(refused.status.includes('Native URL refused'));assert.ok(refused.snapshot.refusal);assert.equal(refused.snapshot.counts.selected_rows,0);assert.equal(refused.download_disabled,true);assert.equal(refused.export_refused,true);assert.equal(refused.profile,'calendar-bp1950-incompatible');
        const invalidOrigin=await evaluate('performance.timeOrigin');await cdp.send('Page.navigateToHistoryEntry',{entryId:entries[3].id});await waitFor(`performance.timeOrigin !== ${invalidOrigin}`);await ready(kind);
        assert.deepEqual(await observe(kind,width,'refusal-back-recovery'),baselines[3]);await stableDocument();
        receipt.native_refusals.push({width,profile:'calendar-bp1950-incompatible',visible_refusal:true,no_selected_rows:true,export_refused:true,incoming_invalid_profile_preserved:true,history_recovery_equal:true});
      }
    }
  }
  assert.equal(receipt.runtime_errors.length,0);
  receipt.status='PASS';
} catch(error) { receipt.error=String(error.stack||error);if(cdp)receipt.diagnostic=await evaluate("({hash:location.hash,snapshot:globalThis.BijuxPollenomicsAtlasCapture?.snapshot(),modeled:document.getElementById('modeled-context-state')?.textContent,native:document.getElementById('lra-selection-status')?.textContent})");process.exitCode=1; }
finally {
  clearTimeout(budget);if(cdp)cdp.close();browser.kill('SIGTERM');const kill=setTimeout(()=>browser.kill('SIGKILL'),4000);await closed;clearTimeout(kill);
  await new Promise(accept=>server.close(accept));
  receipt.served_files_sha256=Object.fromEntries([...requests].sort());
  receipt.verifier_sha256=createHash('sha256').update(await readFile(new URL(import.meta.url))).digest('hex');
  receipt.verifier_imports_sha256=Object.fromEntries(await Promise.all(['native-lra.mjs','signed-native-lra.mjs'].map(async name=>[name,createHash('sha256').update(await readFile(new URL(name,import.meta.url))).digest('hex')])));
  await writeFile(join(output,'receipt.json'),`${JSON.stringify(receipt,null,2)}\n`);
  await writeFile(join(output,'browser.log'),log);
  await rm(join(output,'browser-profile'),{recursive:true,force:true});
}

function digest(bytes){return createHash('sha256').update(bytes).digest('hex');}
function modeledCases(){const windows=generation.modeled.manifest.windows_oldest_to_present;return [
 {index:0,family:'source_land_cover_types',metric:'OL',countries:null},
 {index:12,family:'source_pft_codes',metric:'ISTS',countries:'Denmark'},
 {index:24,family:'exact_taxa',metric:'Alnus.glutinosa',countries:'Finland'},
 {index:24,family:'source_land_cover_types',metric:'ET',countries:null},
].map(item=>({hash:new URLSearchParams({basemap:'none',modeled_context:windows[item.index].label,modeled_family:item.family,modeled_metric:item.metric,...(item.countries?{countries:item.countries}:{})}).toString()}));}
function nativeCases(){const unique=field=>[...new Set(nativeView.rows.map(row=>row[field]))].sort();const all={roles:unique('role'),site_ids:unique('site_id'),taxa:unique('taxon'),bin_ids:unique('bin_id')};return [
 {selection:all,window:[-.75,.75]},
 {selection:{...all,roles:['regional'],taxa:[all.taxa[0]]},window:[-.25,.25]},
 {selection:{...all,roles:['local']},window:[0,0]},
 {selection:{...all,roles:[]},window:[-.5,.5]},
].map(item=>({hash:new URLSearchParams({basemap:'none',lra_view:generation.native.native_view_sha256,lra_selection:JSON.stringify(item.selection),calendar_younger:String(item.window[0]),calendar_older:String(item.window[1]),calendar_profile:generation.native.temporal_profile,calendar_view:generation.native.native_view_sha256}).toString()}));}
async function ready(kind){await waitFor(`globalThis.BijuxPollenomicsAtlasCapture?.snapshot().ready === true ${kind==='native'?"&& globalThis.__BIJUX_LRA_VIEW__ !== undefined":''}`);}
async function observe(kind,width,stage){
  const capture=await evaluate('BijuxPollenomicsAtlasCapture.snapshot()');
  if(kind==='modeled') {
    const frame=capture.modeled_context;assert.ok(frame);assert.equal(frame.evidence_role,'context_only');assert.equal(frame.interpolation_allowed,false);assert.equal(frame.propagation_use_allowed,false);
    const directory=join(output,kind,`${width}-${stage}`);const payload=await downloaded(directory,'modeled-context-download');
    const context=payload.value.modeled_context;
    assert.equal(payload.value.schema_version,'modeled-context-visible-frame.v3');assert.equal(context.metric_key,frame.metric_key);assert.equal(context.metric_family_key,frame.metric_family_key);assert.equal(context.evidence_role,'context_only');assert.equal(context.interpolation_allowed,false);assert.equal(context.propagation_use_allowed,false);
    const expected=sourceFeatures.filter(feature=>feature.properties.time_label===frame.window_label&&capture.countries.includes(feature.properties.country)).sort((left,right)=>left.properties.record_id.localeCompare(right.properties.record_id));
    assert.deepEqual(payload.value.features,expected,'actual frame differs from exact retained modeled source records');
    const missing=expected.filter(feature=>feature.properties.quality_class==='no_pollen_data');
    for(const feature of missing)for(const field of ['reconstruction_values','standard_errors'])assert.ok(Object.values(feature.properties[field]).every(value=>value===null));
    assert.equal(context.quality_class_counts.no_pollen_data||0,missing.length);assert.equal(context.quality_class_count_denominator,expected.length);
    assert.equal(context.source_quality_class_counts.no_pollen_data,generation.modeled.manifest.no_pollen_data_count??generation.modeled.manifest.quality_class_counts.no_pollen_data);
    receipt.modeled_frames.push({width,stage,window:frame.window_label,family:frame.metric_family_key,metric:frame.metric_key,countries:capture.countries,source_records_equal:true,features:expected.length,no_pollen_data_null_records:missing.length,path:relative(output,payload.file),sha256:payload.sha256,evidence_role:'context_only',interpolation_allowed:false,propagation_use_allowed:false});
    return {hash:await evaluate('location.hash'),frame,countries:capture.countries,time:capture.time_window_bp,download_sha256:payload.sha256,metric:await evaluate("document.getElementById('modeled-context-metric').value"),family:await evaluate("document.getElementById('modeled-context-family').value")};
  }
  const observation=await evaluate(`(async()=>({snapshot:__BIJUX_LRA_VIEW__.snapshot(),exported:await __BIJUX_LRA_VIEW__.exportSelection(),capture:BijuxPollenomicsAtlasCapture.snapshot(),dom:{selection:Object.fromEntries(Object.entries({roles:'lra-role',site_ids:'lra-site',taxa:'lra-taxon',bin_ids:'lra-bin'}).map(([key,id])=>[key,[...document.getElementById(id).selectedOptions].map(option=>option.value)])),rows:[...document.querySelectorAll('#lra-estimates tbody tr[data-row-id]')].map(row=>({row_id:row.dataset.rowId,role:row.cells[0].textContent,site_id:row.cells[1].textContent,taxon:row.cells[2].textContent,statistic:row.cells[3].textContent,value:row.dataset.nativeValue,unit:row.dataset.nativeUnit,missing:row.dataset.missing,visible_value:row.cells[4].textContent,visible_unit:row.cells[5].textContent})),model_cues:[...document.querySelectorAll('.leaflet-marker-icon [data-lra-role]')].map(node=>({role:node.dataset.lraRole,text:node.textContent,anchor_id:node.dataset.lraAnchorId}))}}))()`);
  assert.ok(selectionAgreement(nativeView,observation,generation.native.native_view_sha256),'native source units/missingness/selection agreement');
  assert.equal(observation.exported.payload.scientific_acceptance,'not_evaluated');assert.equal(observation.exported.payload.publication_authorized,false);
  const payload=await downloaded(join(output,kind,`${width}-${stage}`),'lra-download');assert.equal(payload.sha256,observation.exported.sha256);assert.deepEqual(payload.value,observation.exported.payload);
  receipt.native_selections.push({width,stage,selection:observation.snapshot.selection,calendar_window:observation.snapshot.global_context.time_window_bp,profile:generation.native.temporal_profile,source_rows_equal:true,selected_rows:observation.snapshot.counts.selected_rows,missing_values:observation.snapshot.counts.missing_values,path:relative(output,payload.file),sha256:payload.sha256,scientific_acceptance:'not_evaluated',publication_authorized:false,posterior_draw_channel:'unavailable_in_retained_paired_view'});
  return {hash:await evaluate('location.hash'),snapshot:observation.snapshot,download_sha256:payload.sha256,dom:observation.dom};
}
async function downloaded(directory,button){await mkdir(directory,{recursive:true});await cdp.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:directory});await evaluate(`document.getElementById('${button}').click()`);const deadline=Date.now()+20000;while(Date.now()<deadline){const files=(await readdir(directory)).filter(name=>!name.endsWith('.crdownload'));if(files.length===1){const file=join(directory,files[0]);try{const bytes=await readFile(file);return {file,sha256:digest(bytes),value:JSON.parse(bytes.toString('utf8'))};}catch{}}await new Promise(accept=>setTimeout(accept,50));}throw Error(`actual download timed out: ${button}`);}
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
