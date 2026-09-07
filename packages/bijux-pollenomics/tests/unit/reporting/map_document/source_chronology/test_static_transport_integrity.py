from __future__ import annotations

import json
from pathlib import Path
import re
from typing import cast

from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE
from bijux_pollenomics.reporting.map_publication import MapScopePolicy

from ..browser_semantics.support import (
    check_javascript_syntax,
    run_node_json,
    template_block,
)
from .support import (
    compressed_node_asset,
    compressed_provenance_asset,
    sharded_index_payload,
)


def test_rendered_browser_javascript_is_syntactically_valid(tmp_path: Path) -> None:
    policy = MapScopePolicy(
        key="source-chronology-test",
        label="Source chronology test",
        eyebrow_label="Test",
        summary="Test",
        bounds_summary="Test",
        default_basemap="none",
        initial_diameter_km=0,
        minimum_bounds=((0.0, 0.0), (1.0, 1.0)),
        filter_surfaces=(),
        legend_sections=(),
        visible_caveats=(),
        engine_summary="Test",
    )
    rendered = render_multi_country_map_html(
        "Source chronology test",
        "source-chronology-test-build",
        "2026-09-05",
        ("Sweden",),
        policy,
        [],
        [],
        "assets",
    )
    executable_scripts = [
        body
        for attributes, body in re.findall(
            r"<script([^>]*)>(.*?)</script>", rendered, flags=re.DOTALL
        )
        if 'type="application/json"' not in attributes
    ]
    check_javascript_syntax("\n".join(executable_scripts), tmp_path / "atlas.js")


def test_sharded_indexes_merge_without_dropped_references() -> None:
    helpers = template_block(
        "const STATIC_ATLAS_INDEX_KINDS", "function validateStaticAtlasPayload"
    )
    payload = json.dumps(sharded_index_payload(), separators=(",", ":"))
    observed = run_node_json(
        f"""
const STATIC_ATLAS_BOOTSTRAP={{budgets:{{chunk_max_bytes:4194304}}}};
function staticAtlasFailure(message){{throw new Error(`Static atlas data cannot be loaded: ${{message}}`)}}
function staticAtlasNonnegativeInteger(value,label){{
  const numeric=Number(value);
  if(!Number.isSafeInteger(numeric)||numeric<0) staticAtlasFailure(`${{label}} is invalid`);
  return numeric;
}}
async function staticAtlasSha256(text){{
  const digest=await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest)).map((value)=>value.toString(16).padStart(2,'0')).join('');
}}
{helpers}
const row={{asset_key:'indexes:1',record_count:4}};
const payload={payload};
(async()=>{{
  const merged=await staticAtlasMergeIndexShards(row,payload);
  console.log(JSON.stringify({{
    schema:merged.schema_version,
    referenceCount:merged.reference_count,
    countries:merged.country_feature_indexes,
    spatial:merged.spatial_degree_feature_indexes,
    time:merged.time_interval_feature_indexes,
    signals:merged.signal_layer_indexes,
    details:merged.detail_record_asset_keys,
  }}));
}})();
"""
    )

    assert observed == {
        "schema": "atlas-static-indexes.v2",
        "referenceCount": 4,
        "countries": {
            "Norway": {"source-samples": [1]},
            "Sweden": {"source-samples": [0, 2]},
        },
        "spatial": {"59:18": {"source-samples": [0, 1]}},
        "time": [[100, 200, "source-samples", 0]],
        "signals": {"source-samples": ["source-samples"]},
        "details": {"neotoma:site:1": "details:1"},
    }


