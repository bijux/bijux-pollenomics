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
    NATIVE_LRA_PROFILE,
    NORDIC_SOURCE_CHRONOLOGY_PROFILE,
    RAA_RETAINED_CONTEXT_PROFILE,
    SIGNED_NATIVE_LRA_PROFILE,
)
from bijux_pollenomics_dev.ci.atlas_browser.verdict import PROFILE_REQUIRED_ASSERTIONS


def _run_browser_identity(
    version: dict[str, str], binary: str = "/usr/bin/chromium"
) -> subprocess.CompletedProcess[str]:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    match = re.search(
        r"function browserIdentity.*?\n}",
        probe,
        re.DOTALL,
    )
    assert match is not None
    function_source = match.group(0)
    script = (
        f"{function_source}\n"
        f"const version = {json.dumps(version)};\n"
        f"const binary = {json.dumps(binary)};\n"
        "try { console.log(JSON.stringify(browserIdentity(version, binary))); } "
        "catch (error) { console.error(error.message); process.exitCode = 2; }\n"
    )
    return subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )


def test_probe_records_runtime_browser_identity_without_brand_assumptions() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    assert "Browser.getVersion" in probe
    assert "browser: browserVersion" in probe
    assert "Brave Browser" not in probe
    assert "brave-browser.log" not in probe


def test_probe_preserves_browser_supplied_product_and_version_identity() -> None:
    result = _run_browser_identity(
        {
            "product": "Chrome/140.0.0.0",
            "revision": "@0123456789abcdef",
            "userAgent": "Mozilla/5.0 HeadlessChrome/140.0.0.0",
            "jsVersion": "14.0.0",
            "protocolVersion": "1.3",
        }
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "product": "Chrome/140.0.0.0",
        "revision": "@0123456789abcdef",
        "user_agent": "Mozilla/5.0 HeadlessChrome/140.0.0.0",
        "javascript_version": "14.0.0",
        "protocol_version": "1.3",
        "binary": "/usr/bin/chromium",
    }


def test_probe_refuses_incomplete_browser_identity() -> None:
    result = _run_browser_identity(
        {
            "product": "",
            "revision": "@0123456789abcdef",
            "userAgent": "Mozilla/5.0",
            "jsVersion": "14.0.0",
            "protocolVersion": "1.3",
        }
    )

    assert result.returncode == 2
    assert "browser identity field is unavailable: product" in result.stderr


def _probe_function_block(start: str, end: str) -> str:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    match = re.search(rf"{start}.*?\n}}\n\n{end}", probe, re.DOTALL)
    assert match is not None
    return match.group(0).removesuffix(f"\n\n{end}")


def test_browser_shutdown_awaits_term_and_kill_completion() -> None:
    functions = _probe_function_block(
        "function browserHasExited", "function closeServer"
    )
    script = f"""
import {{ EventEmitter }} from 'node:events';
{functions}

class FakeBrowser extends EventEmitter {{
  constructor(closeAfter) {{
    super();
    this.closeAfter = closeAfter;
    this.exitCode = null;
    this.signalCode = null;
    this.signals = [];
  }}
  kill(signal) {{
    this.signals.push(signal);
    if (signal === this.closeAfter) {{
      setTimeout(() => {{ this.signalCode = signal; this.emit('close', null, signal); }}, 1);
    }}
    return true;
  }}
}}

async function exercise(closeAfter) {{
  const browser = new FakeBrowser(closeAfter);
  const closed = new Promise((resolve) => browser.once('close', resolve));
  let error = null;
  try {{ await stopBrowser(browser, closed, 5); }} catch (caught) {{ error = caught.message; }}
  return {{ signals: browser.signals, error }};
}}

const alreadyClosed = {{ exitCode: 0, signalCode: null, signals: [], kill(signal) {{ this.signals.push(signal); }} }};
await stopBrowser(alreadyClosed, Promise.resolve(), 5);
process.stdout.write(JSON.stringify({{
  graceful: await exercise('SIGTERM'),
  forced: await exercise('SIGKILL'),
  refused: await exercise('never'),
  already_closed_signals: alreadyClosed.signals,
}}));
"""

    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["graceful"] == {"signals": ["SIGTERM"], "error": None}
    assert result["forced"] == {
        "signals": ["SIGTERM", "SIGKILL"],
        "error": None,
    }
    assert result["refused"] == {
        "signals": ["SIGTERM", "SIGKILL"],
        "error": "browser process did not close after SIGKILL",
    }
    assert result["already_closed_signals"] == []


def test_cleanup_preserves_original_verification_error() -> None:
    function = _probe_function_block(
        "async function finalizeBrowserVerification",
        "async function verifyNordicSourceChronologyScope",
    )
    script = f"""
{function}
const original = new Error('verification failed');
const completed = [];
const messages = [];
console.error = (message) => messages.push(message);
let caught = null;
try {{
  await finalizeBrowserVerification(original, [
    ['browser process', async () => {{ throw new Error('shutdown failed'); }}],
    ['browser log', async () => {{ completed.push('browser log'); }}],
  ]);
}} catch (error) {{ caught = error; }}
process.stdout.write(JSON.stringify({{
  original_preserved: caught === original,
  completed,
  messages,
}}));
"""

    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "original_preserved": True,
        "completed": ["browser log"],
        "messages": [
            "atlas browser cleanup also failed (browser process): shutdown failed"
        ],
    }


def test_browser_log_is_closed_before_profile_cleanup_with_bounded_retries() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    assert "const completion = finished(stream);" in probe
    assert "await completion;" in probe
    assert "['browser log', () => closeBrowserLog(browserLog)]" in probe
    assert "maxRetries: 5" in probe
    assert "retryDelay: 100" in probe
    assert probe.index("['browser log'") < probe.index("['browser profile'")


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


def _run_provider_refusal_readiness_checks() -> subprocess.CompletedProcess[str]:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    match = re.search(
        r"async function waitForProviderRefusal.*?\n}\n\nasync function pageFacts",
        probe,
        re.DOTALL,
    )
    assert match is not None
    function_source = match.group(0).removesuffix("\n\nasync function pageFacts")
    script = f"""
{function_source}
const timeoutMs = 250;
let activeObserver = null;
globalThis.MutationObserver = class {{
  constructor(callback) {{
    this.callback = callback;
    this.disconnected = false;
    activeObserver = this;
  }}
  observe() {{}}
  disconnect() {{ this.disconnected = true; }}
}};
globalThis.document = {{
  documentElement: {{}},
  getElementById: () => ({{ textContent: 'provider unavailable' }}),
}};
let initialReady = false;
async function captureReady() {{ await Promise.resolve(); initialReady = true; }}
async function evaluate(_cdp, source) {{
  if (!initialReady) throw Error('Provider observer ran before initial capture readiness');
  initialReady = false;
  return (0, eval)(source);
}}

async function successScenario() {{
  let state = {{ basemap: 'street', ready: true, visible_point_count: 1239 }};
  let resolveReady;
  let awaitReadyCalls = 0;
  const ready = new Promise((resolve) => {{ resolveReady = resolve; }});
  globalThis.BijuxPollenomicsAtlasCapture = {{
    snapshot: () => structuredClone(state),
    awaitReady: () => {{ awaitReadyCalls += 1; return ready; }},
  }};
  const pending = waitForProviderRefusal(null);
  await new Promise(resolve => setImmediate(resolve));
  const observer = activeObserver;
  state = {{ basemap: 'none', ready: false, visible_point_count: 0 }};
  observer.callback();
  let settled = false;
  void pending.then(() => {{ settled = true; }}, () => {{ settled = true; }});
  await Promise.resolve();
  await Promise.resolve();
  const settledBeforeReady = settled;
  resolveReady({{ basemap: 'none', ready: true, visible_point_count: 1239 }});
  const observation = await pending;
  return {{
    settled_before_ready: settledBeforeReady,
    await_ready_calls: awaitReadyCalls,
    observer_disconnected: observer.disconnected,
    observation,
  }};
}}

async function rejectionScenario() {{
  let state = {{ basemap: 'street', ready: true }};
  globalThis.BijuxPollenomicsAtlasCapture = {{
    snapshot: () => structuredClone(state),
    awaitReady: () => Promise.reject(new Error('readiness failed')),
  }};
  const pending = waitForProviderRefusal(null);
  await new Promise(resolve => setImmediate(resolve));
  state = {{ basemap: 'none', ready: false }};
  activeObserver.callback();
  try {{
    await pending;
    return null;
  }} catch (error) {{
    return error.message;
  }}
}}

const result = {{
  success: await successScenario(),
  rejection: await rejectionScenario(),
}};
process.stdout.write(JSON.stringify(result));
"""
    return subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )


def _run_fit_active_checks(
    scenarios: dict[str, dict[str, object]],
) -> subprocess.CompletedProcess[str]:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    match = re.search(
        r"function fitActivePasses.*?\n}\n\nfunction renderedEvidenceChangesWithCounts",
        probe,
        re.DOTALL,
    )
    assert match is not None
    function_source = match.group(0).removesuffix(
        "\n\nfunction renderedEvidenceChangesWithCounts"
    )
    script = (
        f"{function_source}\n"
        f"const scenarios = {json.dumps(scenarios)};\n"
        "const results = Object.fromEntries(Object.entries(scenarios).map("
        "([name, facts]) => [name, fitActivePasses(facts)]));\n"
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
    function_source = match.group(0).removesuffix("\n\nfunction captureColorIsVisible")
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


def _run_signed_capture_view_checks(
    scenarios: dict[str, dict[str, object]],
) -> subprocess.CompletedProcess[str]:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    match = re.search(
        r"function webMercatorPixelPoint.*?\n}\n\nfunction renderedEvidenceChangesWithCounts",
        probe,
        re.DOTALL,
    )
    assert match is not None
    function_source = match.group(0).removesuffix(
        "\n\nfunction renderedEvidenceChangesWithCounts"
    )
    script = (
        f"{function_source}\n"
        f"const scenarios = {json.dumps(scenarios)};\n"
        "const results = Object.fromEntries(Object.entries(scenarios).map("
        "([name, value]) => [name, signedCaptureViewPreserved(value)]));\n"
        "process.stdout.write(JSON.stringify(results));\n"
    )
    return subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )


