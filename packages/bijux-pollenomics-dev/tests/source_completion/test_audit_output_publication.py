"""Audit output failures preserve competing entries and remove owned partial sets."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pytest

from bijux_pollenomics_dev.source_completion import __main__ as audit_cli
from bijux_pollenomics_dev.source_completion.publication import json_outputs


def test_complete_output_set_matches_serialized_payloads(tmp_path: Path) -> None:
    """Each result is a complete regular file and staging names disappear."""
    audit, summary = tmp_path / "audit.json", tmp_path / "summary.json"
    json_outputs.publish_json_outputs([(audit, {"rows": [1]}), (summary, {"count": 1})])
    assert audit.read_bytes() == b'{\n  "rows": [\n    1\n  ]\n}\n'
    assert summary.read_bytes() == b'{\n  "count": 1\n}\n'
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "audit.json",
        "summary.json",
    ]


@pytest.mark.parametrize("kind", ["file", "directory", "symlink"])
def test_existing_destination_is_preserved(tmp_path: Path, kind: str) -> None:
    """An occupied destination never becomes a replacement output."""
    output = tmp_path / "audit.json"
    if kind == "file":
        output.write_bytes(b"competitor")
    elif kind == "directory":
        output.mkdir()
    else:
        output.symlink_to("missing-competitor")
    before = output.lstat()
    with pytest.raises(FileExistsError):
        json_outputs.publish_json_outputs([(output, {"rows": []})])
    assert (output.lstat().st_dev, output.lstat().st_ino) == (
        before.st_dev,
        before.st_ino,
    )
    assert list(tmp_path.iterdir()) == [output]
    if kind == "file":
        assert output.read_bytes() == b"competitor"
    elif kind == "symlink":
        assert output.readlink() == Path("missing-competitor")


@pytest.mark.parametrize("mutation", ["inode", "payload", "symlink"])
def test_stage_substitution_is_refused_without_foreign_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    """The fsync boundary cannot replace content selected for publication."""
    output = tmp_path / "audit.json"
    original_fsync = os.fsync
    stages: list[Path] = []

    def substitute(descriptor: int) -> None:
        original_fsync(descriptor)
        stage = next(tmp_path.glob(".audit.json.pending-*"))
        stages.append(stage)
        if mutation == "payload":
            stage.write_bytes(b"mutated")
        else:
            stage.unlink()
            if mutation == "inode":
                stage.write_bytes(b"competitor")
            else:
                stage.symlink_to("competitor-target")

    monkeypatch.setattr(os, "fsync", substitute)
    with pytest.raises(ValueError, match="JSON publication (inode|payload) changed"):
        json_outputs.publish_json_outputs([(output, {"rows": []})])
    assert not output.exists()
    if mutation == "payload":
        assert not stages[0].exists()
    elif mutation == "inode":
        assert stages[0].read_bytes() == b"competitor"
    else:
        assert stages[0].readlink() == Path("competitor-target")


@pytest.mark.parametrize("mutation", ["inode", "payload"])
def test_link_boundary_substitution_never_returns_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    """A mutation after stage validation is detected against the published link."""
    original_link = os.link
    output = tmp_path / "audit.json"

    def substitute(source: Path, target: Path, *, follow_symlinks: bool) -> None:
        if mutation == "inode":
            source.unlink()
            source.write_bytes(b"competitor")
        else:
            source.write_bytes(b"mutated")
        original_link(source, target, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(os, "link", substitute)
    with pytest.raises(ValueError, match="JSON publication (inode|payload) changed"):
        json_outputs.publish_json_outputs([(output, {"rows": []})])
    if mutation == "inode":
        assert output.read_bytes() == b"competitor"
        assert (
            next(tmp_path.glob(".audit.json.pending-*")).read_bytes() == b"competitor"
        )
    else:
        assert list(tmp_path.iterdir()) == []


def test_summary_link_failure_rolls_back_owned_audit(tmp_path: Path) -> None:
    """A conflicting summary does not leave a newly written audit behind."""
    audit, summary = tmp_path / "audit.json", tmp_path / "summary.json"
    summary.write_bytes(b"competitor-summary")
    with pytest.raises(FileExistsError):
        json_outputs.publish_json_outputs(
            [(audit, {"rows": []}), (summary, {"count": 0})]
        )
    assert not audit.exists()
    assert summary.read_bytes() == b"competitor-summary"
    assert list(tmp_path.iterdir()) == [summary]


def test_rollback_preserves_replaced_audit_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failure of the next link cannot delete a competitor's replacement audit."""
    original_link = os.link
    audit, summary = tmp_path / "audit.json", tmp_path / "summary.json"
    owned_audit = tmp_path / "retained-owned-audit.json"

    def substitute(source: Path, target: Path, *, follow_symlinks: bool) -> None:
        if target == summary:
            audit.rename(owned_audit)
            audit.write_bytes(b"competitor-audit")
            summary.write_bytes(b"competitor-summary")
        original_link(source, target, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(os, "link", substitute)
    with pytest.raises(FileExistsError):
        json_outputs.publish_json_outputs(
            [(audit, {"rows": []}), (summary, {"count": 0})]
        )
    assert audit.read_bytes() == b"competitor-audit"
    assert summary.read_bytes() == b"competitor-summary"
    assert json.loads(owned_audit.read_bytes()) == {"rows": []}
    assert not list(tmp_path.glob(".*.pending-*"))


def test_successful_summary_link_checks_earlier_audit_ownership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A later successful link cannot hide substitution of an earlier output."""
    original_link = os.link
    audit, summary = tmp_path / "audit.json", tmp_path / "summary.json"

    def substitute(source: Path, target: Path, *, follow_symlinks: bool) -> None:
        if target == summary:
            audit.unlink()
            audit.write_bytes(b"competitor-audit")
        original_link(source, target, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(os, "link", substitute)
    with pytest.raises(ValueError, match="JSON publication inode changed"):
        json_outputs.publish_json_outputs(
            [(audit, {"rows": []}), (summary, {"count": 0})]
        )
    assert audit.read_bytes() == b"competitor-audit"
    assert not summary.exists()
    assert list(tmp_path.iterdir()) == [audit]


def test_summary_staging_failure_creates_no_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second staging failure leaves no destination and no owned staging file."""
    original_fsync = os.fsync
    calls = 0

    def fail_summary(descriptor: int) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic fsync failure")
        original_fsync(descriptor)

    monkeypatch.setattr(os, "fsync", fail_summary)
    with pytest.raises(OSError, match="synthetic fsync failure"):
        json_outputs.publish_json_outputs(
            [
                (tmp_path / "audit.json", {"rows": []}),
                (tmp_path / "summary.json", {"count": 0}),
            ]
        )
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("invalid", [object(), float("nan")])
def test_summary_serialization_failure_creates_no_output(
    tmp_path: Path, invalid: object
) -> None:
    """All payloads serialize before staging and linking the first result."""
    with pytest.raises((TypeError, ValueError)):
        json_outputs.publish_json_outputs(
            [
                (tmp_path / "audit.json", {"rows": []}),
                (tmp_path / "summary.json", {"bad": invalid}),
            ]
        )
    assert list(tmp_path.iterdir()) == []


def test_repeated_output_name_rolls_back_first_link(tmp_path: Path) -> None:
    """One path cannot receive two members of the same output set."""
    output = tmp_path / "audit.json"
    with pytest.raises(FileExistsError):
        json_outputs.publish_json_outputs(
            [(output, {"rows": []}), (output, {"count": 0})]
        )
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("failure", ["summary-build", "summary-link"])
def test_cli_summary_failure_leaves_no_audit_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    """The command prepares its optional summary before publishing its output set."""
    audit, summary = tmp_path / "audit.json", tmp_path / "summary.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "audit",
            "--root",
            str(tmp_path),
            "--output",
            str(audit),
            "--summary-output",
            str(summary),
        ],
    )
    monkeypatch.setattr(
        audit_cli,
        "build_source_audit",
        lambda _: {
            "source_count": 0,
            "country_cell_count": 0,
            "accounting_checks_pass": True,
        },
    )
    monkeypatch.setattr(audit_cli, "find_hyde_candidates", lambda _: [])

    def summarize(_: dict[str, object]) -> dict[str, object]:
        if failure == "summary-build":
            raise ValueError("synthetic summary failure")
        return {"source_count": 0}

    monkeypatch.setattr(audit_cli, "summarize_source_audit", summarize)
    if failure == "summary-link":
        summary.write_bytes(b"competitor-summary")
    with pytest.raises((ValueError, FileExistsError)):
        audit_cli.main()
    assert not audit.exists()
    assert not list(tmp_path.glob(".*.pending-*"))
    if failure == "summary-link":
        assert summary.read_bytes() == b"competitor-summary"
