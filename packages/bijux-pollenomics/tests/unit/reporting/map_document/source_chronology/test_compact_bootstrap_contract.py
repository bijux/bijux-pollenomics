from __future__ import annotations

import json
from typing import cast

from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    ASSET_TABLE_STORED_FIELDS,
)

from ..browser_semantics.support import (
    run_node_json,
    template_block,
)
from .support import (
    ASSET_TABLE_FIELDS,
    compact_bootstrap,
)


def test_compact_bootstrap_reconstructs_exact_rows_and_preserves_v1() -> None:
    normalizer = template_block(
        "function normalizeStaticAtlasBootstrap",
        "function validateStaticAtlasBootstrap",
    )
    observed = run_node_json(
        f"""
const STATIC_ATLAS_ASSET_TABLE_FIELDS=Object.freeze({json.dumps(ASSET_TABLE_FIELDS)});
const STATIC_ATLAS_ASSET_CORE_FIELD_COUNT=12;
function staticAtlasFailure(message){{throw new Error(message)}}
{normalizer}
const compact={json.dumps(compact_bootstrap(), separators=(",", ":"))};
const normalized=normalizeStaticAtlasBootstrap(compact);
const legacy={{schema_version:'atlas-static-bootstrap.v1',assets:[{{asset_key:'legacy'}}]}};
console.log(JSON.stringify({{
  schema:normalized.schema_version,
  node:normalized.assets[0],
  indexes:normalized.assets[1],
  legacyIdentity:normalizeStaticAtlasBootstrap(legacy)===legacy,
}}));
"""
    )

    assert observed["schema"] == "atlas-static-bootstrap.v2"
    assert observed["node"]["layer_key"] == "source-samples"
    assert observed["node"]["bounds"] == [55.0, 10.0, 70.0, 25.0]
    assert observed["indexes"]["asset_key"] == "indexes:1"
    assert "layer_key" not in observed["indexes"]
    assert observed["legacyIdentity"] is True


def test_derived_bootstrap_reconstructs_transport_metadata() -> None:
    integrity_helper = template_block(
        "function staticAtlasIntegrityFromHex",
        "function normalizeStaticAtlasBootstrap",
    )
    normalizer = template_block(
        "function normalizeStaticAtlasBootstrap",
        "function validateStaticAtlasBootstrap",
    )
    legacy_table = cast(dict[str, object], compact_bootstrap()["assets"])
    legacy_records = cast(list[list[object]], legacy_table["records"])
    field_indexes = {field: index for index, field in enumerate(ASSET_TABLE_FIELDS)}
    v2_stored_fields = [
        field
        for field in ASSET_TABLE_STORED_FIELDS
        if field
        not in {
            "chronology_absent_record_count",
            "refused_chronology_record_count",
            "contextual_chronology_record_count",
        }
    ]
    compact = {
        "schema_version": "atlas-static-bootstrap.v2",
        "assets": {
            "schema_version": "atlas-static-asset-table.v2",
            "scope_slug": "nordic",
            "fields": v2_stored_fields,
            "record_count": len(legacy_records),
            "records": [
                [record[field_indexes[field]] for field in v2_stored_fields]
                for record in legacy_records
            ],
        },
    }
    observed = run_node_json(
        f"""
const STATIC_ATLAS_ASSET_TABLE_FIELDS=Object.freeze({json.dumps(ASSET_TABLE_FIELDS)});
const STATIC_ATLAS_ASSET_TABLE_STORED_FIELDS=Object.freeze({json.dumps(ASSET_TABLE_STORED_FIELDS)});
const STATIC_ATLAS_ASSET_CORE_FIELD_COUNT=12;
function staticAtlasFailure(message){{throw new Error(message)}}
{integrity_helper}
{normalizer}
const normalized=normalizeStaticAtlasBootstrap({json.dumps(compact, separators=(",", ":"))});
console.log(JSON.stringify({{node:normalized.assets[0],indexes:normalized.assets[1]}}));
"""
    )

    assert observed["node"]["asset_key"] == "nodes:0"
    assert observed["node"]["path"] == "nordic.atlas-nodes.0000.aaaaaaaaaaaaaaaa.js"
    assert observed["node"]["payload_encoding"] == "gzip_base64"
    assert observed["node"]["initial_load"] is False
    assert observed["indexes"]["asset_key"] == "indexes:1"
    assert observed["indexes"]["path"] == (
        "nordic.atlas-indexes.0001.cccccccccccccccc.js"
    )
    assert observed["indexes"]["payload_encoding"] == "json"
    assert observed["indexes"]["initial_load"] is False


