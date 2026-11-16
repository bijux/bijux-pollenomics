"""Owned staged writes cannot follow redirected directories or overwrite data."""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any

import pytest


def owner() -> Any:
    return importlib.import_module("bijux_pollenomics.core.filesystem.owned_writes")


def tree(tmp_path: Path, **kwargs: Any) -> Any:
    root = tmp_path / "stage"
    return owner().OwnedTreeWriter(
        root,
        max_bytes=kwargs.get("max_bytes", 100),
        max_files=kwargs.get("max_files", 10),
    )


def test_exclusive_nested_writes_and_descriptor_close(tmp_path: Path) -> None:
    writer = tree(tmp_path)
    with writer:
        writer.write_bytes("catalogue/one.json", b"one")
        writer.write_bytes("catalogue/two.json", b"two")
        descriptor = writer._root_fd
        assert os.fstat(descriptor)
        with pytest.raises(FileExistsError):
            writer.write_bytes("catalogue/one.json", b"replace")
    with pytest.raises(OSError):
        os.fstat(descriptor)
    assert (tmp_path / "stage/catalogue/one.json").read_bytes() == b"one"


@pytest.mark.parametrize(
    "relative",
    [
        "",
        ".",
        "../outside",
        "/absolute",
        "a/../b",
        "a//b",
        "a/./b",
        "a\\b",
        "a\x00b",
        "/".join(["a"] * 33),
    ],
)
def test_noncanonical_or_unbounded_paths_refuse_before_creating_children(
    tmp_path: Path, relative: str
) -> None:
    with tree(tmp_path) as writer, pytest.raises(ValueError):
        writer.write_bytes(relative, b"source")
    assert list((tmp_path / "stage").iterdir()) == []


@pytest.mark.parametrize("kind", ["symlink", "directory_replacement", "late_symlink"])
def test_staging_redirection_never_writes_foreign_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "user").write_bytes(b"original")
    writer = tree(tmp_path)
    stage = tmp_path / "stage"
    retained = tmp_path / "original-stage"
    with writer:
        if kind == "late_symlink":
            original = os.open

            def swapping(path: Any, *args: Any, **kwargs: Any) -> int:
                if path == "later.bin":
                    stage.rename(retained)
                    stage.symlink_to(foreign, target_is_directory=True)
                return original(path, *args, **kwargs)

            monkeypatch.setattr(os, "open", swapping)
        else:
            stage.rename(retained)
            if kind == "symlink":
                stage.symlink_to(foreign, target_is_directory=True)
            else:
                foreign.rename(stage)
        with pytest.raises((ValueError, OSError)):
            writer.write_bytes("later.bin", b"must not be foreign")
    actual = stage if kind == "directory_replacement" else foreign
    assert sorted(p.name for p in actual.iterdir()) == ["user"]
    assert (actual / "user").read_bytes() == b"original"


@pytest.mark.parametrize("kind", ["symlink", "directory_replacement"])
def test_existing_owned_child_directory_identity_cannot_be_borrowed(
    tmp_path: Path, kind: str
) -> None:
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "user").write_bytes(b"original")
    with tree(tmp_path) as writer:
        writer.write_bytes("child/first", b"one")
        child = tmp_path / "stage/child"
        child.rename(tmp_path / "owned-child")
        if kind == "symlink":
            child.symlink_to(foreign, target_is_directory=True)
        else:
            foreign.rename(child)
        with pytest.raises((ValueError, OSError)):
            writer.write_bytes("child/second", b"two")
    actual = child if kind == "directory_replacement" else foreign
    assert sorted(p.name for p in actual.iterdir()) == ["user"]


@pytest.mark.parametrize("kind", ["bytes", "files"])
def test_budget_is_checked_before_any_excess_write(tmp_path: Path, kind: str) -> None:
    with tree(tmp_path, max_bytes=3, max_files=1) as writer:
        writer.write_bytes("first", b"one")
        with pytest.raises(ValueError):
            writer.write_bytes("second", b"x" if kind == "files" else b"four")
    assert sorted(p.name for p in (tmp_path / "stage").iterdir()) == ["first"]


