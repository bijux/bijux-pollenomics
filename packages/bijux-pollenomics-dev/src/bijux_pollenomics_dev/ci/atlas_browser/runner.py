"""Orchestrate static and live browser verification without mutating the candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from .contracts import (
    AtlasBrowserContractError,
    AtlasCandidate,
    BrowserVerificationPlan,
    JsonObject,
    load_plan,
)
from .static_integrity import audit_static_atlas
from .verdict import evaluate_browser_report


def _git(repository_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AtlasBrowserContractError(
            f"git {' '.join(arguments)} failed: {completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def _observed_candidate(plan: BrowserVerificationPlan) -> AtlasCandidate:
    root = plan.repository_root
    return AtlasCandidate(
        repository_head=_git(root, "rev-parse", "HEAD"),
        repository_tree=_git(root, "rev-parse", "HEAD^{tree}"),
        atlas_output_commit=_git(
            root,
            "log",
            "-1",
            "--format=%H",
            "--",
            *(scope.document for scope in plan.scopes),
        ),
        build_id=plan.candidate.build_id,
    )


def _require_candidate(plan: BrowserVerificationPlan) -> None:
    observed = _observed_candidate(plan)
    if observed != plan.candidate:
        raise AtlasBrowserContractError(
            f"candidate identity mismatch: expected={plan.candidate.as_json()}, "
            f"observed={observed.as_json()}"
        )
    if _git(plan.repository_root, "diff", "--name-only") or _git(
        plan.repository_root, "diff", "--cached", "--name-only"
    ):
        raise AtlasBrowserContractError(
            "tracked worktree changes make the candidate mutable"
        )


def _stable_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run_browser_verification(plan: BrowserVerificationPlan) -> JsonObject:
    """Run the independent browser verifier and return its fail-closed summary."""
    artifact_root = plan.artifact_root.resolve()
    if artifact_root.exists() and any(artifact_root.iterdir()):
        raise AtlasBrowserContractError("artifact_root must be absent or empty")
    artifact_root.mkdir(parents=True, exist_ok=True)
    _require_candidate(plan)
    static_before = [
        audit_static_atlas(plan.repository_root, scope, plan.candidate)
        for scope in plan.scopes
    ]
    _write_json(artifact_root / "plan.json", plan.as_json())
    _write_json(artifact_root / "static-integrity-before.json", static_before)
    probe = Path(__file__).with_name("probe.mjs")
    completed = subprocess.run(
        ("node", str(probe), str(artifact_root / "plan.json")),
        cwd=plan.repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    (artifact_root / "runner.stdout.log").write_text(completed.stdout, encoding="utf-8")
    (artifact_root / "runner.stderr.log").write_text(completed.stderr, encoding="utf-8")
    report_path = artifact_root / "browser-runtime-report.json"
    if not report_path.is_file():
        raise AtlasBrowserContractError(
            f"browser process produced no report (exit {completed.returncode})"
        )
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AtlasBrowserContractError("browser report is unreadable") from error
    summary = evaluate_browser_report(
        report,
        candidate=plan.candidate,
        verification_profile=plan.verification_profile,
    )
    _require_candidate(plan)
    static_after = [
        audit_static_atlas(plan.repository_root, scope, plan.candidate)
        for scope in plan.scopes
    ]
    if _stable_digest(static_before) != _stable_digest(static_after):
        raise AtlasBrowserContractError("static atlas changed during browser execution")
    _write_json(artifact_root / "static-integrity-after.json", static_after)
    final: JsonObject = {
        **summary,
        "browser_exit_code": completed.returncode,
        "static_integrity_unchanged": True,
        "static_integrity": static_after,
    }
    if completed.returncode != 0:
        final["status"] = "FAIL"
    _write_json(artifact_root / "summary.json", final)
    return final


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify a content-bound published atlas in Brave via CDP."
    )
    parser.add_argument("--plan", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Execute the repository-owned browser verifier CLI."""
    try:
        plan = load_plan(_parser().parse_args(argv).plan)
        result = run_browser_verification(plan)
    except AtlasBrowserContractError as error:
        print(f"atlas browser verification refused: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
