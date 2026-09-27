// Reconcile four-country retained source navigation and complete chronology display.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir, readdir, rm } from 'node:fs/promises';
import { resolve, relative, join, extname } from 'node:path';
import { gunzipSync } from 'node:zlib';

const [candidateDirectory, outputDirectory, browserBinary] = process.argv.slice(2);
if (!candidateDirectory || !outputDirectory || !browserBinary) throw Error('usage: node nordic-country.mjs CANDIDATE_DIRECTORY OUTPUT_DIRECTORY BROWSER_BINARY');
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
const receipt = {schema_version:'atlas-nordic-source-browser-verification.v1',status:'FAIL',country_filters:[],record_navigation:[],chronology_tables:[],runtime_errors:[]};
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
    await navigate(`${origin}#basemap=none`);
    await waitFor("globalThis.BijuxPollenomicsAtlasCapture?.snapshot().ready === true");
    const all=await evaluate('BijuxPollenomicsAtlasCapture.snapshot()');
    assert.deepEqual(all.countries,[...generation.countries].sort());
    assert.equal(all.visible_point_count,8);assert.equal(all.visible_governed_candidate_count,0);
    assert.equal(all.scientific_posture.observation_chronology_is_propagation,false);
    receipt.country_filters.push({width,selection:'all',visible_source_sites:8,visible_governed_candidates:0});
    for(const country of generation.countries) {
      const records=generation.source_records.filter(record=>record.country===country);
      for(const record of records) {
        const hash=new URLSearchParams({basemap:'none',countries:country,focus_layer:record.layer_key,focus_feature:record.feature_identity,focus_record:record.record_id,focus_tab:'chronology'});
        await navigate(`${origin}&record=${encodeURIComponent(record.record_id)}#${hash}`);
        await waitFor(`document.getElementById('focus-title')?.textContent === ${JSON.stringify(record.title)} && document.getElementById('focus-tab-chronology')?.getAttribute('aria-selected') === 'true' && !document.getElementById('focus-detail').textContent.includes('Loading')`);
        const snapshot=await evaluate('BijuxPollenomicsAtlasCapture.snapshot()');
        assert.deepEqual(snapshot.countries,[country]);assert.equal(snapshot.visible_point_count,2);
        assert.equal(snapshot.visible_governed_candidate_count,0);
        const table=sourceDetails.get(record.record_id).tabs.chronology;
        if(table.records) {
          const expected=decodedChronology(table),actual=[];
          const headings=await evaluate("[...document.querySelectorAll('#focus-detail .focus-detail-table thead th')].map(cell=>cell.textContent)");
          assert.deepEqual(headings,Object.keys(expected[0]).map(field=>field.replaceAll('_',' ')));
          while(true) {
            actual.push(...await evaluate("[...document.querySelectorAll('#focus-detail .focus-detail-table tbody tr')].map(row=>[...row.cells].map(cell=>cell.textContent))"));
            const next=await evaluate("document.querySelector('#focus-detail [data-page-direction=next]')?.disabled === false");
            if(!next)break;
            await evaluate("document.querySelector('#focus-detail [data-page-direction=next]').click()");
          }
          assert.deepEqual(actual,expected.map(row=>Object.values(row).map(displayText)),'chronology cells must equal all retained source claims');
          const statuses={};for(const row of expected){const key=JSON.stringify([row.calibration_status,row.comparability_status,row.chronology_eligibility??null]);statuses[key]=(statuses[key]||0)+1;}
          receipt.chronology_tables.push({width,record_id:record.record_id,rows:actual.length,all_source_cells_equal:true,status_counts:statuses,numeric_null_count:expected.filter(row=>row.younger_bp===null&&row.older_bp===null).length});
        } else {
          const text=await evaluate("document.getElementById('focus-detail').textContent");assert.ok(text.includes(table.reason_code));
          receipt.chronology_tables.push({width,record_id:record.record_id,status:'unavailable',reason_code:table.reason_code,source_null_not_zero:true});
        }
        for(const tab of ['classification','relation','provenance']) {
          await evaluate(`document.getElementById('focus-tab-${tab}').click()`);
          await waitFor(`document.getElementById('focus-tab-${tab}').getAttribute('aria-selected') === 'true'`);
          const text=await evaluate("document.getElementById('focus-detail').textContent");
          const expected=tab==='provenance'?record.source_provenance.build_id:record[tab].reason_code;
          if(expected)assert.ok(text.includes(expected),`${record.record_id} ${tab} lost source refusal/build identity`);
        }
        const other=records.find(candidate=>candidate.record_id!==record.record_id);
        await evaluate("document.getElementById('focus-next').focus()");await key('Enter',13);
        await waitFor(`document.getElementById('focus-title').textContent === ${JSON.stringify(other.title)}`);
        assert.equal(new URLSearchParams((await evaluate('location.hash')).slice(1)).get('focus_record'),other.record_id);
        receipt.record_navigation.push({width,country,record_id:record.record_id,next_record_id:other.record_id,exact_url_identity:true,classification_refusal_preserved:true,relation_refusal_preserved:true,source_build_visible:true});
      }
      receipt.country_filters.push({width,selection:country,visible_source_sites:2,visible_governed_candidates:0});
    }
    await evaluate("document.getElementById('countries-none').click()");
    await waitFor('BijuxPollenomicsAtlasCapture.snapshot().visible_point_count === 0');
    assert.equal(await evaluate("document.getElementById('focus-card').hidden"),true);
    await evaluate("document.getElementById('countries-all').click()");
    await waitFor('BijuxPollenomicsAtlasCapture.snapshot().visible_point_count === 8');
    receipt.country_filters.push({width,selection:'none_then_all',zero_visible:true,all_visible:8});
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