def test_unknown_preexisting_child_and_file_are_preserved(tmp_path: Path) -> None:
    with tree(tmp_path) as writer:
        child = tmp_path / "stage/unowned"
        child.mkdir()
        (child / "user").write_bytes(b"owned elsewhere")
        with pytest.raises(FileExistsError):
            writer.write_bytes("unowned/new", b"new")
        (tmp_path / "stage/existing").write_bytes(b"original")
        with pytest.raises(FileExistsError):
            writer.write_bytes("existing", b"replacement")
    assert (child / "user").read_bytes() == b"owned elsewhere"


def test_nonempty_root_is_not_a_new_owned_staging_directory(tmp_path: Path) -> None:
    root = tmp_path / "stage"
    root.mkdir()
    (root / "user").write_bytes(b"preserve")
    with pytest.raises(FileExistsError):
        owner().OwnedTreeWriter(root, max_bytes=100, max_files=10)
    assert (root / "user").read_bytes() == b"preserve"


def test_constructor_parent_anchor_cannot_be_replaced_during_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = tmp_path / "output"
    parent.mkdir()
    root = parent / "stage"
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    original = os.open
    changed = False

    def replacing(path: Any, *args: Any, **kwargs: Any) -> int:
        nonlocal changed
        if path == parent:
            parent.rename(tmp_path / "owned-parent")
            foreign.rename(parent)
            changed = True
        return original(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", replacing)
    monkeypatch.setattr(os, "supports_dir_fd", {*os.supports_dir_fd, replacing})
    with pytest.raises(ValueError):
        owner().OwnedTreeWriter(root, max_bytes=100, max_files=10)
    assert changed and not root.exists()
    assert list(parent.iterdir()) == []


def test_new_child_replaced_during_open_is_not_adopted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "user").write_bytes(b"preserve")
    with tree(tmp_path) as writer:
        original = os.open
        changed = False

        def replacing(path: Any, *args: Any, **kwargs: Any) -> int:
            nonlocal changed
            if path == "child" and not changed:
                changed = True
                child = tmp_path / "stage/child"
                child.rename(tmp_path / "owned-child")
                foreign.rename(child)
            return original(path, *args, **kwargs)

        monkeypatch.setattr(os, "open", replacing)
        with pytest.raises(ValueError):
            writer.write_bytes("child/data", b"foreign write refused")
    assert sorted(p.name for p in (tmp_path / "stage/child").iterdir()) == ["user"]


@pytest.mark.parametrize("nonempty", [False, True])
@pytest.mark.parametrize("moment", ["creation", "attachment"])
def test_competing_canonical_directory_is_never_adopted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    nonempty: bool,
    moment: str,
) -> None:
    subject = owner()
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    if nonempty:
        (foreign / "user").write_bytes(b"preserve")
    stage = tmp_path / "stage"
    changed = False
    with tree(tmp_path) as writer:
        if moment == "creation":
            mkdir = os.mkdir

            def creating(path: Any, *args: Any, **kwargs: Any) -> None:
                nonlocal changed
                mkdir(path, *args, **kwargs)
                if (
                    not changed
                    and isinstance(path, str)
                    and (path == "child" or path.startswith(".owned-directory-"))
                ):
                    canonical = stage / "child"
                    if canonical.exists():
                        canonical.rename(tmp_path / "original-child")
                    foreign.rename(canonical)
                    changed = True

            monkeypatch.setattr(os, "mkdir", creating)
        else:
            assert hasattr(subject, "_rename_directory"), (
                "Exclusive fd-relative canonical attachment is missing"
            )
            rename = subject._rename_directory

            def attaching(descriptor: int, source: str, target: str) -> None:
                nonlocal changed
                rename(descriptor, source, target)
                if not changed:
                    canonical = stage / target
                    canonical.rename(tmp_path / "original-child")
                    foreign.rename(canonical)
                    changed = True

            monkeypatch.setattr(subject, "_rename_directory", attaching)
        with pytest.raises((ValueError, OSError)):
            writer.write_bytes("child/data", b"must not enter foreign directory")
    assert changed
    assert sorted(p.name for p in (stage / "child").iterdir()) == (
        ["user"] if nonempty else []
    )
    if nonempty:
        assert (stage / "child/user").read_bytes() == b"preserve"
    if moment == "creation":
        assert any(p.name.startswith(".owned-directory-") for p in stage.iterdir())


