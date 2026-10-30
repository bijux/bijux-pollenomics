"""A distributed controller consumes the original browser resource budget."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)

from ...atlas.static_assets.fixtures.layers import (
    build_point_layers,
    build_polygon_layers,
)
from ..browser_semantics.support import run_node_json, template_block


def test_real_bootstrap_accounts_for_runtime_requests_bytes_and_transport_identity(
    tmp_path: Path,
) -> None:
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="v66",
        point_layers=build_point_layers(),
        polygon_layers=build_polygon_layers(),
    )
    constants = template_block(
        "const STATIC_ATLAS_ASSET_TABLE_FIELDS", "const STATIC_ATLAS_BOOTSTRAP"
    )
    helpers = template_block(
        "const STATIC_ATLAS_SCHEMAS", "async function staticAtlasSha256"
    ).replace("__VERSION_JSON__", '"v66"')
    observed = cast(
        dict[str, Any],
        run_node_json(
            constants
            + "let STATIC_ATLAS_BOOTSTRAP=normalizeStaticAtlasBootstrap("
            + json.dumps(assets.manifest)
            + ");"
            + helpers
            + r"""
let binding={textContent:JSON.stringify({source_text:'🌿'.repeat(100)})};
const document={getElementById(id){if(id!=='atlas-native-lra-binding')throw Error(id);return binding;}};
const inlineBytes=new TextEncoder().encode(binding.textContent).byteLength;
const base=structuredClone(STATIC_ATLAS_BOOTSTRAP);
const runtime={path:'nordic.atlas-runtime.'+'a'.repeat(16)+'.js',byte_count:64000,integrity:'sha256-'+'A'.repeat(43)+'='};
const initial=base.assets.filter(row=>row.initial_load===true);
const initialBytes=initial.reduce((total,row)=>total+row.byte_count,0);
const totalBytes=base.assets.reduce((total,row)=>total+row.byte_count,0);
function outcome(change){
  STATIC_ATLAS_BOOTSTRAP=structuredClone(base);
  change(STATIC_ATLAS_BOOTSTRAP);
  try {validateStaticAtlasBootstrap();return 'accepted';}
  catch(error){return error.message;}
}
const result={
  inline:outcome(()=>{}),
  runtime:outcome(b=>{b.runtime=runtime;}),
  exactLimits:outcome(b=>{b.runtime=runtime;b.budgets.initial_max_requests=initial.length+1;b.budgets.initial_max_bytes=initialBytes+runtime.byte_count+inlineBytes;b.budgets.static_assets_max_bytes=totalBytes+runtime.byte_count+inlineBytes;}),
  requestOverflow:outcome(b=>{b.runtime=runtime;b.budgets.initial_max_requests=initial.length;}),
  byteOverflow:outcome(b=>{b.runtime=runtime;b.budgets.initial_max_bytes=initialBytes+runtime.byte_count+inlineBytes-1;}),
  omittedInlineInitial:outcome(b=>{b.runtime=runtime;b.budgets.initial_max_bytes=initialBytes+runtime.byte_count;}),
  omittedInlineTotal:outcome(b=>{b.runtime=runtime;b.budgets.static_assets_max_bytes=totalBytes+runtime.byte_count;}),
  totalOverflow:outcome(b=>{b.runtime=runtime;b.budgets.static_assets_max_bytes=totalBytes+runtime.byte_count+inlineBytes-1;}),
  unsafePath:outcome(b=>{b.runtime={...runtime,path:'../runtime.js'};}),
  wrongPathType:outcome(b=>{b.runtime={...runtime,path:[runtime.path]};}),
  wrongIntegrity:outcome(b=>{b.runtime={...runtime,integrity:'unknown'};}),
  zeroBytes:outcome(b=>{b.runtime={...runtime,byte_count:0};}),
  oversized:outcome(b=>{b.runtime={...runtime,byte_count:524289};}),
  booleanBytes:outcome(b=>{b.runtime={...runtime,byte_count:true};}),
  nullRuntime:outcome(b=>{b.runtime=null;}),
};
binding=null;
result.missingBinding=outcome(()=>{});
console.log(JSON.stringify(result));
"""
        ),
    )
    assert (
        observed["inline"]
        == observed["runtime"]
        == observed["exactLimits"]
        == "accepted"
    )
    assert "initial request budget exceeded" in observed["requestOverflow"]
    assert "initial byte budget exceeded" in observed["byteOverflow"]
    assert "initial byte budget exceeded" in observed["omittedInlineInitial"]
    assert "total asset byte budget exceeded" in observed["omittedInlineTotal"]
    assert "total asset byte budget exceeded" in observed["totalOverflow"]
    assert "native binding payload is unavailable" in observed["missingBinding"]
    for field in ("unsafePath", "wrongPathType", "wrongIntegrity", "nullRuntime"):
        assert "runtime transport identity is invalid" in observed[field]
    assert "runtime byte budget exceeded" in observed["zeroBytes"]
    assert "runtime byte budget exceeded" in observed["oversized"]
    assert "runtime byte count is invalid" in observed["booleanBytes"]
