from __future__ import annotations

import json

from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE
from bijux_pollenomics.reporting.map_publication import MapScopePolicy

from .support import run_node_json, template_block


def test_static_assets_keep_generic_untimed_context_at_full_extent() -> None:
    helper = template_block(
        "function staticAtlasTimeNeeded", "function staticAtlasSignalNeeded"
    )
    observed = run_node_json(
        """
const TIME_HAS_DATA=true;
let timeStartBp=0,timeIntervalYears=1000;
function timeWindowEndBp(){return timeStartBp+timeIntervalYears}
function timeFilterUsesFullExtent(){return timeStartBp===0&&timeWindowEndBp()>=1000}
function staticAtlasNonnegativeInteger(value){return Number(value)}
const row={asset_key:'untimed',record_count:359,untimed_record_count:359,time_min_bp:null,time_max_bp:null};
const generic={applies_time_filter:true,semantic_role:'archaeological_context'};
const source={applies_time_filter:true,semantic_role:'source_chronology_context'};
"""
        + helper
        + """
const genericFull=staticAtlasTimeNeeded(row,generic);
const sourceFull=staticAtlasTimeNeeded(row,source);
timeStartBp=100;timeIntervalYears=100;
console.log(JSON.stringify({genericFull,sourceFull,genericNarrow:staticAtlasTimeNeeded(row,generic)}));
"""
    )

    assert observed == {
        "genericFull": True,
        "sourceFull": False,
        "genericNarrow": False,
    }


def test_country_filtered_assets_require_a_governed_active_country() -> None:
    helper = template_block(
        "function staticAtlasCountryNeeded", "function staticAtlasTimeNeeded"
    )
    observed = run_node_json(
        """
const activeCountries=new Set(['Sweden']);
const layer={applies_country_filter:true};
function animalSourceChronologyCountryFilterBypassed(){return false}
"""
        + helper
        + """
console.log(JSON.stringify({
  sweden:staticAtlasCountryNeeded({country_keys:['Sweden']},layer),
  norway:staticAtlasCountryNeeded({country_keys:['Norway']},layer),
  unassigned:staticAtlasCountryNeeded({country_keys:['UNASSIGNED']},layer),
  blank:staticAtlasCountryNeeded({country_keys:[]},layer),
}));
"""
    )

    assert observed == {
        "sweden": True,
        "norway": False,
        "unassigned": False,
        "blank": False,
    }


def test_country_filtered_features_refuse_blank_country_values() -> None:
    visibility = template_block(
        "function pointFeatureVisible", "function geoJsonPositionIsAdmitted"
    )
    observed = run_node_json(
        """
const activeLayerKeys=new Set(['points','polygons']);
const activeCountries=new Set(['Sweden']);
function featureCoordinatePair(){return {latitude:59,longitude:18}}
function pointFeatureInTimeWindow(){return true}
function sourceChronologyFeatureMatches(){return true}
function featureMatchesAnimalFilters(){return true}
function featureMatchesScientificSelection(){return true}
function animalSourceChronologyCountryFilterBypassed(){return false}
function animalSourceChronologyLayerIsValid(){return true}
function animalSourceChronologyFeatureIsValid(){return true}
function modeledContextFeatureVisible(){return true}
function featureInTimeWindow(){return true}
const points={key:'points',applies_country_filter:true};
const polygons={key:'polygons',applies_country_filter:true};
"""
        + visibility
        + """
console.log(JSON.stringify({
  pointSweden:pointFeatureVisible(points,{country:'Sweden'}),
  pointBlank:pointFeatureVisible(points,{country:''}),
  polygonSweden:polygonFeatureVisible(polygons,{country:'Sweden'}),
  polygonBlank:polygonFeatureVisible(polygons,{country:''}),
}));
"""
    )

    assert observed == {
        "pointSweden": True,
        "pointBlank": False,
        "polygonSweden": True,
        "polygonBlank": False,
    }


def test_animal_candidates_refuse_blank_country_values() -> None:
    helper = template_block(
        "function animalCandidateEntries", "function animalEntryMatchesFilters"
    )
    observed = run_node_json(
        """
const layer={key:'animals',applies_country_filter:true,features:[
  {record_id:'sweden',country:'Sweden'},
  {record_id:'blank',country:''},
]};
const POINT_LAYERS=[layer];
const activeLayerKeys=new Set(['animals']);
const activeCountries=new Set(['Sweden']);
function isAnimalLayer(){return true}
function pointFeatureInTimeWindow(){return true}
function animalSourceChronologyCountryFilterBypassed(){return false}
"""
        + helper
        + """
console.log(JSON.stringify(animalCandidateEntries().map(({feature})=>feature.record_id)));
"""
    )

    assert observed == ["sweden"]


