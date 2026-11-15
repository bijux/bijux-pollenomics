"""Invoke the actual packaged metadata reader with explicit transport bindings."""

from __future__ import annotations

import json
from typing import Any, cast

from ...support import run_node_json


def invoke(
    resource_browser: dict[str, Any], action: str, *, transport_setup: str = ""
) -> dict[str, Any]:
    result = run_node_json(
        resource_browser["source"]
        + "\nconst manifest="
        + json.dumps(resource_browser["manifest"])
        + ";const payloads="
        + json.dumps(resource_browser["payloads"])
        + ";const routes="
        + json.dumps(resource_browser["routes"])
        + """;
const calls=[],loaded=new Map();let downloadLocation=new URL('https://atlas.example/nordic/');
let fetcher=async(url,options)=>{calls.push(new URL(url).pathname);const value=routes[new URL(url).pathname];if(!value)return new Response('missing',{status:404});return new Response(new Uint8Array(value),{status:200,headers:{'Content-Length':String(value.length)}});};
"""
        + transport_setup
        + """
const tools=BijuxPollenomicsEvidenceTools(String,String);
const reader=tools.sourceResources({manifest,loadAsset:async row=>loaded.set(row.asset_key,payloads[row.asset_key]),payloadForAsset:key=>loaded.get(key),
 downloadTransport:{fetcher,cryptoProvider:require('node:crypto').webcrypto,location:downloadLocation}});
"""
        + action
    )

    assert isinstance(result, dict)
    return cast(dict[str, Any], result)
