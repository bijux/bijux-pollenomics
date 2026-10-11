"""Attempt stale-run, forged-artifact and source-identity bypasses using a fake server."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
import zipfile

import pytest

from bijux_pollenomics_dev.ci.lra_reference import release_gate as gate
from bijux_pollenomics_dev.ci.lra_reference.contracts import ReferenceRefusal
from bijux_pollenomics_dev.ci.lra_reference.source_identity import SourceIdentity
from bijux_pollenomics_dev.ci.lra_reference.sources import (
    SOURCE_STATUS_ARGUMENTS,
    SOURCE_TREE_ARGUMENTS,
)

from .support import LOCK, REPOSITORY, SHA, bundle_fixture


class FakeReader:
    def __init__(self, root: Path, mutation: str | None = None):
        self.mutation = mutation
        self.collections = 0
        source = root / "source"
        bundle_fixture(source)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for path in source.rglob("*"):
                if path.is_file():
                    archive.writestr(
                        path.relative_to(source).as_posix(), path.read_bytes()
                    )
        self.data = buffer.getvalue()
        self.run: dict[str, Any] = {
            "id": 7,
            "run_attempt": 1,
            "head_sha": SHA,
            "head_repository": {"full_name": REPOSITORY},
            "path": ".github/workflows/verify.yml",
            "event": "push",
            "status": "completed",
            "conclusion": "success",
        }
        self.job = {
            "id": 12,
            "name": "lra-reference / lra-live-r-certification",
            "head_sha": SHA,
            "run_id": 7,
            "status": "completed",
            "conclusion": "success",
        }
        self.artifact = {
            "id": 9,
            "name": f"lra-live-r-{SHA}-attempt-1",
            "expired": False,
            "digest": "sha256:" + hashlib.sha256(self.data).hexdigest(),
            "workflow_run": {"id": 7, "head_sha": SHA},
        }

    def read(self, path: str) -> bytes:
        if "/runs?head_sha=" in path:
            self.collections += 1
            run = copy.deepcopy(self.run)
            if self.mutation == "pending":
                run["status"] = "in_progress"
                run["conclusion"] = None
            elif self.mutation == "failed":
                run["conclusion"] = "failure"
            elif self.mutation == "wrong_sha":
                run["head_sha"] = "a" * 40
            elif self.mutation == "wrong_repo":
                run["head_repository"] = {"full_name": "untrusted/fork"}
            elif self.mutation == "pull_request":
                run["event"] = "pull_request"
            elif self.mutation == "newer_run" and self.collections > 1:
                run["id"] = 8
            return json.dumps({"total_count": 1, "workflow_runs": [run]}).encode()
        if "/attempts/1/jobs?" in path:
            job = copy.deepcopy(self.job)
            if self.mutation == "job_skipped":
                job["conclusion"] = "skipped"
            elif self.mutation == "wrong_job":
                job["name"] = "unrelated"
            elif self.mutation == "wrong_job_sha":
                job["head_sha"] = "a" * 40
            return json.dumps({"total_count": 1, "jobs": [job]}).encode()
        if "/runs/7/artifacts?" in path:
            artifact = copy.deepcopy(self.artifact)
            if self.mutation == "expired":
                artifact["expired"] = True
            elif self.mutation == "wrong_artifact_sha":
                artifact["workflow_run"] = {"id": 7, "head_sha": "a" * 40}
            elif self.mutation == "wrong_attempt":
                artifact["name"] = f"lra-live-r-{SHA}-attempt-2"
            elif self.mutation == "wrong_digest":
                artifact["digest"] = "sha256:" + "a" * 64
            rows = (
                []
                if self.mutation == "missing_artifact"
                else [artifact, artifact]
                if self.mutation == "duplicate_artifact"
                else [artifact]
            )
            return json.dumps({"total_count": len(rows), "artifacts": rows}).encode()
        if path.endswith("/artifacts/9/zip"):
            return self.data
        if path.endswith("/artifacts/9"):
            artifact = copy.deepcopy(self.artifact)
            if self.mutation == "artifact_drift":
                artifact["expired"] = True
            return json.dumps(artifact).encode()
        if path.endswith("/runs/7"):
            run = copy.deepcopy(self.run)
            if self.mutation == "attempt_drift":
                run["run_attempt"] = 2
            return json.dumps(run).encode()
        raise AssertionError(path)


def fake_git(_repository: Path, *arguments: str) -> bytes:
    if arguments[0] == "status":
        return b""
    if arguments[0] == "show":
        return LOCK.read_bytes()
    return (("5" * 40 if arguments[-1].endswith("^{tree}") else SHA) + "\n").encode()


@pytest.mark.parametrize(
    "mutation",
    [
        None,
        "pending",
        "failed",
        "wrong_sha",
        "wrong_repo",
        "pull_request",
        "job_skipped",
        "wrong_job",
        "wrong_job_sha",
        "expired",
        "wrong_artifact_sha",
        "wrong_attempt",
        "wrong_digest",
        "missing_artifact",
        "duplicate_artifact",
        "artifact_drift",
        "attempt_drift",
        "newer_run",
    ],
)
def test_release_gate_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str | None
) -> None:
    monkeypatch.setattr(gate, "git_bytes", fake_git)
    monkeypatch.setattr(
        gate, "source_inventory", lambda _root: {"synthetic.py": "6" * 64}
    )
    monkeypatch.setattr(
        gate,
        "inspect_source_identity",
        lambda *_args: SourceIdentity(
            {"synthetic.py": "6" * 64},
            {"synthetic.py": "7" * 40},
            {},
            {"synthetic.py": "6" * 64},
        ),
    )
    reader = FakeReader(tmp_path, mutation)
    output = tmp_path / "output"
    if mutation is None:
        receipt = gate.verify_release(
            repository_root=tmp_path,
            repository=REPOSITORY,
            target_sha=SHA,
            release_tag="v0.2.0",
            output=output,
            reader=reader,
        )
        assert receipt["published"] is False
        assert receipt["run_id"] == 7
    else:
        with pytest.raises(ReferenceRefusal):
            gate.verify_release(
                repository_root=tmp_path,
                repository=REPOSITORY,
                target_sha=SHA,
                release_tag="v0.2.0",
                output=output,
                reader=reader,
            )


@pytest.mark.parametrize("failure", ["timeout", "unknown", "oversize"])
def test_git_failure_is_not_a_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    def run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        if failure == "timeout":
            raise subprocess.TimeoutExpired("git", 15)
        if failure == "oversize":
            kwargs["stdout"].write(b"x" * (2 * 1024 * 1024 + 1))
        return subprocess.CompletedProcess(args[0], 1 if failure == "unknown" else 0)

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(ReferenceRefusal):
        gate.git_bytes(tmp_path, "rev-parse", "--verify", "HEAD")


def test_stdlib_only_gate_import(tmp_path: Path) -> None:
    module = Path(gate.__file__).resolve().parents[3]
    code = 'import bijux_pollenomics_dev.ci.lra_reference.release_gate;import sys;assert not any(name == "bijux_pollenomics" or name.startswith(("bijux_pollenomics.", "numpy", "yaml")) for name in sys.modules)'
    result = subprocess.run(
        [sys.executable, "-S", "-c", code],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(module)},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "member", ["../escape", "/absolute", "nested/../escape", "a\\b"]
)
def test_zip_traversal_is_refused(tmp_path: Path, member: str) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(member, b"x")
    with pytest.raises(ReferenceRefusal):
        gate._extract_archive(buffer.getvalue(), tmp_path / "output")
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "dirty",
    [
        " M packages/bijux-pollenomics-dev/pyproject.toml\n",
        "?? packages/bijux-pollenomics-dev/src/untracked.py\n",
    ],
)
def test_relevant_dirty_checkout_refuses_before_remote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dirty: str
) -> None:
    def dirty_git(repository: Path, *arguments: str) -> bytes:
        if arguments[0] == "status":
            assert "packages/bijux-pollenomics-dev/pyproject.toml" in arguments
            assert "packages/bijux-pollenomics-dev/src" in arguments
            assert "--untracked-files=all" in arguments
            assert "docs" not in arguments
            return dirty.encode()
        return fake_git(repository, *arguments)

    monkeypatch.setattr(gate, "git_bytes", dirty_git)
    reader = FakeReader(tmp_path)
    with pytest.raises(ReferenceRefusal, match="uncommitted or untracked"):
        gate.verify_release(
            repository_root=tmp_path,
            repository=REPOSITORY,
            target_sha=SHA,
            release_tag="v0.2.0",
            output=tmp_path / "output",
            reader=reader,
        )
    assert reader.collections == 0


def test_real_query_boundary_accepts_only_exact_status_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        calls.append(args[0])
        return subprocess.CompletedProcess(args[0], 0)

    monkeypatch.setattr(subprocess, "run", run)
    gate.require_clean_checkout(tmp_path)
    assert calls == [["git", *SOURCE_STATUS_ARGUMENTS]]
    with pytest.raises(ReferenceRefusal, match="Unsupported"):
        gate.git_bytes(tmp_path, "status", "--porcelain")


def test_real_query_boundary_accepts_only_exact_tree_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        calls.append(args[0])
        return subprocess.CompletedProcess(args[0], 0)

    monkeypatch.setattr(subprocess, "run", run)
    gate.git_bytes(tmp_path, *SOURCE_TREE_ARGUMENTS)
    assert calls == [["git", *SOURCE_TREE_ARGUMENTS]]
    with pytest.raises(ReferenceRefusal, match="Unsupported"):
        gate.git_bytes(tmp_path, "ls-tree", "-rz", "HEAD")
