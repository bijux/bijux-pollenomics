// Execute the maintained loader with controlled responses, independently of retained maps.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createContext, runInContext} from 'node:vm';

export const controllerDirectory = 'packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets';
export function documentFunction(source, name) {
  const start = source.indexOf(`      function ${name}(`) >= 0
    ? source.indexOf(`      function ${name}(`) : source.indexOf(`      async function ${name}(`);
  if (start < 0) throw Error(`maintained function is unavailable: ${name}`);
  const rest = source.slice(start);
  const next = rest.slice(1).search(/\n      (?:async )?function |\n      __SELECTION_LOADING_CONTROLLER__/);
  if (next < 0) throw Error(`maintained function boundary is unavailable: ${name}`);
  return rest.slice(0,next+1);
}

export async function verifySelectionRuntime(repository) {
  const source = await readFile(join(repository,controllerDirectory,'document.html'),'utf8');
  const controller = await readFile(join(repository,controllerDirectory,'selection-loading.js'),'utf8');
  const functions = ['staticAtlasFailure','staticAtlasTemporalIdentity','validateStaticAtlasPayload',
    'consumeStaticAtlasAsset','loadStaticAtlasAsset'].map(name => documentFunction(source,name)).join('\n');
  const context = createContext({assert, AbortController, TextEncoder, Map, Set, Error, Promise,
    sha256:text=>createHash('sha256').update(text).digest('hex')});
  runInContext(`
    const STATIC_ATLAS_BOOTSTRAP={schema_version:'atlas-static-bootstrap.v2',build_id:'controlled-build',scope_slug:'controlled',version:'controlled-version',budgets:{chunk_max_bytes:1048576}};
    const STATIC_ATLAS_SCHEMAS={nodes:['atlas-node-chunk.v1']};
    const STATIC_ATLAS_CHUNKS={nodes:[],details:[]},STATIC_ATLAS_RAW_CHUNKS=[];
    const staticAtlasLoadedAssets=new Set(),staticAtlasInFlightAssets=new Map();
    const window={location:{protocol:'http:'}};
    const staticAtlasSha256=async text=>sha256(text);
    ${functions}
    ${controller}
    globalThis.run=async()=>{
      const requests=[], aborted=[];
      globalThis.fetch=(path,options)=>new Promise(resolve=>{
        const request={path,options,resolve}; requests.push(request);
        options.signal.addEventListener('abort',()=>aborted.push(path),{once:true});
      });
      const asset=(key,changes={})=>{
        const payload={asset_key:key,build_id:STATIC_ATLAS_BOOTSTRAP.build_id,scope_slug:'controlled',version:'controlled-version',schema_version:'atlas-node-chunk.v1',features:[],feature_indexes:[],layer_key:'pollen',layer_index:0,layer_kind:'point',...changes};
        const payload_json=JSON.stringify(payload),payload_sha256=sha256(payload_json);
        const envelope={asset_key:key,payload_sha256,payload_json};
        const text='globalThis.__BIJUX_ATLAS_RAW_CHUNKS__=globalThis.__BIJUX_ATLAS_RAW_CHUNKS__||[];globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push('+JSON.stringify(envelope)+');\\n';
        return {row:{asset_key:key,path:key+'.js',domain:'nodes',record_count:0,layer_key:'pollen',layer_index:0,layer_kind:'point',payload_sha256,sha256:sha256(text),byte_count:new TextEncoder().encode(text).length,integrity:'controlled-sri'},text};
      };
      const finish=(request,text,ok=true)=>request.resolve({ok,text:async()=>text});
      const a=asset('A'),b=asset('B');
      const signalA=beginStaticAtlasSelection([a.row]);
      const oldOperation=loadStaticAtlasAsset(a.row,true);
      const oldA=waitForStaticAtlasSelection(oldOperation,signalA).then(()=>false,()=>true);
      const signalB=beginStaticAtlasSelection([b.row]);
      assert.equal(requests[0].options.signal.aborted,true);
      const resultB=waitForStaticAtlasSelection(loadStaticAtlasAsset(b.row,true),signalB);
      finish(requests[1],b.text); await resultB;
      const newSignalA=beginStaticAtlasSelection([a.row]);
      const newA=waitForStaticAtlasSelection(loadStaticAtlasAsset(a.row,true),newSignalA);
      assert.equal(requests.length,3); assert.notEqual(requests[0].options.signal,requests[2].options.signal);
      finish(requests[0],a.text); await oldOperation.catch(()=>{});
      assert.equal(staticAtlasInFlightAssets.has('A'),true);
      finish(requests[2],a.text); await newA;
      assert.equal(await oldA,true); assert.deepEqual(aborted,['./A.js']);
      assert.deepEqual(STATIC_ATLAS_CHUNKS.nodes.map(row=>row.asset_key),['B','A']);
      assert.equal(staticAtlasInFlightAssets.size,0);
      const refusals={};
      for(const [name,changes] of [['build',{build_id:'foreign-build'}],['version',{version:'foreign-version'}]]){
        const item=asset(name,changes),operation=fetchStaticAtlasNodeAsset(item.row,new AbortController().signal);
        finish(requests.at(-1),item.text);
        try {await operation; assert.fail('mismatched asset accepted');}
        catch(error){assert.match(error.message,new RegExp(name+' mismatch'));assert.match(error.message,/Reload the page.*same build/);refusals[name]=error.message;}
        assert.equal(staticAtlasLoadedAssets.has(name),false);
      }
      for(const kind of ['transport-digest','byte-count','http']){
        const item=asset(kind),row={...item.row};
        if(kind==='transport-digest')row.sha256='0'.repeat(64);
        if(kind==='byte-count')row.byte_count++;
        const operation=fetchStaticAtlasNodeAsset(row,new AbortController().signal);
        finish(requests.at(-1),item.text,kind!=='http');
        try {await operation; assert.fail('invalid transport accepted');}
        catch(error){assert.match(error.message,/Static atlas data cannot be loaded:.*Reload the page.*same build/);refusals[kind]=error.message;}
        assert.equal(staticAtlasLoadedAssets.has(kind),false);
      }
      assert.deepEqual(STATIC_ATLAS_CHUNKS.nodes.map(row=>row.asset_key),['B','A']);
      return {scope:'Controlled maintained JavaScript loader only; no retained-map or full-atlas performance claim.',
        assertions:{obsolete_request_aborted:aborted.length===1,obsolete_waiter_refused:await oldA,reselected_asset_fresh_request:requests.filter(row=>row.path==='./A.js').length===2,old_completion_preserves_new_operation:true,only_current_valid_assets_accepted:true,actionable_build_and_version_refusals:true,transport_integrity_refusals:true},refusals};
    };
  `,context,{filename:join(controllerDirectory,'selection-loading.js'),timeout:5000});
  return await context.run();
}

if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  if(process.argv.length!==3)throw Error('usage: node selection-runtime.mjs REPOSITORY');
  console.log(JSON.stringify(await verifySelectionRuntime(resolve(process.argv[2])),null,2));
}