def _run_probe_boundary_parsers() -> subprocess.CompletedProcess[str]:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    sources = []
    for name in (
        "parseNonnegativeIntegerText",
        "parseSliderBounds",
    ):
        match = re.search(
            rf"function {name}\([^)]*\) \{{.*?^\}}",
            probe,
            re.DOTALL | re.MULTILINE,
        )
        assert match is not None
        sources.append(match.group(0))
    script = "\n".join(
        [
            *sources,
            """
const sliderCases = {
  valid_zero: { min: '0', max: '100' },
  both_zero: { min: '0', max: '0' },
  missing_minimum: { max: '100' },
  blank_maximum: { min: '0', max: ' ' },
  malformed_minimum: { min: 'zero', max: '100' },
  fractional_minimum: { min: '0.5', max: '100' },
  negative_minimum: { min: '-1', max: '100' },
  nonscalar_maximum: { min: '0', max: ['100'] },
  reversed: { min: '100', max: '0' },
};
const sliderResults = Object.fromEntries(Object.entries(sliderCases).map(([name, values]) => {
  try {
    return [name, parseSliderBounds({ getAttribute: (attribute) => values[attribute] })];
  } catch (error) {
    return [name, { refused: true, message: error.message }];
  }
}));
const countCases = {
  zero: '0',
  positive: '42',
  padded: ' 7 ',
  missing: undefined,
  blank: '',
  whitespace: '   ',
  decimal: '1.5',
  negative: '-1',
  malformed: 'four',
  nonscalar: ['4'],
  unsafe: '9007199254740992',
};
const countResults = Object.fromEntries(Object.entries(countCases).map(
  ([name, value]) => [name, parseNonnegativeIntegerText(value)],
));
process.stdout.write(JSON.stringify({ sliderResults, countResults }));
""",
        ]
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
        "? expandedLegendPasses(value.facts) "
        ": mapVisibilityPasses(value.facts, value.minimum)]));\n"
        "process.stdout.write(JSON.stringify(results));\n"
    )
    return subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )


def _run_visual_density_checks(
    scenarios: dict[str, dict[str, object]],
) -> subprocess.CompletedProcess[str]:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    match = re.search(
        r"function visualDensityPasses.*?\n}\n\nfunction mapVisibilityPasses",
        probe,
        re.DOTALL,
    )
    assert match is not None
    function_source = match.group(0).removesuffix("\n\nfunction mapVisibilityPasses")
    script = (
        f"{function_source}\n"
        f"const scenarios = {json.dumps(scenarios)};\n"
        "const results = Object.fromEntries(Object.entries(scenarios).map("
        "([name, value]) => [name, visualDensityPasses("
        "value.facts, value.maximum)]));\n"
        "process.stdout.write(JSON.stringify(results));\n"
    )
    return subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )


