"""Admit the narrow manually dispatched, nonpublishing verification surface."""

from __future__ import annotations

import json
from pathlib import Path
import runpy
from typing import Any

from .contracts import require

ACTIONS = {
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
    "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0",
    "astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2",
    "actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1",
    "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9",
}


def verify_workflow(document: dict[str, Any]) -> None:
    """Reject automatic triggers, mutable source, credentials and publishing actions."""
    require(
        document.get("on")
        == {
            "workflow_dispatch": {
                "inputs": {
                    "accepted_commit": {
                        "description": "Exact accepted main source to verify without publishing",
                        "required": True,
                        "type": "string",
                    }
                }
            }
        },
        "verification requires one explicit manual commit input",
    )
    require(
        document.get("permissions") == {"contents": "read"},
        "verification must remain read-only",
    )
    require(
        set(document["jobs"]) == {"reading"}, "verification requires one bounded job"
    )
    job = document["jobs"]["reading"]
    require(
        "if" not in job
        and job.get("runs-on") == "ubuntu-24.04"
        and job.get("timeout-minutes") == 60,
        "verification runtime or exact main admission differs",
    )
    require(
        not set(job).intersection(
            {"permissions", "environment", "secrets", "uses", "services", "container"}
        ),
        "verification job adds privileged execution",
    )
    required = [
        "Checkout exact accepted source",
        "Check accepted source selection",
        "Set up supported Python",
        "Set up supported uv",
        "Set up Node.js",
        "Check nonpublishing workflow contract",
        "Admit exact documentation standards",
        "Install admitted documentation renderer",
        "Check retained publication downloads",
        "Check native report configuration",
        "Build and verify the production-site artifact",
        "Locate hosted Chromium",
        "Verify actual scientific reading and download routes",
        "Verify production-origin Nordic iframe",
        "Retain verification evidence",
        "Retain verified site",
    ]
    require(
        [step.get("name") for step in job["steps"]] == required,
        "ordered verification steps are missing, duplicated or replaced",
    )
    for step in job["steps"][:-2]:
        require("if" not in step, "verification may not skip a required step")
    by_name = {step["name"]: step for step in job["steps"]}
    require(
        by_name["Install admitted documentation renderer"].get("run")
        == "make gh-docs-install"
        and by_name["Build and verify the production-site artifact"].get("run")
        == "make gh-docs-build gh-docs-verify"
        and by_name["Build and verify the production-site artifact"].get("id")
        == "publication",
        "the admitted build and verifier must both execute",
    )
    downloads = by_name["Check retained publication downloads"]
    download_commands = downloads.get("run")
    require(
        downloads.get("shell") == "bash"
        and isinstance(download_commands, str)
        and download_commands.strip()
        == (
            "set -euo pipefail\n"
            "PYTHONPATH=packages/bijux-pollenomics-dev/src:packages/bijux-pollenomics/src \\\n"
            "  artifacts/docs/publication/python/bin/python -B \\\n"
            "  -m bijux_pollenomics_dev.ci.scientific_reading.runner --help\n"
            "make docs-publication-controls"
        ),
        "the admitted reading runtime and download controls must execute before build",
    )
    require(
        by_name["Check native report configuration"].get("run")
        == (
            "artifacts/docs/publication/python/bin/python "
            ".bijux/shared/bijux-docs/security/render_publication.py "
            "--config mkdocs.yml --site-dir artifacts/docs/site "
            "--site-url https://bijux.io/bijux-pollenomics/ "
            "--interactive-report-owner configs/docs/maps/report-owner.json --preflight"
        ),
        "the selected native report configuration must pass source preflight",
    )
    for source_check in (
        "Check retained publication downloads",
        "Check native report configuration",
    ):
        source_path = by_name[source_check].get("env", {}).get("PYTHONPATH")
        source_roots = source_path.split(":") if isinstance(source_path, str) else []
        require(
            len(source_roots) == 4
            and set(source_roots)
            == {
                "packages/bijux-pollenomics/src",
                "packages/bijux-pollenomics-dev/src",
                "packages/bijux-pollenomics-lra/src",
                "packages/pollenomics/src",
            },
            "native report preflight requires all four distinct owned package source roots",
        )
    require(
        by_name["Set up supported Python"].get("with", {}).get("python-version")
        == "3.11.17"
        and by_name["Set up supported uv"].get("with", {}).get("version") == "0.11.17"
        and by_name["Set up Node.js"].get("with", {}).get("node-version") == "24.21.0",
        "supported renderer or browser transport runtime differs",
    )
    browser_step = by_name["Verify actual scientific reading and download routes"]
    require(
        all(
            clause in browser_step.get("run", "")
            for clause in (
                "-m bijux_pollenomics_dev.ci.scientific_reading.runner",
                '--accepted-commit "$ACCEPTED_COMMIT"',
                '--browser "$BROWSER_BINARY"',
                '--output "$PWD/artifacts/scientific-reading/evidence"',
            )
        )
        and browser_step.get("env", {}).get("ACCEPTED_COMMIT")
        == "${{ inputs.accepted_commit }}",
        "the actual browser runner or accepted input is missing",
    )
    native = by_name["Verify production-origin Nordic iframe"]
    require(
        all(
            clause in native.get("run", "")
            for clause in (
                "artifacts/docs/publication/python/bin/python",
                "wrapper-runtime.mjs",
                "run_bounded_argv(",
                "timeout_seconds=1080, max_output_bytes=16 * 1024 * 1024,",
                'receipt["source_revision"] != os.environ["ACCEPTED_COMMIT"]',
                'len(receipt["scenarios"]) != 10',
            )
        )
        and native.get("env", {}).get("ACCEPTED_COMMIT")
        == "${{ inputs.accepted_commit }}",
        "the bounded source-bound native iframe runner is missing",
    )
    require(
        by_name["Retain verification evidence"].get("if") == "always()"
        and by_name["Retain verified site"].get("if")
        == "${{ always() && steps.publication.outcome == 'success' }}"
        and all(
            by_name[name].get("with", {}).get("retention-days") == 14
            for name in required[-2:]
        ),
        "evidence retention or qualified-build site upload differs",
    )
    admissions = [
        step
        for step in job["steps"]
        if step.get("name") == "Check accepted source selection"
    ]
    require(len(admissions) == 1, "exact source admission step is missing")
    admission = admissions[0]
    require(
        admission.get("env", {}).get("ACCEPTED_COMMIT")
        == "${{ inputs.accepted_commit }}"
        and all(
            clause in admission.get("run", "")
            for clause in (
                'test "$GITHUB_EVENT_NAME" = workflow_dispatch',
                'test "$GITHUB_REF" = refs/heads/main',
                '[[ "$ACCEPTED_COMMIT" =~ ^[0-9a-f]{40}$ ]]',
                'test "$ACCEPTED_COMMIT" = "$GITHUB_SHA"',
                'test "$(git rev-parse HEAD)" = "$ACCEPTED_COMMIT"',
            )
        ),
        "manual main source selection must fail rather than skip",
    )
    serialized = json.dumps(document)
    require(
        not any(
            value in serialized
            for value in (
                "secrets.",
                "github.token",
                "id-token",
                "deploy-pages",
                "upload-pages-artifact",
                "gh-pages",
            )
        ),
        "verification must not request credentials or publish",
    )
    for step in job["steps"]:
        require(
            set(step) <= {"name", "uses", "with", "run", "shell", "env", "id", "if"},
            "verification step adds unsupported authority",
        )
        if "uses" in step:
            require(
                step["uses"] in ACTIONS, "verification action differs from pinned owner"
            )
            if step["uses"].startswith("actions/checkout@"):
                require(
                    step.get("with", {}).get("ref") == "${{ github.sha }}"
                    and step["with"].get("persist-credentials") is False,
                    "checkout must use immutable source without persisted credentials",
                )


def main() -> None:
    """Check the authored workflow through the canonical YAML parser."""
    root = Path.cwd()
    parser = runpy.run_path(
        str(root / ".github/scripts/workflow_execution/yaml_io.py")
    )["parse_workflow"]
    path = root / ".github/workflows/scientific-reading-verification.yml"
    verify_workflow(parser(path.read_bytes(), path.name))


if __name__ == "__main__":
    main()
