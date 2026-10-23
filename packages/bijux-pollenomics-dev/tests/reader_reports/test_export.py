import ast
import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from bijux_pollenomics_dev.reader_reports import export
from bijux_pollenomics_dev.reader_reports.export import (
    ExportError,
    _command,
    _verify_revision_input,
)
from bijux_pollenomics_dev.reader_reports.source import file_sha256

ROOT = Path(__file__).resolve().parents[4]


def _retained_producer_paths() -> set[str]:
    manifest = json.loads((ROOT / "reports/exports/papers/manifest.json").read_text())
    return set(manifest["producer_sha256"])


def test_renderer_relative_imports_stay_inside_retained_producer_owner() -> None:
    """The established export owner covers every direct relative module import."""
    paths = _retained_producer_paths()
    names = {Path(path).stem for path in paths}
    assert len(names) == 8
    for path in paths:
        for node in ast.walk(ast.parse((ROOT / path).read_text())):
            if isinstance(node, ast.ImportFrom) and node.level:
                assert node.level == 1 and node.module is not None
                assert node.module.split(".")[0] in names


@pytest.mark.parametrize("change", ["none", "unrelated", "producer", "missing"])
def test_export_receipt_tracks_only_rendering_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    """Unrelated tools do not invalidate export; changed renderer inputs still do."""
    (tmp_path / ".git").mkdir()
    report = tmp_path / "reports/science/paper.md"
    report.parent.mkdir(parents=True)
    report.write_text("# Controlled paper\n")
    inventory = report.with_name("paper-accounts.csv")
    inventory.write_text("paper_id,canonical_report\npaper,reports/science/paper.md\n")
    paths = _retained_producer_paths()
    for relative in paths:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('"""Controlled rendering dependency."""\n')
    owner = next(tmp_path / path for path in paths if path.endswith("/export.py"))
    unrelated = owner.with_name("field_decisions.py")
    unrelated.write_text('"""Unrelated field review tool."""\n')
    renderer = owner.with_name("render.py")
    expected = {path: file_sha256(tmp_path / path) for path in paths}
    monkeypatch.setattr(export, "__file__", str(owner))
    monkeypatch.setattr(export, "_revision", lambda _: "a" * 40)
    monkeypatch.setattr(export, "_verify_revision_input", lambda *_: None)
    monkeypatch.setattr(export, "_versions", lambda _: {})

    def compile_paper(*_: object) -> dict[str, Any]:
        if change == "unrelated":
            unrelated.write_text('"""Changed unrelated field review tool."""\n')
        elif change == "producer":
            renderer.write_text('"""Changed rendering dependency."""\n')
        elif change == "missing":
            renderer.unlink()
        return {"paper_id": "paper"}

    monkeypatch.setattr(export, "_compile_paper", compile_paper)
    output = tmp_path / "artifacts/export"
    if change == "producer":
        with pytest.raises(ExportError, match="producer changed during export"):
            export.export_reports(tmp_path, inventory, output)
    elif change == "missing":
        with pytest.raises(FileNotFoundError):
            export.export_reports(tmp_path, inventory, output)
    else:
        receipt = export.export_reports(tmp_path, inventory, output)
        assert json.loads(receipt.read_text())["producer_sha256"] == expected


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
