"""Obsolete selection waits cancel without corrupting reusable static evidence."""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    canonical_json,
    chunk_script_bytes,
)

from ..support import run_node_json, template_block


def writer_asset(name: str, *, encoding: str = "json") -> dict[str, Any]:
    payload = {
        "schema_version": "atlas-node-chunk.v1",
        "asset_key": name,
        "scope_slug": "fixture",
        "version": "fixture",
        "build_id": "atlas-" + "a" * 64,
        "layer_key": "points",
        "layer_index": 0,
        "layer_kind": "point",
        "feature_indexes": [0],
        "features": [
            {"record_id": name, "title": 'Åland "quoted" (site); .push( is data'}
        ],
    }
    body = canonical_json(payload)
    payload_sha = hashlib.sha256(body.encode()).hexdigest()
    script = chunk_script_bytes(
        asset_key=name,
        payload_sha256=payload_sha,
        payload_json=body,
        payload_encoding=encoding,
    )
    digest = hashlib.sha256(script).digest()
    return {
        "row": {
            "asset_key": name,
            "path": hashlib.sha256(script).hexdigest() + ".js",
            "domain": "nodes",
            "layer_key": "points",
            "layer_index": 0,
            "layer_kind": "point",
            "record_count": 1,
            "payload_encoding": encoding,
            "payload_sha256": payload_sha,
            "decoded_byte_count": len(body.encode()),
            "byte_count": len(script),
            "sha256": digest.hex(),
            "integrity": "sha256-" + base64.b64encode(digest).decode(),
        },
        "script": script.decode(),
    }


SETUP = r"""
const assert=require('node:assert/strict'), cryptoNode=require('node:crypto');
const STATIC_ATLAS_BOOTSTRAP={schema_version:'atlas-static-bootstrap.v2',build_id:'atlas-'+'a'.repeat(64),scope_slug:'fixture',version:'fixture',budgets:{chunk_max_bytes:4194304}};
const STATIC_ATLAS_SCHEMAS={nodes:['atlas-node-chunk.v1']};
const STATIC_ATLAS_RAW_CHUNKS=[],STATIC_ATLAS_CHUNKS={nodes:[],details:[]};
const staticAtlasLoadedAssets=new Set(),staticAtlasInFlightAssets=new Map();
const window={location:{protocol:'https:'}};
let requests=[],scripts=[],selectionNames=[],refreshes=0;
function fixture(name){return fixtures.find(item=>item.row.asset_key===name)}
function envelope(item){const prefix='globalThis.__BIJUX_ATLAS_RAW_CHUNKS__=globalThis.__BIJUX_ATLAS_RAW_CHUNKS__||[];globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push(';return JSON.parse(item.script.slice(prefix.length,-3))}
globalThis.fetch=(path,options)=>new Promise((resolve,reject)=>{
  const request={path,options,aborted:false};requests.push(request);
  options.signal.addEventListener('abort',()=>{request.aborted=true;reject(options.signal.reason)},{once:true});
  request.finish=(text)=>resolve({ok:true,text:async()=>text});
  request.headers=()=>resolve({ok:true,text:()=>new Promise(done=>{request.body=done})});
  request.fail=reject;
});
const document={createElement(){const script={callbacks:{},addEventListener(name,fn){this.callbacks[name]=fn}};return script},head:{appendChild(script){scripts.push(script)}}};
async function tick(){await new Promise(resolve=>setImmediate(resolve))}
function reset(){
  beginStaticAtlasSelection([]);staticAtlasInFlightAssets.clear();staticAtlasLoadedAssets.clear();
  STATIC_ATLAS_RAW_CHUNKS.length=0;STATIC_ATLAS_CHUNKS.nodes.length=0;requests=[];scripts=[];refreshes=0;window.location.protocol='https:';
}
function requiredStaticAtlasNodeAssets(){return selectionNames.map(name=>fixture(name).row)}
function refreshStaticAtlasLayers(){refreshes++}
function start(names){selectionNames=names;return ensureStaticAtlasSelectionLoaded()}
function accepted(name){return staticAtlasLoadedAssets.has(name)}
async function serve(request,item){request.finish(item.script);await tick()}
function reseal(row,text){return {...row,byte_count:Buffer.byteLength(text),sha256:cryptoNode.createHash('sha256').update(text).digest('hex')}}
"""