def test_sharded_indexes_reject_duplicate_missing_and_count_drift() -> None:
    helpers = template_block(
        "const STATIC_ATLAS_INDEX_KINDS", "function validateStaticAtlasPayload"
    )
    duplicate = json.dumps(
        sharded_index_payload(duplicate_country=True), separators=(",", ":")
    )
    missing_payload = sharded_index_payload()
    missing_shards = list(cast(list[dict[str, object]], missing_payload["shards"]))
    missing_payload["shards"] = missing_shards[:-1]
    missing_payload["shard_count"] = len(missing_shards) - 1
    missing = json.dumps(missing_payload, separators=(",", ":"))
    drift_payload = sharded_index_payload()
    drift_payload["reference_count"] = 5
    drift = json.dumps(drift_payload, separators=(",", ":"))
    shard_count_payload = sharded_index_payload()
    shard_count_rows = cast(list[dict[str, object]], shard_count_payload["shards"])
    shard_count_rows[0]["record_count"] = 2
    shard_count = json.dumps(shard_count_payload, separators=(",", ":"))
    observed = run_node_json(
        f"""
const STATIC_ATLAS_BOOTSTRAP={{budgets:{{chunk_max_bytes:4194304}}}};
function staticAtlasFailure(message){{throw new Error(`Static atlas data cannot be loaded: ${{message}}`)}}
function staticAtlasNonnegativeInteger(value,label){{
  const numeric=Number(value);
  if(!Number.isSafeInteger(numeric)||numeric<0) staticAtlasFailure(`${{label}} is invalid`);
  return numeric;
}}
async function staticAtlasSha256(text){{
  const digest=await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest)).map((value)=>value.toString(16).padStart(2,'0')).join('');
}}
{helpers}
async function refusal(payload,row){{
  try {{ await staticAtlasMergeIndexShards(row,payload); return null; }}
  catch(error) {{ return error.message; }}
}}
(async()=>{{
  console.log(JSON.stringify({{
    duplicate:await refusal({duplicate},{{asset_key:'indexes:1',record_count:4}}),
    missing:await refusal({missing},{{asset_key:'indexes:1',record_count:4}}),
    drift:await refusal({drift},{{asset_key:'indexes:1',record_count:5}}),
    shardCount:await refusal({shard_count},{{asset_key:'indexes:1',record_count:4}}),
  }}));
}})();
"""
    )

    assert "duplicated or out of order" in observed["duplicate"]
    assert "index shard kind is missing" in observed["missing"]
    assert "merged reference count mismatch" in observed["drift"]
    assert "record count mismatch" in observed["shardCount"]


def test_index_runtime_retains_single_payload_compatibility() -> None:
    assert (
        "indexes: ['atlas-static-indexes.v1', 'atlas-static-indexes.v2', "
        "'atlas-static-indexes.v3']" in MAP_DOCUMENT_TEMPLATE
    )
    consume = template_block(
        "async function consumeStaticAtlasAsset", "function loadStaticAtlasAsset"
    )
    assert (
        "row.domain === 'indexes' && payload.schema_version === "
        "'atlas-static-indexes.v3'" in consume
    )
    assert ": payload;" in consume
    assert "STATIC_ATLAS_CHUNKS[row.domain] = acceptedPayload" in consume


def test_large_static_indexes_are_lazy_without_losing_detail_or_country_support() -> (
    None
):
    startup = template_block(
        "if (!STATIC_ATLAS_INLINE)", "function hydrateStaticAtlasLayers"
    )
    assert "candidate.initial_load === true" in startup
    assert "STATIC_ATLAS_CHUNKS.provenance" in startup
    assert "STATIC_ATLAS_CHUNKS.edges" in startup
    assert "STATIC_ATLAS_CHUNKS.sequences" in startup
    assert "STATIC_ATLAS_CHUNKS.indexes" not in startup

    detail_lookup = template_block(
        "async function detailTabsForRecordId", "async function detailTabsForFeature"
    )
    assert "await ensureStaticAtlasIndexesLoaded()" in detail_lookup
    assert "detail_index_load_failed" in detail_lookup

    country_controls = template_block(
        "function renderCountryControls", "function renderScientificControls"
    )
    assert "visiblePointEntries.filter" in country_controls
    assert "feature.country === country" in country_controls
    assert "STATIC_ATLAS_BOOTSTRAP.assets" not in country_controls
    assert "STATIC_ATLAS_CHUNKS.indexes" not in country_controls


