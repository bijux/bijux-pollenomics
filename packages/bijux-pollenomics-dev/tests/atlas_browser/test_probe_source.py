from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

import pytest

from bijux_pollenomics_dev.ci import atlas_browser
from bijux_pollenomics_dev.ci.atlas_browser.verdict import PROFILE_REQUIRED_ASSERTIONS


def _run_generic_manifest_facts(
    manifest_expression: str,
) -> subprocess.CompletedProcess[str]:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    match = re.search(
        r"function genericManifestFacts.*?\n}\n\nasync function genericTimeJourney",
        probe,
        re.DOTALL,
    )
    assert match is not None
    function_source = match.group(0).removesuffix(
        "\n\nasync function genericTimeJourney"
    )
    script = (
        f"{function_source}\n"
        f"const manifest = {manifest_expression};\n"
        "try { console.log(JSON.stringify(genericManifestFacts(manifest))); } "
        "catch (error) { console.error(error.message); process.exitCode = 2; }\n"
    )
    return subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )


def _generic_manifest(*rows: list[object]) -> dict[str, object]:
    return {
        "assets": {
            "fields": [
                "domain",
                "layer_kind",
                "record_count",
                "time_min_bp",
                "time_max_bp",
                "untimed_record_count",
            ],
            "records": list(rows),
        },
        "domains": {
            "classifications": {"status": "unavailable", "reason_code": "test"},
            "edges": {"record_count": 0},
        },
    }


def test_dependency_free_probe_is_valid_node_module() -> None:
    probe = Path(atlas_browser.__file__).with_name("probe.mjs")

    completed = subprocess.run(
        ("node", "--check", str(probe)),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr


def test_probe_emits_the_exact_profile_assertion_inventories() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    for profile, required in PROFILE_REQUIRED_ASSERTIONS.items():
        match = re.search(
            rf"'{re.escape(profile)}': \[(?P<body>.*?)\n    \]",
            probe,
            re.DOTALL,
        )

        assert match is not None
        assert frozenset(re.findall(r"'([^']+)'", match.group("body"))) == required


def test_generic_profile_does_not_reuse_nordic_source_journeys() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    match = re.search(
        r"async function verifyGenericTimeAwareScope.*?\n}\n\nfunction genericManifestFacts",
        probe,
        re.DOTALL,
    )

    assert match is not None
    generic = match.group(0)
    assert "expectedNordic" not in generic
    assert "shortcutFrame" not in generic
    assert "visible_source_chronology_point_count" not in generic
    assert "genericTimeJourney" in generic
    assert "data-time-interval" in probe
    assert "dataset.timeInterval === '1000'" in probe


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
    assert "Fetch.failRequest" in probe
    assert "errorReason: 'Failed'" in probe
    assert "Fetch.fulfillRequest" not in probe
    assert "refusal_observation: failureObservation" in probe
    assert "timed_out: true" in probe
    refusal = re.search(
        r"async function waitForProviderRefusal.*?\n}\n\nasync function pageFacts",
        probe,
        re.DOTALL,
    )
    assert refusal is not None
    assert "await api.awaitReady()" not in refusal.group(0)
    assert "if (!api || typeof api.snapshot !== 'function') return false" in (
        refusal.group(0)
    )
    assert "observer.observe(document.documentElement" in refusal.group(0)
    assert "? api.snapshot() : null" in refusal.group(0)


def test_generic_time_journey_counts_zero_as_a_real_visibility_state() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    journey = re.search(
        r"async function genericTimeJourney.*?\n}\n\nasync function genericReducedMotionJourney",
        probe,
        re.DOTALL,
    )

    assert journey is not None
    assert "new Set(frames.map((row) => row.snapshot.visible_point_count))" in (
        journey.group(0)
    )
    assert "distinct_visible_counts" in journey.group(0)
    assert "filter((count) => count > 0)" not in journey.group(0)
    assert "slider.value = slider.max" in probe
    assert "after.time_window_bp.younger_bp > before.time_window_bp.younger_bp" in probe


def test_generic_manifest_counts_fail_closed_instead_of_coercing_null() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    assert "Number.isSafeInteger(value)" in probe
    assert "row[index.record_count] || 0" not in probe
    assert "manifest.domains?.edges?.record_count || 0" not in probe


def test_generic_manifest_facts_accepts_paired_ordered_intervals() -> None:
    manifest = _generic_manifest(
        ["nodes", "point", 2, 0, 100, 0],
        ["nodes", "point", 3, None, None, 3],
    )

    completed = _run_generic_manifest_facts(json.dumps(manifest))

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "point_record_count": 5,
        "time_min_bp": 0,
        "time_max_bp": 100,
        "classifications_status": "unavailable",
        "classifications_reason_code": "test",
        "edge_record_count": 0,
    }


