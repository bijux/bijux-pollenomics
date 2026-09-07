from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from .support import run_node_json, template_block


def test_capture_contract_exposes_semantic_frames_and_event_driven_readiness() -> None:
    block = template_block(
        "const ATLAS_CAPTURE_API_VERSION",
        "function updateBasemapReadout",
    )

    assert "'atlas-capture.v1'" in block
    assert "globalThis.BijuxPollenomicsAtlasCapture = Object.freeze" in block
    assert "applyFrame: applyAtlasCaptureFrame" in block
    assert "awaitReady: awaitAtlasCaptureReady" in block
    assert "snapshot: atlasCaptureSnapshot" in block
    assert "new MutationObserver" in block
    assert "document.fonts.ready" in block
    assert "map.invalidateSize({ animate: false })" in block
    assert "window.requestAnimationFrame" in block


def test_capture_contract_preserves_scientific_refusals_and_bp_semantics() -> None:
    block = template_block(
        "const ATLAS_CAPTURE_API_VERSION",
        "function updateBasemapReadout",
    )

    assert "time_start_bp <= time_end_bp" in block
    assert "typeof value !== 'number'" in block
    assert "Number.isFinite(value)" in block
    assert "candidate_succession_capture_not_releasable" in block
    assert "observation_chronology_is_propagation: false" in block
    assert "evidence_role: 'context_only'" in block
    assert "feature_count: sourceWindow.feature_count" in block
    assert "visible_source_chronology_point_count:" in block
    assert "layer.semantic_role === 'source_chronology_context'" in block
    assert "visible_modeled_context_feature_count:" in block
    assert "isModeledContextFeature(layer, feature.properties || {})" in block
    assert "visible_polygon_feature_count: visiblePolygonFeatureEntries.length" in block
    assert "capture_layers:" in block
    assert "capture_presentation: atlasCapturePresentationSnapshot()" in block
    assert "visible_modeled_no_pollen_data_count:" in block
    assert "no_pollen_data_count: sourceWindow.no_pollen_data_count" in block
    assert "capture_layout:" in block
    assert "view: {" in block
    assert "latitude: map.getCenter().lat" in block
    assert "longitude: map.getCenter().lng" in block
    assert "zoom: map.getZoom()" in block
    assert "overlay_visible: overlayVisible" in block
    assert "overlay_bounded:" in block
    assert "overlay_content_bounded: overlayContentBounded" in block
    assert "overlay_content_overflow:" in block
    assert "overlay_overlaps_map: overlayOverlapsMap" in block
    assert "map_bounded: mapBounds.left >= 0" in block
    assert "map_width_px: Math.round(mapBounds.width)" in block
    assert "scroll_x_px: Math.round(window.scrollX)" in block
    assert "scroll_y_px: Math.round(window.scrollY)" in block
    assert "renderAtlasCaptureOverlay(atlasCaptureSnapshot())" in block
    assert "interpolation_allowed: false" in block
    assert "propagation_use_allowed: false" in block
    assert "capture BP interval exceeds the selected source extent" in block
    assert "const minimum = sourceChronologyTimeValue(facet.time_min_bp)" in block


def test_capture_contract_validates_source_facets_context_metrics_and_view() -> None:
    block = template_block(
        "function normalizeAtlasCaptureFrame",
        "globalThis.BijuxPollenomicsAtlasCapture",
    )

    assert "capture source_level is unavailable" in block
    assert "capture source_code is unavailable" in block
    assert "capture source_taxon is unavailable" in block
    assert "capture modeled-context source window is unavailable" in block
    assert "capture modeled-context no-pollen denominator differs" in block
    assert (
        "frameSpec.no_pollen_data_count !== sourceWindow.no_pollen_data_count" in block
    )
    assert "capture modeled-context metric family is unavailable" in block
    assert "capture modeled-context metric is unavailable" in block
    assert "capture basemap is unsupported" in block
    assert "const captureFrame = normalizeAtlasCaptureFrame(frameSpec)" in block
    assert "document.documentElement.classList.add('atlas-capture-mode')" in block
    assert "setBasemap(captureFrame.basemap, { sync: false })" in block
    assert "function atlasCaptureOrientationKeys()" in block
    assert "layer.group === 'orientation'" in block
    assert block.count("activeLayerKeys = new Set(atlasCaptureOrientationKeys())") == 2
    assert "if (sourceLayer) activeLayerKeys.add(sourceLayer.key)" in block
    assert "activeLayerKeys.add(MODELED_CONTEXT.layer_key)" in block
    assert "sourceRecordConcentrationActive = false" in block
    assert "closeHelpDialog()" in block
    assert "setSearchOpen(false, false)" in block
    assert "setFocusState(null)" in block
    assert "map.closePopup()" in block
    assert "map.setView([captureFrame.view.latitude" in block
    assert "setPanelCollapsed(true, false)" in block
    assert "setLegendCollapsed(true, false)" in block
    assert "renderAtlasCaptureOverlay(atlasCaptureSnapshot())" in block
    assert "map.invalidateSize({ animate: false })" in block


