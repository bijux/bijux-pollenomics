"""A distributed controller consumes the original browser resource budget."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document import render as subject
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)

from ...atlas.static_assets.fixtures.layers import (
    build_point_layers,
    build_polygon_layers,
)
from ..browser_semantics.support import run_node_json, template_block
from ..static_assets.test_runtime_packaging import request_args as request_args


@pytest.mark.parametrize("scope", ["initial", "total"])
def test_optional_bytes_only_charge_total_at_exact_boundaries(
    request_args: dict[str, Any], monkeypatch: pytest.MonkeyPatch, scope: str
) -> None:
    document = subject._compose_map_document(**request_args)
    rows = normalize_asset_inventory(request_args["static_assets"].manifest["assets"])
    count = sum(
        cast(int, row["byte_count"])
        for row in rows
        if scope == "total" or row["initial_load"] is True
    )
    inline = sum(
        len(pattern.findall(document)[0].encode())
        for pattern in (subject._NATIVE_BINDING, subject._MODELED_BINDING)
    )
    limit = (
        "ATLAS_INITIAL_MAX_BYTES"
        if scope == "initial"
        else "ATLAS_STATIC_ASSETS_MAX_BYTES"
    )
    exact = count + 100 + inline + (200 if scope == "total" else 0)
    monkeypatch.setattr(subject, limit, exact)
    subject._runtime_resources(request_args["static_assets"], 100, document, 200)
    monkeypatch.setattr(subject, limit, exact - 1)
    with pytest.raises(ValueError, match=f"{scope}.*byte budget"):
        subject._runtime_resources(request_args["static_assets"], 100, document, 200)


@pytest.mark.parametrize("size", [-1, True, 524289])
def test_optional_controller_has_its_own_existing_document_size_limit(
    request_args: dict[str, Any], size: int
) -> None:
    with pytest.raises(ValueError, match="optional controller"):
        subject._runtime_resources(
            request_args["static_assets"],
            100,
            subject._compose_map_document(**request_args),
            size,
        )


def test_optional_file_count_is_charged_only_to_total(
    request_args: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    document = subject._compose_map_document(**request_args)
    assets = request_args["static_assets"]
    count = len(normalize_asset_inventory(assets.manifest["assets"]))
    monkeypatch.setattr(subject, "ATLAS_STATIC_ASSETS_MAX_FILES", count + 2)
    subject._runtime_resources(assets, 100, document, 200)
    monkeypatch.setattr(subject, "ATLAS_STATIC_ASSETS_MAX_FILES", count + 1)
    with pytest.raises(ValueError, match="asset count budget"):
        subject._runtime_resources(assets, 100, document, 200)


@pytest.mark.parametrize(
    "defect", ["bytes", "null", "foreign", "path", "size", "integrity", "extra"]
)
def test_bundle_inventory_authenticates_exact_optional_transport_reference(
    tmp_path: Path, request_args: dict[str, Any], defect: str
) -> None:
    html, _ = subject.write_static_map_document(tmp_path / "atlas.html", **request_args)
    evidence = subject.static_map_optional_controller_paths(html)[0]
    if defect == "bytes":
        evidence.write_bytes(b"altered code")
    else:
        document = html.read_text()
        (match,) = subject._BOOTSTRAP.finditer(document)
        bootstrap = json.loads(match.group(2))
        runtime = bootstrap["runtime"]
        reference = runtime["optional_controllers"]["evidence_tools"]
        if defect == "null":
            runtime["optional_controllers"] = None
        elif defect == "foreign":
            runtime["optional_controllers"] = {"foreign": reference}
        elif defect == "path":
            reference["path"] = "../outside.js"
        elif defect == "size":
            reference["byte_count"] += 1
        elif defect == "integrity":
            reference["integrity"] = "unknown"
        else:
            reference["extra"] = True
        html.write_text(
            document[: match.start(2)]
            + json.dumps(bootstrap)
            + document[match.end(2) :]
        )
    with pytest.raises(ValueError, match="optional controller"):
        subject.static_map_optional_controller_paths(html)


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
    helpers = (
        template_block(
            "const STATIC_ATLAS_SCHEMAS", "async function staticAtlasSha256"
        ).replace("__VERSION_JSON__", '"v66"')
        + template_block(
            "function evidenceToolsDescriptor", "function loadEvidenceTools"
        )
        + template_block(
            "function indexTransportDescriptor",
            "function validateStaticAtlasEdgeAssets",
        )
    )
    observed = cast(
        dict[str, Any],
        run_node_json(
            constants
            + "let STATIC_ATLAS_BOOTSTRAP=normalizeStaticAtlasBootstrap("
            + json.dumps(assets.manifest)
            + ");"
            + helpers
            + r"""