@pytest.mark.parametrize(
    "rows",
    [
        [["nodes", "point", 1, 0, None, 0], ["nodes", "point", 1, 10, 20, 0]],
        [["nodes", "point", 1, 20, 10, 0], ["nodes", "point", 1, 10, 20, 0]],
        [["nodes", "point", 1, True, 10, 0], ["nodes", "point", 1, 10, 20, 0]],
    ],
)
def test_generic_manifest_facts_rejects_invalid_row_intervals(
    rows: list[list[object]],
) -> None:
    completed = _run_generic_manifest_facts(json.dumps(_generic_manifest(*rows)))

    assert completed.returncode == 2
    assert "BP bounds" in completed.stderr


def test_generic_manifest_facts_rejects_non_finite_row_interval() -> None:
    manifest = json.dumps(
        _generic_manifest(
            ["nodes", "point", 1, "__INFINITY__", 100, 0],
            ["nodes", "point", 1, 10, 20, 0],
        )
    ).replace('"__INFINITY__"', "Infinity")

    completed = _run_generic_manifest_facts(manifest)

    assert completed.returncode == 2
    assert "finite safe numbers" in completed.stderr


@pytest.mark.parametrize(
    "row",
    [
        ["nodes", "point", 1, 0, 100, 1],
        ["nodes", "point", 1, None, None, 0],
        ["nodes", "point", 0, 0, 100, 0],
        ["nodes", "point", 1, 0, 100, 2],
    ],
)
def test_generic_manifest_facts_rejects_untimed_time_contradictions(
    row: list[object],
) -> None:
    completed = _run_generic_manifest_facts(json.dumps(_generic_manifest(row)))

    assert completed.returncode == 2
    assert "untimed_record_count" in completed.stderr


def test_generic_manifest_facts_rejects_unsafe_time_magnitude() -> None:
    manifest = _generic_manifest(["nodes", "point", 1, 0, "__UNSAFE_TIME__", 0])
    expression = json.dumps(manifest).replace(
        '"__UNSAFE_TIME__"', "Number.MAX_SAFE_INTEGER + 1"
    )

    completed = _run_generic_manifest_facts(expression)

    assert completed.returncode == 2
    assert "finite safe numbers" in completed.stderr


def test_generic_manifest_facts_rejects_unsafe_aggregate_count() -> None:
    manifest = _generic_manifest(
        ["nodes", "point", 9_007_199_254_740_991, 0, 100, 0],
        ["nodes", "point", 9_007_199_254_740_991, 0, 100, 0],
    )

    completed = _run_generic_manifest_facts(json.dumps(manifest))

    assert completed.returncode == 2
    assert "aggregate point record_count" in completed.stderr


def test_cereal_finder_can_navigate_beyond_the_preferred_shortcut_result() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    journey = re.search(
        r"async function cerealFinderFrame.*?\n}\n\nasync function sliderChronologyJourney",
        probe,
        re.DOTALL,
    )

    assert journey is not None
    assert "row.value === 'source:neotoma:taxon:3924'" in journey.group(0)
    assert "select.dispatchEvent(new Event('change'" in journey.group(0)


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
    assert "layout.mobile.expanded.close_uncovered" in probe
    assert "layout.mobile.expanded.scrim_catches_outside_panel" in probe
    assert "layout.mobile.closed.scrim_hidden" in probe
    assert "layout.clear_map.panel_collapsed" in probe
    assert "layout.clear_map.legend_collapsed" in probe
    assert "layout.clear_map.search_collapsed" in probe
    assert "layout.clear_map.center_uncovered" in probe
    assert "layout.clear_map.uncovered_sample_count" in probe
    assert "document.getElementById('legend-body')" in probe
    assert "document.getElementById('topbar-search')" in probe
    assert "mapElement.contains(mapCenterHit)" in probe


def test_responsive_contract_proves_compact_search_keyboard_journey() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    for literal in (
        "document.documentElement.classList.add('atlas-probe-motion-mode')",
        "document.getElementById('search-toggle')",
        "document.getElementById('topbar-search')",
        "document.getElementById('search-input')",
        "searchToggle.click()",
        "document.activeElement === searchInput",
        "searchToggle.getAttribute('aria-expanded') === 'true'",
        "searchInput.dispatchEvent(new KeyboardEvent('keydown'",
        "key: 'Escape', code: 'Escape', bubbles: true, cancelable: true",
        "topbarSearch.hidden && !visible(topbarSearch)",
        "searchToggle.getAttribute('aria-expanded') === 'false'",
        "document.activeElement === searchToggle",
        "searchControlPasses(layout.search_control)",
    ):
        assert literal in probe
    assert "classList.add('atlas-capture-mode')" not in probe


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