def _run_interaction_visibility_checks(
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
        "([name, value]) => [name, value.kind === 'search' "
        "? populatedSearchPasses(value.facts) "
        ": focusedRecordPasses(value.facts)]));\n"
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
        if profile == NATIVE_LRA_PROFILE:
            assert (
                "import { NATIVE_LRA_REQUIRED_ASSERTIONS, SIGNED_NATIVE_LRA_REQUIRED_ASSERTIONS, verifyNativeLraScope } from './native-lra.mjs';"
                in probe
            )
            assert f"'{profile}': NATIVE_LRA_REQUIRED_ASSERTIONS" in probe
            source = (
                Path(atlas_browser.__file__)
                .with_name("native-lra.mjs")
                .read_text(encoding="utf-8")
            )
            match = re.search(
                r"export const NATIVE_LRA_REQUIRED_ASSERTIONS = Object.freeze\(\[(?P<body>.*?)\]\);",
                source,
                re.DOTALL,
            )
            assert match is not None
            assert frozenset(re.findall(r"'([^']+)'", match.group("body"))) == required
            continue
        if profile == SIGNED_NATIVE_LRA_PROFILE:
            assert f"'{profile}': SIGNED_NATIVE_LRA_REQUIRED_ASSERTIONS" in probe
            module = Path(atlas_browser.__file__).with_name("native-lra.mjs").as_uri()
            result = subprocess.run(
                [
                    "node",
                    "--input-type=module",
                    "--eval",
                    f"import {{SIGNED_NATIVE_LRA_REQUIRED_ASSERTIONS as names}} from {json.dumps(module)}; console.log(JSON.stringify(names));",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            names = json.loads(result.stdout)
            assert len(names) == len(set(names))
            assert frozenset(names) == required
            continue
        if profile == RAA_RETAINED_CONTEXT_PROFILE:
            assert f"'{profile}': RAA_RETAINED_CONTEXT_REQUIRED_ASSERTIONS" in probe
            source = (
                Path(atlas_browser.__file__)
                .with_name("raa-retained-context.mjs")
                .read_text(encoding="utf-8")
            )
            match = re.search(
                r"export const RAA_RETAINED_CONTEXT_REQUIRED_ASSERTIONS = "
                r"\[(?P<body>.*?)\];",
                source,
                re.DOTALL,
            )
            assert match is not None
            assert frozenset(re.findall(r"'([^']+)'", match.group("body"))) == required
            continue
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
    assert "captureSignedView" not in generic
    assert "signed_capture_view" not in generic
    assert "visible_source_chronology_point_count" not in generic
    assert "genericTimeJourney" in generic
    assert "time_start_bp.negative" not in generic
    assert "time_end_bp.negative" not in generic
    assert (
        "['frame', 'story_kind', 'basemap', 'view', 'view.latitude', "
        "'view.longitude', 'view.zoom']" in generic
    )
    assert "data-time-interval" in probe
    assert "dataset.timeInterval === '1000'" in probe
    assert (
        "capture_frames_uncluttered"
        not in PROFILE_REQUIRED_ASSERTIONS[GENERIC_TIME_AWARE_PROFILE]
    )


def test_capture_input_probes_keep_source_bp_checks_in_nordic_scope() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    common_match = re.search(
        r"async function captureInvalidCommonInputs.*?\n}\n\nasync function captureSignedView",
        probe,
        re.DOTALL,
    )
    nordic_match = re.search(
        r"async function captureNullInputs.*?\n}\n\nasync function responsiveFacts",
        probe,
        re.DOTALL,
    )
    verifier_match = re.search(
        r"async function verifyNordicSourceChronologyScope.*?\n}\n\nasync function verifyGenericTimeAwareScope",
        probe,
        re.DOTALL,
    )

    assert common_match is not None
    assert nordic_match is not None
    assert verifier_match is not None
    common = common_match.group(0)
    nordic = nordic_match.group(0)
    assert "time_start_bp.negative" not in common
    assert "time_end_bp.negative" not in common
    assert "time_start_bp: null" in nordic
    assert "time_end_bp: null" in nordic
    assert "time_start_bp.negative" in nordic
    assert "time_end_bp.negative" in nordic
    assert "captureSignedView(normal.cdp)" in verifier_match.group(0)


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

    interceptor = (
        Path(atlas_browser.__file__)
        .with_name("provider-failures.mjs")
        .read_text(encoding="utf-8")
    )
    assert "Fetch.enable" in probe
    assert "providerInterception" in probe
    assert "from './provider-failures.mjs'" in probe
    assert "interception.handle(event)" in probe
    assert "Fetch.requestPaused" in interceptor
    assert "Fetch.failRequest" in interceptor
    assert "errorReason: 'Failed'" in interceptor
    assert "Fetch.fulfillRequest" in interceptor
    assert "providerFailure: failure" in interceptor
    assert "refusal_observation: failureObservation" in probe
    assert "timed_out: true" in probe
    refusal = re.search(
        r"async function waitForProviderRefusal.*?\n}\n\nasync function pageFacts",
        probe,
        re.DOTALL,
    )
    assert refusal is not None
    assert "typeof api.awaitReady !== 'function'" in refusal.group(0)
    assert ".then(() => api.awaitReady())" in refusal.group(0)
    assert ".catch(reject)" in refusal.group(0)
    assert "observer.observe(document.documentElement" in refusal.group(0)
    assert "? api.snapshot() : null" in refusal.group(0)


def test_provider_failure_waits_for_capture_readiness_and_propagates_failure() -> None:
    completed = _run_provider_refusal_readiness_checks()

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result == {
        "success": {
            "settled_before_ready": False,
            "await_ready_calls": 1,
            "observer_disconnected": True,
            "observation": {
                "snapshot": {
                    "basemap": "none",
                    "ready": True,
                    "visible_point_count": 1239,
                },
                "timed_out": False,
            },
        },
        "rejection": "readiness failed",
    }


def test_fit_active_journey_uses_control_and_evidence_geometry() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    journey = re.search(
        r"async function fitActiveJourney.*?\n}\n\nasync function helpDialogFacts",
        probe,
        re.DOTALL,
    )

    assert journey is not None
    source = journey.group(0)
    assert "document.getElementById('fit-active')" in source
    assert "zoomOut.click()" in source
    assert "fitActive.click()" in source
    assert "await waitForStableView()" in source
    assert "api.awaitReady()" in source
    assert "evidence_geometry: evidenceGeometry()" in source
    assert ".leaflet-point-pane path" in source
    assert ".leaflet-marker-pane .leaflet-marker-icon" in source
    assert ".leaflet-boundary-pane" not in source
    assert probe.count("const fitActive = await fitActiveJourney(normal.cdp);") == 2
    assert (
        probe.count(
            "desktopLayoutPasses(responsive[1440]) && fitActivePasses(fitActive)"
        )
        == 2
    )
    assert probe.count("fit_active_evidence_framed: fitActivePasses(fitActive)") == 2


def test_fit_active_contract_rejects_near_world_nordic_collapse() -> None:
    valid_geometry: dict[str, object] = {
        "rendered_element_count": 12,
        "horizontal_span_ratio": 0.62,
        "vertical_span_ratio": 0.78,
        "envelope_center_offset_ratio": 0.04,
    }
    valid_nordic: dict[str, object] = {
        "control_visible": True,
        "control_enabled": True,
        "control_bounded": True,
        "control_uncovered": True,
        "action_triggered": True,
        "zoom_out_click_count": 4,
        "collapsed_to_minimum_zoom": True,
        "before_view": {"latitude": 62.0, "longitude": 18.0, "zoom": 4},
        "collapsed_view": {"latitude": 62.0, "longitude": 18.0, "zoom": 0},
        "fitted_view": {"latitude": 62.0, "longitude": 18.0, "zoom": 4},
        "snapshot": {
            "ready": True,
            "countries": ["DK", "FI", "NO", "SE"],
            "visible_point_count": 195,
        },
        "evidence_geometry": valid_geometry,
    }
    valid_world = deepcopy(valid_nordic)
    valid_world["collapsed_view"] = {
        "latitude": 12.0,
        "longitude": 0.0,
        "zoom": 0,
    }
    valid_world["fitted_view"] = {
        "latitude": 12.0,
        "longitude": 0.0,
        "zoom": 0,
    }
    valid_world["snapshot"] = {
        "ready": True,
        "countries": ["AU", "DK", "US"],
        "visible_point_count": 1239,
    }
    scenarios: dict[str, dict[str, object]] = {
        "valid_nordic": valid_nordic,
        "valid_world": valid_world,
        "nordic_near_world_zoom": {
            **valid_nordic,
            "fitted_view": {"latitude": 62.0, "longitude": 18.0, "zoom": 0},
        },
        "orientation_outlier_collapse": {
            **valid_nordic,
            "fitted_view": {"latitude": 20.0, "longitude": 0.0, "zoom": 0},
            "evidence_geometry": {
                "rendered_element_count": 1,
                "horizontal_span_ratio": 0.0,
                "vertical_span_ratio": 0.0,
                "envelope_center_offset_ratio": 0.31,
            },
        },
        "off_center_evidence": {
            **valid_nordic,
            "evidence_geometry": {
                **valid_geometry,
                "envelope_center_offset_ratio": 0.5,
            },
        },
        "hidden_control": {**valid_nordic, "control_visible": False},
        "missing_geometry": {**valid_nordic, "evidence_geometry": None},
    }

    completed = _run_fit_active_checks(scenarios)

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "valid_nordic": True,
        "valid_world": True,
        "nordic_near_world_zoom": False,
        "orientation_outlier_collapse": False,
        "off_center_evidence": False,
        "hidden_control": False,
        "missing_geometry": False,
    }


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


def test_probe_numeric_boundaries_refuse_coercion_without_losing_zero() -> None:
    completed = _run_probe_boundary_parsers()

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["sliderResults"] == {
        "valid_zero": {"minimum": 0, "maximum": 100},
        "both_zero": {"minimum": 0, "maximum": 0},
        "missing_minimum": {
            "refused": True,
            "message": "time slider bounds are invalid",
        },
        "blank_maximum": {
            "refused": True,
            "message": "time slider bounds are invalid",
        },
        "malformed_minimum": {
            "refused": True,
            "message": "time slider bounds are invalid",
        },
        "fractional_minimum": {
            "refused": True,
            "message": "time slider bounds are invalid",
        },
        "negative_minimum": {
            "refused": True,
            "message": "time slider bounds are invalid",
        },
        "nonscalar_maximum": {
            "refused": True,
            "message": "time slider bounds are invalid",
        },
        "reversed": {
            "refused": True,
            "message": "time slider bounds are invalid",
        },
    }
    assert result["countResults"] == {
        "zero": 0,
        "positive": 42,
        "padded": 7,
        "missing": None,
        "blank": None,
        "whitespace": None,
        "decimal": None,
        "negative": None,
        "malformed": None,
        "nonscalar": None,
        "unsafe": None,
    }


def test_probe_journeys_and_status_use_strict_boundary_parsers() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    assert (
        probe.count(
            "const parseNonnegativeIntegerText = "
            "${parseNonnegativeIntegerText.toString()};"
        )
        == 3
    )
    assert (
        probe.count("const parseSliderBounds = ${parseSliderBounds.toString()};") == 2
    )
    assert probe.count("const { minimum, maximum } = parseSliderBounds(slider);") == 2
    assert "Number(slider.min)" not in probe
    assert "Number(slider.max)" not in probe
    assert "Number(nodeParts[0])" not in probe
    assert "Number(visibleObservationValue)" not in probe
    assert "? parseNonnegativeIntegerText(nodeParts[0])" in probe
    assert "? parseNonnegativeIntegerText(visibleObservationValue)" in probe


def test_slider_journeys_bind_count_changes_to_rendered_map_evidence() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    assert probe.count("const renderedMapEvidenceSignature = async () => {") == 2
    assert (
        probe.count("rendered_evidence_signature: await renderedMapEvidenceSignature()")
        == 2
    )
    assert ".leaflet-point-pane path" in probe
    assert ".leaflet-point-pane .leaflet-marker-icon" in probe
    assert ".leaflet-marker-pane .leaflet-marker-icon" in probe
    assert ".leaflet-point-pane canvas" in probe
    assert "context.getImageData(0, 0, canvas.width, canvas.height).data" in probe
    assert "crypto.subtle.digest('SHA-256', pixels)" in probe
    assert "point_canvas_digests: canvasDigests" in probe
    assert (
        "renderedEvidenceChangesWithCounts(journey.frames, "
        "'visible_source_chronology_point_count')"
    ) in probe
    assert (
        "renderedEvidenceChangesWithCounts(timeJourney.frames, 'visible_point_count')"
    ) in probe


def test_rendered_evidence_check_fails_closed_on_stale_or_missing_rendering() -> None:
    def frame(count: int, signature: str | None = None) -> dict[str, object]:
        result: dict[str, object] = {"snapshot": {"visible_point_count": count}}
        if signature is not None:
            result["rendered_evidence_signature"] = signature
        return result

    scenarios: dict[str, dict[str, object]] = {
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


def test_signed_capture_view_allows_only_leaflet_half_pixel_quantization() -> None:
    requested = {"latitude": -33.9, "longitude": -70.7, "zoom": 4}
    scenarios = {
        "nearest_pixel": {
            "accepted": True,
            "requested_view": requested,
            "view": {
                "latitude": -33.87041555094183,
                "longitude": -70.66406250000001,
                "zoom": 4,
            },
        },
        "longitude_beyond_half_pixel": {
            "accepted": True,
            "requested_view": requested,
            "view": {"latitude": -33.9, "longitude": -70.6, "zoom": 4},
        },
        "latitude_sign_lost": {
            "accepted": True,
            "requested_view": requested,
            "view": {"latitude": 33.9, "longitude": -70.7, "zoom": 4},
        },
        "longitude_sign_lost": {
            "accepted": True,
            "requested_view": requested,
            "view": {"latitude": -33.9, "longitude": 70.7, "zoom": 4},
        },
        "zoom_changed": {
            "accepted": True,
            "requested_view": requested,
            "view": {"latitude": -33.9, "longitude": -70.7, "zoom": 5},
        },
        "latitude_outside_web_mercator": {
            "accepted": True,
            "requested_view": requested,
            "view": {"latitude": -89.0, "longitude": -70.7, "zoom": 4},
        },
        "not_accepted": {
            "accepted": False,
            "requested_view": requested,
            "view": requested,
        },
    }

    completed = _run_signed_capture_view_checks(scenarios)

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "nearest_pixel": True,
        "longitude_beyond_half_pixel": False,
        "latitude_sign_lost": False,
        "longitude_sign_lost": False,
        "zoom_changed": False,
        "latitude_outside_web_mercator": False,
        "not_accepted": False,
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


def test_cerealia_preset_and_hordeum_secale_taxon_are_distinct_journeys() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    preset_journey = re.search(
        r"async function sourcePresetFrame.*?\n}\n\nasync function sliderChronologyJourney",
        probe,
        re.DOTALL,
    )

    assert preset_journey is not None
    assert "document.querySelectorAll('[data-source-preset]')" in preset_journey.group(
        0
    )
    assert "row.dataset.sourcePreset" in preset_journey.group(0)
    assert (
        "source_preset: selected.source_chronology.source_preset"
        in preset_journey.group(0)
    )
    assert "[data-source-shortcut]" not in preset_journey.group(0)
    assert "expectedNordic.hordeumSecale" in probe
    assert "expectedNordic.cerealia.preset" in probe


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
        "nodes: 676, observations: 676, younger: 10891, older: 11891",
        "memberTaxonIds: [416, 427, 1947, 2941]",
        "catalogSha256: '8f1751802e1ed25b9631729df80b21ac845490464cb678f7349fcc4446e57673'",
    ):
        assert literal in probe
    assert "exactSourceState(defaultSnapshot, expectedNordic.sample)" in probe
    assert "exactSourceState(sourceStates.TRSH, expectedNordic.TRSH)" in probe
    assert "exactTaxonState(secale, expectedNordic.secale" in probe
    assert "exactTaxonState(hordeumSecale, expectedNordic.hordeumSecale" in probe
    assert "exactPresetState(cerealia, expectedNordic.cerealia)" in probe


def test_cerealia_preset_state_rejects_authority_or_denominator_drift() -> None:
    functions = _probe_function_block(
        "function exactSourceState", "function webMercatorPixelPoint"
    )
    script = f"""
{functions}
const expected = {{
  level: 'source_taxon', code: null, taxon: 'all', preset: 'cerealia',
  nodes: 676, observations: 676, younger: 10891, older: 11891,
  memberTaxonIds: [416, 427, 1947, 2941],
  catalogSha256: '8f1751802e1ed25b9631729df80b21ac845490464cb678f7349fcc4446e57673',
}};
const baseline = {{
  preset: 'cerealia', button_label: 'Cerealia labels', button_pressed: 'true',
  snapshot: {{
    time_window_bp: {{ younger_bp: 10891, older_bp: 11891 }},
    source_chronology: {{
      level: 'source_taxon', source_code: null, source_taxon: 'all',
      source_preset: 'cerealia', source_preset_member_taxon_ids: [416, 427, 1947, 2941],
      source_preset_catalog_sha256: expected.catalogSha256,
      facet_node_count: 676, facet_observation_denominator: 676,
    }},
  }},
}};
const changed = (mutate) => {{ const value = structuredClone(baseline); mutate(value); return value; }};
process.stdout.write(JSON.stringify({{
  baseline: exactPresetState(baseline, expected),
  wrong_members: exactPresetState(changed((value) => {{ value.snapshot.source_chronology.source_preset_member_taxon_ids[0] = 999; }}), expected),
  wrong_digest: exactPresetState(changed((value) => {{ value.snapshot.source_chronology.source_preset_catalog_sha256 = '0'.repeat(64); }}), expected),
  wrong_nodes: exactPresetState(changed((value) => {{ value.snapshot.source_chronology.facet_node_count = 675; }}), expected),
  wrong_observations: exactPresetState(changed((value) => {{ value.snapshot.source_chronology.facet_observation_denominator = 675; }}), expected),
}}));
"""

    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "baseline": True,
        "wrong_members": False,
        "wrong_digest": False,
        "wrong_nodes": False,
        "wrong_observations": False,
    }


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
    assert "!boxesOverlap(elements.topbar, elements.sidebar)" in probe
    assert "layout.mobile.expanded.scrim_visible" in probe
    assert (
        "scrim.classList.contains('is-visible') && scrim.getAttribute('aria-hidden') === 'true' && visible(scrim)"
        in probe
    )
    assert "layout.mobile.expanded.close_visible" in probe
    assert "layout.mobile.expanded.close_uncovered" in probe
    assert "layout.mobile.expanded.scrim_catches_outside_panel" in probe
    assert "layout.mobile.expanded.close_focused" in probe
    assert "layout.mobile.expanded.scrim_dismisses_panel" in probe
    assert "layout.mobile.expanded.escape_dismisses_panel" in probe
    assert "layout.mobile.closed.scrim_hidden" in probe
    assert "layout.clear_map.panel_collapsed" in probe
    assert "layout.clear_map.legend_collapsed" in probe
    assert "layout.clear_map.search_collapsed" in probe
    assert "const ratios = Array.from({ length: 9 }" in probe
    assert "center_uncovered:" in probe
    assert "uncovered_sample_count:" in probe
    assert "legendToggle.click()" in probe
    assert "expanded_legend: expandedLegend" in probe
    assert "content_accessible:" in probe
    assert "map_visibility: sampleMapVisibility()" in probe
    assert "mapVisibilityPasses(layout.clear_map, 0.8)" in probe
    assert "expandedLegendPasses(layout.expanded_legend)" in probe
    assert "facts.sample_count >= 81" in probe
    assert "Math.ceil(facts.sample_count * minimumClearFraction)" in probe
    assert "panel_center_uncovered: uncovered(legendPanel)" in probe
    assert "sidebar_center_uncovered: uncovered(sidebar)" in probe
    assert "topbar_non_overlapping:" in probe
    assert "document.getElementById('legend-body')" in probe
    assert "document.getElementById('floating-legend')" in probe
    assert "document.getElementById('topbar-search')" in probe
    assert "mapElement.contains(mapCenterHit)" in probe
    assert "body_horizontally_contained:" in probe
    assert "body_top_contained:" in probe
    assert "legendBody.scrollTop = legendBody.scrollHeight" in probe
    assert "const legendVisibleContent = [...legendBody.querySelectorAll('*')]" in probe
    assert ".filter((element) => visible(element))" in probe
    assert "querySelector('#density-ramp > :last-child')" not in probe
    assert "last_content_reachable:" in probe
    assert "legendLastContentBox.bottom <= legendBodyBox.bottom" in probe


def test_map_visibility_requires_dense_sampling_and_contextual_clear_fraction() -> None:
    expanded_visibility = {
        "center_uncovered": True,
        "uncovered_sample_count": 57,
        "sample_count": 81,
    }
    default_visibility = {
        **expanded_visibility,
        "uncovered_sample_count": 65,
    }
    valid_legend = {
        "expanded": True,
        "toggle_expanded": True,
        "toggle_uncovered": True,
        "body_visible": True,
        "panel_center_uncovered": True,
        "panel_bounded": True,
        "body_horizontally_contained": True,
        "body_top_contained": True,
        "content_accessible": True,
        "scrolled_to_end": True,
        "last_content_reachable": True,
        "topbar_non_overlapping": True,
        "collapsed_after_journey": True,
        "map_visibility": expanded_visibility,
    }
    scenarios = {
        "valid_default": {
            "legend": False,
            "minimum": 0.8,
            "facts": default_visibility,
        },
        "below_eighty_percent": {
            "legend": False,
            "minimum": 0.8,
            "facts": {**default_visibility, "uncovered_sample_count": 64},
        },
        "valid_expanded": {
            "legend": False,
            "minimum": 0.7,
            "facts": expanded_visibility,
        },
        "covered_center": {
            "legend": False,
            "minimum": 0.7,
            "facts": {**expanded_visibility, "center_uncovered": False},
        },
        "below_seventy_percent": {
            "legend": False,
            "minimum": 0.7,
            "facts": {**expanded_visibility, "uncovered_sample_count": 56},
        },
        "weak_sample": {
            "legend": False,
            "minimum": 0.7,
            "facts": {
                "center_uncovered": True,
                "uncovered_sample_count": 56,
                "sample_count": 80,
            },
        },
        "valid_legend": {"legend": True, "facts": valid_legend},
        "clipped_legend": {
            "legend": True,
            "facts": {**valid_legend, "content_accessible": False},
        },
        "horizontally_overflowing_legend": {
            "legend": True,
            "facts": {**valid_legend, "body_horizontally_contained": False},
        },
        "misplaced_legend_body": {
            "legend": True,
            "facts": {**valid_legend, "body_top_contained": False},
        },
        "unreachable_legend_end": {
            "legend": True,
            "facts": {**valid_legend, "last_content_reachable": False},
        },
        "occluded_legend": {
            "legend": True,
            "facts": {**valid_legend, "panel_center_uncovered": False},
        },
        "legend_overlaps_topbar": {
            "legend": True,
            "facts": {**valid_legend, "topbar_non_overlapping": False},
        },
        "legend_hides_map": {
            "legend": True,
            "facts": {
                **valid_legend,
                "map_visibility": {
                    **expanded_visibility,
                    "uncovered_sample_count": 56,
                },
            },
        },
    }

    completed = _run_map_visibility_checks(scenarios)

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "valid_default": True,
        "below_eighty_percent": False,
        "valid_expanded": True,
        "covered_center": False,
        "below_seventy_percent": False,
        "weak_sample": False,
        "valid_legend": True,
        "clipped_legend": False,
        "horizontally_overflowing_legend": False,
        "misplaced_legend_body": False,
        "unreachable_legend_end": False,
        "occluded_legend": False,
        "legend_overlaps_topbar": False,
        "legend_hides_map": False,
    }


