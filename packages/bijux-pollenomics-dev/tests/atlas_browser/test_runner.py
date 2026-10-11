"""Tests for bounded atlas-browser process orchestration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.atlas_browser import runner
from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
    AtlasBrowserContractError,
    BrowserVerificationPlan,
)
from bijux_pollenomics_dev.ci.atlas_media.process_execution import CompletedCommand

from .fixtures import candidate, write_static_atlas


def _completed(command: tuple[str, ...], *, stdout: bytes = b"") -> CompletedCommand:
    return CompletedCommand(
        command=("/absolute/tool", *command[1:]),
        returncode=0,
        stdout=stdout,
        stderr=b"",
        duration_seconds=0.01,
        timed_out=False,
        termination="not_required",
    )


def test_git_uses_bounded_argv_execution(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    observed: dict[str, object] = {}

    def run(
        command: tuple[str, ...],
        *,
        cwd: Path,
        timeout_seconds: float,
        max_output_bytes: int = 0,
    ) -> CompletedCommand:
        observed.update(
            command=command,
            cwd=cwd,
            timeout_seconds=timeout_seconds,
            max_output_bytes=max_output_bytes,
        )
        return _completed(command, stdout=b"candidate\n")

    monkeypatch.setattr(runner, "run_bounded_argv", run)

    assert runner._git(tmp_path, "rev-parse", "HEAD") == "candidate"
    assert observed == {
        "command": ("git", "rev-parse", "HEAD"),
        "cwd": tmp_path,
        "timeout_seconds": 30,
        "max_output_bytes": 0,
    }


def test_browser_probe_uses_a_bounded_deadline(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    scope = write_static_atlas(tmp_path)
    browser = tmp_path / "brave"
    browser.write_text("browser", encoding="utf-8")
    plan = BrowserVerificationPlan(
        repository_root=tmp_path,
        artifact_root=tmp_path / "artifacts/browser",
        browser_binary=browser,
        candidate=candidate(),
        scopes=(scope,),
    )
    observed: dict[str, object] = {}
    audited_profiles: list[str | None] = []

    def audit(
        *_arguments: object, verification_profile: str | None = None
    ) -> dict[str, object]:
        audited_profiles.append(verification_profile)
        return {"status": "PASS"}

    def run(
        command: tuple[str, ...],
        *,
        cwd: Path,
        timeout_seconds: float,
        max_output_bytes: int,
    ) -> CompletedCommand:
        observed.update(
            command=command,
            cwd=cwd,
            timeout_seconds=timeout_seconds,
            max_output_bytes=max_output_bytes,
        )
        report = Path(command[-1]).with_name("browser-runtime-report.json")
        report.write_text(json.dumps({"probe": "bounded"}), encoding="utf-8")
        return _completed(command)

    monkeypatch.setattr(runner, "_require_candidate", lambda _plan: None)
    monkeypatch.setattr(runner, "audit_static_atlas", audit)
    monkeypatch.setattr(
        runner,
        "evaluate_browser_report",
        lambda *_arguments, **_keywords: {"status": "PASS"},
    )
    monkeypatch.setattr(runner, "run_bounded_argv", run)

    result = runner.run_browser_verification(plan)

    assert result["status"] == "PASS"
    assert audited_profiles == [plan.verification_profile, plan.verification_profile]
    assert observed["command"] == (
        "node",
        str(Path(runner.__file__).with_name("probe.mjs")),
        str(plan.artifact_root / "plan.json"),
    )
    assert observed["cwd"] == tmp_path
    assert observed["timeout_seconds"] == 45 * 32
    assert observed["max_output_bytes"] == 16 * 1024 * 1024


def test_browser_probe_refuses_a_timed_out_process(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    scope = write_static_atlas(tmp_path)
    browser = tmp_path / "brave"
    browser.write_text("browser", encoding="utf-8")
    plan = BrowserVerificationPlan(
        repository_root=tmp_path,
        artifact_root=tmp_path / "artifacts/browser",
        browser_binary=browser,
        candidate=candidate(),
        scopes=(scope,),
    )

    def run(*_arguments: object, **_keywords: object) -> CompletedCommand:
        return CompletedCommand(
            command=("/absolute/node",),
            returncode=-9,
            stdout=b"",
            stderr=b"",
            duration_seconds=300,
            timed_out=True,
            termination="killed_process_group",
        )

    monkeypatch.setattr(runner, "_require_candidate", lambda _plan: None)
    monkeypatch.setattr(
        runner,
        "audit_static_atlas",
        lambda *_arguments, **_keywords: {"status": "PASS"},
    )
    monkeypatch.setattr(runner, "run_bounded_argv", run)

    with pytest.raises(
        AtlasBrowserContractError, match="exceeded its bounded deadline"
    ):
        runner.run_browser_verification(plan)


@pytest.mark.parametrize("mutation", [None, "output", "verifier", "refused_read"])
def test_artifact_runner_binds_pre_post_and_actual_serving(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutation: str | None
) -> None:
    from bijux_pollenomics_dev.ci.atlas_browser import artifact_candidate as audit

    from .artifact_fixtures import artifact_plan

    plan = artifact_plan(tmp_path, monkeypatch)
    observed = audit.audit_artifact_candidate(plan)
    verifier = {"probe.mjs": "frozen"}
    monkeypatch.setattr(runner, "_verifier_files", lambda: dict(verifier))
    monkeypatch.setattr(
        runner, "audit_static_atlas", lambda *_args, **_keywords: {"status": "PASS"}
    )
    monkeypatch.setattr(
        runner, "evaluate_browser_report", lambda *_args, **_kwargs: {"status": "PASS"}
    )

    def run(command: tuple[str, ...], **_kwargs: object) -> CompletedCommand:
        refused = []
        if mutation == "output":
            (tmp_path / plan.scopes[0].document).write_text("changed")
        elif mutation == "verifier":
            verifier["probe.mjs"] = "changed"
        elif mutation == "refused_read":
            refused = [
                {"path": plan.scopes[0].document, "error": "altered and restored"}
            ]
        report = {
            "served_artifact_bytes": observed["files"],
            "refused_artifact_reads": refused,
        }
        (plan.artifact_root / "browser-runtime-report.json").write_text(
            json.dumps(report)
        )
        return _completed(command)

    monkeypatch.setattr(runner, "run_bounded_argv", run)
    if mutation is None:
        result = runner.run_browser_verification(plan)
        assert result["served_artifact_bytes_verified"] is True
        assert result["artifact_integrity_unchanged"] is True
        assert result["verifier_integrity_unchanged"] is True
    else:
        with pytest.raises(AtlasBrowserContractError):
            runner.run_browser_verification(plan)


def test_generated_report_runner_uses_receipt_bound_serving(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from bijux_pollenomics_dev.ci.atlas_browser import (
        generated_report_candidate as audit,
    )

    from .generated_report_fixtures import generated_report_plan

    plan = generated_report_plan(tmp_path)
    observed = audit.audit_generated_report_candidate(plan)
    monkeypatch.setattr(
        runner, "audit_static_atlas", lambda *_args, **_keywords: {"status": "PASS"}
    )
    monkeypatch.setattr(
        runner, "evaluate_browser_report", lambda *_args, **_kwargs: {"status": "PASS"}
    )

    def run(command: tuple[str, ...], **_kwargs: object) -> CompletedCommand:
        report = {
            "served_artifact_bytes": observed["files"],
            "refused_artifact_reads": [],
        }
        (plan.artifact_root / "browser-runtime-report.json").write_text(
            json.dumps(report)
        )
        return _completed(command)

    monkeypatch.setattr(runner, "run_bounded_argv", run)

    result = runner.run_browser_verification(plan)

    assert result["status"] == "PASS"
    assert result["served_artifact_bytes_verified"] is True
    assert result["artifact_integrity_unchanged"] is True
