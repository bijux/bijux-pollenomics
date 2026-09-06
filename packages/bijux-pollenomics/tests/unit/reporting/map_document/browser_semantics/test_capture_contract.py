from __future__ import annotations

from .support import template_block


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
    assert "Number.isFinite(number)" in block
    assert "candidate_succession_capture_not_releasable" in block
    assert "observation_chronology_is_propagation: false" in block
    assert "evidence_role: 'context_only'" in block
    assert "feature_count: sourceWindow.feature_count" in block
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
    assert "map.setView([captureFrame.view.latitude" in block
    assert "setPanelCollapsed(true, false)" in block
    assert "setLegendCollapsed(true, false)" in block
