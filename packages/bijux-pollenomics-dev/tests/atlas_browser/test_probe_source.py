from __future__ import annotations

from pathlib import Path
import subprocess

import bijux_pollenomics_dev.ci.atlas_browser as atlas_browser


def test_dependency_free_probe_is_valid_node_module() -> None:
    probe = Path(atlas_browser.__file__).with_name("probe.mjs")

    completed = subprocess.run(
        ("node", "--check", str(probe)),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr


def test_page_readiness_uses_capture_api_and_mutation_observer() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    assert "BijuxPollenomicsAtlasCapture" in probe
    assert "api.awaitReady()" in probe
    assert "new MutationObserver" in probe
    assert "atlas capture API readiness timed out" in probe
    assert "observer.observe(document.documentElement" in probe
    assert "exact source taxon readiness timed out" in probe
    assert "observer.observe(select, { childList: true })" in probe
    assert "row.value === ${JSON.stringify(expected.taxon)}" in probe
    assert "setInterval(" not in probe


def test_provider_failure_uses_request_interception() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    assert "Fetch.enable" in probe
    assert "Fetch.requestPaused" in probe
    assert "Fetch.fulfillRequest" in probe
    assert "responseCode: 503" in probe


def test_nordic_source_states_are_literal_release_requirements() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    for literal in (
        "nodes: 9988, observations: 215903, younger: 21911, older: 22911",
        "code: 'TRSH', taxon: null, nodes: 9978, observations: 114225, younger: 21911, older: 22911",
        "code: 'UPHE', taxon: null, nodes: 9928, observations: 91739, younger: 21911, older: 22911",
        "code: 'AQVP', taxon: null, nodes: 4991, observations: 9666, younger: 18190, older: 19190",
        "taxon: 'source:neotoma:taxon:967', nodes: 469, observations: 469, younger: 3961, older: 4461",
        "taxon: 'source:neotoma:taxon:3924', nodes: 2, observations: 2, younger: 1651, older: 1751",
        "cereal.query_before_capture === 'cereal|secale'",
    ):
        assert literal in probe
    assert "exactSourceState(defaultSnapshot, expectedNordic.sample)" in probe
    assert "exactSourceState(sourceStates.TRSH, expectedNordic.TRSH)" in probe
    assert "exactTaxonState(secale, expectedNordic.secale" in probe
    assert "exactTaxonState(cereal, expectedNordic.cereal" in probe


def test_responsive_contract_proves_desktop_and_bottom_sheet_states() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    for selector in (
        "document.querySelector('.map-topbar')",
        "document.querySelector('.topbar-time-stepper')",
        "document.getElementById('sidebar')",
        "document.getElementById('panel-toggle')",
        "document.getElementById('mobile-scrim')",
        "document.getElementById('mobile-panel-close')",
        "document.getElementById('time-step-older')",
        "document.getElementById('time-step-newer')",
        "document.getElementById('time-stepper-status')",
        "document.getElementById('time-playback-toggle')",
    ):
        assert selector in probe
    assert "elements.topbar.right <= elements.sidebar.left - 1" in probe
    assert "layout.mobile.expanded.scrim_visible" in probe
    assert "layout.mobile.expanded.close_visible" in probe
    assert "layout.mobile.closed.scrim_hidden" in probe


def test_chronology_contract_drives_real_controls_and_refuses_null() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    assert "{ width: 1440, height: 900 }" in probe
    assert "{ width: 390, height: 844 }" in probe
    assert "slider.dispatchEvent(new Event('input', { bubbles: true }))" in probe
    assert "visible_source_chronology_point_count" in probe
    assert "newer.click()" in probe
    assert "older.click()" in probe
    assert "playback.click()" in probe
    assert "time_start_bp: null" in probe
    assert "time_end_bp: null" in probe
    assert "view: null" in probe
    assert "evidence_unchanged" in probe
    assert "document.elementFromPoint" in probe


def test_status_actions_prove_chronology_and_basemap_discoverability() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    for literal in (
        "discoverabilityFacts(normal.cdp, width)",
        "document.getElementById('time-stepper-status')",
        "document.getElementById('source-chronology-controls')",
        "document.getElementById('basemap-readout')",
        "document.getElementById('view-controls')",
        "document.getElementById('basemap-switch')",
        "OpenStreetMap · no key",
        "OpenTopoMap · no key",
        "Offline · no tiles",
        "document.activeElement === activeBasemap",
    ):
        assert literal in probe
    assert "chronology_status_action:" in probe
    assert "basemap_discoverability:" in probe