def test_v3_bootstrap_requires_reconciled_chronology_split() -> None:
    integrity_helper = template_block(
        "function staticAtlasIntegrityFromHex",
        "function normalizeStaticAtlasBootstrap",
    )
    normalizer = template_block(
        "function normalizeStaticAtlasBootstrap",
        "function validateStaticAtlasBootstrap",
    )
    legacy_table = cast(dict[str, object], compact_bootstrap()["assets"])
    legacy_records = cast(list[list[object]], legacy_table["records"])
    old_indexes = {field: index for index, field in enumerate(ASSET_TABLE_FIELDS)}
    split_fields = {
        "chronology_absent_record_count",
        "refused_chronology_record_count",
        "contextual_chronology_record_count",
    }
    current_fields = [
        *ASSET_TABLE_FIELDS[:-1],
        "chronology_absent_record_count",
        "refused_chronology_record_count",
        "contextual_chronology_record_count",
        ASSET_TABLE_FIELDS[-1],
    ]
    records = [
        [
            (
                0
                if field in split_fields and record[old_indexes["domain"]] == "nodes"
                else None
                if field in split_fields
                else record[old_indexes[field]]
            )
            for field in ASSET_TABLE_STORED_FIELDS
        ]
        for record in legacy_records
    ]
    bootstrap = {
        "schema_version": "atlas-static-bootstrap.v2",
        "assets": {
            "schema_version": "atlas-static-asset-table.v3",
            "scope_slug": "nordic",
            "fields": list(ASSET_TABLE_STORED_FIELDS),
            "record_count": len(records),
            "records": records,
        },
    }
    observed = run_node_json(
        f"""
const STATIC_ATLAS_ASSET_TABLE_FIELDS=Object.freeze({json.dumps(current_fields)});
const STATIC_ATLAS_ASSET_TABLE_STORED_FIELDS=Object.freeze({json.dumps(ASSET_TABLE_STORED_FIELDS)});
const STATIC_ATLAS_ASSET_CORE_FIELD_COUNT=12;
function staticAtlasFailure(message){{throw new Error(message)}}
{integrity_helper}
{normalizer}
const base={json.dumps(bootstrap, separators=(",", ":"))};
const valid=normalizeStaticAtlasBootstrap(base);
const missing=structuredClone(base);
const indexes=Object.fromEntries(missing.assets.fields.map((field,index)=>[field,index]));
for (const field of ['chronology_absent_record_count','refused_chronology_record_count','contextual_chronology_record_count']) missing.assets.records[0][indexes[field]]=null;
let refusal=null;
try{{normalizeStaticAtlasBootstrap(missing)}}catch(error){{refusal=error.message}}
console.log(JSON.stringify({{split:valid.assets[0].chronology_absent_record_count,refusal}}));
"""
    )

    assert observed["split"] == 0
    assert "chronology split is required" in observed["refusal"]


def test_compact_bootstrap_rejects_schema_width_count_identity_and_type_tamper() -> (
    None
):
    normalizer = template_block(
        "function normalizeStaticAtlasBootstrap",
        "function validateStaticAtlasBootstrap",
    )
    observed = run_node_json(
        f"""
const STATIC_ATLAS_ASSET_TABLE_FIELDS=Object.freeze({json.dumps(ASSET_TABLE_FIELDS)});
const STATIC_ATLAS_ASSET_CORE_FIELD_COUNT=12;
function staticAtlasFailure(message){{throw new Error(message)}}
{normalizer}
const base={json.dumps(compact_bootstrap(), separators=(",", ":"))};
function changed(change){{const value=structuredClone(base);change(value);return value}}
function refusal(value){{try{{normalizeStaticAtlasBootstrap(value);return null}}catch(error){{return error.message}}}}
const cases={{
  unknownTableKey:changed((value)=>{{value.assets.extra=true}}),
  duplicateField:changed((value)=>{{value.assets.fields[20]='asset_key'}}),
  width:changed((value)=>{{value.assets.records[0].pop()}}),
  count:changed((value)=>{{value.assets.record_count=3}}),
  duplicatePath:changed((value)=>{{value.assets.records[1][3]=value.assets.records[0][3]}}),
  sequence:changed((value)=>{{value.assets.records[1][2]=4}}),
  accountingType:changed((value)=>{{value.assets.records[0][8]='300'}}),
  nonNodeSelection:changed((value)=>{{value.assets.records[1][12]=0}}),
}};
console.log(JSON.stringify(Object.fromEntries(Object.entries(cases).map(([key,value])=>[key,refusal(value)]))));
"""
    )

    assert "asset table shape is invalid" in observed["unknownTableKey"]
    assert "asset table fields are invalid" in observed["duplicateField"]
    assert "width is invalid" in observed["width"]
    assert "record count is invalid" in observed["count"]
    assert "identity is duplicated" in observed["duplicatePath"]
    assert "sequence is invalid" in observed["sequence"]
    assert "accounting field is invalid" in observed["accountingType"]
    assert "non-node selection field is not null" in observed["nonNodeSelection"]


def test_static_asset_numbers_reject_non_scalar_zero_coercion() -> None:
    helpers = template_block(
        "function staticAtlasNonnegativeInteger",
        "function staticAtlasIntegrityFromHex",
    )
    observed = run_node_json(
        """
function staticAtlasFailure(message){throw new Error(message)}
function outcome(callback){
  try{return {status:'accepted',value:callback()}}
  catch(error){return {status:'refused',message:error.message}}
}
"""
        + helpers
        + """
const invalid=[[],[0],{},true,null,'1'];
console.log(JSON.stringify({
  integerZero:outcome(()=>staticAtlasNonnegativeInteger(0,'count')),
  integerStringZero:outcome(()=>staticAtlasNonnegativeInteger('0','count')),
  integerInvalid:invalid.map((value)=>outcome(()=>staticAtlasNonnegativeInteger(value,'count')).status),
  nullableMissing:outcome(()=>staticAtlasNullableFiniteNumber(null,'bound',-180,180)),
  nullableZero:outcome(()=>staticAtlasNullableFiniteNumber(0,'bound',-180,180)),
  nullableStringZero:outcome(()=>staticAtlasNullableFiniteNumber('0','bound',-180,180)),
  nullableInvalid:invalid.map((value)=>outcome(()=>staticAtlasNullableFiniteNumber(value,'bound',-180,180)).status),
}));
"""
    )

    assert observed == {
        "integerZero": {"status": "accepted", "value": 0},
        "integerStringZero": {"status": "refused", "message": "count is invalid"},
        "integerInvalid": ["refused"] * 6,
        "nullableMissing": {"status": "accepted", "value": None},
        "nullableZero": {"status": "accepted", "value": 0},
        "nullableStringZero": {"status": "accepted", "value": 0},
        "nullableInvalid": ["refused"] * 4 + ["accepted"] * 2,
    }
