from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess

import pytest

from bijux_pollenomics_dev.ci import atlas_browser
from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
    GENERIC_TIME_AWARE_PROFILE,
    NORDIC_SOURCE_CHRONOLOGY_PROFILE,
)
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


def _run_capture_frame_clarity(
    snapshots: dict[str, dict[str, object]],
) -> subprocess.CompletedProcess[str]:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    match = re.search(
        r"function captureColorIsVisible.*?\n}\n\nfunction mapVisibilityPasses",
        probe,
        re.DOTALL,
    )
    assert match is not None
    function_source = match.group(0).removesuffix("\n\nfunction mapVisibilityPasses")
    script = (
        f"{function_source}\n"
        f"const snapshots = {json.dumps(snapshots)};\n"
        "const results = Object.fromEntries(Object.entries(snapshots).map("
        "([name, snapshot]) => [name, captureFrameIsClear("
        "snapshot, 'observation_chronology')]));\n"
        "process.stdout.write(JSON.stringify(results));\n"
    )
    return subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )


def _run_rendered_evidence_checks(
    scenarios: dict[str, dict[str, object]],
) -> subprocess.CompletedProcess[str]:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    match = re.search(
        r"function renderedEvidenceChangesWithCounts.*?\n}\n\nfunction captureColorIsVisible",
        probe,
        re.DOTALL,
    )
    assert match is not None
    function_source = match.group(0).removesuffix(
        "\n\nfunction captureColorIsVisible"
    )
    script = (
        f"{function_source}\n"
        f"const scenarios = {json.dumps(scenarios)};\n"
        "const results = Object.fromEntries(Object.entries(scenarios).map("
        "([name, value]) => [name, renderedEvidenceChangesWithCounts("
        "value.frames, value.count_field)]));\n"
        "process.stdout.write(JSON.stringify(results));\n"
    )
    return subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )


def _run_map_visibility_checks(
    scenarios: dict[str, dict[str, object]],
) -> subprocess.CompletedProcess[str]:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    match = re.search(
        r"function mapVisibilityPasses.*?\n}\n\nfunction desktopLayoutPasses",
        probe,
        re.DOTALL,
    )
    assert match is not None
    function_source = match.group(0).removesuffix("\n\nfunction desktopLayoutPasses")
    script = (
        f"{function_source}\n"
        f"const scenarios = {json.dumps(scenarios)};\n"
        "const results = Object.fromEntries(Object.entries(scenarios).map("
        "([name, value]) => [name, value.legend "
        "? expandedLegendPasses(value.facts) : mapVisibilityPasses(value.facts)]));\n"
        "process.stdout.write(JSON.stringify(results));\n"
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
    assert "captureFrameIsClear" not in generic
    assert "visible_source_chronology_point_count" not in generic
    assert "genericTimeJourney" in generic
    assert "data-time-interval" in probe
    assert "dataset.timeInterval === '1000'" in probe
    assert (
        "capture_frames_uncluttered"
        not in PROFILE_REQUIRED_ASSERTIONS[GENERIC_TIME_AWARE_PROFILE]
    )


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


def test_slider_journeys_bind_count_changes_to_rendered_map_evidence() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    assert probe.count("const renderedMapEvidenceSignature = () => JSON.stringify(") == 2
    assert probe.count("rendered_evidence_signature: renderedMapEvidenceSignature()") == 2
    assert ".leaflet-point-pane path" in probe
    assert ".leaflet-marker-pane .marker-cluster" in probe
    assert (
        "renderedEvidenceChangesWithCounts(journey.frames, "
        "'visible_source_chronology_point_count')"
    ) in probe
    assert (
        "renderedEvidenceChangesWithCounts(timeJourney.frames, "
        "'visible_point_count')"
    ) in probe


def test_rendered_evidence_check_fails_closed_on_stale_or_missing_rendering() -> None:
    def frame(count: int, signature: str | None = None) -> dict[str, object]:
        result: dict[str, object] = {"snapshot": {"visible_point_count": count}}
        if signature is not None:
            result["rendered_evidence_signature"] = signature
        return result

    scenarios = {
        "valid": {
            "count_field": "visible_point_count",
            "frames": [frame(0, "[]"), frame(3, '[["path","three"]]')],
        },
        "equal_counts_may_share_rendering": {
            "count_field": "visible_point_count",
            "frames": [frame(3, "same"), frame(3, "same")],
        },
        "stale_rendering": {
            "count_field": "visible_point_count",
            "frames": [frame(0, "same"), frame(3, "same")],
        },
        "missing_signature": {
            "count_field": "visible_point_count",
            "frames": [frame(0, "[]"), frame(3)],
        },
        "blank_signature": {
            "count_field": "visible_point_count",
            "frames": [frame(0, "[]"), frame(3, "")],
        },
        "one_frame": {
            "count_field": "visible_point_count",
            "frames": [frame(0, "[]")],
        },
    }

    completed = _run_rendered_evidence_checks(scenarios)

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "valid": True,
        "equal_counts_may_share_rendering": True,
        "stale_rendering": False,
        "missing_signature": False,
        "blank_signature": False,
        "one_frame": False,
    }


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
        [["nodes", "point", 1, -1, 10, 0], ["nodes", "point", 1, 10, 20, 0]],
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
    assert "center_uncovered:" in probe
    assert "uncovered_sample_count:" in probe
    assert "legendToggle.click()" in probe
    assert "expanded_legend: expandedLegend" in probe
    assert "content_accessible:" in probe
    assert "map_visibility: sampleMapVisibility()" in probe
    assert "mapVisibilityPasses(layout.clear_map)" in probe
    assert "expandedLegendPasses(layout.expanded_legend)" in probe
    assert "facts.sample_count >= 25" in probe
    assert "Math.ceil(facts.sample_count * 0.7)" in probe
    assert "document.getElementById('legend-body')" in probe
    assert "document.getElementById('floating-legend')" in probe
    assert "document.getElementById('topbar-search')" in probe
    assert "mapElement.contains(mapCenterHit)" in probe


