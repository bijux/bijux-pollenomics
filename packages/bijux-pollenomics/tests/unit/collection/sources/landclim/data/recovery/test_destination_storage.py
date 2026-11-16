"""Installed collection recovery follows its destination and retains failures."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.landclim.raw_assets import transaction
from bijux_pollenomics.core.filesystem import recovery_storage


def standalone(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text('[project]\nname="synthetic-collection"\n')


def workspace(root: Path) -> None:
    package = root / "packages/bijux-pollenomics"
    source = package / "src/bijux_pollenomics"
    source.mkdir(parents=True)
    (source / "__init__.py").write_text('"""Synthetic host marker."""\n')
    (root / "pyproject.toml").write_text(
        '[tool.bijux_pollenomics]\nrepository="bijux-pollenomics"\n'
        '[tool.uv.workspace]\nmembers=["packages/*"]\n'
    )
    (package / "pyproject.toml").write_text('[project]\nname="bijux-pollenomics"\n')


def write_candidate(root: Path, value: bytes) -> None:
    (root / "result.bin").write_bytes(value)


def test_installed_location_and_cwd_never_select_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    standalone(tmp_path)
    destination = tmp_path / "collection"
    destination.mkdir()
    (destination / "user.txt").write_bytes(b"user work")
    installed = tmp_path / "site-packages/landclim/transaction.py"
    installed.parent.mkdir(parents=True)
    installed.write_text('"""Nonexecuted installed-path marker."""\n')
    monkeypatch.setattr(transaction, "__file__", str(installed))
    storage = recovery_storage.resolve_publication_workspace_parent(
        destination, namespace="landclim-collection"
    )
    for name in ("caller-a", "caller-b"):
        caller = tmp_path / name
        caller.mkdir()
        monkeypatch.chdir(caller)
        value = name.encode()
        transaction.transact(
            destination,
            lambda candidate, value=value: write_candidate(candidate, value),
        )
        assert list(caller.iterdir()) == []
    records = list(storage.glob("capture-*/published.json"))
    assert len(records) == 2
    assert all(not path.is_relative_to(destination) for path in records)
    assert (destination / "result.bin").read_bytes() == b"caller-b"
    assert (destination / "user.txt").read_bytes() == b"user work"
    assert any(
        (path.parent / "prior/result.bin").read_bytes() == b"caller-a"
        for path in records
        if (path.parent / "prior/result.bin").exists()
    )


@pytest.mark.parametrize("nested", [False, True])
def test_recovery_uses_only_the_destination_project(
    tmp_path: Path, nested: bool
) -> None:
    owner = tmp_path / "destination-workspace"
    workspace(owner)
    root = owner / "packages/bijux-pollenomics/nested" if nested else owner
    if nested:
        root.mkdir()
        (root / ".git").mkdir()
    destination = root / "collection"
    transaction.transact(
        destination, lambda candidate: write_candidate(candidate, b"owned")
    )
    storage = recovery_storage.resolve_publication_workspace_parent(
        destination, namespace="landclim-collection"
    )
    assert len(list(storage.glob("capture-*/published.json"))) == 1
    assert (
        storage.is_relative_to(root / ".bijux-publication-recovery")
        if nested
        else storage.is_relative_to(owner / "artifacts/landclim-collection")
    )
    assert not storage.is_relative_to(destination)


@pytest.mark.parametrize("prior", [False, True])
def test_receipt_failure_never_masks_original_publication_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prior: bool
) -> None:
    standalone(tmp_path)
    destination = tmp_path / "collection"
    if prior:
        destination.mkdir()
        (destination / "result.bin").write_bytes(b"prior")
    primary = OSError("published receipt failed")
    secondary = PermissionError("refusal receipt failed")
    original = transaction._receipt

    def record(run, status, **fields):  # type: ignore[no-untyped-def]
        if status == "published":
            raise primary
        if status == "refused":
            raise secondary
        original(run, status, **fields)

    monkeypatch.setattr(transaction, "_receipt", record)
    with pytest.raises(OSError) as caught:
        transaction.transact(
            destination, lambda candidate: write_candidate(candidate, b"new")
        )
    assert caught.value is primary
    assert any("PermissionError" in note for note in primary.__notes__)
    storage = recovery_storage.resolve_publication_workspace_parent(
        destination, namespace="landclim-collection"
    )
    runs = list(storage.glob("capture-*"))
    assert len(runs) == 1
    assert str(runs[0]) in " ".join(primary.__notes__)
    assert (runs[0] / "refused-publication/result.bin").read_bytes() == b"new"
    if prior:
        assert (destination / "result.bin").read_bytes() == b"prior"
    else:
        assert not destination.exists()


def test_failed_producer_and_foreign_storage_keep_primary_and_user_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    standalone(tmp_path)
    destination = tmp_path / "collection"
    destination.mkdir()
    (destination / "result.bin").write_bytes(b"prior")
    primary = RuntimeError("producer failed after source replacement")
    foreign = []

    def fail(candidate: Path) -> None:
        run = candidate.parent
        run.rename(run.with_name("displaced-owned-run"))
        run.mkdir()
        (run / "foreign.txt").write_bytes(b"foreign owner")
        foreign.append(run)
        raise primary

    with pytest.raises(RuntimeError) as caught:
        transaction.transact(destination, fail)
    assert caught.value is primary
    assert (destination / "result.bin").read_bytes() == b"prior"
    assert (foreign[0] / "foreign.txt").read_bytes() == b"foreign owner"
    assert {path.name for path in foreign[0].iterdir()} == {"foreign.txt"}


@pytest.mark.parametrize("foreign", ["alias", "inside_publication"])
def test_unsafe_resolver_output_refuses_before_producer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, foreign: str
) -> None:
    standalone(tmp_path)
    destination = tmp_path / "collection"
    destination.mkdir()
    actual = tmp_path / "foreign-owner"
    actual.mkdir()
    (actual / "notes.txt").write_bytes(b"foreign")
    alias = tmp_path / "storage-alias"
    alias.symlink_to(actual, target_is_directory=True)
    chosen = alias if foreign == "alias" else destination / "private"
    monkeypatch.setattr(
        recovery_storage,
        "resolve_publication_workspace_parent",
        lambda *args, **kwargs: chosen,
    )
    called = []
    with pytest.raises((OSError, ValueError)):
        transaction.transact(destination, lambda candidate: called.append(candidate))
    assert called == []
    assert (actual / "notes.txt").read_bytes() == b"foreign"


def test_declared_collection_scope_must_contain_destination(tmp_path: Path) -> None:
    standalone(tmp_path)
    called = []
    with pytest.raises(ValueError, match="publication root"):
        transaction.transact(
            tmp_path / "raw",
            lambda candidate: called.append(candidate),
            publication_root=tmp_path / "unrelated",
        )
    assert called == []


def test_actual_recovery_descriptor_device_is_rechecked_before_producer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    standalone(tmp_path)
    destination = tmp_path / "collection"
    storage = recovery_storage.resolve_publication_workspace_parent(
        destination, namespace="landclim-collection"
    )
    original_directory, original_stat = transaction._Directory, os.fstat
    descriptors, events, called = set(), [], []

    def directory(path, *args, **kwargs):  # type: ignore[no-untyped-def]
        result = original_directory(path, *args, **kwargs)
        if Path(path) == storage:
            descriptors.add(result.fd)
        return result

    def device(fd):  # type: ignore[no-untyped-def]
        result = original_stat(fd)
        if fd in descriptors:
            fields = list(result)
            fields[2] += 1
            events.append(fd)
            return os.stat_result(fields)
        return result

    monkeypatch.setattr(transaction, "_Directory", directory)
    monkeypatch.setattr(os, "fstat", device)
    with pytest.raises(ValueError, match="one filesystem"):
        transaction.transact(destination, lambda candidate: called.append(candidate))
    assert events and called == []
    assert not destination.exists()
