"""Explicit evidence-panel loading preserves its optional transport boundary."""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.render import _separate_evidence_tools

from ...edges.inspection.test_relation_time_summary import edge
from ...support import run_node_json, template_block

HELPERS = template_block(
    "/* atlas-evidence-tools:begin */", "/* atlas-evidence-tools:end */"
)
_, OPTIONAL_BODY = _separate_evidence_tools(
    template_block("(async () => {", "    </script>")
)
DIGEST = hashlib.sha256(OPTIONAL_BODY).digest()
DESCRIPTOR = {
    "path": f"map.atlas-evidence-tools.{DIGEST.hex()[:16]}.js",
    "integrity": "sha256-" + base64.b64encode(DIGEST).decode("ascii"),
    "byte_count": len(OPTIONAL_BODY),
}


def observe(
    action: str,
    *,
    descriptor: object = DESCRIPTOR,
    protocol: str = "https:",
    inline: bool = False,
    rows: list[dict[str, Any]] | None = None,
) -> Any:
    source = (
        template_block("function escapeHtml", "function normalizedMediaLinks")
        + template_block("function scientificCueGlyph", "function finiteControlNumber")
        + (HELPERS if inline else "")
        + "const STATIC_ATLAS_BOOTSTRAP={runtime:{optional_controllers:{evidence_tools:"
        + json.dumps(descriptor)
        + "}}};const window={location:{protocol:"
        + json.dumps(protocol)
        + "}};const optionalBody="
        + json.dumps(OPTIONAL_BODY.decode())
        + ";let activeEdges="
        + json.dumps(rows or [])
        + ";\n"
        + r"""
const scripts=[],listeners={},containers={
  'relation-country-summary':{innerHTML:'',textContent:''},
  'relation-time-summary':{innerHTML:'',textContent:''}};
const panel={open:false,addEventListener(name,fn){listeners[name]=fn},querySelectorAll(){return Object.values(containers)}};
const document={head:{appendChild(script){scripts.push(script)}},
  createElement(tag){if(tag!=='script')throw Error('Unexpected element');return {events:{},addEventListener(name,fn){this.events[name]=fn}}},
  getElementById(id){return containers[id]||null},querySelectorAll(){return [panel]}};
function visibleGovernedEdges(){return activeEdges}
const atlasURLState={canPublish(){return false}},DETAIL_TABLE_PAGE_SIZE=25;
const tick=()=>new Promise(resolve=>setImmediate(resolve));
"""
        + template_block("let evidenceTools = null", "async function openEdgeDetail")
        + template_block(
            "document.querySelectorAll('details[data-evidence-tools]')",
            "document.getElementById('fullscreen-toggle')",
        )
        + "\n(async()=>{\n"
        + action
        + "\n})().catch(error=>{console.error(error);process.exitCode=1});"
    )
    return run_node_json(source)


def test_closed_or_rendered_panels_do_not_request_optional_code() -> None:
    observed = observe(
        "renderEvidenceToolPanels();listeners.toggle();await tick();"
        "console.log(JSON.stringify({requests:scripts.length,current:currentEvidenceTools(),"
        "country:containers['relation-country-summary'].innerHTML}));"
    )
    assert observed["requests"] == 0 and observed["current"] is None
    assert "Open this panel to load" in observed["country"]


@pytest.mark.parametrize("protocol", ["http:", "https:", "file:"])
def test_concurrent_explicit_load_is_shared_and_binds_actual_factory(
    protocol: str,
) -> None:
    observed = observe(
        "const first=loadEvidenceTools(),second=loadEvidenceTools();await tick();"
        "const script=scripts[0];(0,eval)(optionalBody);script.events.load();"
        "const tools=await first;const again=await loadEvidenceTools();"
        "const catalog=tools.pickerCatalog([{signal_id:'one',label:'<unsafe>',feature_key:'taxon:one',"
        "resolution:'taxon',status:'accepted',color:'#123456',non_color_cue:'diamond'}]);"
        "const html=tools.pickerHtml(catalog,tools.pickerInitial(catalog,['one']).state);"
        "console.log(JSON.stringify({same:first===second,cached:tools===again,"
        "requests:scripts.length,src:script.src,integrity:script.integrity||null,"
        "crossOrigin:script.crossOrigin||null,html,error:evidenceToolsError}));",
        protocol=protocol,
    )
    assert observed["same"] and observed["cached"] and observed["requests"] == 1
    assert observed["src"] == f"./{DESCRIPTOR['path']}"
    assert observed["integrity"] == (
        None if protocol == "file:" else DESCRIPTOR["integrity"]
    )
    assert observed["crossOrigin"] == (None if protocol == "file:" else "anonymous")
    assert observed["error"] is None
    assert "&lt;unsafe&gt;" in observed["html"] and "<unsafe>" not in observed["html"]
    assert "◆" in observed["html"]