def test_map_visibility_requires_clear_center_and_seventy_percent_sample() -> None:
    valid_visibility = {
        "center_uncovered": True,
        "uncovered_sample_count": 18,
        "sample_count": 25,
    }
    valid_legend = {
        "expanded": True,
        "toggle_expanded": True,
        "toggle_uncovered": True,
        "body_visible": True,
        "panel_bounded": True,
        "body_bounded": True,
        "content_accessible": True,
        "collapsed_after_journey": True,
        "map_visibility": valid_visibility,
    }
    scenarios = {
        "valid_map": {"legend": False, "facts": valid_visibility},
        "covered_center": {
            "legend": False,
            "facts": {**valid_visibility, "center_uncovered": False},
        },
        "below_seventy_percent": {
            "legend": False,
            "facts": {**valid_visibility, "uncovered_sample_count": 17},
        },
        "weak_sample": {
            "legend": False,
            "facts": {
                "center_uncovered": True,
                "uncovered_sample_count": 7,
                "sample_count": 10,
            },
        },
        "valid_legend": {"legend": True, "facts": valid_legend},
        "clipped_legend": {
            "legend": True,
            "facts": {**valid_legend, "content_accessible": False},
        },
        "legend_hides_map": {
            "legend": True,
            "facts": {
                **valid_legend,
                "map_visibility": {
                    **valid_visibility,
                    "uncovered_sample_count": 17,
                },
            },
        },
    }

    completed = _run_map_visibility_checks(scenarios)

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "valid_map": True,
        "covered_center": False,
        "below_seventy_percent": False,
        "weak_sample": False,
        "valid_legend": True,
        "clipped_legend": False,
        "legend_hides_map": False,
    }


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
    assert (
        "capture_frames_uncluttered"
        in PROFILE_REQUIRED_ASSERTIONS[NORDIC_SOURCE_CHRONOLOGY_PROFILE]
    )


