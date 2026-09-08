"""Provider interception drains replies without hiding application failures."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

from bijux_pollenomics_dev.ci import atlas_browser


def test_interception_requires_exact_cancellation_and_drains_pending_replies() -> None:
    probe = Path(atlas_browser.__file__).with_name("probe.mjs").read_text()
    match = re.search(
        r"function providerInterception.*?\n}\n\nasync function openAtlas",
        probe,
        re.DOTALL,
    )
    assert match is not None
    helper = match.group(0).removesuffix("\n\nasync function openAtlas")
    script = (
        helper
        + r"""
async function exercise(cancellation, errorPayload, canceledId = 'network-1') {
  const requests = [];
  const failures = [{ kind: 'console-error', detail: 'application error' }];
  const commands = [];
  let rejectRequest;
  const cdp = { send(method, params) {
    commands.push({ method, params });
    if (method === 'Fetch.failRequest') return new Promise((_, reject) => { rejectRequest = reject; });
    return Promise.resolve({});
  }};
  const tracker = providerInterception(cdp, requests, failures, true);
  tracker.handle({ method: 'Fetch.requestPaused', params: {
    requestId: 'fetch-1', networkId: 'network-1', request: { url: 'https://tile.example/1' },
  }});
  let settled = false;
  const finishing = tracker.settle().then(() => { settled = true; });
  await Promise.resolve();
  const settledBeforeReply = settled;
  if (cancellation !== null) tracker.handle({ method: 'Network.loadingFailed', params: {
    requestId: canceledId, canceled: cancellation,
  }});
  rejectRequest(new Error(JSON.stringify(errorPayload)));
  await finishing;
  return { settledBeforeReply, failures, requests, commands };
}
const stale = { code: -32602, message: 'Invalid InterceptionId.' };
console.log(JSON.stringify({
  canceled: await exercise(true, stale),
  unknown: await exercise(null, stale),
  unrelated: await exercise(true, stale, 'network-other'),
  notCanceled: await exercise(false, stale),
  wrongError: await exercise(true, { code: -32602, message: 'Invalid parameters' }),
}));
"""
    )
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    results = json.loads(completed.stdout)
    for result in results.values():
        assert result["settledBeforeReply"] is False
        assert result["failures"][0] == {
            "kind": "console-error",
            "detail": "application error",
        }
        assert [row["method"] for row in result["commands"]] == [
            "Fetch.failRequest",
            "Fetch.disable",
        ]
    assert len(results["canceled"]["failures"]) == 1
    assert results["canceled"]["requests"][0]["interception_status"] == (
        "canceled_before_failure_reply"
    )
    for case in ("unknown", "unrelated", "notCanceled", "wrongError"):
        assert len(results[case]["failures"]) == 2
        assert results[case]["failures"][1]["kind"] == "provider-interception"


def test_provider_verdict_is_taken_after_interception_teardown() -> None:
    probe = Path(atlas_browser.__file__).with_name("probe.mjs").read_text()
    failure_blocks = re.findall(
        r"const failure = await openAtlas.*?scopeScenarios.push\(failureResult\);",
        probe,
        re.DOTALL,
    )
    assert len(failure_blocks) == 2
    for block in failure_blocks:
        assert block.index("await closeAtlas(failure, debuggerOrigin);") < block.index(
            "const failureResult = {"
        )
    close = probe[probe.index("async function closeAtlas(") :]
    assert close.index("await atlas.interception.settle();") < close.index(
        "atlas.cdp.close();"
    )