@pytest.mark.parametrize(
    "change",
    [
        None,
        {},
        {"path": "../outside.js"},
        {"path": "https://outside.invalid/tools.js"},
        {"path": "map.atlas-evidence-tools.abc.js"},
        {"path": None},
        {"path": [DESCRIPTOR["path"]]},
        {"integrity": "sha256-invalid"},
        {"integrity": None},
        {"integrity": [DESCRIPTOR["integrity"]]},
        {"byte_count": None},
        {"byte_count": 0},
        {"byte_count": True},
        {"byte_count": 524289},
        {"extra": "unbound"},
    ],
)
def test_invalid_descriptor_refuses_before_request_and_exposes_sticky_error(
    change: dict[str, Any] | None,
) -> None:
    descriptor = (
        None if change is None else {} if not change else {**DESCRIPTOR, **change}
    )
    observed = observe(
        "const first=loadEvidenceTools();const error=await first.catch(error=>error.message);"
        "const second=loadEvidenceTools();await second.catch(()=>{});renderEvidenceToolPanels();"
        "console.log(JSON.stringify({same:first===second,requests:scripts.length,error,"
        "recorded:evidenceToolsError,country:containers['relation-country-summary'].innerHTML,"
        "time:containers['relation-time-summary'].innerHTML}));",
        descriptor=descriptor,
    )
    assert observed["same"] and observed["requests"] == 0
    assert observed["error"] == observed["recorded"]
    assert "transport identity is unavailable" in observed["error"]
    assert (
        observed["error"] in observed["country"]
        and observed["error"] in observed["time"]
    )


@pytest.mark.parametrize(
    "failure", ["missing_factory", "incomplete_factory", "factory_error", "network"]
)
def test_load_failures_remain_visible_without_retrying(failure: str) -> None:
    setup = {
        "missing_factory": "scripts[0].events.load();",
        "incomplete_factory": "globalThis.BijuxPollenomicsEvidenceTools=()=>({});scripts[0].events.load();",
        "factory_error": "globalThis.BijuxPollenomicsEvidenceTools=()=>{throw Error('<img src=x onerror=unsafe()>')};scripts[0].events.load();",
        "network": "scripts[0].events.error();",
    }[failure]
    observed = observe(
        "panel.open=true;listeners.toggle();await tick();"
        + setup
        + "await tick();const first=evidenceToolsRequest;"
        "listeners.toggle();await tick();"
        "console.log(JSON.stringify({same:first===evidenceToolsRequest,requests:scripts.length,"
        "error:evidenceToolsError,current:currentEvidenceTools(),"
        "country:containers['relation-country-summary'].innerHTML}));"
    )
    assert observed["same"] and observed["requests"] == 1
    assert observed["current"] is None and observed["error"]
    if failure == "factory_error":
        assert "&lt;img" in observed["country"] and "<img" not in observed["country"]
    else:
        assert observed["error"] in observed["country"]


def test_inline_helpers_use_no_optional_request_or_descriptor() -> None:
    observed = observe(
        "panel.open=true;listeners.toggle();const tools=await loadEvidenceTools();await tick();"
        "console.log(JSON.stringify({requests:scripts.length,current:tools===currentEvidenceTools(),"
        "error:evidenceToolsError,country:containers['relation-country-summary'].innerHTML}));",
        descriptor=None,
        protocol="unsupported:",
        inline=True,
    )
    assert observed["requests"] == 0 and observed["current"] is True
    assert observed["error"] is None
    assert "No retained active relation rows" in observed["country"]


def test_unsupported_protocol_does_not_request_or_claim_integrity() -> None:
    observed = observe(
        "const error=await loadEvidenceTools().catch(error=>error.message);"
        "console.log(JSON.stringify({requests:scripts.length,error}));",
        protocol="data:",
    )
    assert observed["requests"] == 0
    assert "require HTTP, HTTPS or a local file" in observed["error"]


def test_async_panel_mount_uses_latest_selection_and_respects_closed_panel() -> None:
    row = edge("latest-selection")
    observed = observe(
        "panel.open=true;listeners.toggle();await tick();"
        "panel.open=false;activeEdges="
        + json.dumps([row])
        + ";(0,eval)(optionalBody);scripts[0].events.load();await tick();"
        "const closed=containers['relation-country-summary'].innerHTML;"
        "panel.open=true;listeners.toggle();await tick();"
        "console.log(JSON.stringify({closed,requests:scripts.length,"
        "country:containers['relation-country-summary'].innerHTML,"
        "time:containers['relation-time-summary'].innerHTML}));"
    )
    assert observed["closed"] == "" and observed["requests"] == 1
    assert row["edge_id"] in observed["country"]
    assert "No retained active relation rows" not in observed["country"]
    assert "endpoint BP envelopes" in observed["time"]