def test_visual_density_contract_rejects_loud_or_ambiguous_symbols() -> None:
    cluster: dict[str, object] = {
        "width_px": 44,
        "height_px": 44,
        "diameter_px": 44,
        "border_width_px": 2,
        "count_text": "12",
        "count": 12,
    }
    baseline: dict[str, object] = {
        "boundary_count": 1,
        "boundaries": [{"stroke_width_px": 1.4, "opacity": 0.72, "fill_opacity": 0.04}],
        "cluster_count": 1,
        "clusters": [cluster],
        "aggregate_cluster_footprint_ratio": 0.04,
    }
    scenarios: dict[str, dict[str, object]] = {
        "valid_desktop": {"facts": baseline, "maximum": 0.04},
        "valid_mobile": {
            "facts": {**baseline, "aggregate_cluster_footprint_ratio": 0.08},
            "maximum": 0.08,
        },
        "valid_without_clusters": {
            "facts": {
                **baseline,
                "cluster_count": 0,
                "clusters": [],
                "aggregate_cluster_footprint_ratio": 0,
            },
            "maximum": 0.04,
        },
        "missing_boundary": {
            "facts": {**baseline, "boundary_count": 0, "boundaries": []},
            "maximum": 0.04,
        },
        "thick_boundary": {
            "facts": {
                **baseline,
                "boundaries": [
                    {"stroke_width_px": 1.41, "opacity": 0.72, "fill_opacity": 0.04}
                ],
            },
            "maximum": 0.04,
        },
        "opaque_boundary": {
            "facts": {
                **baseline,
                "boundaries": [
                    {"stroke_width_px": 1.4, "opacity": 0.73, "fill_opacity": 0.04}
                ],
            },
            "maximum": 0.04,
        },
        "strong_boundary_fill": {
            "facts": {
                **baseline,
                "boundaries": [
                    {"stroke_width_px": 1.4, "opacity": 0.72, "fill_opacity": 0.041}
                ],
            },
            "maximum": 0.04,
        },
        "invisible_boundary_stroke": {
            "facts": {
                **baseline,
                "boundaries": [
                    {"stroke_width_px": 0, "opacity": 0.72, "fill_opacity": 0.04}
                ],
            },
            "maximum": 0.04,
        },
        "transparent_boundary": {
            "facts": {
                **baseline,
                "boundaries": [
                    {"stroke_width_px": 1.4, "opacity": 0, "fill_opacity": 0}
                ],
            },
            "maximum": 0.04,
        },
        "small_cluster": {
            "facts": {
                **baseline,
                "clusters": [{**cluster, "diameter_px": 31.9}],
            },
            "maximum": 0.04,
        },
        "large_cluster": {
            "facts": {
                **baseline,
                "clusters": [{**cluster, "diameter_px": 44.1}],
            },
            "maximum": 0.04,
        },
        "thick_cluster_border": {
            "facts": {
                **baseline,
                "clusters": [{**cluster, "border_width_px": 2.1}],
            },
            "maximum": 0.04,
        },
        "non_integer_cluster_count": {
            "facts": {
                **baseline,
                "clusters": [{**cluster, "count": 12.5}],
            },
            "maximum": 0.04,
        },
        "mismatched_cluster_label": {
            "facts": {
                **baseline,
                "clusters": [{**cluster, "count_text": "13"}],
            },
            "maximum": 0.04,
        },
        "desktop_footprint_exceeded": {
            "facts": {**baseline, "aggregate_cluster_footprint_ratio": 0.0401},
            "maximum": 0.04,
        },
    }

    completed = _run_visual_density_checks(scenarios)

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "valid_desktop": True,
        "valid_mobile": True,
        "valid_without_clusters": True,
        "missing_boundary": False,
        "thick_boundary": False,
        "opaque_boundary": False,
        "strong_boundary_fill": False,
        "invisible_boundary_stroke": False,
        "transparent_boundary": False,
        "small_cluster": False,
        "large_cluster": False,
        "thick_cluster_border": False,
        "non_integer_cluster_count": False,
        "mismatched_cluster_label": False,
        "desktop_footprint_exceeded": False,
    }


