"""Only the selected pinned source entity becomes a byte-exact browser download."""

from __future__ import annotations

from collections.abc import Callable
import json
from typing import Any

import pytest

from .browser_invocation import invoke


def test_download_uses_actual_native_entity_bytes_and_only_selected_body(
    resource_browser: dict[str, Any],
) -> None:
    observed = invoke(
        resource_browser,
        """
(async()=>{
const supported=typeof reader.downloadResource==='function';
let result=null;if(supported){result=await reader.downloadResource('201','current');}
console.log(JSON.stringify({supported,calls,bytes:result?[...result.bytes]:null,filename:result?.filename}));
})().catch(error=>{console.error(error);process.exit(1)});
""",
    )
    assert observed["supported"] is True
    body_paths = [path for path in observed["calls"] if path.endswith(".body")]
    assert len(body_paths) == 1 and "dataset-201-current" in body_paths[0]
    assert observed["bytes"] == resource_browser["routes"][body_paths[0]]
    assert observed["filename"].endswith(".body")


@pytest.mark.parametrize(
    ("dataset", "version", "code"),
    [
        ("203", "current", "blocked_role"),
        ("204", "doi_frozen", "blocked_role"),
        ("201", "original_paper", "resource_identity"),
        (201, "current", "resource_identity"),
    ],
)
def test_invalid_identity_and_protected_roles_never_fetch_archive_or_body(
    resource_browser: dict[str, Any], dataset: Any, version: str, code: str
) -> None:
    observed = invoke(
        resource_browser,
        """
(async()=>{try{await reader.downloadResource(DATASET,VERSION);console.log(JSON.stringify({accepted:true}));}
catch(error){console.log(JSON.stringify({code:error.code,calls}));}})();
""".replace("DATASET", json.dumps(dataset)).replace("VERSION", json.dumps(version)),
    )
    assert observed["code"] == code and observed["calls"] == []


def test_file_mode_download_refuses_with_local_http_instruction_before_fetch(
    resource_browser: dict[str, Any],
) -> None:
    observed = invoke(
        resource_browser,
        """
(async()=>{try{await reader.downloadResource('201','current');console.log(JSON.stringify({accepted:true}));}
catch(error){console.log(JSON.stringify({code:error.code,reason:error.message,calls}));}})();
""",
        transport_setup="downloadLocation=new URL('file:///controlled/atlas.html');",
    )
    assert observed["code"] == "file_protocol"
    assert "local HTTP" in observed["reason"] and observed["calls"] == []


@pytest.mark.parametrize("damage", ["corrupt_bytes", "long_response", "short_response"])
def test_selected_native_buffer_must_match_exact_size_and_sha(
    resource_browser: dict[str, Any], damage: str
) -> None:
    setup = """
const normalFetch=fetcher;
fetcher=async(url,options)=>{const path=new URL(url).pathname;
if(path.endsWith('.body')){let value=[...routes[path]];if(DAMAGE==='corrupt_bytes')value[0]^=1;
else if(DAMAGE==='long_response')value.push(10);else value.pop();
calls.push(path);return new Response(new Uint8Array(value),{status:200,headers:{'Content-Length':String(value.length)}});}
return normalFetch(url,options);};
""".replace("DAMAGE", json.dumps(damage))
    observed = invoke(
        resource_browser,
        """
(async()=>{try{await reader.downloadResource('201','current');console.log(JSON.stringify({accepted:true}));}
catch(error){console.log(JSON.stringify({code:error.code,calls}));}})();
""",
        transport_setup=setup,
    )
    assert observed["code"] == (
        "file_digest" if damage == "corrupt_bytes" else "response_size"
    )
    assert sum(path.endswith(".body") for path in observed["calls"]) == 1


def test_oversized_metadata_response_header_refuses_before_reading_stream(
    resource_browser: dict[str, Any],
) -> None:
    observed = invoke(
        resource_browser,
        """
(async()=>{try{await reader.downloadResource('201','current');console.log(JSON.stringify({accepted:true}));}
catch(error){console.log(JSON.stringify({code:error.code,reads,calls}));}})();
""",
        transport_setup="""
let reads=0;const normalFetch=fetcher;
fetcher=async(url,options)=>{const response=await normalFetch(url,options);
if(new URL(url).pathname.endsWith('/manifest.json')){
 response.headers.set('Content-Length',String(16*1024*1024+1));
 const actual=response.body.getReader.bind(response.body);response.body.getReader=()=>{reads++;return actual()};}
return response;};
""",
    )
    assert observed["code"] == "response_size" and observed["reads"] == 0
    assert not any(path.endswith(".body") for path in observed["calls"])


