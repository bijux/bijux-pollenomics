"""Preserve competing staging owners while publishing complete rebuild manifests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import IO, Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    ReportRebuildError,
    atomic_write_json,
)


def test_manifest_is_complete_before_existing_destination_is_replaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "manifest.json"
    destination.write_bytes(b"previous manifest")
    original = Path.replace

    def replace(source: Path, target: Path) -> Path:
        assert target.read_bytes() == b"previous manifest"
        assert source.read_bytes() == b'{\n  "value": 1\n}\n'
        return original(source, target)

    monkeypatch.setattr(Path, "replace", replace)
    atomic_write_json(destination, {"value": 1})
    assert destination.read_bytes() == b'{\n  "value": 1\n}\n'
    assert not (tmp_path / ".manifest.json.writing").exists()


def test_competing_stage_created_at_open_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "manifest.json"
    staging = tmp_path / ".manifest.json.writing"
    original = Path.open

    def open_file(path: Path, mode: str = "r", *args: Any, **kwargs: Any) -> IO[Any]:
        if path == staging and mode in {"xb", "w"}:
            with original(path, "wb") as stream:
                stream.write(b"competing owner")
        return original(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", open_file)
    with pytest.raises(ReportRebuildError, match="staging path already exists"):
        atomic_write_json(destination, {"value": 1})
    assert staging.read_bytes() == b"competing owner"
    assert not destination.exists()


@pytest.mark.parametrize("replace_inode", [False, True])
def test_changed_staging_identity_or_bytes_refuse_and_preserve_rival(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, replace_inode: bool
) -> None:
    destination = tmp_path / "manifest.json"
    destination.write_bytes(b"previous manifest")
    staging = tmp_path / ".manifest.json.writing"

    def fsync(_descriptor: int) -> None:
        if replace_inode:
            staging.rename(tmp_path / "owned-stage.json")
        staging.write_bytes(b"competing owner")

    monkeypatch.setattr(os, "fsync", fsync)
    with pytest.raises(ReportRebuildError, match="staging identity changed"):
        atomic_write_json(destination, {"value": 1})
    assert destination.read_bytes() == b"previous manifest"
    assert staging.read_bytes() == b"competing owner"


def test_failed_staging_flush_preserves_destination_and_removes_owned_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "manifest.json"
    destination.write_bytes(b"previous manifest")

    def fsync(_descriptor: int) -> None:
        raise OSError("flush refused")

    monkeypatch.setattr(os, "fsync", fsync)
    with pytest.raises(OSError, match="flush refused"):
        atomic_write_json(destination, {"value": 1})
    assert destination.read_bytes() == b"previous manifest"
    assert not (tmp_path / ".manifest.json.writing").exists()