def test_visual_density_facts_measure_rendered_boundaries_and_cluster_footprint() -> (
    None
):
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    for literal in (
        "document.querySelectorAll('.leaflet-boundary-pane path')",
        "numericStyle(style.strokeWidth)",
        "numericStyle(style.strokeOpacity)",
        "numericStyle(style.fillOpacity)",
        "document.querySelectorAll('.leaflet-marker-pane .cluster-pill')",
        "diameter_px: Math.max(bounds.width, bounds.height)",
        "style.borderTopWidth",
        "borderWidths.every((value) => value !== null)",
        "count: /^[1-9]\\\\d*$/.test(countText) ? Number(countText) : null",
        "Math.PI * cluster.width_px * cluster.height_px / 4",
        "aggregate_cluster_footprint_ratio:",
        "visualDensityPasses(layout.visual_density, 0.04)",
        "visualDensityPasses(layout.visual_density, 0.08)",
    ):
        assert literal in probe
    assert "facts.cluster_count <=" not in probe


def test_responsive_contract_proves_compact_search_keyboard_journey() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )

    for literal in (
        "document.documentElement.classList.add('atlas-probe-motion-mode')",
        "document.getElementById('search-toggle')",
        "document.getElementById('topbar-search')",
        "document.getElementById('search-input')",
        "document.getElementById('search-results')",
        "document.getElementById('focus-card')",
        "document.getElementById('focus-close')",
        "searchToggle.click()",
        "searchInput.dispatchEvent(new Event('input', { bubbles: true }))",
        "searchResults.querySelectorAll('[data-search-index]').length",
        "chronology_controls_uncovered:",
        "expanded_panel: expandedPanel",
        "focused_record: focusedRecord",
        "const focusSearchResult = searchResults.querySelector('[data-search-index]')",
        "focusSearchResult?.isConnected",
        "focusSearchResult.click()",
        "panel_collapsed: sidebar.classList.contains('is-collapsed')",
        "document.activeElement === searchInput",
        "searchToggle.getAttribute('aria-expanded') === 'true'",
        "searchInput.dispatchEvent(new KeyboardEvent('keydown'",
        "key: 'Escape', code: 'Escape', bubbles: true, cancelable: true",
        "topbarSearch.hidden && !visible(topbarSearch)",
        "searchToggle.getAttribute('aria-expanded') === 'false'",
        "document.activeElement === searchToggle",
        "toggle_visible_while_open: visible(searchToggle)",
        "toggle_uncovered_while_open: uncovered(searchToggle)",
        "pointer_hides_region",
        "pointer_collapses_toggle",
        "pointer_restores_focus",
        "searchControlPasses(layout.search_control)",
    ):
        assert literal in probe
    assert probe.count("searchInput.value = 'a';") == 2
    assert (
        probe.count("searchInput.dispatchEvent(new Event('input', { bubbles: true }))")
        == 2
    )
    assert probe.index("searchControl.escape_restores_focus") < probe.index(
        "const focusSearchResult = searchResults.querySelector('[data-search-index]')"
    )
    assert "classList.add('atlas-capture-mode')" not in probe


def test_mobile_panel_must_not_cover_the_topbar() -> None:
    probe = (
        Path(atlas_browser.__file__).with_name("probe.mjs").read_text(encoding="utf-8")
    )
    mobile_contract = re.search(
        r"function mobileLayoutPasses.*?\n}\n\nfunction searchControlPasses",
        probe,
        re.DOTALL,
    )

    assert mobile_contract is not None
    assert "layout.mobile.expanded.topbar_non_overlapping" in mobile_contract.group(0)
    assert (
        probe.count(
            "topbar_non_overlapping: !boxesOverlap(legendPanelBox, box(topbar))"
        )
        == 1
    )


def test_populated_search_and_focused_record_checks_fail_closed() -> None:
    map_visibility = {
        "center_uncovered": True,
        "uncovered_sample_count": 57,
        "sample_count": 81,
    }
    search = {
        "query": "a",
        "results_visible": True,
        "results_bounded": True,
        "results_uncovered": True,
        "result_count": 1,
        "content_accessible": True,
        "chronology_controls_uncovered": True,
        "map_visibility": map_visibility,
    }
    focus = {
        "result_available": True,
        "card_visible": True,
        "card_center_uncovered": True,
        "card_bounded": True,
        "content_accessible": True,
        "panel_collapsed": True,
        "panel_hidden": True,
        "legend_collapsed": True,
        "search_collapsed": True,
        "topbar_non_overlapping": True,
        "map_visibility": map_visibility,
        "closed_after_journey": True,
    }
    scenarios: dict[str, dict[str, object]] = {
        "valid_search": {"kind": "search", "facts": search},
        "empty_search": {
            "kind": "search",
            "facts": {**search, "result_count": 0},
        },
        "search_hides_chronology": {
            "kind": "search",
            "facts": {**search, "chronology_controls_uncovered": False},
        },
        "search_hides_map": {
            "kind": "search",
            "facts": {
                **search,
                "map_visibility": {**map_visibility, "uncovered_sample_count": 56},
            },
        },
        "valid_focus": {"kind": "focus", "facts": focus},
        "focus_keeps_panel": {
            "kind": "focus",
            "facts": {**focus, "panel_collapsed": False},
        },
        "focus_hides_map": {
            "kind": "focus",
            "facts": {
                **focus,
                "map_visibility": {**map_visibility, "center_uncovered": False},
            },
        },
        "focus_is_occluded": {
            "kind": "focus",
            "facts": {**focus, "card_center_uncovered": False},
        },
        "focus_overlaps_topbar": {
            "kind": "focus",
            "facts": {**focus, "topbar_non_overlapping": False},
        },
        "focus_not_dismissed": {
            "kind": "focus",
            "facts": {**focus, "closed_after_journey": False},
        },
    }

    completed = _run_interaction_visibility_checks(scenarios)

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "valid_search": True,
        "empty_search": False,
        "search_hides_chronology": False,
        "search_hides_map": False,
        "valid_focus": True,
        "focus_keeps_panel": False,
        "focus_hides_map": False,
        "focus_is_occluded": False,
        "focus_overlaps_topbar": False,
        "focus_not_dismissed": False,
    }


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
            "caveat": "Observed records only; no interpolation, flow, propagation, migration, or causation inference.",
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
            "capture_presentation.caveat",
            "Observed records only; interpolation and propagation are inferred.",
        ),
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


