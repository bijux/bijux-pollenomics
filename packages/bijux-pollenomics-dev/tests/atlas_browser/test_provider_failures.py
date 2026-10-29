"""Keep distinct provider failures, local fallback and request bounds observable."""

from __future__ import annotations

import base64
import json
from pathlib import Path
import struct
import subprocess
import zlib

import pytest

from bijux_pollenomics_dev.ci import atlas_browser
from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
    NORDIC_SOURCE_CHRONOLOGY_PROFILE,
    AtlasBrowserContractError,
)
from bijux_pollenomics_dev.ci.atlas_browser.verdict import (
    evaluate_browser_report,
    evaluate_provider_failure_matrix,
)

from .fixtures import candidate


def _node(script: str) -> object:
    module = Path(atlas_browser.__file__).with_name("provider-failures.mjs").as_uri()
    completed = subprocess.run(
        [
            "node",
            "--input-type=module",
            "--eval",
            f"import * as provider from {json.dumps(module)};\n" + script,
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    return json.loads(completed.stdout)


@pytest.fixture(scope="module")
def replies() -> dict[str, object]:
    result = _node("""
      console.log(JSON.stringify(Object.fromEntries(provider.PROVIDER_FAILURE_CASES.map(failure => [
        failure.name, {failure,
          primary: provider.providerReply('https://tile.openstreetmap.org/3/1/1.png', failure),
          fallback: provider.providerReply('https://tile.opentopomap.org/3/1/1.png', failure)},
      ]))));
    """)
    assert isinstance(result, dict)
    return result


@pytest.mark.parametrize(
    "name,status,retry",
    [
        ("http-401", 401, None),
        ("http-403", 403, None),
        ("http-404", 404, None),
        ("http-429", 429, None),
        ("http-429-retry-after", 429, "1"),
        ("dual-provider", 503, None),
    ],
)
def test_http_failures_are_real_distinct_local_responses(
    replies: dict[str, object], name: str, status: int, retry: str | None
) -> None:
    row = replies[name]
    assert isinstance(row, dict)
    primary = row["primary"]
    assert primary["method"] == "Fetch.fulfillRequest"
    assert primary["params"]["responseCode"] == status
    headers = {
        item["name"]: item["value"] for item in primary["params"]["responseHeaders"]
    }
    assert headers.get("Retry-After") == retry
    assert str(status).encode() in base64.b64decode(primary["params"]["body"])
    assert row["fallback"]["params"]["responseCode"] == (
        503 if name == "dual-provider" else 200
    )


@pytest.mark.parametrize(
    "name,reason",
    [
        ("timeout", "TimedOut"),
        ("aborted", "Aborted"),
        ("offline", "InternetDisconnected"),
    ],
)
def test_transport_failures_preserve_actual_browser_error_kind(
    replies: dict[str, object], name: str, reason: str
) -> None:
    row = replies[name]
    assert isinstance(row, dict)
    assert row["primary"] == {
        "method": "Fetch.failRequest",
        "params": {"errorReason": reason},
    }
    if name == "offline":
        assert row["fallback"] == row["primary"]


def test_decode_failure_is_http_success_with_invalid_image_and_valid_fallback(
    replies: dict[str, object],
) -> None:
    row = replies["corrupt-image"]
    assert isinstance(row, dict)
    assert row["primary"]["params"]["responseCode"] == 200
    assert base64.b64decode(row["primary"]["params"]["body"]) == b"invalid PNG bytes"
    png = base64.b64decode(row["fallback"]["params"]["body"])
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    offset = 8
    chunks = []
    while offset < len(png):
        length = struct.unpack(">I", png[offset : offset + 4])[0]
        body = png[offset + 4 : offset + 8 + length]
        expected = struct.unpack(">I", png[offset + 8 + length : offset + 12 + length])[
            0
        ]
        assert zlib.crc32(body) == expected
        chunks.append(body[:4])
        offset += length + 12
    assert chunks == [b"IHDR", b"IDAT", b"IEND"]


def test_provider_policy_refuses_other_hosts_protocols_and_credentials() -> None:
    result = _node("""
      const urls = ['https://unexpected.example/1.png', 'http://tile.openstreetmap.org/1.png',
        'https://tile.openstreetmap.org/1.png?token=secret',
        'https://user:password@tile.openstreetmap.org/1.png'];
      console.log(JSON.stringify(urls.map(url => {
        try {provider.providerReply(url, provider.PROVIDER_FAILURE_CASES[0]); return false;}
        catch {return true;}
      })));
    """)
    assert result == [True] * 4


def test_request_bounds_detect_retries_missing_interception_and_offline() -> None:
    result = _node("""
      const url = 'https://tile.openstreetmap.org/1/1/1.png';
      const sent = {url, request_id:'network-1'};
      const intercepted = {url, request_id:'fetch-1', network_id:'network-1', intercepted:true};
      const good = [sent, intercepted];
      console.log(JSON.stringify({
        good: provider.providerAttemptFacts(good),
        retry: provider.providerAttemptFacts([...good, {...intercepted, request_id:'fetch-2', network_id:'network-2'}]),
        missed: provider.providerAttemptFacts([sent]),
        offline: provider.providerAttemptFacts([{...sent, offline_blocked:true}, intercepted]),
        teardown: provider.providerAttemptFacts([{...sent, blocked_during_teardown:true}]),
        unbounded: provider.providerAttemptFacts(Array.from({length:129}, (_,i) => ({
          ...intercepted, network_id:`network-${i}`, url:`https://tile.openstreetmap.org/1/${i}/1.png`}))),
      }));
    """)
    assert isinstance(result, dict)
    assert result["good"]["bounded"] and result["good"]["all_locally_handled"]
    assert not result["retry"]["bounded"]
    assert not result["missed"]["all_locally_handled"]
    assert result["offline"]["all_locally_handled"]
    assert result["offline"]["bounded"]
    assert result["offline"]["counts"]["tile.openstreetmap.org"] == 1
    assert result["teardown"]["all_locally_handled"]
    assert not result["unbounded"]["bounded"]


def test_offline_failure_is_proven_by_network_event_not_assumed() -> None:
    result = _node("""
      const requests = [{url:'https://tile.openstreetmap.org/1/1/1.png',request_id:'network-1'}];
      const tracker = provider.providerInterception({}, requests, [], false,
        provider.PROVIDER_FAILURE_CASES.find(row => row.name==='offline'));
      tracker.handle({method:'Network.loadingFailed',params:{requestId:'network-1',errorText:'net::ERR_FAILED'}});
      const wrong = provider.providerAttemptFacts(requests).all_locally_handled;
      tracker.handle({method:'Network.loadingFailed',params:{requestId:'network-1',errorText:'net::ERR_INTERNET_DISCONNECTED'}});
      console.log(JSON.stringify([wrong, provider.providerAttemptFacts(requests).all_locally_handled]));
    """)
    assert result == [False, True]


def _matrix_report() -> dict[str, object]:
    contract = _node(
        "console.log(JSON.stringify({cases:provider.PROVIDER_FAILURE_CASES, assertions:provider.PROVIDER_MATRIX_ASSERTIONS}));"
    )
    assert isinstance(contract, dict)
    return {
        "schema_version": "atlas-browser-runtime-report.v2",
        "verification_mode": "provider-failure-matrix",
        "candidate": candidate().as_json(),
        "browser": dict.fromkeys(
            (
                "product",
                "revision",
                "user_agent",
                "javascript_version",
                "protocol_version",
                "binary",
            ),
            "test-browser",
        ),
        "scenarios": [
            {
                "scope": "nordic",
                "name": "provider-" + row["name"],
                "assertions": dict.fromkeys(contract["assertions"], True),
            }
            for row in contract["cases"]
        ],
        "served_canonical_files": [{"repository_path": "docs/report/map.html"}],
    }


def test_native_matrix_verdict_is_scoped_and_cannot_pass_full_profile() -> None:
    report = _matrix_report()
    result = evaluate_provider_failure_matrix(
        report, candidate=candidate(), scopes=frozenset({"nordic"})
    )
    assert result["status"] == "PASS"
    assert result["scenario_count"] == 10
    assert result["full_profile_qualified"] is False
    assert result["deployment_qualified"] is False
    with pytest.raises(
        AtlasBrowserContractError, match="not a complete browser profile"
    ):
        evaluate_browser_report(
            report,
            candidate=candidate(),
            verification_profile=NORDIC_SOURCE_CHRONOLOGY_PROFILE,
        )


@pytest.mark.parametrize(
    "change", ["missing", "duplicate", "wrong_candidate", "missing_servable"]
)
def test_native_matrix_verdict_rejects_incomplete_identity_or_coverage(
    change: str,
) -> None:
    report = _matrix_report()
    rows = report["scenarios"]
    assert isinstance(rows, list)
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows.append(rows[0])
    elif change == "wrong_candidate":
        report["candidate"] = {}
    else:
        report["served_canonical_files"] = []
    with pytest.raises(AtlasBrowserContractError):
        evaluate_provider_failure_matrix(
            report, candidate=candidate(), scopes=frozenset({"nordic"})
        )


def test_native_matrix_keeps_false_outcomes_in_denominator() -> None:
    report = _matrix_report()
    rows = report["scenarios"]
    assert isinstance(rows, list)
    rows[0]["assertions"]["provider_matrix_payload_unchanged"] = False
    result = evaluate_provider_failure_matrix(
        report, candidate=candidate(), scopes=frozenset({"nordic"})
    )
    assert result["status"] == "FAIL"
    assert result["scenario_count"] == 10
    assert result["failed_assertions"] == [
        "nordic/provider-http-401:provider_matrix_payload_unchanged"
    ]


def test_completion_requires_terminal_availability_not_unavailable_text() -> None:
    result = _node("""
      console.log(JSON.stringify([
        provider.providerTerminal({basemap:'terrain'}, 'Basemap degraded: street unavailable; using terrain. Evidence data unaffected.', 'terrain'),
        provider.providerTerminal({basemap:'terrain'}, 'terrain loading', 'terrain'),
        provider.providerTerminal({basemap:'terrain'}, 'terrain available', 'terrain'),
        provider.providerTerminal({basemap:'street'}, 'terrain available', 'terrain'),
        provider.providerTerminal({basemap:'none'}, 'Basemap degraded: terrain unavailable; no-basemap mode active. Evidence data unaffected.', 'none'),
      ]));
    """)
    assert result == [False, False, True, False, True]


@pytest.mark.parametrize("full_span", [False, True])
def test_ui_journey_reacquires_replaced_country_control_before_restoring(
    full_span: bool,
) -> None:
    result = _node(
        f"const fullSpan={json.dumps(full_span)};\n"
        """
      let interval = fullSpan ? 10000 : 1000;
      const presetClicks = [];
      const state = {countries:['Sweden','Norway'], time_window_bp:{younger_bp:0,older_bp:interval},
        visible_point_count:10, visible_governed_candidate_count:0};
      let current, detachedClicks=0, countryClicks=0;
      function renderCountry() {
        current = {value:'Sweden',checked:state.countries.includes('Sweden'),click() {
          if (this!==current) {detachedClicks++;return;}
          countryClicks++;
          state.countries = this.checked ? ['Norway'] : ['Sweden','Norway'];
          state.visible_point_count = this.checked ? 4 : 10;
          renderCountry();
        }};
      }
      renderCountry();
      const legend = {value:'false', getAttribute(){return this.value;},
        click(){this.value=this.value==='false'?'true':'false';}};
      const slider = {value:'0',min:'0',max:fullSpan?'0':'10000',dispatchEvent(){
        state.time_window_bp={younger_bp:Number(this.value),older_bp:Number(this.value)+interval};}};
      const presets = ['full','1000'].map(value=>({dataset:{timeInterval:value},
        classList:{contains:()=>value==='full' && fullSpan},
        click(){presetClicks.push(value);interval=value==='full'?10000:1000;
          slider.value='0';slider.max=value==='full'?'0':'9000';slider.dispatchEvent();}}));
      const popup={hidden:true};
      const elements = {
        'legend-toggle':legend,'time-start-slider':slider,'search-toggle':{click(){}},
        'search-input':{value:'',dispatchEvent(){}},'focus-card':popup,
        'focus-title':{textContent:'Source record'},'focus-close':{click(){popup.hidden=true;}},
      };
      globalThis.document={
        getElementById:id=>elements[id],
        querySelector(selector){
          if(selector==='.country-checkbox:checked')return current.checked?current:null;
          if(selector==='[data-search-index]')return {click(){popup.hidden=false;}};
          return {};
        },
        querySelectorAll:selector=>selector==='.country-checkbox'?[current]:presets,
      };
      globalThis.requestAnimationFrame=callback=>queueMicrotask(callback);
      globalThis.BijuxPollenomicsAtlasCapture={awaitReady:async()=>structuredClone(state)};
      const ui=await provider.providerUiJourney();
      console.log(JSON.stringify({ui,detachedClicks,countryClicks,presetClicks}));
    """
    )
    assert isinstance(result, dict)
    assert result["detachedClicks"] == 0
    assert result["countryClicks"] == 2
    assert result["presetClicks"] == (["1000", "full"] if full_span else [])
    assert all(result["ui"].values())


def test_target_closure_waits_for_late_pairing_or_positive_cancellation() -> None:
    result = _node("""
      async function exercise(mode) {
        const requests=[{url:'https://tile.openstreetmap.org/1/1/1.png',request_id:'network-1'}];
        const failures=[], commands=[];
        let tracker;
        const cdp={send(method){
          commands.push(method);
          if(method==='Page.stopLoading')setTimeout(()=>{
            tracker.handle(mode==='paired'
              ? {method:'Fetch.requestPaused',params:{requestId:'fetch-1',networkId:'network-1',
                request:{url:requests[0].url,headers:{}}}}
              : {method:'Network.loadingFailed',params:{requestId:'network-1',
                canceled:true,errorText:'net::ERR_ABORTED'}});
          },0);
          return Promise.resolve({});
        }};
        tracker=provider.providerInterception(cdp,requests,failures,true,
          provider.PROVIDER_FAILURE_CASES[0]);
        let finalAtClose;
        await tracker.settle(async()=>{
          finalAtClose=provider.providerAttemptFacts(requests).all_locally_handled;
          commands.push('Target.closeTarget');
        });
        return {commands,finalAtClose,failures,requests};
      }
      console.log(JSON.stringify({paired:await exercise('paired'),canceled:await exercise('canceled')}));
    """)
    assert isinstance(result, dict)
    for row in result.values():
        assert row["finalAtClose"] is True
        assert row["failures"] == []
        assert row["commands"][0:2] == ["Network.setBlockedURLs", "Page.stopLoading"]
        assert row["commands"][-1] == "Target.closeTarget"
    assert result["paired"]["commands"][2] == "Fetch.fulfillRequest"
    assert result["canceled"]["requests"][0]["observed_cancellation"] == {
        "canceled": True,
        "error_text": "net::ERR_ABORTED",
    }


def test_unknown_network_failure_does_not_become_positive_cancellation() -> None:
    result = _node("""
      console.log(JSON.stringify([
        {canceled:true,errorText:'net::ERR_ABORTED'},
        {canceled:false,errorText:'net::ERR_ABORTED'},
        {canceled:true,errorText:'net::ERR_FAILED'},
      ].map(failure=>{
        const requests=[{url:'https://tile.openstreetmap.org/1/1/1.png',request_id:'network-1'}];
        const tracker=provider.providerInterception({},requests,[],false);
        tracker.handle({method:'Network.loadingFailed',params:{requestId:'network-1',...failure}});
        return provider.providerAttemptFacts(requests).all_locally_handled;
      })));
    """)
    assert result == [True, False, False]