def test_aborted_download_intent_does_not_open_archive_or_source(
    resource_browser: dict[str, Any],
) -> None:
    observed = invoke(
        resource_browser,
        """
(async()=>{const controller=new AbortController();controller.abort();
try{await reader.downloadResource('201','current',{signal:controller.signal});console.log(JSON.stringify({accepted:true}));}
catch(error){console.log(JSON.stringify({name:error.name,calls}));}})();
""",
    )
    assert observed["name"] == "AbortError" and observed["calls"] == []


def test_rehashed_non200_entity_claim_never_bypasses_source_availability(
    resource_browser: dict[str, Any],
) -> None:
    observed = invoke(
        resource_browser,
        """
(async()=>{try{await reader.downloadResource('201','current');console.log(JSON.stringify({accepted:true}));}
catch(error){console.log(JSON.stringify({code:error.code,calls}));}})();
""",
        transport_setup="""
const prefix='/data/neotoma/source-resources/',hash=bytes=>require('node:crypto').createHash('sha256').update(new Uint8Array(bytes)).digest('hex');
const manifestObject=JSON.parse(new TextDecoder().decode(new Uint8Array(routes[prefix+'manifest.json'])));
const indexObject=JSON.parse(new TextDecoder().decode(new Uint8Array(routes[prefix+'downloads/index.json'])));
const row=indexObject.resources.find(value=>value.dataset_id==='201'&&value.version==='current');row.source.http_status=404;
for(const payload of Object.values(payloads))if(payload.kind==='resources'){
 const resource=payload.records.find(value=>value.dataset_id==='201');if(resource)resource.versions.current.source.http_status=404;
}
const indexBytes=[...new TextEncoder().encode(JSON.stringify(indexObject))];
manifestObject.source_bytes+=indexBytes.length-manifestObject.files['downloads/index.json'].bytes;
manifestObject.files['downloads/index.json']={bytes:indexBytes.length,sha256:hash(indexBytes)};
routes[prefix+'downloads/index.json']=indexBytes;
const manifestBytes=[...new TextEncoder().encode(JSON.stringify(manifestObject))];routes[prefix+'manifest.json']=manifestBytes;
for(const payload of Object.values(payloads))if(payload.kind==='context'){
 const reference=payload.records[0].provenance.source_archive;reference.manifest_sha256=hash(manifestBytes);
 reference.index={path:'downloads/index.json',...manifestObject.files['downloads/index.json']};
}
""",
    )
    assert observed["code"] == "source_unavailable"
    assert not any(path.endswith(".body") for path in observed["calls"])


def test_actual_browser_saves_only_verified_selected_native_buffer(
    browser_probe: Callable[..., dict[str, Any]], resource_browser: dict[str, Any]
) -> None:
    observed = browser_probe("""(async()=>{document.getElementById('source-resources-open').click();
for(let i=0;i<150&&!document.querySelector('[data-resource-dataset="201"] button');i++)await new Promise(ok=>setTimeout(ok,20));
document.querySelector('[data-resource-dataset="201"] button').click();
for(let i=0;i<150&&!document.querySelector('[data-resource-download="body"]');i++)await new Promise(ok=>setTimeout(ok,20));
document.querySelector('[data-resource-download="body"]').click();
for(let i=0;i<150&&!document.querySelector('[data-download-status]')?.textContent.startsWith('Verified ');i++)await new Promise(ok=>setTimeout(ok,20));
await new Promise(ok=>setTimeout(ok,150));return {status:document.querySelector('[data-download-status]')?.textContent};})()""")
    assert observed["result"]["status"].startswith("Verified ")
    paths = [path for path in observed["calls"] if path.endswith(".body")]
    assert len(paths) == 1
    assert len(observed["downloads"]) == 1
    assert observed["downloads"][0]["bytes"] == resource_browser["routes"][paths[0]]
    assert observed["downloads"][0]["name"] == paths[0].split("/")[-1]
    assert observed["failures"] == []