let binding={tagName:'SCRIPT',type:'application/json',textContent:JSON.stringify({source_text:'🌿'.repeat(100)})};
let modeledBinding={tagName:'SCRIPT',type:'application/json',textContent:JSON.stringify({source_text:'🌿'.repeat(50)})};
let duplicateBinding=false;
const document={querySelectorAll(selector){const value=selector.includes('atlas-native-lra-binding')?binding:modeledBinding;return value?(duplicateBinding?[value,value]:[value]):[];}};
const inlineBytes=new TextEncoder().encode(binding.textContent).byteLength+new TextEncoder().encode(modeledBinding.textContent).byteLength;
const base=structuredClone(STATIC_ATLAS_BOOTSTRAP);
const runtime={path:'nordic.atlas-runtime.'+'a'.repeat(16)+'.js',byte_count:64000,integrity:'sha256-'+'A'.repeat(43)+'='};
const tools={path:'nordic.atlas-evidence-tools.'+'b'.repeat(16)+'.js',byte_count:20000,integrity:'sha256-'+'B'.repeat(43)+'='};
const optional=()=>({...runtime,optional_controllers:{evidence_tools:{...tools}}});
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
  optional:outcome(b=>{b.runtime=optional();}),
  exactOptional:outcome(b=>{b.runtime=optional();b.budgets.initial_max_requests=initial.length+1;b.budgets.initial_max_bytes=initialBytes+runtime.byte_count+inlineBytes;b.budgets.static_assets_max_bytes=totalBytes+runtime.byte_count+inlineBytes+tools.byte_count;}),
  omittedOptional:outcome(b=>{b.runtime=optional();b.budgets.static_assets_max_bytes=totalBytes+runtime.byte_count+inlineBytes+tools.byte_count-1;}),
  optionalUnsafe:outcome(b=>{b.runtime=optional();b.runtime.optional_controllers.evidence_tools.path='../outside.js';}),
  optionalArrayPath:outcome(b=>{b.runtime=optional();b.runtime.optional_controllers.evidence_tools.path=[tools.path];}),
  optionalArrayIntegrity:outcome(b=>{b.runtime=optional();b.runtime.optional_controllers.evidence_tools.integrity=[tools.integrity];}),
  optionalLarge:outcome(b=>{b.runtime=optional();b.runtime.optional_controllers.evidence_tools.byte_count=524289;}),
  optionalBoolean:outcome(b=>{b.runtime=optional();b.runtime.optional_controllers.evidence_tools.byte_count=true;}),
  optionalExtra:outcome(b=>{b.runtime=optional();b.runtime.optional_controllers.evidence_tools.extra=true;}),
  optionalNull:outcome(b=>{b.runtime=optional();b.runtime.optional_controllers=null;}),
};
duplicateBinding=true;
result.duplicateBinding=outcome(()=>{});
duplicateBinding=false;
const oldModeled=modeledBinding;
modeledBinding={...oldModeled,textContent:'{'};
result.invalidModeled=outcome(()=>{});
modeledBinding=oldModeled;
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
        == observed["optional"]
        == observed["exactOptional"]
        == "accepted"
    )
    assert "initial request budget exceeded" in observed["requestOverflow"]
    assert "initial byte budget exceeded" in observed["byteOverflow"]
    assert "initial byte budget exceeded" in observed["omittedInlineInitial"]
    assert "total asset byte budget exceeded" in observed["omittedInlineTotal"]
    assert "total asset byte budget exceeded" in observed["totalOverflow"]
    assert (
        "atlas-native-lra-binding binding payload is unavailable"
        in observed["missingBinding"]
    )
    for field in ("unsafePath", "wrongPathType", "wrongIntegrity", "nullRuntime"):
        assert "runtime transport identity is invalid" in observed[field]
    assert "runtime byte budget exceeded" in observed["zeroBytes"]
    assert "runtime byte budget exceeded" in observed["oversized"]
    assert "runtime byte count is invalid" in observed["booleanBytes"]
    assert "total asset byte budget exceeded" in observed["omittedOptional"]
    assert "optional runtime controllers are invalid" in observed["optionalNull"]
    for key in (
        "optionalUnsafe",
        "optionalArrayPath",
        "optionalArrayIntegrity",
        "optionalLarge",
        "optionalBoolean",
        "optionalExtra",
    ):
        assert "Evidence tools transport identity is unavailable" in observed[key]