def test_capture_resets_prior_obscuring_ui_and_concentration_state() -> None:
    apply_frame = template_block(
        "async function applyAtlasCaptureFrame",
        "globalThis.BijuxPollenomicsAtlasCapture",
    )
    observed = run_node_json(
        """
let sourceRecordConcentrationActive=true;
let sourceRecordConcentrationSnapshot={status:'available'};
let atlasCapturePresentation={stale:true};
let activeCountries=new Set();
let activeLayerKeys=new Set();
let activeSourceChronologyCode='';
let activeSourceChronologyTaxon='';
let sourceChronologyTaxonSearch='stale';
let timeStartBp=0;
let timeIntervalYears=0;
let helpOpen=true;
let searchOpen=true;
let focusOpen=true;
let popupOpen=true;
const document={documentElement:{classList:{add(){}}}};
const window={scrollTo(){}};
const map={invalidateSize(){},setView(){},closePopup(){popupOpen=false;}};
function normalizeAtlasCaptureFrame(value){return value;}
function stopTimePlayback(){}
function stopModeledContextPlayback(){}
function closeHelpDialog(){helpOpen=false;}
function setSearchOpen(open){searchOpen=open;}
function setFocusState(state){focusOpen=Boolean(state);}
function setBasemap(){}
function deactivateModeledContext(){}
function selectSourceChronologyLevel(){}
function sourceChronologyLayerForLevel(){return {key:'source-taxon'};}
function atlasCaptureOrientationKeys(){return ['boundaries'];}
function setPanelCollapsed(){}
function setLegendCollapsed(){}
async function renderMapState(){}
function atlasCaptureSnapshot(){return {
  sourceRecordConcentrationActive,
  sourceRecordConcentrationSnapshot,
  helpOpen,
  searchOpen,
  focusOpen,
  popupOpen,
};}
function renderAtlasCaptureOverlay(){}
async function awaitAtlasCaptureReady(){return atlasCaptureSnapshot();}
"""
        + apply_frame
        + """
(async()=>console.log(JSON.stringify(await applyAtlasCaptureFrame({
  storyKind:'source_chronology',countries:['SE'],basemap:'none',
  sourceLevel:'source_taxon',sourceTaxon:'Secale',
  frameWindow:{youngerBp:0,olderBp:100},view:null,
}))))();
"""
    )
    assert observed == {
        "sourceRecordConcentrationActive": False,
        "sourceRecordConcentrationSnapshot": None,
        "helpOpen": False,
        "searchOpen": False,
        "focusOpen": False,
        "popupOpen": False,
    }


