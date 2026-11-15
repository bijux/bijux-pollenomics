"""A source archive is replaced only by a complete, reconciled candidate."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.neotoma import archive
from bijux_pollenomics.collection.sources.neotoma.collection import (
    write_neotoma_download_archive,
)
from bijux_pollenomics.core.files import write_json


def _rows(identifiers: list[int]) -> list[dict[str, object]]:
    return [{"site": {"dataset": {"datasetid": identity}}} for identity in identifiers]


def _write(raw: Path, identifiers: list[int]) -> Path:
    return write_neotoma_download_archive(
        raw,
        requested_dataset_ids=identifiers,
        downloaded_dataset_ids=identifiers,
        download_rows=_rows(identifiers),
        rows_per_part=1,
    )


def _bodies(directory: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}


def test_smaller_recollection_replaces_the_complete_owned_archive(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "raw"
    manifest = _write(raw, [201, 202, 203])
    assert len(list(manifest.parent.glob("part-*.json"))) == 3
    assert _write(raw, [201]) == manifest
    assert set(_bodies(manifest.parent)) == {"manifest.json", "part-001.json"}


def test_failed_part_write_preserves_the_published_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = tmp_path / "raw"
    manifest = _write(raw, [201, 202, 203])
    original = _bodies(manifest.parent)
    writer = write_json
    calls = 0

    def fail_during_publication(path: Path, value: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("source archive disk write failed")
        writer(path, value)

    monkeypatch.setattr(archive, "write_json", fail_during_publication)
    with pytest.raises(OSError, match="disk write failed"):
        _write(raw, [201, 202])
    assert _bodies(manifest.parent) == original


def test_archive_refuses_a_declared_download_missing_from_rows(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Neotoma"):
        write_neotoma_download_archive(
            tmp_path / "raw",
            requested_dataset_ids=[201, 202],
            downloaded_dataset_ids=[201, 202],
            download_rows=_rows([201]),
            rows_per_part=1,
        )
    assert not list(tmp_path.rglob("manifest.json"))


def test_archive_refuses_a_declared_download_not_matching_actual_rows(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="Neotoma"):
        write_neotoma_download_archive(
            tmp_path / "raw",
            requested_dataset_ids=[201],
            downloaded_dataset_ids=[202],
            download_rows=_rows([201]),
            rows_per_part=1,
        )
    assert not list(tmp_path.rglob("manifest.json"))


def test_archive_preserves_unowned_files_in_existing_output(tmp_path: Path) -> None:
    manifest = _write(tmp_path / "raw", [201])
    (manifest.parent / "research-notes.txt").write_text("unrelated user notes")
    original = _bodies(manifest.parent)
    with pytest.raises(ValueError, match="unowned"):
        _write(tmp_path / "raw", [201, 202])
    assert _bodies(manifest.parent) == original


def test_archive_refuses_a_symlinked_destination(tmp_path: Path) -> None:
    source_manifest = _write(tmp_path / "source", [201])
    raw = tmp_path / "raw"
    raw.mkdir()
    destination = raw / source_manifest.parent.name
    destination.symlink_to(source_manifest.parent, target_is_directory=True)
    original = _bodies(source_manifest.parent)
    with pytest.raises(ValueError, match="symlink"):
        _write(raw, [202])
    assert destination.is_symlink()
    assert _bodies(source_manifest.parent) == original


def test_archive_refuses_foreign_json_with_matching_member_names(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "raw"
    destination = raw / "neotoma_pollen_dataset_downloads"
    destination.mkdir(parents=True)
    (destination / "manifest.json").write_text('{"owner":"unrelated research"}')
    (destination / "part-001.json").write_text('{"unpublished":"native user work"}')
    original = _bodies(destination)
    with pytest.raises(ValueError, match="unowned"):
        _write(raw, [201])
    assert _bodies(destination) == original


def test_archive_refuses_symlinked_output_ancestry(tmp_path: Path) -> None:
    physical = tmp_path / "physical-raw"
    manifest = _write(physical, [201])
    alias = tmp_path / "raw-alias"
    alias.symlink_to(physical, target_is_directory=True)
    original = _bodies(manifest.parent)
    with pytest.raises(ValueError, match="symlink"):
        _write(alias, [202])
    assert _bodies(manifest.parent) == original
