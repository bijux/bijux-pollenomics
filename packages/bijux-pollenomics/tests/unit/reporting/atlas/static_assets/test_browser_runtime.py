from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess


from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from .fixtures.scientific_evidence import (
    build_detail_records,
    build_scientific_point_layers,
    build_scientific_signals,
)


def test_compressed_detail_chunk_round_trips_in_web_runtime(tmp_path: Path) -> None:
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="v66",
        point_layers=build_scientific_point_layers(),
        polygon_layers=[],
        detail_records=build_detail_records(),
        scientific_signals=build_scientific_signals(),
    )
    rows = normalize_asset_inventory(assets.manifest["assets"])
    detail_index = next(
        index for index, row in enumerate(rows) if row["domain"] == "details"
    )
    detail_row = rows[detail_index]
    assert detail_row["payload_encoding"] == "gzip_base64"
    script = assets.asset_paths[detail_index].read_text(encoding="utf-8")
    probe = (
        script
        + "\n(async()=>{const envelope=globalThis.__BIJUX_ATLAS_RAW_CHUNKS__[0];"
        + "const binary=atob(envelope.payload_gzip_base64);"
        + "const bytes=Uint8Array.from(binary,(character)=>character.charCodeAt(0));"
        + "const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));"
        + "const text=await new Response(stream).text();"
        + "const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))).map((value)=>value.toString(16).padStart(2,'0')).join('');"
        + "const payload=JSON.parse(text);console.log(JSON.stringify({digest,record_id:payload.records[0].record_id}));"
        + "})().catch((error)=>{console.error(error);process.exit(1)});"
    )
    node = shutil.which("node")
    assert node is not None
    result = subprocess.run(
        [node, "-e", probe], check=True, capture_output=True, text=True
    )
    observed = json.loads(result.stdout)
    assert observed == {
        "digest": detail_row["payload_sha256"],
        "record_id": "site:1",
    }


def test_detail_drawer_decodes_and_pages_governed_sead_tables() -> None:
    node = shutil.which("node")
    assert node is not None
    helper_start = MAP_DOCUMENT_TEMPLATE.index("function detailTableShape")
    helper_end = MAP_DOCUMENT_TEMPLATE.index("function renderFocusDetail", helper_start)
    helper_source = MAP_DOCUMENT_TEMPLATE[helper_start:helper_end]
    probe = (
        "const DETAIL_TABLE_PAGE_SIZE=25; const detailTablePages=new Map();"
        "function escapeHtml(value){return String(value)"
        ".replaceAll('&','&amp;').replaceAll('<','&lt;')"
        ".replaceAll('>','&gt;').replaceAll('\\\"','&quot;')}\n"
        + helper_source
        + r"""
const observationFields = [
  'source_value', 'source_value_state', 'source_unit_id',
  'taxon_relation_id', 'chronology_link_status', 'event_refusal_reason_codes',
];
const observationRecords = Array.from({length: 26}, (_, index) => [
  index === 0 ? null : (index === 1 ? 0 : index),
  index === 0 ? 0 : 1,
  8,
  'sead-taxon:5',
  0,
  [0],
]);
observationRecords[25][3] = 'sead-taxon:last-page';
const observations = {
  record_count: 26,
  fields: observationFields,
  records: observationRecords,
  encoding: 'sead-source-native-observation-table.v1',
  column_dictionaries: {
    source_value_state: ['source_null', 'reported'],
    chronology_link_status: ['direct_analysis_entity_eligible_claim'],
  },
  list_dictionary_fields: ['event_refusal_reason_codes'],
  list_value_dictionary: ['source_classification_not_accepted'],
};
const claim = {
  record_count: 1,
  fields: [
    'claim_type', 'source_age_value', 'source_age_unit',
    'analysis_entity_id', 'source_relation_path',
  ],
  records: [[0, [1850, null], 0, 90, 0]],
  encoding: 'sead-chronology-claim-table.v1',
  common_fields: {source_site_id: '2', country_code: 'DK'},
  column_dictionaries: {
    claim_type: ['dating_range'],
    source_age_unit: ['calendar_year'],
  },
  list_dictionary_fields: [],
  list_value_dictionary: [],
  source_age_value_columns_by_claim_type: {
    dating_range: ['low_value', 'high_value'],
  },
  source_age_value_inherited_fields_by_claim_type: {
    dating_range: {analysis_entity_id: 'analysis_entity_id'},
  },
  source_age_value_dictionaries_by_claim_type: {dating_range: {}},
  source_relation_path_dictionary: [[
    ['tbl_sites', 'site_id', 'common_fields.source_site_id'],
    ['tbl_analysis_entities', 'analysis_entity_id', 'analysis_entity_id'],
  ]],
};
const units = {
  record_count: 1,
  fields: ['source_unit_id', 'unit_name', 'unit_abbrev'],
  records: [['8', 'Years', 'yrs']],
  identifier_prefixes: {source_unit_id: 'sead-unit:'},
};
const taxa = {
  record_count: 1,
  fields: ['taxon_relation_id', 'genus_name', 'source_ecocodes'],
  records: [['sead-taxon:5', 'Triticum', [{abbreviation: 'CR'}]]],
};
const firstPage = renderDetailTable(observations, 'observations');
detailTablePages.set('observations', 1);
const secondPage = renderDetailTable(observations, 'observations');
const invalidObservations = {...observations, records: [[0, 99, 8, 'forged', 0, [0]]]};
invalidObservations.record_count = 1;
console.log(JSON.stringify({
  nullRow: decodeDetailTableRow(observations, observations.records[0]),
  zeroRow: decodeDetailTableRow(observations, observations.records[1]),
  claimRow: decodeDetailTableRow(claim, claim.records[0]),
  firstPage,
  secondPage,
  units: renderDetailTable(units, 'units'),
  taxa: renderDetailTable(taxa, 'taxa'),
  composition: renderDetailValue({...observations, value_semantics: units, taxa}, 'composition'),
  invalid: renderDetailTable(invalidObservations, 'invalid'),
}));
"""
    )
    result = subprocess.run(
        [node, "-e", probe], check=True, capture_output=True, text=True
    )
    observed = json.loads(result.stdout)

    assert observed["nullRow"]["source_value"] is None
    assert observed["nullRow"]["source_value_state"] == "source_null"
    assert observed["zeroRow"]["source_value"] == 0
    assert observed["zeroRow"]["source_value_state"] == "reported"
    assert observed["zeroRow"]["source_unit_id"] == 8
    assert observed["zeroRow"]["taxon_relation_id"] == "sead-taxon:5"
    assert observed["zeroRow"]["chronology_link_status"] == (
        "direct_analysis_entity_eligible_claim"
    )
    assert observed["zeroRow"]["event_refusal_reason_codes"] == [
        "source_classification_not_accepted"
    ]
    assert observed["claimRow"]["source_age_unit"] == "calendar_year"
    assert observed["claimRow"]["source_age_value"] == {
        "analysis_entity_id": 90,
        "high_value": None,
        "low_value": 1850,
    }
    assert observed["claimRow"]["source_relation_path"] == [
        {"table": "tbl_sites", "key": "site_id", "value": "2"},
        {
            "table": "tbl_analysis_entities",
            "key": "analysis_entity_id",
            "value": 90,
        },
    ]
    assert "Showing 1–25 of 26" in observed["firstPage"]
    assert "sead-taxon:last-page" not in observed["firstPage"]
    assert "Showing 26–26 of 26" in observed["secondPage"]
    assert "sead-taxon:last-page" in observed["secondPage"]
    assert "Years" in observed["units"]
    assert "sead-unit:8" in observed["units"]
    assert "Triticum" in observed["taxa"]
    assert "CR" in observed["taxa"]
    assert "Years" in observed["composition"]
    assert "Triticum" in observed["composition"]
    assert "column dictionaries" not in observed["composition"]
    assert "encoded_detail_table_invalid" in observed["invalid"]
    assert "forged" not in observed["invalid"]


