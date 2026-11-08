"""Protect the authored manual verification workflow from publishing authority."""

from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.scientific_reading.workflow import verify_workflow

ROOT = Path(__file__).resolve().parents[4]


def workflow(monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, Any], Any]:
    monkeypatch.syspath_prepend(str(ROOT / ".github/scripts"))
    owner = importlib.import_module("workflow_execution")
    path = ROOT / ".github/workflows/scientific-reading-verification.yml"
    return owner.parse_workflow(path.read_bytes(), path.name), owner


def test_owned_manual_workflow_passes_canonical_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document, owner = workflow(monkeypatch)
    manifest = json.loads(
        (ROOT / ".github/standards/repo-config.manifest.json").read_text()
    )
    policy = owner.validate_manifest(manifest, ["bijux-pollenomics"])[
        "bijux-pollenomics"
    ]
    owner.validate_owned_execution(
        {".github/workflows/scientific-reading-verification.yml": document}, policy
    )
    verify_workflow(document)


@pytest.mark.parametrize(
    "change",
    [
        "automatic",
        "permissions",
        "job_permissions",
        "environment",
        "secret",
        "action",
        "mutable_checkout",
        "credentials",
        "skip",
        "main",
        "commit",
        "timeout",
        "platform",
    ],
)
def test_automatic_privileged_or_unbound_workflow_is_refused(
    monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    document, _ = workflow(monkeypatch)
    document = copy.deepcopy(document)
    job = document["jobs"]["reading"]
    if change == "automatic":
        document["on"]["push"] = {}
    elif change == "permissions":
        document["permissions"]["pages"] = "write"
    elif change == "job_permissions":
        job["permissions"] = {"id-token": "write"}
    elif change == "environment":
        job["environment"] = "github-pages"
    elif change == "secret":
        job["steps"][1]["env"]["TOKEN"] = "${{ secrets.DEPLOY }}"
    elif change == "action":
        job["steps"][0]["uses"] = "actions/checkout@main"
    elif change == "mutable_checkout":
        job["steps"][0]["with"]["ref"] = "main"
    elif change == "credentials":
        job["steps"][0]["with"]["persist-credentials"] = True
    elif change == "skip":
        job["if"] = "${{ inputs.accepted_commit == github.sha }}"
    elif change == "main":
        job["steps"][1]["run"] = job["steps"][1]["run"].replace(
            'test "$GITHUB_REF" = refs/heads/main', "true"
        )
    elif change == "commit":
        job["steps"][1]["run"] = job["steps"][1]["run"].replace(
            'test "$ACCEPTED_COMMIT" = "$GITHUB_SHA"', "true"
        )
    elif change == "timeout":
        job["timeout-minutes"] = 600
    elif change == "platform":
        job["runs-on"] = "macos-latest"
    with pytest.raises(ValueError):
        verify_workflow(document)


def test_browser_path_parser_refuses_outside_routes() -> None:
    script = (
        ROOT
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/scientific_reading/browser.mjs"
    )
    program = """import assert from 'node:assert/strict';
const {relativePath}=await import(process.argv[1]);
assert.equal(relativePath('/bijux-pollenomics/public/pollenomics/science/'),'public/pollenomics/science/index.html');
for(const path of ['/outside','/bijux-pollenomics/%2e%2e/outside','/bijux-pollenomics/a%2f..%2foutside','/bijux-pollenomics/a%5cb','/bijux-pollenomics/a%00b']) assert.throws(()=>relativePath(path));
"""
    subprocess.run(
        ("node", "--input-type=module", "-e", program, script.as_uri()),
        check=True,
        timeout=10,
    )


@pytest.mark.parametrize(
    "name",
    [
        "Install admitted documentation renderer",
        "Check retained publication downloads",
        "Check native report configuration",
        "Build and verify the production-site artifact",
        "Verify actual scientific reading and download routes",
        "Verify production-origin Nordic iframe",
        "Check accepted source selection",
    ],
)
def test_omitted_critical_execution_is_refused(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    document, _ = workflow(monkeypatch)
    steps = document["jobs"]["reading"]["steps"]
    steps[:] = [step for step in steps if step.get("name") != name]
    with pytest.raises(ValueError, match="ordered verification"):
        verify_workflow(document)


def test_omitted_site_verifier_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    document, _ = workflow(monkeypatch)
    for step in document["jobs"]["reading"]["steps"]:
        if step.get("name") == "Build and verify the production-site artifact":
            step["run"] = "make gh-docs-build"
    with pytest.raises(ValueError, match="both execute"):
        verify_workflow(document)


@pytest.mark.parametrize("change", ["after_build", "replaced_command"])
def test_download_boundary_must_execute_before_site_build(
    monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    document, _ = workflow(monkeypatch)
    steps = document["jobs"]["reading"]["steps"]
    selected = next(
        step for step in steps if step["name"] == "Check retained publication downloads"
    )
    if change == "after_build":
        steps.remove(selected)
        position = next(
            i
            for i, step in enumerate(steps)
            if step["name"] == "Build and verify the production-site artifact"
        )
        steps.insert(position + 1, selected)
    else:
        selected["run"] = "true"
    with pytest.raises(ValueError):
        verify_workflow(document)


@pytest.mark.parametrize(
    "change", ["after_build", "missing_preflight", "foreign_owner"]
)
def test_native_configuration_requires_early_selected_source_preflight(
    monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    document, _ = workflow(monkeypatch)
    steps = document["jobs"]["reading"]["steps"]
    selected = next(
        step for step in steps if step["name"] == "Check native report configuration"
    )
    if change == "after_build":
        steps.remove(selected)
        position = next(
            i
            for i, step in enumerate(steps)
            if step["name"] == "Build and verify the production-site artifact"
        )
        steps.insert(position + 1, selected)
    elif change == "missing_preflight":
        selected["run"] = selected["run"].replace(" --preflight", "")
    else:
        selected["run"] = selected["run"].replace(
            "configs/docs/maps/report-owner.json",
            "configs/docs/maps/foreign-owner.json",
        )
    with pytest.raises(ValueError):
        verify_workflow(document)