def test_capture_frame_clarity_rejects_obstruction_and_semantic_drift() -> None:
    baseline: dict[str, object] = {
        "capture_layers": {
            "active_keys": [
                "country-boundaries",
                "neotoma-source-ecological-code",
            ],
            "evidence_layer_key": "neotoma-source-ecological-code",
            "orientation_keys": ["country-boundaries"],
        },
        "capture_presentation": {
            "schema_version": "atlas-capture-presentation.v1",
            "evidence_role": "observation_chronology",
            "null_handling": "null_not_zero",
            "interpolation_allowed": False,
            "propagation_use_allowed": False,
            "title": "Neotoma TRSH",
            "key_labels": [
                "source record",
                "records grouped at current zoom",
                "country boundary",
            ],
            "key_items": [
                {
                    "label": "source record",
                    "cue": "point",
                    "fill": "rgb(37, 99, 235)",
                    "stroke": "rgb(30, 64, 175)",
                },
                {
                    "label": "records grouped at current zoom",
                    "cue": "cluster-count",
                    "fill": "rgba(255, 255, 255, 0.9)",
                    "stroke": "rgba(24, 37, 61, 0.35)",
                },
                {
                    "label": "country boundary",
                    "cue": "line",
                    "fill": "rgba(0, 0, 0, 0)",
                    "stroke": "rgb(100, 116, 139)",
                },
            ],
            "caveat": "Observed records only; no interpolation or propagation inference.",
        },
        "capture_layout": {
            "overlay_visible": True,
            "overlay_bounded": True,
            "overlay_content_bounded": True,
            "overlay_content_overflow": False,
            "overlay_overlaps_map": False,
            "map_bounded": True,
            "scroll_x_px": 0,
            "scroll_y_px": 0,
            "map_width_px": 936,
            "viewport_width_px": 1440,
        },
        "visible_point_count": 1,
        "visible_source_chronology_point_count": 1,
        "visible_modeled_context_feature_count": 0,
        "visible_polygon_layer_count": 1,
        "visible_polygon_feature_count": 1,
    }
    mutations: tuple[tuple[str, object], ...] = (
        (
            "capture_layers.active_keys",
            ["country-boundaries", "neotoma-source-ecological-code", "noise"],
        ),
        ("capture_presentation.evidence_role", "modeled_context"),
        ("capture_presentation.null_handling", "null_as_zero"),
        ("capture_presentation.interpolation_allowed", True),
        ("capture_presentation.propagation_use_allowed", True),
        (
            "capture_presentation.key_labels",
            [
                "records grouped at current zoom",
                "source record",
                "country boundary",
            ],
        ),
        (
            "capture_presentation.key_items",
            [
                {
                    "label": "source record",
                    "cue": "area",
                    "fill": "rgb(37, 99, 235)",
                    "stroke": "rgb(30, 64, 175)",
                },
                {
                    "label": "records grouped at current zoom",
                    "cue": "cluster-count",
                    "fill": "rgba(255, 255, 255, 0.9)",
                    "stroke": "rgba(24, 37, 61, 0.35)",
                },
                {
                    "label": "country boundary",
                    "cue": "line",
                    "fill": "rgba(0, 0, 0, 0)",
                    "stroke": "rgb(100, 116, 139)",
                },
            ],
        ),
        ("capture_layout.overlay_visible", False),
        ("capture_layout.overlay_bounded", False),
        ("capture_layout.overlay_content_bounded", False),
        ("capture_layout.overlay_content_overflow", True),
        ("capture_layout.overlay_overlaps_map", True),
        ("capture_layout.map_bounded", False),
        ("capture_layout.scroll_x_px", 1),
        ("capture_layout.scroll_y_px", 1),
        ("capture_layout.map_width_px", 935),
        ("visible_point_count", 2),
        ("visible_modeled_context_feature_count", 1),
    )
    snapshots = {"valid": baseline}
    for path, invalid_value in mutations:
        mutated = deepcopy(baseline)
        parts = path.split(".")
        target = mutated
        for part in parts[:-1]:
            nested = target[part]
            assert isinstance(nested, dict)
            target = nested
        target[parts[-1]] = invalid_value
        snapshots[path] = mutated
    for name, item_index, field, invalid_value in (
        ("key_item_label_drift", 0, "label", "observation"),
        ("transparent_point_fill", 0, "fill", "rgba(0, 0, 0, 0)"),
        ("blank_cluster_stroke", 1, "stroke", ""),
        ("transparent_line_stroke", 2, "stroke", "transparent"),
    ):
        mutated = deepcopy(baseline)
        presentation = mutated["capture_presentation"]
        assert isinstance(presentation, dict)
        key_items = presentation["key_items"]
        assert isinstance(key_items, list)
        item = key_items[item_index]
        assert isinstance(item, dict)
        item[field] = invalid_value
        snapshots[name] = mutated

    completed = _run_capture_frame_clarity(snapshots)

    assert completed.returncode == 0, completed.stderr
    results = json.loads(completed.stdout)
    assert results == {
        "valid": True,
        **{path: False for path, _invalid_value in mutations},
        "key_item_label_drift": False,
        "transparent_point_fill": False,
        "blank_cluster_stroke": False,
        "transparent_line_stroke": False,
    }


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
