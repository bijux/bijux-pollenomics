"""Static checks for dependency-free, event-driven Brave capture."""

from __future__ import annotations

import json
from pathlib import Path
import os
import subprocess
import sys
import time

import bijux_pollenomics_dev.ci.atlas_media as atlas_media
from bijux_pollenomics_dev.ci.atlas_media import admission
from bijux_pollenomics_dev.ci.atlas_media.contracts import AtlasMediaError
import pytest


def test_renderer_is_valid_dependency_free_node_module() -> None:
    renderer = Path(atlas_media.__file__).with_name("render.mjs")

    completed = subprocess.run(
        ("node", "--check", str(renderer)),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr


def test_debugger_policy_requires_exact_loopback_authority() -> None:
    policy = Path(atlas_media.__file__).with_name("debugger_policy.mjs")
    script = """
      import { requireLoopbackDebuggerEndpoint, requireTargetDebuggerEndpoint } from %s;
      const accepted = requireLoopbackDebuggerEndpoint('ws://127.0.0.1:8123/devtools/browser/id');
      requireTargetDebuggerEndpoint(
        'ws://127.0.0.1:8123/devtools/page/id',
        new URL('http://127.0.0.1:8123'),
      );
      const rejected = [];
      for (const value of [
        'ws://localhost:8123/devtools/browser/id',
        'ws://127.0.0.1/devtools/browser/id',
        'ws://user@127.0.0.1:8123/devtools/browser/id',
      ]) {
        try { requireLoopbackDebuggerEndpoint(value); } catch { rejected.push(value); }
      }
      try {
        requireTargetDebuggerEndpoint(
          'ws://127.0.0.1:8124/devtools/page/id',
          new URL('http://127.0.0.1:8123'),
        );
      } catch { rejected.push('wrong-target-port'); }
      process.stdout.write(JSON.stringify({ accepted, rejected }));
    """ % json.dumps(policy.as_uri())
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["accepted"] == "ws://127.0.0.1:8123/devtools/browser/id"
    assert result["rejected"] == [
        "ws://localhost:8123/devtools/browser/id",
        "ws://127.0.0.1/devtools/browser/id",
        "ws://user@127.0.0.1:8123/devtools/browser/id",
        "wrong-target-port",
    ]


def test_python_candidate_git_timeout_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def timeout(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del args, kwargs
        raise subprocess.TimeoutExpired(("git", "status"), timeout=30)

    monkeypatch.setattr(admission.shutil, "which", lambda _name: "/usr/bin/git")
    monkeypatch.setattr(admission.subprocess, "run", timeout)

    try:
        admission._git(tmp_path, "status")
    except AtlasMediaError as error:
        assert str(error) == "git status timed out"
    else:
        raise AssertionError("timed-out candidate admission unexpectedly succeeded")


def test_node_candidate_git_timeout_fails_closed(tmp_path: Path) -> None:
    policy = Path(atlas_media.__file__).with_name("candidate_git.mjs")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text(
        f"#!{sys.executable}\nimport time\ntime.sleep(5)\n", encoding="utf-8"
    )
    fake_git.chmod(0o755)
    script = """
      import { boundedGit } from %s;
      try {
        boundedGit(%s, ['status'], 25);
        process.exitCode = 2;
      } catch (error) {
        process.stdout.write(error.message);
      }
    """ % (json.dumps(policy.as_uri()), json.dumps(str(tmp_path)))
    started = time.monotonic()
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
        timeout=2,
        env={**os.environ, "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}"},
    )

    assert time.monotonic() - started < 1
    assert completed.returncode == 0, completed.stderr
    assert "bounded candidate git command failed" in completed.stdout


def test_renderer_uses_capture_api_without_polling_or_provider_tiles() -> None:
    renderer = (
        Path(atlas_media.__file__).with_name("render.mjs").read_text(encoding="utf-8")
    )

    assert "BijuxPollenomicsAtlasCapture" in renderer
    assert "api.applyFrame" in renderer
    assert "const initial = await captureReady(cdp)" in renderer
    assert "new MutationObserver(finish)" in renderer
    assert "observer.observe(document.documentElement" in renderer
    assert "atlas capture API readiness timed out" in renderer
    assert "atlas capture API unavailable" not in renderer
    assert "Page.captureScreenshot" in renderer
    assert "Page.loadEventFired" in renderer
    assert "setInterval(" not in renderer
    assert "Fetch.enable" in renderer
    assert "Fetch.requestPaused" in renderer
    assert "Fetch.failRequest" in renderer
    assert "Fetch.disable" not in renderer
    assert "urls: ['ws://*', 'wss://*', 'ftp://*', 'file://*']" in renderer
    assert "connect-src 'self'" in renderer
    assert "deny-before-send-governed-origin-data-blob-only.v2" in renderer
    assert "network-rejection-receipt.json" in renderer
    assert "host-resolver-rules=MAP * ~NOTFOUND" in renderer
    assert "const canonicalPath = await realpath(requestedPath)" in renderer
    assert "validateStaticAssetPayload" in renderer
    assert "governed_static_assets" in renderer
    assert "network_requests: networkRequests" in renderer
    assert "capture denied non-local requests" in renderer
    assert "facet_node_count" in renderer
    assert "facet_observation_denominator" in renderer
    assert "modeled_context?.feature_count" in renderer
    assert "visible_feature_count" in renderer
    assert "source story rendered no selected-layer evidence" in renderer
    assert "visible_source_chronology_point_count" in renderer
    assert "visible_modeled_context_feature_count" in renderer
    assert "#basemap=none" in renderer
    assert "git('status', '--porcelain=v1', '--untracked-files=no')" in renderer
    assert "--untracked-files=all" not in renderer
    assert "atlas frame application timed out" in renderer
    assert "AbortSignal.timeout(timeoutMs)" in renderer
    assert "requireLoopbackDebuggerEndpoint" in renderer
    assert "requireTargetDebuggerEndpoint" in renderer
    assert "boundedGit(repositoryRoot, args)" in renderer
    assert "browser log close timed out" in renderer
    assert "CDP WebSocket open timed out" in renderer
    assert "requireExactNavigation" in renderer


def test_package_export_does_not_eagerly_import_runner() -> None:
    package = "bijux_pollenomics_dev.ci.atlas_media"
    completed = subprocess.run(
        (
            sys.executable,
            "-W",
            "error",
            "-c",
            (
                f"import sys; import {package}; "
                f"print({package!r} + '.runner' in sys.modules)"
            ),
        ),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "False"


def test_package_module_help_is_free_of_runpy_import_warnings() -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "-W",
            "error",
            "-m",
            "bijux_pollenomics_dev.ci.atlas_media",
            "--help",
        ),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "RuntimeWarning" not in completed.stderr


def test_node_network_policy_allows_only_loopback_and_embedded_urls() -> None:
    policy = Path(atlas_media.__file__).with_name("network_policy.mjs")
    script = """
      import { classifyNetworkRequest } from %s;
      const urls = [
        'http://127.0.0.1:8123/atlas.json',
        'http://127.0.0.1:8124/atlas.json',
        'http://127.0.0.2:8123/atlas.json',
        'http://127.0.0.1:8123/unrelated.json',
        'http://127.0.0.1:8123/atlas.json?cache=1',
        'https://localhost/atlas.json',
        'data:image/png;base64,AA==',
        'blob:http://127.0.0.1:8123/id',
        'https://tile.openstreetmap.org/1/2/3.png',
        'https://127.0.0.1.example.invalid/',
        'file:///private/source',
      ];
      const authority = {
        origin: 'http://127.0.0.1:8123',
        allowedPaths: new Set(['/atlas.json']),
      };
      const rows = urls.map((url, index) => classifyNetworkRequest(
        { requestId: String(index), type: 'Image', request: { url, method: 'GET' } },
        authority,
      ));
      process.stdout.write(JSON.stringify(rows));
    """ % json.dumps(policy.as_uri())
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    rows = json.loads(completed.stdout)
    assert [row["allowed"] for row in rows] == [
        True,
        False,
        False,
        False,
        False,
        False,
        True,
        True,
        False,
        False,
        False,
    ]
    assert [row["receipt"]["url"] for row in rows] == [
        "http://127.0.0.1:8123/atlas.json",
        "http://127.0.0.1:8124/atlas.json",
        "http://127.0.0.2:8123/atlas.json",
        "http://127.0.0.1:8123/unrelated.json",
        "http://127.0.0.1:8123/atlas.json?cache=1",
        "https://localhost/atlas.json",
        "data:image/png;base64,AA==",
        "blob:http://127.0.0.1:8123/id",
        "https://tile.openstreetmap.org/1/2/3.png",
        "https://127.0.0.1.example.invalid/",
        "file:///private/source",
    ]


def test_static_asset_policy_refuses_bytes_changed_after_planning() -> None:
    policy = Path(atlas_media.__file__).with_name("static_asset_policy.mjs")
    script = """
      import { createHash } from 'node:crypto';
      import { normalizeStaticAssetAuthority, validateStaticAssetPayload } from %s;
      const original = Buffer.from('candidate bytes');
      const rows = [{
        path: '/atlas.html',
        byte_count: original.length,
        sha256: createHash('sha256').update(original).digest('hex'),
      }];
      const authority = normalizeStaticAssetAuthority(rows);
      validateStaticAssetPayload(authority.get('/atlas.html'), original);
      let rejected = false;
      try {
        validateStaticAssetPayload(authority.get('/atlas.html'), Buffer.from('mutated bytes'));
      } catch {
        rejected = true;
      }
      process.stdout.write(JSON.stringify(rejected));
    """ % json.dumps(policy.as_uri())
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) is True
