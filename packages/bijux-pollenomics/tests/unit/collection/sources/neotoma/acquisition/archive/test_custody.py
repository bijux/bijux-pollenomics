"""Standalone archives never write or clean a foreign substituted candidate."""

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import archive
from bijux_pollenomics.core.files import write_json

from .test_publication import _write


def test_foreign_candidate_is_neither_written_nor_deleted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = write_json
    foreign: list[Path] = []

    def substituted(path: Path, value: Any, **kwargs: Any) -> None:
        writer = kwargs.get("writer")
        root = path.parent if writer is None else writer.root
        root.rename(root.with_name("displaced-owned"))
        root.mkdir()
        (root / "foreign.txt").write_text("preserve foreign")
        foreign.append(root)
        original(path, value, **kwargs)
        raise OSError("stop after attempted write")

    monkeypatch.setattr(archive, "write_json", substituted)
    with pytest.raises((ValueError, OSError)):
        _write(tmp_path / "raw", [201])
    assert len(foreign) == 1
    assert (foreign[0] / "foreign.txt").read_text() == "preserve foreign"
    assert {p.name for p in foreign[0].iterdir()} == {"foreign.txt"}


@pytest.mark.parametrize("destination_volume", [False, True])
def test_repeated_replacement_retains_prior_with_bounded_recovery_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, destination_volume: bool
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.publication import replacement

    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "pyproject.toml").write_text('[project]\nname="bijux-pollenomics"\n')
    monkeypatch.setattr(replacement, "find_repository_root", lambda _: repository)
    if destination_volume:
        monkeypatch.setattr(replacement, "_same_filesystem", lambda *args: False)
    raw = repository / "data" / "raw"
    manifest = _write(raw, [201, 202])
    _write(raw, [201])
    _write(raw, [201, 203])
    assert json.loads(manifest.read_text())["downloaded_dataset_ids"] == [201, 203]
    receipts = repository / "artifacts/neotoma-publication"
    published = list(receipts.glob("*/receipts/published.json"))
    assert len(published) == 3
    assert (
        sum(json.loads(path.read_text())["retained_predecessor"] for path in published)
        == 2
    )
    for path in published:
        record = json.loads(path.read_text())
        recovery = Path(record["recovery_root"])
        assert record["destination_volume_recovery"] is destination_volume
        assert recovery.parent == (raw if destination_volume else receipts)
    assert not (raw / f".{manifest.parent.name}.recovery").exists()


def test_installed_source_location_does_not_select_archive_storage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.publication import replacement
    from bijux_pollenomics.core.repository import (
        RepositoryRootNotFoundError,
        find_repository_root,
    )

    installed = tmp_path / "installed" / "replacement.py"
    installed.parent.mkdir()
    installed.write_text('"""Installed module fixture."""\n')
    with pytest.raises(RepositoryRootNotFoundError):
        find_repository_root(installed)
    monkeypatch.setattr(replacement, "__file__", str(installed))
    manifest = _write(tmp_path / "raw", [201])
    assert manifest.is_file()


@pytest.mark.parametrize("marker", ["unrelated", "malformed", "partial"])
def test_nearest_unowned_project_uses_private_destination_recovery(
    tmp_path: Path, marker: str
) -> None:
    import json

    project = tmp_path / "unowned"
    project.mkdir()
    if marker == "partial":
        (project / "packages/bijux-pollenomics").mkdir(parents=True)
    else:
        (project / "pyproject.toml").write_text(
            '[project]\nname="unrelated-research"\n'
            if marker == "unrelated"
            else "[broken"
        )
    raw = project / "data" / "raw"
    manifest = _write(raw, [201])
    assert manifest.is_file()
    recoveries = list(raw.glob(".neotoma-recovery-*"))
    assert len(recoveries) == 1
    receipt = json.loads((recoveries[0] / "receipts/published.json").read_text())
    assert receipt["owning_repository"] is None
    assert receipt["recovery_root"] == str(recoveries[0])
    assert not (project / "artifacts").exists()


def test_existing_archive_manifest_is_bounded_before_initial_decode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.production import validation

    raw = tmp_path / "raw"
    destination = raw / "neotoma_pollen_dataset_downloads"
    destination.mkdir(parents=True)
    path = destination / "manifest.json"
    before = b"{}" + b" " * 32
    path.write_bytes(before)
    monkeypatch.setattr(archive, "MANIFEST_MAX_BYTES", 2, raising=False)
    monkeypatch.setattr(
        validation,
        "json_object",
        lambda *args: pytest.fail("Decoded before manifest bound"),
    )
    with pytest.raises(ValueError, match="unowned|invalid"):
        _write(raw, [201])
    assert path.read_bytes() == before


def test_refusal_receipt_fault_preserves_original_producer_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "standalone"
    project.mkdir()
    (project / "pyproject.toml").write_text('[project]\nname="standalone-user"\n')
    raw = project / "raw"
    manifest = _write(raw, [201])
    before = {p.name: p.read_bytes() for p in manifest.parent.iterdir()}
    foreign: list[Path] = []

    def refused(path: Path, payload: Any, **kwargs: Any) -> None:
        writer = kwargs["writer"]
        receipts = writer.root.parent / "receipts"
        receipts.rename(receipts.with_name("displaced-receipts"))
        receipts.mkdir()
        (receipts / "foreign.txt").write_text("user metadata")
        foreign.append(receipts)
        raise OSError("primary producer failure")

    monkeypatch.setattr(archive, "write_json", refused)
    with pytest.raises(OSError, match="primary producer failure") as caught:
        _write(raw, [201, 202])
    assert any("recovery" in note for note in caught.value.__notes__)
    assert {p.name: p.read_bytes() for p in manifest.parent.iterdir()} == before
    assert (foreign[0] / "foreign.txt").read_text() == "user metadata"