@pytest.mark.parametrize("scope", ["initial", "total"])
def test_both_json_bindings_and_both_controllers_use_exact_byte_limits(
    request_args: dict[str, Any], monkeypatch: pytest.MonkeyPatch, scope: str
) -> None:
    document = subject._compose_map_document(**request_args)
    assets = request_args["static_assets"]
    rows = normalize_asset_inventory(assets.manifest["assets"])
    inline = sum(
        len(pattern.findall(document)[0].encode())
        for pattern in (subject._NATIVE_BINDING, subject._MODELED_BINDING)
    )
    count = sum(
        cast(int, row["byte_count"])
        for row in rows
        if scope == "total" or row["initial_load"] is True
    )
    limit = (
        "ATLAS_INITIAL_MAX_BYTES"
        if scope == "initial"
        else "ATLAS_STATIC_ASSETS_MAX_BYTES"
    )
    exact = count + inline + 100 + (500 if scope == "total" else 0)
    monkeypatch.setattr(subject, limit, exact)
    subject._runtime_resources(assets, 100, document, (200, 300))
    monkeypatch.setattr(subject, limit, exact - 1)
    with pytest.raises(ValueError, match=f"{scope}.*byte budget"):
        subject._runtime_resources(assets, 100, document, (200, 300))


@pytest.mark.parametrize("binding", ["_NATIVE_BINDING", "_MODELED_BINDING"])
@pytest.mark.parametrize(
    "defect",
    ["missing", "duplicate", "reordered_duplicate", "invalid_json", "wrong_tag"],
)
def test_each_fixed_binding_has_exactly_one_owner(
    request_args: dict[str, Any], binding: str, defect: str
) -> None:
    document = subject._compose_map_document(**request_args)
    pattern = getattr(subject, binding)
    match = pattern.search(document)
    assert match is not None
    if defect == "missing":
        document = document[: match.start()] + document[match.end() :]
    elif defect == "reordered_duplicate":
        identity = (
            "atlas-native-lra-binding"
            if binding == "_NATIVE_BINDING"
            else "atlas-modeled-context-binding"
        )
        document += f"<script type='application/json' id='{identity}'>null</script>"
    elif defect == "invalid_json":
        document = document[: match.start(1)] + "{" + document[match.end(1) :]
    elif defect == "wrong_tag":
        document = (
            document[: match.start()]
            + match.group(0).replace("script", "div")
            + document[match.end() :]
        )
    else:
        document += match.group(0)
    with pytest.raises(ValueError):
        subject._runtime_resources(
            request_args["static_assets"], 100, document, (200, 300)
        )
