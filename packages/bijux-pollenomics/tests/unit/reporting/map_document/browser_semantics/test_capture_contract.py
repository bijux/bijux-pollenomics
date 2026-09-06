from __future__ import annotations

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
    assert "capture modeled-context metric family is unavailable" in block
    assert "capture modeled-context metric is unavailable" in block
    assert "capture basemap is unsupported" in block
    assert "const captureFrame = normalizeAtlasCaptureFrame(frameSpec)" in block
    assert "document.documentElement.classList.add('atlas-capture-mode')" in block
    assert "setBasemap(captureFrame.basemap, { sync: false })" in block
    assert (
        ".filter((layer) => layer.semantic_role === 'source_chronology_context')"
        in block
    )
    assert ".forEach((layer) => activeLayerKeys.delete(layer.key))" in block
    assert "sourceRecordConcentrationActive = false" in block
    assert "map.setView([captureFrame.view.latitude" in block
    assert "setPanelCollapsed(true, false)" in block
    assert "setLegendCollapsed(true, false)" in block


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
const invalidNumbers=[null,undefined,'','0',false,true,[],{}];
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
  invalidViews:invalidViews.map((value)=>outcome(()=>captureFrameView(value)).status),
}));
"""
    )

    assert observed == {
        "zero": {"status": "accepted", "value": 0},
        "invalidNumbers": ["refused"] * 8,
        "defaultView": {"status": "accepted", "value": None},
        "zeroView": {
            "status": "accepted",
            "value": {"latitude": 0, "longitude": 0, "zoom": 0},
        },
        "invalidViews": ["refused"] * 6,
    }
