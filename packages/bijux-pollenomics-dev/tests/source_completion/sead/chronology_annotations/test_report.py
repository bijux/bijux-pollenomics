"""Keep private native witnesses outside the configured public report tree."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.sead.chronology_annotations import (
    cli as report,
)


def prepare(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, arguments: list[str]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    (tmp_path / "artifacts").mkdir()
    aggregate = {"source_id": "synthetic", "scientific_admission": False}
    witness = [{"raw_annotations": {"unknown": None, "value": 1.5}}]

    def build(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        assert root == tmp_path
        return aggregate, witness

    monkeypatch.setattr(report, "build", build)
    monkeypatch.setattr(
        "sys.argv", ["report", "--repository", str(tmp_path), *arguments]
    )
    return aggregate, witness


def test_configured_private_witness_is_not_a_public_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "artifacts/public"
    private = tmp_path / "artifacts/private"
    aggregate, witness = prepare(
        tmp_path,
        monkeypatch,
        ["--output", str(output), "--retained-artifacts-root", str(private)],
    )
    assert report.main() == 0
    assert [p.name for p in output.iterdir()] == ["report.json"]
    assert json.loads((output / "report.json").read_bytes()) == aggregate
    assert (
        json.loads((private / "claim-annotation-witness.json").read_bytes()) == witness
    )


def test_original_two_product_capture_remains_supported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "artifacts/capture"
    aggregate, witness = prepare(tmp_path, monkeypatch, ["--output", str(output)])
    assert report.main() == 0
    assert json.loads((output / "report.json").read_bytes()) == aggregate
    assert (
        json.loads((output / "claim-annotation-witness.json").read_bytes()) == witness
    )


@pytest.mark.parametrize("target", ["public", "public/private", "outside"])
def test_private_output_overlap_or_escape_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    output = tmp_path / "artifacts/public"
    private = tmp_path / "artifacts" / target
    if target == "outside":
        private = tmp_path / "outside"
    prepare(
        tmp_path,
        monkeypatch,
        ["--output", str(output), "--retained-artifacts-root", str(private)],
    )
    with pytest.raises((ValueError, ReportRebuildError, FileNotFoundError)):
        report.main()
    assert not output.exists()