def test_generic_untimed_exclusion_reports_exact_or_ambiguous_denominator() -> None:
    helper = template_block(
        "function genericUntimedExclusion", "function sourceChronologyUntimedExclusion"
    )
    observed = run_node_json(
        """
let STATIC_ATLAS_INLINE=false;
const COUNTRIES=['Denmark','Finland','Norway','Sweden'];
const activeLayerKeys=new Set(['context']);
const ALL_LAYERS=[{key:'context',applies_time_filter:true,applies_country_filter:true,semantic_role:'context'}];
const STATIC_ATLAS_BOOTSTRAP={assets:[
  {asset_key:'sweden',domain:'nodes',layer_key:'context',country_keys:['Sweden'],untimed_record_count:4,chronology_absent_record_count:1,refused_chronology_record_count:2,contextual_chronology_record_count:1},
  {asset_key:'mixed',domain:'nodes',layer_key:'context',country_keys:['Sweden','Norway'],untimed_record_count:3,chronology_absent_record_count:1,refused_chronology_record_count:1,contextual_chronology_record_count:1},
]};
function staticAtlasNonnegativeInteger(value){return Number(value)}
function featureTimeAdmission(feature){return {status:feature.status}}
let activeCountries=new Set(COUNTRIES);
"""
        + helper
        + """
const all=genericUntimedExclusion();
activeCountries=new Set(['Sweden']);
const sweden=genericUntimedExclusion();
STATIC_ATLAS_INLINE=true;
ALL_LAYERS[0].features=[
  {country:'Sweden',status:'absent'},
  {country:'Sweden',status:'valid'},
  {country:'Sweden',status:'refused'},
  {country:'Norway',status:'contextual'},
];
const inline=genericUntimedExclusion();
console.log(JSON.stringify({all,sweden,inline}));
"""
    )

    assert observed == {
        "all": {
            "status": "available",
            "count": 7,
            "split_status": "available",
            "absent_count": 2,
            "refused_count": 3,
            "contextual_count": 2,
        },
        "sweden": {
            "status": "unavailable",
            "count": None,
            "split_status": "unavailable",
            "absent_count": None,
            "refused_count": None,
            "contextual_count": None,
        },
        "inline": {
            "status": "available",
            "count": 2,
            "split_status": "available",
            "absent_count": 1,
            "refused_count": 1,
            "contextual_count": 0,
        },
    }


def test_provider_failure_reaches_no_basemap_without_mutating_evidence() -> None:
    basemap_helpers = template_block(
        "function nextBasemapAfter", "Object.entries(basemaps)"
    )
    observed = run_node_json(
        """
const BASEMAP_FALLBACK_ORDER=['street','terrain','none'];
const BASEMAP_NAMES=[...BASEMAP_FALLBACK_ORDER];
const failedBasemaps=new Set(['street','terrain']);
const basemapErrorCounts=new Map();
const evidence=[{record_id:'site:1',latitude:0,longitude:0}];
let currentBasemap='terrain', activeBasemap='terrain', readout='';
const map={removed:0,removeLayer(){this.removed += 1}};
const basemaps={terrain:{added:0,addTo(){this.added += 1}}};
const document={querySelectorAll(){return []}};
function updateBasemapReadout(message){readout=message}
function syncHashState(){}
"""
        + basemap_helpers
        + """
const fallback=nextBasemapAfter('terrain');
setBasemap(fallback,{reason:'provider unavailable; evidence unaffected'});
console.log(JSON.stringify({fallback,currentBasemap,activeBasemap,readout,evidence,mapRemoved:map.removed}));
"""
    )

    assert observed == {
        "fallback": "none",
        "currentBasemap": "none",
        "activeBasemap": None,
        "readout": "provider unavailable; evidence unaffected",
        "evidence": [{"record_id": "site:1", "latitude": 0, "longitude": 0}],
        "mapRemoved": 1,
    }