def test_canonical_directories_keep_ordinary_publication_permissions(
    tmp_path: Path,
) -> None:
    import stat

    with tree(tmp_path) as writer:
        expected = stat.S_IMODE((tmp_path / "stage").stat().st_mode)
        writer.write_bytes("child/data", b"source")
        assert stat.S_IMODE((tmp_path / "stage/child").stat().st_mode) == expected


def test_failed_private_creation_evidence_has_a_finite_directory_budget(
    tmp_path: Path,
) -> None:
    with tree(tmp_path, max_files=1) as writer:
        blocked = tmp_path / "stage/blocked"
        blocked.mkdir()
        for _ in range(31):
            with pytest.raises(FileExistsError):
                writer.write_bytes("blocked/data", b"source")
        with pytest.raises(ValueError, match="directory.*bound"):
            writer.write_bytes("blocked/data", b"source")
    assert len(list((tmp_path / "stage").iterdir())) == 32


@pytest.mark.parametrize("nonempty", [False, True])
def test_creation_rejects_existing_canonical_root_without_adoption(
    tmp_path: Path, nonempty: bool
) -> None:
    root = tmp_path / "stage"
    root.mkdir()
    if nonempty:
        (root / "user").write_bytes(b"preserve")
    with pytest.raises(FileExistsError):
        owner().OwnedTreeWriter(root, max_bytes=100, max_files=10)
    assert sorted(p.name for p in root.iterdir()) == (["user"] if nonempty else [])


def test_root_loss_after_child_attachment_closes_every_opened_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    subject = owner()
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "user").write_bytes(b"preserve")
    opened = []
    with tree(tmp_path) as writer:
        original_open = os.open
        rename = subject._rename_directory

        def tracking(path: Any, *args: Any, **kwargs: Any) -> int:
            descriptor = original_open(path, *args, **kwargs)
            opened.append(descriptor)
            return descriptor

        def redirect(descriptor: int, source: str, target: str) -> None:
            rename(descriptor, source, target)
            if target == "child":
                stage = tmp_path / "stage"
                stage.rename(tmp_path / "owned-root")
                stage.symlink_to(foreign, target_is_directory=True)

        monkeypatch.setattr(os, "open", tracking)
        monkeypatch.setattr(subject, "_rename_directory", redirect)
        with pytest.raises((ValueError, OSError)):
            writer.write_bytes("child/data", b"source")
    assert opened
    for descriptor in opened:
        with pytest.raises(OSError):
            os.fstat(descriptor)
    assert sorted(p.name for p in foreign.iterdir()) == ["user"]


def test_replaced_canonical_leaf_cannot_return_write_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with tree(tmp_path) as writer:
        original = os.open

        def replacing(path: Any, *args: Any, **kwargs: Any) -> int:
            descriptor = original(path, *args, **kwargs)
            if path == "record.bin":
                canonical = tmp_path / "stage/record.bin"
                canonical.rename(tmp_path / "owned-leaf")
                canonical.write_bytes(b"FOREIG")
            return descriptor

        monkeypatch.setattr(os, "open", replacing)
        with pytest.raises(ValueError, match="leaf|identity|file"):
            writer.write_bytes("record.bin", b"source")
    assert (tmp_path / "stage/record.bin").read_bytes() == b"FOREIG"
    assert (tmp_path / "owned-leaf").read_bytes() == b"source"


def test_descriptor_relative_attachment_supports_distinct_parents(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.core.filesystem.owned_writes import _rename_directory

    source, target = tmp_path / "source", tmp_path / "target"
    (source / "child").mkdir(parents=True)
    target.mkdir()
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    left, right = os.open(source, flags), os.open(target, flags)
    try:
        _rename_directory(left, "child", "attached", destination_descriptor=right)
        assert (target / "attached").is_dir()
        (source / "child").mkdir()
        inode = (target / "attached").stat().st_ino
        with pytest.raises(FileExistsError):
            _rename_directory(left, "child", "attached", destination_descriptor=right)
        assert (target / "attached").stat().st_ino == inode
        assert (source / "child").is_dir()
    finally:
        os.close(left)
        os.close(right)