def test_lazy_index_loader_is_one_time_and_refuses_invalid_inventory() -> None:
    loader = template_block(
        "async function ensureStaticAtlasIndexesLoaded",
        "async function detailTabsForRecordId",
    )
    observed = run_node_json(
        f"""
function staticAtlasNonnegativeInteger(value,label){{
  const numeric=Number(value);
  if(!Number.isSafeInteger(numeric)||numeric<0) throw new Error(`${{label}} is invalid`);
  return numeric;
}}
async function probe(assets, existingIndexes, interactionBytes, loadOutcome){{
  const STATIC_ATLAS_INLINE=false;
  const STATIC_ATLAS_BOOTSTRAP={{assets,budgets:{{interaction_max_bytes:interactionBytes}}}};
  const STATIC_ATLAS_CHUNKS={{indexes:existingIndexes}};
  let loadCount=0;
  async function loadStaticAtlasAsset(row){{
    loadCount+=1;
    if(loadOutcome==='failure') throw new Error('request failed');
    STATIC_ATLAS_CHUNKS.indexes={{detail_record_asset_keys:{{'site:1':'details:2'}}}};
  }}
  {loader}
  const first=await ensureStaticAtlasIndexesLoaded();
  const second=loadOutcome==='valid' ? await ensureStaticAtlasIndexesLoaded() : null;
  return {{first,second,loadCount}};
}}
const indexRow={{asset_key:'indexes:1',domain:'indexes',byte_count:512}};
(async()=>{{
  console.log(JSON.stringify({{
    already:await probe([indexRow],{{detail_record_asset_keys:{{}}}},1024,'valid'),
    valid:await probe([indexRow],null,1024,'valid'),
    missing:await probe([],null,1024,'valid'),
    duplicate:await probe([indexRow,{{...indexRow,asset_key:'indexes:2'}}],null,1024,'valid'),
    oversized:await probe([indexRow],null,511,'valid'),
    loadFailure:await probe([indexRow],null,1024,'failure'),
  }}));
}})();
"""
    )

    assert observed == {
        "already": {"first": True, "second": True, "loadCount": 0},
        "valid": {"first": True, "second": True, "loadCount": 1},
        "missing": {"first": False, "second": False, "loadCount": 0},
        "duplicate": {"first": False, "second": False, "loadCount": 0},
        "oversized": {"first": False, "second": False, "loadCount": 0},
        "loadFailure": {"first": False, "second": None, "loadCount": 1},
    }


def test_compressed_node_transport_is_bounded_authenticated_and_counted() -> None:
    valid_row, valid_envelope = compressed_node_asset("nodes:valid")
    drift_row, drift_envelope = compressed_node_asset("nodes:drift")
    drift_row["decoded_byte_count"] = cast(int, drift_row["decoded_byte_count"]) + 1
    over_row, over_envelope = compressed_node_asset(
        "nodes:over", padding="x" * 4096, decoded_byte_count=900
    )
    digest_row, digest_envelope = compressed_node_asset(
        "nodes:digest", payload_sha256="0" * 64
    )
    runtime = template_block(
        "async function staticAtlasSha256", "function loadStaticAtlasAsset"
    )
    observed = run_node_json(
        f"""
const STATIC_ATLAS_BOOTSTRAP={{
  build_id:'atlas-{"a" * 64}',scope_slug:'nordic',version:'test',
  budgets:{{chunk_max_bytes:1024}},
}};
const STATIC_ATLAS_SCHEMAS={{nodes:['atlas-node-chunk.v1'],details:['atlas-details-chunk.v1'],provenance:[],edges:[],sequences:[],indexes:['atlas-static-indexes.v1','atlas-static-indexes.v2','atlas-static-indexes.v3']}};
const STATIC_ATLAS_RAW_CHUNKS={json.dumps([valid_envelope, drift_envelope, over_envelope, digest_envelope], separators=(",", ":"))};
const STATIC_ATLAS_CHUNKS={{nodes:[],details:[]}};
const staticAtlasLoadedAssets=new Set();
function staticAtlasFailure(message){{throw new Error(`Static atlas data cannot be loaded: ${{message}}`)}}
function staticAtlasNonnegativeInteger(value,label){{
  const numeric=Number(value);
  if(!Number.isSafeInteger(numeric)||numeric<0) staticAtlasFailure(`${{label}} is invalid`);
  return numeric;
}}
{runtime}
async function refusal(row){{
  try {{ await consumeStaticAtlasAsset(row); return null; }}
  catch(error) {{ return error.message; }}
}}
(async()=>{{
  await consumeStaticAtlasAsset({json.dumps(valid_row, separators=(",", ":"))});
  console.log(JSON.stringify({{
    valid:{{loaded:[...staticAtlasLoadedAssets],nodeCount:STATIC_ATLAS_CHUNKS.nodes.length}},
    sizeDrift:await refusal({json.dumps(drift_row, separators=(",", ":"))}),
    overBudget:await refusal({json.dumps(over_row, separators=(",", ":"))}),
    digestDrift:await refusal({json.dumps(digest_row, separators=(",", ":"))}),
  }}));
}})();
"""
    )

    assert observed["valid"] == {"loaded": ["nodes:valid"], "nodeCount": 1}
    assert "decoded byte count mismatch" in observed["sizeDrift"]
    assert "decoded payload exceeds its byte budget" in observed["overBudget"]
    assert "payload integrity mismatch" in observed["digestDrift"]