def test_empty_and_provider_failure_modes_are_explicit() -> None:
    assert "const MAX_PROVIDER_TILE_ERRORS = 3" in MAP_DOCUMENT_TEMPLATE
    assert "failedBasemaps.add(name)" in MAP_DOCUMENT_TEMPLATE
    assert "return 'none'" in MAP_DOCUMENT_TEMPLATE
    assert 'data-basemap="none"' in MAP_DOCUMENT_TEMPLATE
    assert "Evidence data unaffected." in MAP_DOCUMENT_TEMPLATE
    assert (
        "emptyState.hidden = visiblePointEntries.length > 0 || renderedPolygonLayers.length > 0"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert "failure.setAttribute('role', 'alert')" in MAP_DOCUMENT_TEMPLATE


def test_scientific_controls_cover_all_resolution_levels() -> None:
    resolution_order = template_block(
        "const SCIENTIFIC_RESOLUTION_ORDER", "const DETAIL_RECORDS"
    )
    selection_helpers = template_block(
        "function featureMatchesScientificSelection", "function pointFeatureVisible"
    )
    control_renderer = template_block(
        "function renderScientificControls", "function visibleGovernedEdges"
    )
    observed = run_node_json(
        """
const SCIENTIFIC_SIGNALS=[
  {signal_id:'group:crops',resolution:'group'},
  {signal_id:'subgroup:cereals',resolution:'subgroup'},
  {signal_id:'role:direct',resolution:'role'},
  {signal_id:'taxon:wheat',resolution:'taxon'},
];
const activeScientificSignalIds=new Set(['subgroup:cereals']);
const ATLAS_EVIDENCE={classifications_status:'available'};
const scientificStatus={textContent:''}, scientificFilters={innerHTML:''};
const scientificActions={hidden:false};
const scientificSummary={textContent:''};
const sourceChronologyShortcuts={hidden:false,querySelectorAll(){return []}};
const document={querySelectorAll(){return []}};
function sourceChronologyLayers(){return []}
function escapeHtml(value){return String(value)}
function scientificCueGlyph(){return 'x'}
"""
        + resolution_order
        + selection_helpers
        + control_renderer
        + """
const layer={scientific_selection_enabled:true};
const feature={scientific_signal_ids:['subgroup:cereals']};
renderScientificControls();
console.log(JSON.stringify({
  order:SCIENTIFIC_RESOLUTION_ORDER,
  selected:featureMatchesScientificSelection(layer,feature),
  signals:scientificSignalsForFeature(feature).map((row)=>row.signal_id),
  subgroupControl:scientificFilters.innerHTML.includes('value="subgroup:cereals"'),
}));
"""
    )

    assert observed == {
        "order": ["whole", "group", "subgroup", "role", "taxon"],
        "selected": True,
        "signals": ["subgroup:cereals"],
        "subgroupControl": True,
    }


def test_scientific_controls_only_offer_source_views_when_the_scope_has_them() -> None:
    control_renderer = template_block(
        "function renderScientificControls", "function visibleGovernedEdges"
    )
    observed = run_node_json(
        """
const SCIENTIFIC_SIGNALS=[];
const SCIENTIFIC_RESOLUTION_ORDER=['whole','group','subgroup','role','taxon'];
const activeScientificSignalIds=new Set();
const ATLAS_EVIDENCE={classifications_status:'unavailable'};
const scientificStatus={textContent:''}, scientificFilters={innerHTML:''};
const scientificActions={hidden:false};
const scientificSummary={textContent:''};
const shortcutButtons=Array.from({length:6},()=>({disabled:false}));
const sourceChronologyShortcuts={
  hidden:false,
  querySelectorAll(selector){
    if(selector!=='[data-source-shortcut]') throw new Error('unexpected selector');
    return shortcutButtons;
  },
};
const document={querySelectorAll(){return []}};
let sourceLayerCount=0;
function sourceChronologyLayers(){return Array.from({length:sourceLayerCount},()=>({}))}
function escapeHtml(value){return String(value)}
function scientificCueGlyph(){return 'x'}
"""
        + control_renderer
        + """
function snapshot(){
  return {
    status:scientificStatus.textContent,
    summary:scientificSummary.textContent,
    shortcutsHidden:sourceChronologyShortcuts.hidden,
    shortcutsDisabled:shortcutButtons.every((button)=>button.disabled),
  };
}
renderScientificControls();
const withoutSourceChronology=snapshot();
sourceLayerCount=1;
renderScientificControls();
const withSourceChronology=snapshot();
console.log(JSON.stringify({withoutSourceChronology,withSourceChronology}));
"""
    )

    assert observed == {
        "withoutSourceChronology": {
            "status": (
                "Harmonized scientific classifications are awaiting qualified "
                "review. This scope has no source-native pollen chronology layers."
            ),
            "summary": "Accepted classifications unavailable",
            "shortcutsHidden": True,
            "shortcutsDisabled": True,
        },
        "withSourceChronology": {
            "status": (
                "Harmonized scientific classifications are awaiting qualified "
                "review. Source-native pollen-bearing sample presence, ecological-code, "
                "and exact-label chronology remains available below without asserting "
                "equivalence."
            ),
            "summary": "Source-native views available",
            "shortcutsHidden": False,
            "shortcutsDisabled": False,
        },
    }
    assert ".source-shortcuts[hidden] { display: none; }" in MAP_DOCUMENT_TEMPLATE


def test_inline_payload_supplies_the_runtime_filter_budget() -> None:
    policy = MapScopePolicy(
        key="test",
        label="Test",
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
    document = render_multi_country_map_html(
        "Test",
        "test-build",
        "2026-09-05",
        ("Sweden",),
        policy,
        [],
        [],
        "assets",
    )
    bootstrap_json = document.split(
        '<script id="atlas-static-bootstrap" type="application/json">', 1
    )[1].split("</script>", 1)[0]
    bootstrap = json.loads(bootstrap_json)
    runtime = run_node_json(
        f"const bootstrap={bootstrap_json}; console.log(JSON.stringify({{"
        "budget:bootstrap.budgets.filter_main_thread_max_ms,"
        "slow:51 > Number(bootstrap.budgets.filter_main_thread_max_ms)"
        "}));"
    )

    assert bootstrap["schema_version"] == "atlas-inline-bootstrap.v1"
    assert bootstrap["budgets"]["filter_main_thread_max_ms"] == 50
    assert isinstance(bootstrap["budgets"]["filter_main_thread_max_ms"], int)
    assert runtime == {"budget": 50, "slow": True}
