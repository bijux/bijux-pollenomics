from pathlib import Path
import subprocess

import pytest

from bijux_pollenomics_dev.reader_reports.export import (
    ExportError,
    _command,
    _verify_revision_input,
)
from bijux_pollenomics_dev.reader_reports.source import file_sha256


def test_mutated_canonical_report_cannot_claim_committed_source_identity(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    report = root / "paper.md"
    report.write_text("# Committed source\n", encoding="utf-8")
    for args in (
        ["init", "--quiet"],
        ["add", "paper.md"],
        [
            "-c",
            "user.name=Bijux",
            "-c",
            "user.email=checks@bijux.io",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--quiet",
            "-m",
            "docs(science): bind source identity",
        ],
    ):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    _verify_revision_input(root, revision, report, file_sha256(report))
    report.write_text("# Changed source\n", encoding="utf-8")
    with pytest.raises(ExportError, match="source does not match"):
        _verify_revision_input(root, revision, report, file_sha256(report))


def test_compile_timeout_preserves_a_recovery_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def timed_out(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired("latexmk", 180)

    monkeypatch.setattr(subprocess, "run", timed_out)
    prefix = tmp_path / "compiler"
    with pytest.raises(ExportError, match="timed out after 180s"):
        _command(
            ["latexmk", "report.tex"],
            cwd=tmp_path,
            environment={},
            timeout=180,
            log_prefix=prefix,
        )
    assert "timeout_seconds: 180" in prefix.with_suffix(".timeout.log").read_text()