@pytest.mark.parametrize(
    "extra_browser_args",
    [
        [],
        [
            "--disable-extensions",
            "--disable-sync",
            "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
        ],
    ],
)
def test_chromium_uses_private_short_ipc_and_reaps_its_process_group(
    tmp_path: Path,
    extra_browser_args: list[str],
) -> None:
    transport = Path(atlas_browser.__file__).with_name("browser-transport.mjs")
    fake = tmp_path / "chromium"
    child = tmp_path / "chromium.mjs"
    child.write_text("""import {spawn} from 'node:child_process';
import {createServer} from 'node:net';
import {join} from 'node:path';
const descendant=spawn(process.execPath,['-e',"process.on('SIGTERM',()=>{});setInterval(()=>{},1000)"],{stdio:'ignore'});
console.error('descendant='+descendant.pid);
process.on('SIGTERM',()=>{});
createServer().listen(join(process.env.TMPDIR,'SingletonSocket'),()=>{
 console.error('DevTools listening on ws://127.0.0.1:1/devtools/browser/test');
});
""")
    import shlex

    fake.write_text(f"#!/bin/sh\nexec node {shlex.quote(str(child))}\n")
    fake.chmod(0o700)
    program = """import assert from 'node:assert/strict';
import {stat} from 'node:fs/promises';
const {launchChromium,debuggerEndpoint,requireChromiumSocketPath}=await import(process.argv[1]);
assert.throws(()=>requireChromiumSocketPath('/tmp/'+'é'.repeat(50)),/socket budget/);
const inherited=process.env.TMPDIR,extra=JSON.parse(process.argv[4]);
const runtime=extra.length ? await launchChromium(process.argv[2],process.argv[3],Object.freeze(extra)) : await launchChromium(process.argv[2],process.argv[3]);
assert.deepEqual(runtime.browser.spawnargs.slice(1),[
 '--headless=new','--disable-gpu','--disable-background-networking','--disable-component-update',
 '--disable-default-apps','--no-default-browser-check','--no-first-run','--remote-allow-origins=*',
 '--remote-debugging-port=0',...extra,`--user-data-dir=${process.argv[3]}`,'about:blank',
]);
let log='';runtime.browser.stderr.on('data',chunk=>{log+=chunk;});
try {
 assert.notEqual(runtime.directory,inherited);
 assert.ok(Buffer.byteLength(requireChromiumSocketPath(runtime.directory))<104);
 assert.equal((await stat(runtime.directory)).mode&0o777,0o700);
 assert.ok(!runtime.browser.spawnargs.includes('--no-sandbox'));
 await debuggerEndpoint(runtime.browser,2000);
} finally {await runtime.close();}
await assert.rejects(stat(runtime.directory),{code:'ENOENT'});
assert.notEqual(runtime.browser.exitCode===null && runtime.browser.signalCode===null,true);
const descendant=Number(log.match(/descendant=([0-9]+)/)[1]);
let gone=false;
for(let attempt=0;attempt<50;attempt++){
 try{process.kill(descendant,0);}catch(error){if(error.code==='ESRCH'){gone=true;break;}throw error;}
 await new Promise(accept=>setTimeout(accept,20));
}
assert.ok(gone,'Chromium descendant survived process-group cleanup');
"""
    import os

    environment = dict(os.environ, TMPDIR=str(tmp_path / ("long-artifact-path" * 10)))
    subprocess.run(
        (
            "node",
            "--input-type=module",
            "-e",
            program,
            transport.as_uri(),
            str(fake),
            str(tmp_path),
            json.dumps(extra_browser_args),
        ),
        check=True,
        capture_output=True,
        text=True,
        env=environment,
        timeout=10,
    )