@pytest.mark.parametrize("version", ["current", "doi_frozen"])
def test_captured_body_and_receipt_keep_exact_selected_version(
    resource_browser: dict[str, Any], version: str
) -> None:
    observed = invoke(
        resource_browser,
        """
(async()=>{const body=await reader.downloadResource('202',VERSION),receipt=await reader.downloadReceipt('202',VERSION);
console.log(JSON.stringify({body:[...body.bytes],receipt:[...receipt.bytes],calls,version:body.version}));})();
""".replace("VERSION", json.dumps(version)),
    )
    bodies = [path for path in observed["calls"] if path.endswith(".body")]
    receipts = [path for path in observed["calls"] if path.endswith(".receipt.json")]
    assert len(bodies) == len(receipts) == 1
    assert observed["version"] == version
    assert observed["body"] == resource_browser["routes"][bodies[0]]
    assert observed["receipt"] == resource_browser["routes"][receipts[0]]


def test_corrupt_selected_entity_never_becomes_a_browser_download(
    browser_probe: Callable[..., dict[str, Any]],
) -> None:
    observed = browser_probe(
        """(async()=>{document.getElementById('source-resources-open').click();
for(let i=0;i<150&&!document.querySelector('[data-resource-dataset="201"] button');i++)await new Promise(ok=>setTimeout(ok,20));document.querySelector('[data-resource-dataset="201"] button').click();
for(let i=0;i<150&&!document.querySelector('[data-resource-download="body"]');i++)await new Promise(ok=>setTimeout(ok,20));document.querySelector('[data-resource-download="body"]').click();
for(let i=0;i<150&&!document.querySelector('[data-download-status]')?.textContent.startsWith('Download unavailable');i++)await new Promise(ok=>setTimeout(ok,20));return {status:document.querySelector('[data-download-status]')?.textContent};})()""",
        transport_mode="corrupt_body",
    )
    assert "verification failed" in observed["result"]["status"]
    assert observed["downloads"] == []
    assert len([path for path in observed["calls"] if path.endswith(".body")]) == 1
    assert observed["failures"] == []


@pytest.mark.parametrize("delivery", ["exact", "long", "short", "corrupt"])
def test_compressed_http_entity_enforces_decoded_size_and_digest(
    resource_browser: dict[str, Any],
    delivery: str,
) -> None:
    observed = invoke(
        resource_browser,
        """
try{const result=await reader.downloadResource('201','current');console.log(JSON.stringify({accepted:true,bytes:[...result.bytes],calls}));}
catch(error){console.log(JSON.stringify({accepted:false,code:error.code,reason:error.message,calls}));}
finally{server.closeAllConnections();await new Promise(ok=>server.close(ok));}
})().catch(error=>{console.error(error);process.exitCode=1});
""",
        transport_setup="""
(async()=>{const {createServer}=require('node:http'),{gzipSync}=require('node:zlib');
const server=createServer((request,response)=>{const path=new URL(request.url,'http://localhost').pathname;calls.push(path);const original=routes[path];if(!original){response.writeHead(404);response.end();return;}let plain=Buffer.from(original);if(path.endsWith('.body')){if(DELIVERY==='long')plain=Buffer.concat([plain,Buffer.from([0])]);else if(DELIVERY==='short')plain=plain.subarray(0,plain.length-1);else if(DELIVERY==='corrupt')plain[0]^=1;}const encoded=gzipSync(plain);response.writeHead(200,{'Content-Encoding':'gzip','Content-Length':encoded.length});response.end(encoded);});
await new Promise(ok=>server.listen(0,'127.0.0.1',ok));downloadLocation=new URL(`http://127.0.0.1:${server.address().port}/nordic/`);fetcher=globalThis.fetch;
""".replace("DELIVERY", json.dumps(delivery)),
    )
    if delivery != "exact":
        assert observed["accepted"] is False
        assert observed["code"] == (
            "file_digest" if delivery == "corrupt" else "response_size"
        )
        assert len([path for path in observed["calls"] if path.endswith(".body")]) == 1
        return
    assert observed["accepted"] is True
    bodies = [path for path in observed["calls"] if path.endswith(".body")]
    assert len(bodies) == 1
    assert observed["bytes"] == resource_browser["routes"][bodies[0]]