CASES = r"""
(async()=>{
  const a=fixture('nodes:a'),b=fixture('nodes:b'),g=fixture('nodes:gzip');
  let passed=[];
  // Shared requests survive while the prior selection waiter cancels.
  let old=start(['nodes:a']);const oldCancelled=assert.rejects(old,{name:'AbortError'});
  let current=start(['nodes:a','nodes:b']);await oldCancelled;
  assert.equal(requests.length,2);assert.equal(requests[0].aborted,false);
  assert.equal(requests[0].options.integrity,a.row.integrity);
  assert.equal(requests[0].options.credentials,'same-origin');
  await serve(requests[0],a);await serve(requests[1],b);await current;
  assert.equal(STATIC_ATLAS_CHUNKS.nodes.length,2);assert.equal(refreshes,1);passed.push('shared-needed-request');
  // A→B→A: late old cleanup/body must not delete the replacement or cache A early.
  reset();old=start(['nodes:a']);const cancelledA=assert.rejects(old,{name:'AbortError'});
  requests[0].headers();await tick();const firstA=requests[0];
  let middle=start(['nodes:b']);const cancelledB=assert.rejects(middle,{name:'AbortError'});
  current=start(['nodes:a']);await cancelledA;await cancelledB;
  assert.equal(firstA.aborted,true);assert.equal(requests[1].aborted,true);
  assert.equal(accepted('nodes:a'),false);const replacement=staticAtlasInFlightAssets.get('nodes:a');
  firstA.body(a.script);await tick();assert.equal(staticAtlasInFlightAssets.get('nodes:a'),replacement);
  await serve(requests[2],a);await current;assert.equal(STATIC_ATLAS_CHUNKS.nodes.length,1);
  passed.push('reversal-aborted-body-cache-and-cleanup');
  // Only cancellation replaces an old waiter error: real current failures remain failures.
  reset();old=start(['nodes:a']);const stale=assert.rejects(old,{name:'AbortError'});
  current=start(['nodes:b']);const timeout=new DOMException('actual transport timeout','TimeoutError');
  const failed=assert.rejects(current,error=>error===timeout);requests[0].fail(new Error('late obsolete error'));requests[1].fail(timeout);
  await stale;await failed;await tick();assert.equal(accepted('nodes:b'),false);
  current=start(['nodes:b']);await serve(requests[2],b);await current;passed.push('stale-error-current-timeout-and-retry');
  // Default startup/detail ownership retains shared work across selections.
  reset();old=start(['nodes:a']);const independent=loadStaticAtlasAsset(a.row);
  const detached=assert.rejects(old,{name:'AbortError'});current=start([]);await detached;await current;
  assert.equal(requests[0].aborted,false);await serve(requests[0],a);await independent;
  const detail=loadStaticAtlasAsset(b.row);beginStaticAtlasSelection([]);
  assert.equal(scripts.length,1);assert.equal(scripts[0].integrity,b.row.integrity);
  STATIC_ATLAS_RAW_CHUNKS.push(envelope(b));scripts[0].callbacks.load();await detail;
  passed.push('startup-detail-owned-work-retained');
  // Offline transport is retained; only obsolete selection waiting is cancelled.
  reset();window.location.protocol='file:';old=start(['nodes:a']);const offline=assert.rejects(old,{name:'AbortError'});
  current=start([]);await offline;await current;assert.equal(requests.length,0);assert.equal(scripts.length,1);
  const offlineRequest=staticAtlasInFlightAssets.get('nodes:a').promise;
  STATIC_ATLAS_RAW_CHUNKS.push(envelope(a));scripts[0].callbacks.load();await offlineRequest;
  assert.equal(accepted('nodes:a'),true);await start(['nodes:a']);assert.equal(scripts.length,1);
  passed.push('offline-waiter-only-reusable-script');
  // Real writer gzip and Unicode/quotes/parentheses survive both protocol layers.
  reset();current=start(['nodes:gzip']);await serve(requests[0],g);await current;
  assert.match(STATIC_ATLAS_CHUNKS.nodes[0].features[0].title,/Åland "quoted" \(site\)/);
  assert.equal(STATIC_ATLAS_RAW_CHUNKS.length,0);passed.push('writer-gzip-unicode-data-only');
  // Exact wrapper, script hash, payload hash/build, and duplicate registration stay strict.
  const rejects=async(row,text,pattern)=>{reset();const promise=loadStaticAtlasAsset(row,true);const refusal=assert.rejects(promise,pattern);requests[0].finish(text);await refusal;assert.equal(staticAtlasLoadedAssets.size,0);assert.equal(STATIC_ATLAS_CHUNKS.nodes.length,0)};
  await rejects(a.row,a.script+' ',/script byte count mismatch/);passed.push('script-byte-count');
  await rejects(a.row,a.script.replace('quoted','broken'),/script integrity mismatch/);passed.push('script-sha');
  let text=a.script+a.script;await rejects(reseal(a.row,text),text,/registration JSON is invalid/);passed.push('duplicate-wrappers');
  text=a.script.replace('globalThis.', 'globalThat.');await rejects(reseal(a.row,text),text,/registration wrapper is invalid/);passed.push('unknown-wrapper');
  const wrap=(env)=>a.script.slice(0,a.script.indexOf('.push(')+6)+JSON.stringify(env)+');\n';
  let env=envelope(a);env.asset_key='foreign';text=wrap(env);await rejects(reseal(a.row,text),text,/registered identity mismatch/);passed.push('foreign-envelope');
  env=envelope(a);env.payload_json=env.payload_json.replace('quoted','broken');text=wrap(env);await rejects(reseal(a.row,text),text,/payload integrity mismatch/);passed.push('payload-sha');
  env=envelope(a);const payload=JSON.parse(env.payload_json);payload.build_id='atlas-'+'b'.repeat(64);env.payload_json=JSON.stringify(payload);env.payload_sha256=cryptoNode.createHash('sha256').update(env.payload_json).digest('hex');text=wrap(env);
  await rejects({...reseal(a.row,text),payload_sha256:env.payload_sha256,decoded_byte_count:Buffer.byteLength(env.payload_json)},text,/build mismatch/);passed.push('foreign-build');
  reset();STATIC_ATLAS_RAW_CHUNKS.push(envelope(a),envelope(a));await assert.rejects(consumeStaticAtlasAsset(a.row),/exactly once/);passed.push('offline-duplicate-envelope');
  // A pending decode reader is actually cancelled; no accepted data/counts appear.
  reset();const originalDecoder=globalThis.DecompressionStream;let cancelledReaders=0;
  globalThis.DecompressionStream=class {constructor(){this.readable=new ReadableStream({cancel(){cancelledReaders++}});this.writable=new WritableStream()}};
  const controller=new AbortController();const decode=consumeStaticAtlasAsset(g.row,controller.signal,envelope(g));
  const stopped=assert.rejects(decode,{name:'AbortError'});await tick();controller.abort();await stopped;
  globalThis.DecompressionStream=originalDecoder;assert.equal(cancelledReaders,1);assert.equal(STATIC_ATLAS_CHUNKS.nodes.length,0);
  passed.push('pending-decoder-cancel');
  console.log(JSON.stringify({passed}));
})().catch(error=>{console.error(error);process.exitCode=1});
"""


def test_selection_owned_requests_cancel_without_poisoning_shared_cache() -> None:
    fixtures = [
        writer_asset("nodes:a"),
        writer_asset("nodes:b"),
        writer_asset("nodes:gzip", encoding="gzip_base64"),
    ]
    runtime = template_block(
        "function staticAtlasFailure", "function normalizeStaticAtlasBootstrap"
    ) + template_block("async function staticAtlasSha256", "if (!STATIC_ATLAS_INLINE)")
    runtime += template_block(
        "async function ensureStaticAtlasSelectionLoaded", "const countryColors"
    )
    result = run_node_json(
        "const fixtures=" + json.dumps(fixtures) + ";\n" + SETUP + runtime + CASES
    )
    assert len(result["passed"]) == 15