def test_nordic_capture_frames_prove_uncluttered_presentation() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    for literal in (
        "capture_frames_uncluttered:",
        "captureFrameIsClear(snapshot, 'observation_chronology')",
        "function captureFrameIsClear(snapshot, evidenceRole)",
        "snapshot?.capture_layers",
        "snapshot?.capture_presentation",
        "snapshot?.capture_layout",
        "atlas-capture-presentation.v1",
        "presentation.null_handling === 'null_not_zero'",
        "presentation.interpolation_allowed === false",
        "presentation.propagation_use_allowed === false",
        "layout.overlay_content_bounded === true",
        "layout.overlay_content_overflow === false",
        "layout.overlay_overlaps_map === false",
        "layout.map_bounded === true",
        "layout.scroll_x_px === 0",
        "layout.scroll_y_px === 0",
        "layout.map_width_px >= Math.floor(layout.viewport_width_px * 0.65)",
        "snapshot.visible_point_count === snapshot.visible_source_chronology_point_count",
        "snapshot.visible_modeled_context_feature_count === 0",
        "snapshot.visible_polygon_feature_count >= snapshot.visible_polygon_layer_count",
    ):
        assert literal in probe


def test_status_actions_prove_chronology_and_basemap_discoverability() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    for literal in (
        "discoverabilityFacts(normal.cdp, width)",
        "document.getElementById('time-stepper-status')",
        "document.getElementById('source-chronology-controls')",
        "document.getElementById('time-controls')",
        "document.getElementById('basemap-readout')",
        "document.getElementById('view-controls')",
        "document.getElementById('basemap-switch')",
        "OpenStreetMap · no key",
        "OpenTopoMap · no key",
        "Offline · no tiles",
        "document.activeElement === activeBasemap",
        "sourceControls.open = false",
        "viewControls.open = false",
        "chronologyStatus.focus()",
        "document.activeElement === sourceChronologyLevel",
        "chronology_close_restored_focus",
        "basemapStatus.focus()",
        "basemap_close_restored_focus",
        "providerButtons.every((button) => visible(button) && bounded(button) && uncovered(button))",
        "sourceState.facet_node_count",
        "sourceState.facet_observation_denominator",
        "chronology_status_has_active_facet",
        "chronology_status_visible_values_valid",
    ):
        assert literal in probe
    assert "chronology_status_action:" in probe
    assert "time_status_action:" in probe
    assert "basemap_discoverability:" in probe
    assert (
        probe.count(
            "[responsive[1440], responsive[1024], responsive[768], responsive[390]].every((layout) => layout."
        )
        >= 2
    )
    assert "const statusUncovered = uncovered(status);" in probe
    assert "button.focus();" in probe
    assert "document.activeElement === button" in probe
    assert "provider_visibility: providerVisibility" in probe
    assert "row.focused && row.visible && row.bounded && row.uncovered" in probe
    assert "providerButtons.map((button) => button.innerText.trim())" in probe


def test_help_dialog_runtime_contract_proves_modal_focus_and_stacking() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    for literal in (
        "helpDialogFacts(normal.cdp, width)",
        "document.getElementById('help-toggle')",
        "document.getElementById('help-dialog')",
        "dialog.querySelector('[role=\"dialog\"]')",
        "document.getElementById('help-close')",
        "appShell.inert === true",
        "document.activeElement === close",
        "Input.dispatchKeyEvent",
        "document.activeElement?.id === 'help-return'",
        "document.activeElement?.id === 'help-close'",
        "document.activeElement === opener",
        "help_dialog_accessible:",
    ):
        assert literal in probe


def test_status_actions_do_not_manufacture_desktop_focus_restoration() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    assert "close_restored_focus: ${width} > 900" not in probe
    assert "chronology_close_restored_focus: ${width} > 900" not in probe
    assert "basemap_close_restored_focus: ${width} > 900" not in probe
    assert "status_enabled: !status.disabled" in probe
    assert (
        "status_controls_time_panel: status.getAttribute('aria-controls') === 'time-controls'"
        in probe
    )
    assert "status_describes_current_bp_window" in probe
    assert "close.dispatchEvent(new KeyboardEvent" not in probe