def test_browser_filter_helpers_preserve_eligibility_and_restore_exact_state() -> None:
    node = shutil.which("node")
    assert node is not None

    start = MAP_DOCUMENT_TEMPLATE.index("function atlasCountryPairKey")
    end = MAP_DOCUMENT_TEMPLATE.index("function clampTimeInterval", start)
    helper_source = MAP_DOCUMENT_TEMPLATE[start:end]
    probe = (
        helper_source
        + """
const edges = [
  {edge_id:'cross', source_country:'Sweden', target_country:'Norway', signal_id:'whole'},
  {edge_id:'domestic', source_country:'Sweden', target_country:'Sweden', signal_id:'group'},
];
const allCountries = new Set(['Sweden', 'Norway']);
const allSignals = new Set(['whole', 'group']);
const defaults = atlasFilterStateSnapshot(allCountries, allSignals, 'all', false);
const changed = atlasFilterStateSnapshot(new Set(['Sweden']), new Set(['group']), 'Sweden|Sweden', true);
const restored = atlasFilterStateSnapshot(new Set(['Norway', 'Sweden']), new Set(['group', 'whole']), 'all', false);
console.log(JSON.stringify({
  eligibility: edges.length,
  all: edges.filter((edge) => atlasEdgeVisible(edge, allCountries, 'all', false, allSignals)).length,
  cross: edges.filter((edge) => atlasEdgeVisible(edge, allCountries, 'all', true, allSignals)).length,
  pair: edges.filter((edge) => atlasEdgeVisible(edge, allCountries, 'Norway|Sweden', false, allSignals)).length,
  sweden: edges.filter((edge) => atlasEdgeVisible(edge, new Set(['Sweden']), 'all', false, allSignals)).length,
  defaults_equal_restored: atlasFilterStateEquals(defaults, restored),
  defaults_equal_changed: atlasFilterStateEquals(defaults, changed),
}));
"""
    )
    result = subprocess.run(
        [node, "-e", probe], check=True, capture_output=True, text=True
    )

    assert json.loads(result.stdout) == {
        "eligibility": 2,
        "all": 2,
        "cross": 1,
        "pair": 1,
        "sweden": 1,
        "defaults_equal_restored": True,
        "defaults_equal_changed": False,
    }