def test_capture_overlay_keeps_map_clear_and_labels_evidence_in_every_frame() -> None:
    block = template_block(
        "function atlasCaptureOrientationKeys",
        "async function applyAtlasCaptureFrame",
    )

    for element_id in (
        "atlas-capture-role",
        "atlas-capture-time",
        "atlas-capture-title",
        "atlas-capture-counts",
        "atlas-capture-key",
        "atlas-capture-caveat",
    ):
        assert f'id="{element_id}"' in MAP_DOCUMENT_TEMPLATE
    assert ".atlas-capture-overlay {\n        display: none;" in MAP_DOCUMENT_TEMPLATE
    assert (
        "html.atlas-capture-mode .atlas-capture-overlay {\n        position: fixed;"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert (
        "html.atlas-capture-mode body {\n        overflow: hidden;"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert (
        "html.atlas-capture-mode .map-stage {\n        position: fixed;"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert "html.atlas-capture-mode .map-topbar" in MAP_DOCUMENT_TEMPLATE
    assert "html.atlas-capture-mode .floating-legend" in MAP_DOCUMENT_TEMPLATE
    assert "html.atlas-capture-mode .control-panel" in MAP_DOCUMENT_TEMPLATE
    assert "html.atlas-capture-mode .map-status" in MAP_DOCUMENT_TEMPLATE
    assert "html.atlas-capture-mode .focus-card" in MAP_DOCUMENT_TEMPLATE
    assert "html.atlas-capture-mode .help-dialog" in MAP_DOCUMENT_TEMPLATE
    assert "html.atlas-capture-mode .leaflet-popup" in MAP_DOCUMENT_TEMPLATE
    assert "html.atlas-capture-mode .map-stage" in MAP_DOCUMENT_TEMPLATE
    assert "atlasCapturePresentation !== null" in MAP_DOCUMENT_TEMPLATE
    assert (
        "window.scrollTo({ top: 0, left: 0, behavior: 'auto' });"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert (
        MAP_DOCUMENT_TEMPLATE.count(
            "window.scrollTo({ top: 0, left: 0, behavior: 'auto' });"
        )
        == 3
    )
    assert "padding-left: 330px" in MAP_DOCUMENT_TEMPLATE
    assert "width: 286px" in MAP_DOCUMENT_TEMPLATE
    assert "html.atlas-capture-mode .atlas-capture-heading" in MAP_DOCUMENT_TEMPLATE
    assert "justify-items: start" in MAP_DOCUMENT_TEMPLATE
    assert ".atlas-capture-time {\n        flex: 0 1 auto;" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert MAP_DOCUMENT_TEMPLATE.count("overflow-wrap: anywhere;") >= 4
    assert "Observed source chronology" in block
    assert "Modeled context · published source window" in block
    assert "Neotoma ${row.value} — ${row.label}" in block
    assert "Neotoma exact source-reported taxon — ${row.label}" in block
    assert "Neotoma source sample presence" in block
    assert "PANGAEA 937075 modeled context — ${metric.label}" in block
    assert "governed source nodes in this interval" in block
    assert "contributing observations" in block
    assert "published cells visible" in block
    assert "no pollen data · N/A, not 0" in block
    assert "display clusters are not abundance" in block
    assert "no interpolation, flow, or propagation inference" in block
    assert "no atlas interpolation, flow, or propagation inference" in block
    assert "schema_version: 'atlas-capture-presentation.v1'" in block
    assert "null_handling: 'null_not_zero'" in block
    assert "interpolation_allowed: false" in block
    assert "propagation_use_allowed: false" in block
    assert "function atlasCapturePresentationSnapshot()" in block
    assert "window.getComputedStyle(cue)" in block
    assert "key_items: keyItems" in block
    assert "style=\"background:${escapeHtml(item.fill)};border-color:${escapeHtml(item.stroke)};\"" in block
    assert "cue: 'cluster-count', fill: layerFill, stroke: layerStroke" in block
    assert (
        "atlasCaptureKey.innerHTML = keyItems.map(atlasCaptureKeyItemHtml).join('')"
        in block
    )


def test_capture_country_framing_is_quiet_without_changing_interactive_style() -> None:
    block = template_block("function renderPolygonLayers", "function updateStats")

    assert "classList.contains('atlas-capture-mode')" in block
    assert "color: '#64748b', weight: 1.1" in block
    assert "fillOpacity: 0.025, opacity: 0.62" in block
    assert "const style = countryStyle(country)" in block


def test_capture_omits_source_chronology_without_an_active_governed_facet() -> None:
    block = template_block("function atlasCaptureSnapshot", "function atlasCaptureOrientationKeys")

    assert "const sourceChronologyAvailable = Boolean(" in block
    assert "activeLayerKeys.has(sourceLayer.key)" in block
    assert "&& sourceFacet" in block
    assert "source_chronology: sourceChronologyAvailable ? {" in block
    assert "} : null," in block


def test_capture_frame_numbers_refuse_coercion_but_preserve_numeric_zero() -> None:
    helpers = template_block(
        "function captureFrameNumber",
        "function normalizeAtlasCaptureFrame",
    )
    observed = run_node_json(
        helpers
        + """
function outcome(callback) {
  try { return {status:'accepted', value:callback()}; }
  catch (error) { return {status:'refused', message:error.message}; }
}
const invalidNumbers=[null,undefined,'','0',-1,false,true,[],{}];
const invalidViews=[
  null,
  [],
  {},
  {latitude:null,longitude:0,zoom:0},
  {latitude:0,longitude:'',zoom:0},
  {latitude:0,longitude:0,zoom:false},
];
console.log(JSON.stringify({
  zero:outcome(()=>captureFrameNumber(0,'frame')),
  invalidNumbers:invalidNumbers.map((value)=>outcome(()=>captureFrameNumber(value,'frame')).status),
  defaultView:outcome(()=>captureFrameView(undefined)),
  zeroView:outcome(()=>captureFrameView({latitude:0,longitude:0,zoom:0})),
  signedView:outcome(()=>captureFrameView({latitude:-33.9,longitude:-70.7,zoom:4})),
  invalidViews:invalidViews.map((value)=>outcome(()=>captureFrameView(value)).status),
}));
"""
    )

    assert observed == {
        "zero": {"status": "accepted", "value": 0},
        "invalidNumbers": ["refused"] * 9,
        "defaultView": {"status": "accepted", "value": None},
        "zeroView": {
            "status": "accepted",
            "value": {"latitude": 0, "longitude": 0, "zoom": 0},
        },
        "signedView": {
            "status": "accepted",
            "value": {"latitude": -33.9, "longitude": -70.7, "zoom": 4},
        },
        "invalidViews": ["refused"] * 6,
    }