def test_chromium_startup_failure_retains_receipt_and_removes_ipc(
    tmp_path: Path,
) -> None:
    transport = Path(atlas_browser.__file__).with_name("browser-transport.mjs")
    output = tmp_path / "failed-startup"
    result = subprocess.run(
        (
            "node",
            str(transport),
            "--probe",
            str(tmp_path / "missing-browser"),
            str(output),
        ),
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    receipt = json.loads((output / "startup.json").read_text())
    assert receipt["status"] == "FAIL"
    assert "ENOENT" in receipt["error"]
    assert receipt["ipc_removed"] is True
    assert not Path(receipt["ipc_directory"]).exists()


def test_chromium_debugger_deadline_cleans_listeners_and_ipc(tmp_path: Path) -> None:
    transport = Path(atlas_browser.__file__).with_name("browser-transport.mjs")
    fake = tmp_path / "silent-browser"
    fake.write_text("#!/bin/sh\nexec sleep 30\n")
    fake.chmod(0o700)
    program = """import assert from 'node:assert/strict';
import {stat} from 'node:fs/promises';
const {launchChromium,debuggerEndpoint}=await import(process.argv[1]);
const runtime=await launchChromium(process.argv[2],process.argv[3]);
try {await assert.rejects(debuggerEndpoint(runtime.browser,30),/debugger endpoint/);
 assert.equal(runtime.browser.stdout.listenerCount('data'),0);
} finally {await runtime.close();}
await assert.rejects(stat(runtime.directory),{code:'ENOENT'});
"""
    subprocess.run(
        (
            "node",
            "--input-type=module",
            "-e",
            program,
            transport.as_uri(),
            str(fake),
            str(tmp_path),
        ),
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_chromium_parent_cancellation_removes_private_ipc(tmp_path: Path) -> None:
    transport = Path(atlas_browser.__file__).with_name("browser-transport.mjs")
    fake = tmp_path / "waiting-browser"
    fake.write_text("#!/bin/sh\nexec sleep 30\n")
    fake.chmod(0o700)
    program = """const {launchChromium}=await import(process.argv[1]);
const runtime=await launchChromium(process.argv[2],process.argv[3]);
console.log(runtime.directory);
setInterval(()=>{},1000);
"""
    child = subprocess.Popen(
        (
            "node",
            "--input-type=module",
            "-e",
            program,
            transport.as_uri(),
            str(fake),
            str(tmp_path),
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert child.stdout is not None
        directory = Path(child.stdout.readline().strip())
        assert directory.is_dir()
        child.terminate()
        _, error = child.communicate(timeout=10)
        assert child.returncode == 143, error
        assert not directory.exists()
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=10)


def test_artifact_length_unix_socket_path_is_rejected_by_the_kernel(
    tmp_path: Path,
) -> None:
    import socket

    with (
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection,
        pytest.raises(OSError, match="AF_UNIX path too long"),
    ):
        connection.bind(str(tmp_path / ("chromium-ipc" * 20)))


def test_fieldwork_reader_checks_require_documentation_and_restore_source_export() -> (
    None
):
    media = [
        {
            "href": "../../../gallery/" + filename,
            "filename": filename,
            "same_origin": True,
            "target": "_blank",
            "rel": "noreferrer",
        }
        for filename in (
            "2026-02-26-data-collection.JPG",
            "2026-02-26-data-collection.mp4",
        )
    ]
    fieldwork: dict[str, object] = {
        "title": "Lyngsjön Lake field sampling",
        "detail_status": "available",
        "tabs": [{"key": "overview", "label": "Documentation", "selected": "true"}],
        "panel_label": "focus-tab-overview",
        "text": "Sampling visit and media; no pollen observations or age-depth series. Sampling date: 2026-02-26 Place: Lyngsjön Lake, southwest of Kristianstad Context: Winter lake sampling",
        "media": media,
        "source_hidden": False,
        "source_href": media[0]["href"],
        "export_hidden": True,
        "export_disabled": True,
        "copy_disabled": False,
        "focus_layer": "fieldwork-documentation",
        "focus_record": "bijux:fieldwork:lyngsjon-lake:2026-02-26",
    }
    ordinary: dict[str, object] = {
        "title": "Ageröds Mosse",
        "export_hidden": False,
        "export_disabled": False,
        "tabs": [
            "overview",
            "samples",
            "chronology",
            "pollen_composition",
            "relation",
            "classification",
            "provenance",
        ],
    }
    facts: dict[str, object] = {
        "fieldwork": fieldwork,
        "keyboard": [{"focus": "focus-tab-overview", "selected": "true"}] * 4,
        "after_tab": "focus-detail",
        "zoom_reached_record": True,
        "ordinary": ordinary,
    }
    scenarios = {
        "complete": facts,
        "wrong_identity": {
            **facts,
            "fieldwork": {**fieldwork, "focus_record": "other"},
        },
        "pollen_tabs": {
            **facts,
            "fieldwork": {
                **fieldwork,
                "tabs": [{"key": "overview", "label": "Overview", "selected": "true"}],
            },
        },
        "missing_media": {**facts, "fieldwork": {**fieldwork, "media": media[:1]}},
        "foreign_media": {
            **facts,
            "fieldwork": {
                **fieldwork,
                "media": [{**media[0], "same_origin": False}, media[1]],
            },
        },
        "pollen_failure": {
            **facts,
            "fieldwork": {
                **fieldwork,
                "text": str(fieldwork["text"]) + " detail_record_not_indexed",
            },
        },
        "pollen_action": {**facts, "fieldwork": {**fieldwork, "export_hidden": False}},
        "wrong_source": {**facts, "fieldwork": {**fieldwork, "source_href": "other"}},
        "disabled_copy": {**facts, "fieldwork": {**fieldwork, "copy_disabled": True}},
        "keyboard_escape": {
            **facts,
            "keyboard": [{"focus": "focus-tab-provenance", "selected": "true"}] * 4,
        },
        "native_tab_blocked": {**facts, "after_tab": "focus-tab-overview"},
        "zoom_wrong_record": {**facts, "zoom_reached_record": False},
        "source_export_not_restored": {
            **facts,
            "ordinary": {**ordinary, "export_hidden": True},
        },
        "ordinary_tabs_lost": {**facts, "ordinary": {**ordinary, "tabs": ["overview"]}},
    }
    function = _probe_function_block(
        "function fieldworkReadingPasses", "async function fieldworkReadingJourney"
    )
    script = (
        function
        + "\nconst cases="
        + json.dumps(scenarios)
        + ";console.log(JSON.stringify(Object.fromEntries(Object.entries(cases).map(([key,value])=>[key,fieldworkReadingPasses(value)]))));"
    )
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        name: name == "complete" for name in scenarios
    }


def test_record_journey_restoration_reacquires_only_after_owned_navigation() -> None:
    function = _probe_function_block(
        "async function restoreRecordReadingView", "async function fitActiveJourney"
    )
    script = (
        "const timeoutMs=15000;let evaluate,captureReady;\n"
        + function
        + r"""
async function exercise(mode){
 const original='http://127.0.0.1/atlas.html#layers=source&time_start=0';
 let href=mode==='same'?original:'http://127.0.0.1/atlas.html#focus_record=fieldwork';
 let destroyed=false,registered=false,ready=false,resolveLoad,rejectLoad;
 const events=[];
 evaluate=async(_cdp,expression)=>{
  if(destroyed)throw Error('Runtime.evaluate used a destroyed context');
  if(expression==='location.href'){events.push('read_url');return href;}
  events.push('close_controls');return true;
 };
 captureReady=async()=>{if(destroyed)throw Error('readiness used a destroyed context');ready=true;events.push('ready');return {ready:true};};
 const cdp={
  waitFor(name,timeout){if(name!=='Page.loadEventFired'||timeout!==timeoutMs)throw Error('wrong navigation deadline');
   registered=true;events.push('wait_load');return new Promise((resolve,reject)=>{resolveLoad=resolve;rejectLoad=reject;});},
  async send(name,params){
   if(name!=='Page.navigate'||params.url!==original||!registered)throw Error('navigation preceded registration or changed URL');
   events.push('navigate');destroyed=true;
   if(mode==='navigation_failure'){rejectLoad(Error('navigation failure'));throw Error('navigation failure');}
   queueMicrotask(()=>{
    if(mode==='load_timeout'){rejectLoad(Error('load timeout'));return;}
    destroyed=false;href=mode==='wrong_url'?original+'&unexpected=true':original;events.push('load');resolveLoad({});
   });
  },
 };
 let result,error=null;
 try{result=await restoreRecordReadingView(cdp,original);}catch(caught){error=caught.message;}
 return {events,ready,error,restored:href===original,result};
}
const observed={};
for(const mode of ['moved','same','navigation_failure','load_timeout','wrong_url'])observed[mode]=await exercise(mode);
console.log(JSON.stringify(observed));
"""
    )
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    observed = json.loads(completed.stdout)
    assert observed["moved"] == {
        "events": [
            "close_controls",
            "read_url",
            "wait_load",
            "navigate",
            "load",
            "ready",
            "read_url",
        ],
        "ready": True,
        "error": None,
        "restored": True,
        "result": {"ready": True},
    }
    assert observed["same"]["events"] == [
        "close_controls",
        "read_url",
        "ready",
        "read_url",
    ]
    for mode, reason in (
        ("navigation_failure", "navigation failure"),
        ("load_timeout", "load timeout"),
    ):
        assert observed[mode]["error"] == reason
        assert observed[mode]["ready"] is False
    assert observed["wrong_url"]["error"] == (
        "Record reading did not restore the original URL"
    )


def test_fieldwork_restoration_failure_preserves_original_reading_failure() -> None:
    finalizer = _probe_function_block(
        "async function finalizeBrowserVerification",
        "async function verifyNordicSourceChronologyScope",
    )
    journey = _probe_function_block(
        "async function fieldworkReadingJourney",
        "async function restoreRecordReadingView",
    )
    script = (
        finalizer
        + "\n"
        + journey
        + r"""
const timeoutMs=15000,primary=Error('fieldwork failure with original facts'),secondary=Error('restoration load timeout'),messages=[];
async function evaluate(_cdp,expression){if(expression==='location.href')return 'http://127.0.0.1/map.html#original';throw primary;}
async function restoreRecordReadingView(){throw secondary;}
console.error=message=>messages.push(message);
let caught;
try{await fieldworkReadingJourney({}, {name:'nordic'}, []);}catch(error){caught=error;}
console.log(JSON.stringify({same_primary:caught===primary,message:caught?.message,secondary:messages}));
"""
    )
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "same_primary": True,
        "message": "fieldwork failure with original facts",
        "secondary": [
            "atlas browser cleanup also failed (record restoration): restoration load timeout"
        ],
    }


def test_record_centering_uses_css_pixels_at_the_observed_zoom() -> None:
    function = _probe_function_block(
        "function recordCenterOffset", "async function fieldworkMapView"
    )
    script = (
        function
        + r"""
const actual={latitude:55.93227936568622,longitude:14.067993164062502,zoom:8};
const cases={actual,wrapped:{...actual,longitude:actual.longitude+360},
  wrong:{...actual,longitude:14.0659044+2*360/65536},
  nonfinite:{...actual,latitude:NaN},polar:{...actual,latitude:90},
  badzoom:{...actual,zoom:Infinity}};
console.log(JSON.stringify(Object.fromEntries(Object.entries(cases).map(([key,view])=>[key,recordCenterOffset(view)]))));
"""
    )
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    observed = json.loads(completed.stdout)
    assert observed["actual"]["distance"] == pytest.approx(0.39477136315244304)
    assert observed["wrapped"]["distance"] == pytest.approx(
        observed["actual"]["distance"]
    )
    assert observed["wrong"]["distance"] > 1
    assert all(observed[key] is None for key in ("nonfinite", "polar", "badzoom"))


def test_record_zoom_requires_ui_movement_and_settled_finite_center() -> None:
    functions = _probe_function_block(
        "function recordCenterOffset", "function fieldworkReadingPasses"
    )
    script = (
        functions
        + r"""
const observed={latitude:55.93227936568622,longitude:14.067993164062502,zoom:8};
const results={};
for(const mode of ['rounded','wrapped','wrong_center','bad_zoom','nonfinite','moving','animating','zoom_out_noop']){
 let time=0,view={...observed},phase='initial',calls=[];
 globalThis.performance={now:()=>time};
 globalThis.requestAnimationFrame=callback=>{time+=16;
   if(phase==='focus'&&mode==='moving')view.longitude+=0.000001;
   queueMicrotask(callback);};
 const map={querySelectorAll:()=>[{transform:'matrix(1,0,0,1,0,0)'}],
   querySelector:()=>null,classList:{contains:()=>phase==='focus'&&mode==='animating'}};
 const zoomOut={classList:{contains:()=>false},click:()=>{
   calls.push('zoom-out');phase='out';if(mode!=='zoom_out_noop')view={...view,zoom:7};}};
 const focus={click:()=>{calls.push('focus-zoom');phase='focus';view={...observed};
   if(mode==='wrapped')view.longitude+=360;
   if(mode==='wrong_center')view.longitude=14.0659044+2*360/65536;
   if(mode==='bad_zoom')view.zoom=7;
   if(mode==='nonfinite')view.latitude=NaN;}};
 globalThis.document={getElementById:id=>id==='map'?map:focus,querySelector:()=>zoomOut};
 globalThis.getComputedStyle=element=>element;
 globalThis.BijuxPollenomicsAtlasCapture={snapshot:()=>({view:{...view}})};
 const facts=await fieldworkMapView({},true);
 results[mode]={passed:facts.passed,calls,elapsed_ms:facts.elapsed_ms,
   before_zoom:facts.before.view.zoom,last_zoom:facts.last.view.zoom,
   last_offset:facts.last.offset,stable_frames:facts.stable_frames};
}
console.log(JSON.stringify(results));
async function evaluate(_cdp,expression){return eval(expression);}
"""
    )
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    observed = json.loads(completed.stdout)
    for mode, facts in observed.items():
        assert facts["passed"] is (mode in {"rounded", "wrapped"})
        assert facts["calls"] == (
            ["zoom-out"] if mode == "zoom_out_noop" else ["zoom-out", "focus-zoom"]
        )
        if facts["passed"]:
            assert facts["before_zoom"] == 7
            assert facts["last_zoom"] == 8
            assert facts["last_offset"]["distance"] <= 1
            assert facts["stable_frames"] >= 2
        else:
            assert 3000 < facts["elapsed_ms"] <= 3016


def test_fieldwork_media_scroll_repeats_in_the_same_page_script_context() -> None:
    journey = _probe_function_block(
        "async function fieldworkReadingJourney",
        "async function restoreRecordReadingView",
    )
    match = re.search(
        r'await evaluate\(cdp, ("[^"\n]*#focus-detail \.popup-media-link[^"\n]*")\);',
        journey,
    )
    assert match is not None
    expression = json.loads(match.group(1))
    script = (
        "import vm from 'node:vm';\nconst expression="
        + json.dumps(expression)
        + r""";
const calls=[],media={focus:()=>calls.push('focus'),scrollIntoView:options=>calls.push(options.block)};
const page=vm.createContext({document:{querySelector:selector=>{
 if(selector!=='#focus-detail .popup-media-link')throw Error('wrong media selector');return media;}}});
for(const width of [1440,390])vm.runInContext(expression,page);
console.log(JSON.stringify(calls));
"""
    )
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == ["focus", "center", "focus", "center"]


def test_landclim_capture_startup_failure_closes_owned_runtime(tmp_path: Path) -> None:
    capture = Path(atlas_browser.__file__).parent / "landclim_export" / "capture.mjs"
    fake = tmp_path / "failed-browser"
    fake.write_text("#!/bin/sh\nexit 42\n")
    fake.chmod(0o700)
    output = tmp_path / "artifacts" / "capture"
    result = subprocess.run(
        ("node", str(capture), str(tmp_path), str(output), str(fake)),
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert "browser exited before debugger readiness: 42" in result.stderr
    assert (output / "browser.log").exists()
    assert not (output / "browser-profile").exists()


def _keyless_process_record(pid: int) -> dict[str, int | str] | None:
    result = subprocess.run(
        ("ps", "-o", "pid=,pgid=,stat=,lstart=", "-p", str(pid)),
        check=False,
        capture_output=True,
        text=True,
    )
    fields = result.stdout.strip().split(None, 3)
    if len(fields) != 4 or fields[2].startswith("Z"):
        return None
    return {"pid": int(fields[0]), "pgid": int(fields[1]), "start": fields[3]}


@pytest.mark.parametrize("failure", ["exit42", "log_refusal", "existing_profile"])
def test_keyless_cli_failure_owns_short_ipc_and_closes_descendants(
    tmp_path: Path, failure: str
) -> None:
    from contextlib import suppress
    import os
    import shutil
    import signal
    import sys

    cli = Path(atlas_browser.__file__).with_name("keyless-cache-matrix.mjs")
    candidate, output = tmp_path / "candidate", tmp_path / "observation"
    candidate.mkdir()
    output.mkdir()
    (candidate / "generation.json").write_text(
        json.dumps(
            {
                "countries": ["Denmark", "Finland", "Norway", "Sweden"],
                "candidate_build_id": "synthetic-lifecycle-only",
            }
        )
    )
    inherited = tmp_path / ("long-owned-artifact-path" * 6)
    inherited.mkdir()
    witness = output / "processes.json"
    fake = tmp_path / "failed-chromium"
    fake.write_text(
        "#!"
        + sys.executable
        + "\n"
        + r"""
import json,os,stat,subprocess,sys
from pathlib import Path
witness=Path(os.environ['KEYLESS_TEST_WITNESS'])
def identity(pid):
 text=subprocess.check_output(['ps','-o','lstart=','-p',str(pid)],text=True).strip()
 return {'pid':pid,'pgid':os.getpgid(pid),'start':text}
record={'processes':[identity(os.getpid())],'ipc':os.environ['TMPDIR'],
 'ipc_mode':stat.S_IMODE(Path(os.environ['TMPDIR']).stat().st_mode),'argv':sys.argv[1:]}
witness.write_text(json.dumps(record))
program="import json,os,signal,subprocess,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print(json.dumps({'pid':os.getpid(),'pgid':os.getpgid(0),'start':subprocess.check_output(['ps','-o','lstart=','-p',str(os.getpid())],text=True).strip()}),flush=True);time.sleep(60)"
child=subprocess.Popen([sys.executable,'-c',program],stdout=subprocess.PIPE,text=True)
record['processes'].append(identity(child.pid));witness.write_text(json.dumps(record))
record['processes'][-1]=json.loads(child.stdout.readline());witness.write_text(json.dumps(record))
print('owned descendant ready',file=sys.stderr,flush=True)
sys.exit(42)
"""
    )
    fake.chmod(0o700)
    if failure == "existing_profile":
        (output / "browser-profile").mkdir()
        (output / "browser-profile/user-state").write_text("preserve")
    if failure == "log_refusal":
        (output / "browser.log").mkdir()
    environment = dict(
        os.environ, TMPDIR=str(inherited), KEYLESS_TEST_WITNESS=str(witness)
    )
    child = subprocess.Popen(
        ("node", str(cli), str(candidate), str(output), str(fake)),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
        start_new_session=True,
    )
    own = _keyless_process_record(child.pid)
    records = [own] if own else []
    completed_before_fallback = False
    observed_closed = False
    try:
        _, stderr = child.communicate(timeout=10)
        completed_before_fallback = True
        if witness.exists():
            records.extend(json.loads(witness.read_text())["processes"])
        observed_closed = all(
            _keyless_process_record(int(row["pid"])) != row for row in records
        )
        assert child.returncode != 0, stderr
        receipt = json.loads((output / "receipt.json").read_text())
        assert receipt["status"] == "FAIL"
        assert receipt["scenarios"] == []
        if failure == "existing_profile":
            assert "EEXIST" in receipt["error"]
            assert (output / "browser-profile/user-state").read_text() == "preserve"
            assert not witness.exists()
        else:
            assert "browser exited before debugger readiness: 42" in receipt["error"]
            details = json.loads(witness.read_text())
            ipc = Path(details["ipc"])
            assert ipc != inherited and details["ipc_mode"] == 0o700
            assert (
                len(os.fsencode(ipc / "com.google.Chrome.XXXXXX/SingletonSocket")) < 104
            )
            assert not ipc.exists()
            assert not (output / "browser-profile").exists()
            assert any(
                argument == "--user-data-dir=" + str(output / "browser-profile")
                for argument in details["argv"]
            )
            if failure == "log_refusal":
                assert any(
                    row["name"] == "browser log" for row in receipt["cleanup_errors"]
                )
            else:
                assert "owned descendant ready" in (output / "browser.log").read_text()
        assert observed_closed, "CLI returned with a live owned descendant"
    finally:
        if witness.exists():
            records.extend(json.loads(witness.read_text())["processes"])
        # The fallback may signal only unchanged PID/start identities and their owned group.
        allowed = {int(row["pid"]) for row in records}
        for row in records:
            current = _keyless_process_record(int(row["pid"]))
            if current != row:
                continue
            processes = subprocess.check_output(("ps", "-axo", "pid=,pgid="), text=True)
            members = {
                int(line.split()[0])
                for line in processes.splitlines()
                if int(line.split()[1]) == int(row["pgid"])
            }
            if members <= allowed:
                with suppress(ProcessLookupError):
                    os.killpg(int(row["pgid"]), signal.SIGKILL)
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=5)
        if witness.exists():
            details = json.loads(witness.read_text())
            ipc = Path(details["ipc"])
            owned_ipc = ipc.is_relative_to(tmp_path) or (
                ipc.parent == Path("/private/tmp")
                and ipc.name.startswith("bjx-")
                and details["ipc_mode"] == 0o700
            )
            if owned_ipc and ipc.exists():
                shutil.rmtree(ipc)
        if failure != "existing_profile" and (output / "browser-profile").exists():
            shutil.rmtree(output / "browser-profile")
    assert completed_before_fallback and observed_closed


def test_keyless_watchdog_cancels_pending_connection_requests_and_page_waits() -> None:
    source = (
        Path(atlas_browser.__file__).with_name("keyless-cache-matrix.mjs").read_text()
    )
    deadline = (
        "async function withDeadline"
        + source.split("async function withDeadline", 1)[1].split(
            "async function boundedCleanup", 1
        )[0]
    )
    navigation = (
        "async function navigate"
        + source.split("async function navigate", 1)[1].split(
            "async function evaluate", 1
        )[0]
    )
    connection = "async function connect" + source.split("async function connect", 1)[1]
    script = (
        "import assert from 'node:assert/strict';\n"
        + deadline
        + navigation
        + connection
        + r"""
let cancellation,cdp,next=0;
const timers=new Map(),sockets=[];
globalThis.setTimeout=(callback,delay)=>{const id=++next;timers.set(id,{callback,delay});return id;};
globalThis.clearTimeout=id=>timers.delete(id);
globalThis.WebSocket=class{
 constructor(){this.events={};this.closed=false;sockets.push(this);}
 addEventListener(name,callback){this.events[name]=callback;}
 send(){}
 close(){this.closed=true;}
};
const results={};
for(const mode of ['connecting','request','page']){
 cancellation=new AbortController();
 const pending=connect('ws://owned');const socket=sockets.at(-1);
 if(mode==='connecting'){
  const refused=assert.rejects(pending,/cancelled/);cancellation.abort(Error('cancelled'));await refused;
 }else{
  socket.events.open();cdp=await pending;
  const work=mode==='page'?navigate('http://owned'):cdp.send('Runtime.evaluate');
  const refused=assert.rejects(work,/cancelled/);
  assert.ok([...timers.values()].every(timer=>timer.delay===20000));
  cancellation.abort(Error('cancelled'));await refused;
 }
 assert.equal(socket.closed,true);assert.equal(timers.size,0);results[mode]=true;
}
cancellation=new AbortController();
const guarded=withDeadline(new Promise(()=>{}),cancellation);
const refused=assert.rejects(guarded,/watchdog timed out/);
const timer=[...timers.values()][0];assert.equal(timer.delay,120000);timer.callback();
await refused;assert.equal(cancellation.signal.aborted,true);assert.equal(timers.size,0);
console.log(JSON.stringify({...results,watchdog:true}));
"""
    )
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "connecting": True,
        "request": True,
        "page": True,
        "watchdog": True,
    }