def test_bootstrap_allows_governed_compressed_domains_without_weakening_legacy_json() -> (
    None
):
    bootstrap = template_block(
        "function validateStaticAtlasBootstrap", "async function staticAtlasSha256"
    )
    assert "!['provenance', 'nodes', 'details'].includes(row.domain)" in bootstrap
    assert (
        "['provenance', 'nodes', 'details'].includes(row.domain) && "
        "payloadEncoding === 'gzip_base64'" in bootstrap
    )
    assert "row.decoded_byte_count" in bootstrap
    assert "BP interval contradicts its untimed record count" in bootstrap
    assert "table.schema_version" not in bootstrap
    consume = template_block(
        "async function consumeStaticAtlasAsset", "function loadStaticAtlasAsset"
    )
    assert "staticAtlasBoundedGunzip" in consume
    assert "new Response(stream).text()" not in consume
    assert "const payloadEncoding = row.payload_encoding || 'json'" in consume


def test_compressed_provenance_uses_bounded_authenticated_transport() -> None:
    row, envelope = compressed_provenance_asset()
    refused_row, refused_envelope = compressed_provenance_asset(
        "provenance:drift", decoded_byte_count=1
    )
    runtime = template_block(
        "async function staticAtlasSha256", "function loadStaticAtlasAsset"
    )
    observed = run_node_json(
        f"""
const STATIC_ATLAS_BOOTSTRAP={{
  build_id:'atlas-{"a" * 64}',scope_slug:'nordic',version:'test',
  budgets:{{chunk_max_bytes:4096}},
}};
const STATIC_ATLAS_SCHEMAS={{nodes:[],details:[],provenance:['atlas-provenance-chunk.v3'],edges:[],sequences:[],indexes:[]}};
const STATIC_ATLAS_RAW_CHUNKS={json.dumps([envelope, refused_envelope], separators=(",", ":"))};
const STATIC_ATLAS_CHUNKS={{nodes:[],details:[],provenance:null}};
const staticAtlasLoadedAssets=new Set();
function staticAtlasFailure(message){{throw new Error(`Static atlas data cannot be loaded: ${{message}}`)}}
function staticAtlasNonnegativeInteger(value,label){{
  const numeric=Number(value);
  if(!Number.isSafeInteger(numeric)||numeric<0) staticAtlasFailure(`${{label}} is invalid`);
  return numeric;
}}
{runtime}
(async()=>{{
  await consumeStaticAtlasAsset({json.dumps(row, separators=(",", ":"))});
  let refusal=null;
  try {{ await consumeStaticAtlasAsset({json.dumps(refused_row, separators=(",", ":"))}); }}
  catch(error) {{ refusal=error.message; }}
  console.log(JSON.stringify({{
    loaded:[...staticAtlasLoadedAssets],
    schema:STATIC_ATLAS_CHUNKS.provenance.schema_version,
    layerCount:STATIC_ATLAS_CHUNKS.provenance.layers.length,
    refusal,
  }}));
}})();
"""
    )

    assert observed["loaded"] == ["provenance:0"]
    assert observed["schema"] == "atlas-provenance-chunk.v3"
    assert observed["layerCount"] == 0
    assert "decoded payload exceeds its declared byte count" in observed["refusal"]