function displayText(value){if(value===null)return 'null (source null)';if(value===undefined||value==='')return 'Unavailable';return typeof value==='object'?JSON.stringify(value):String(value);}
function decodedChronology(table) {
  return table.records.map(encoded=>{
    const row=Object.fromEntries(table.fields.map((field,index)=>{
      let value=encoded[index];
      if(table.column_dictionaries?.[field])value=table.column_dictionaries[field][value];
      if(table.list_dictionary_fields?.includes(field))value=value.map(index=>table.list_value_dictionary[index]);
      if(table.identifier_prefixes?.[field]&&value!==null)value=`${table.identifier_prefixes[field]}${value}`;
      return [field,value];
    }));
    if(table.encoding==='sead-chronology-claim-table.v1') {
      const type=row.claim_type,columns=table.source_age_value_columns_by_claim_type[type];
      const age=Object.fromEntries(columns.map((field,index)=>[field,table.source_age_value_dictionaries_by_claim_type[type]?.[field] ? table.source_age_value_dictionaries_by_claim_type[type][field][row.source_age_value[index]] : row.source_age_value[index]]));
      for(const [sourceField,claimField] of Object.entries(table.source_age_value_inherited_fields_by_claim_type[type]))age[sourceField]=row[claimField];
      row.source_age_value=age;
      row.source_relation_path=table.source_relation_path_dictionary[row.source_relation_path].map(([sourceTable,key,valueField])=>({table:sourceTable,key,value:valueField==='common_fields.source_site_id'?table.common_fields.source_site_id:row[valueField]}));
      return {...table.common_fields,...row};
    }
    return row;
  });
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
async function evaluate(expression){const value=await cdp.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(value.exceptionDetails)throw Error(JSON.stringify(value.exceptionDetails));return value.result.value;}
async function waitFor(expression){const deadline=Date.now()+20000;while(Date.now()<deadline){if(await evaluate(expression))return;await new Promise(accept=>setTimeout(accept,50));}throw Error(`timed out: ${expression}`);}
async function key(name,code){await cdp.send('Input.dispatchKeyEvent',{type:'keyDown',key:name,code:name,windowsVirtualKeyCode:code,...(name==='Enter'?{text:'\r'}:{})});await cdp.send('Input.dispatchKeyEvent',{type:'keyUp',key:name,windowsVirtualKeyCode:code});}
async function connect(url){return new Promise((accept,reject)=>{const socket=new WebSocket(url),pending=new Map(),listeners=new Set();let id=0;socket.addEventListener('error',reject);socket.addEventListener('open',()=>{socket.addEventListener('message',event=>{const value=JSON.parse(event.data);if(!value.id){listeners.forEach(listener=>listener(value));return;}const request=pending.get(value.id);if(!request)return;pending.delete(value.id);clearTimeout(request.timeout);if(value.error)request.reject(Error(JSON.stringify(value.error)));else request.accept(value.result);});accept({send(method,params={}){const requestId=++id;return new Promise((acceptRequest,rejectRequest)=>{const timeout=setTimeout(()=>{pending.delete(requestId);rejectRequest(Error(`CDP timeout: ${method}`));},20000);pending.set(requestId,{accept:acceptRequest,reject:rejectRequest,timeout});socket.send(JSON.stringify({id:requestId,method,params}));});},listen(callback){listeners.add(callback);},close(){socket.close();}});});});}
