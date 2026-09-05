"""Release-evidence manifest publication tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


from bijux_pollenomics.provenance import (
    ReleaseEvidenceError,
    validate_release_evidence_manifest,
)

from .support import (
    _arguments,
    _write,
)


def test_writer_emits_canonical_json_and_validates_immediately(tmp_path: Path) -> None:
    arguments = _arguments(tmp_path)
    manifest = _write(tmp_path, "artifacts/release/manifest.json", arguments)
    output = tmp_path / "artifacts/release/manifest.json"

    expected = (
        json.dumps(
            manifest,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    assert output.read_bytes() == expected
    assert not list(output.parent.glob("*.writing"))
    validate_release_evidence_manifest(tmp_path, manifest)


def test_identical_output_is_preserved_without_rewrite(tmp_path: Path) -> None:
    arguments = _arguments(tmp_path)
    output_path = "artifacts/release/manifest.json"
    first = _write(tmp_path, output_path, arguments)
    output = tmp_path / output_path
    before = output.stat()

    second = _write(tmp_path, output_path, arguments)
    after = output.stat()

    assert second == first
    assert (after.st_ino, after.st_mtime_ns) == (before.st_ino, before.st_mtime_ns)


def test_different_existing_output_is_refused_and_preserved(tmp_path: Path) -> None:
    arguments = _arguments(tmp_path)
    output_path = "artifacts/release/manifest.json"
    _write(tmp_path, output_path, arguments)
    output = tmp_path / output_path
    original = output.read_bytes()
    changed = dict(arguments)
    changed["dirty"] = True

    with pytest.raises(ReleaseEvidenceError, match="different bytes"):
        _write(tmp_path, output_path, changed)

    assert output.read_bytes() == original


@pytest.mark.parametrize(
    "output_path",
    ["release.json", "../release.json", "artifacts/../release.json"],
)
def test_writer_rejects_outputs_outside_artifacts(
    tmp_path: Path, output_path: str
) -> None:
    arguments = _arguments(tmp_path)

    with pytest.raises(ReleaseEvidenceError):
        _write(tmp_path, output_path, arguments)


def test_writer_rejects_symlinked_output_directory(tmp_path: Path) -> None:
    arguments = _arguments(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    release_directory = tmp_path / "artifacts/release"
    release_directory.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ReleaseEvidenceError, match="unsafe output directory"):
        _write(tmp_path, "artifacts/release/manifest.json", arguments)


def test_writer_refuses_output_parent_substitution_during_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments = _arguments(tmp_path)
    release = tmp_path / "artifacts/release"
    release.mkdir(parents=True)
    replacement = tmp_path / "replacement"
    replacement.mkdir()
    original_link = os.link
    substituted = False

    def substituting_link(
        source: str,
        destination: str,
        *,
        src_dir_fd: int | None = None,
        dst_dir_fd: int | None = None,
        follow_symlinks: bool = True,
    ) -> None:
        nonlocal substituted
        release.rename(tmp_path / "artifacts/release-original")
        release.symlink_to(replacement, target_is_directory=True)
        substituted = True
        original_link(
            source,
            destination,
            src_dir_fd=src_dir_fd,
            dst_dir_fd=dst_dir_fd,
            follow_symlinks=follow_symlinks,
        )

    monkeypatch.setattr(os, "link", substituting_link)

    with pytest.raises(ReleaseEvidenceError, match="output parent"):
        _write(tmp_path, "artifacts/release/manifest.json", arguments)

    assert substituted is True
    assert not (replacement / "manifest.json").exists()
