"""Bounded namespace validation inspects ordinary files without opening buffers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.core import filesystem


def validate(root: Path, expected: set[object], **limits: int) -> dict[str, int]:
    owner: Any = getattr(filesystem, "validate_regular_namespace", None)
    assert callable(owner), "Shared bounded regular namespace owner is unavailable"
    result = owner(
        root,
        expected,
        max_files=limits.get("max_files", 10),
        max_bytes=limits.get("max_bytes", 32),
    )
    assert isinstance(result, dict)
    return result


def test_namespace_returns_exact_physical_sizes_without_opening_buffers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "tree"
    (root / "parts").mkdir(parents=True)
    (root / "manifest.json").write_bytes(b"{}")
    (root / "parts/a.json").write_bytes(b"abc")
    monkeypatch.setattr(Path, "read_bytes", lambda _: pytest.fail("buffer opened"))
    assert validate(
        root, {"manifest.json", "parts/a.json"}, max_files=2, max_bytes=5
    ) == {
        "manifest.json": 2,
        "parts/a.json": 3,
    }


@pytest.mark.parametrize(
    "relative",
    ["../file", "/absolute", "./file", "a//file", "a\\file", "a\x00file", "", True],
)
def test_namespace_members_are_canonical_before_traversal(
    tmp_path: Path, relative: object
) -> None:
    with pytest.raises(ValueError):
        validate(tmp_path, {relative})


@pytest.mark.parametrize(
    "entry", ["empty_directory", "fifo", "hardlink", "symlink", "extra_file", "missing"]
)
def test_namespace_rejects_unowned_and_nonordinary_entries(
    tmp_path: Path, entry: str
) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    (root / "owned").write_bytes(b"x")
    if entry == "empty_directory":
        (root / "foreign").mkdir()
    elif entry == "fifo":
        os.mkfifo(root / "foreign")
    elif entry == "hardlink":
        os.link(root / "owned", tmp_path / "alias")
    elif entry == "symlink":
        (root / "foreign").symlink_to(root / "owned")
    elif entry == "extra_file":
        (root / "foreign").write_bytes(b"x")
    else:
        (root / "owned").unlink()
    with pytest.raises(ValueError):
        validate(root, {"owned"})


@pytest.mark.parametrize("limit", ["bytes", "files"])
def test_namespace_has_physical_cumulative_and_declared_file_bounds(
    tmp_path: Path, limit: str
) -> None:
    (tmp_path / "one").write_bytes(b"xx")
    (tmp_path / "two").write_bytes(b"yyy")
    with pytest.raises(ValueError):
        validate(
            tmp_path,
            {"one", "two"},
            max_files=1 if limit == "files" else 2,
            max_bytes=4 if limit == "bytes" else 5,
        )


@pytest.mark.parametrize("replacement", ["symlink", "directory"])
def test_namespace_cannot_accept_replaced_child_at_traversal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, replacement: str
) -> None:
    root = tmp_path / "tree"
    child = root / "parts"
    child.mkdir(parents=True)
    (child / "a").write_bytes(b"owned")
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "a").write_bytes(b"foreign")
    identity = child.stat()
    scan = os.scandir
    changed = False

    def replacing(directory: Any) -> Any:
        nonlocal changed
        selected = (
            (os.fstat(directory).st_dev, os.fstat(directory).st_ino)
            == (identity.st_dev, identity.st_ino)
            if isinstance(directory, int)
            else Path(directory) == child
        )
        if selected and not changed:
            child.rename(root / "detached-owned")
            if replacement == "symlink":
                child.symlink_to(foreign, target_is_directory=True)
            else:
                foreign.rename(child)
            changed = True
        return scan(directory)

    monkeypatch.setattr(os, "scandir", replacing)
    with pytest.raises(ValueError):
        validate(root, {"parts/a"})
    assert changed


@pytest.mark.parametrize("replacement", ["symlink", "directory"])
def test_namespace_cannot_accept_replaced_root_during_traversal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, replacement: str
) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    (root / "a").write_bytes(b"owned")
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "a").write_bytes(b"foreign")
    scan = os.scandir
    changed = False

    def replacing(directory: Any) -> Any:
        nonlocal changed
        if not changed:
            root.rename(tmp_path / "detached-owned")
            if replacement == "symlink":
                root.symlink_to(foreign, target_is_directory=True)
            else:
                foreign.rename(root)
            changed = True
        return scan(directory)

    monkeypatch.setattr(os, "scandir", replacing)
    with pytest.raises(ValueError):
        validate(root, {"a"})
    assert changed


def test_namespace_closes_root_and_child_descriptors_after_traversal_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "tree"
    (root / "parts").mkdir(parents=True)
    (root / "parts/a").write_bytes(b"owned")
    opened: list[int] = []
    native_open = os.open
    native_scan = os.scandir
    child = (root / "parts").stat()

    def opening(*args: Any, **kwargs: Any) -> int:
        descriptor = native_open(*args, **kwargs)
        opened.append(descriptor)
        return descriptor

    def failing(directory: Any) -> Any:
        if isinstance(directory, int) and os.fstat(directory).st_ino == child.st_ino:
            raise OSError("retained filesystem traversal failure")
        return native_scan(directory)

    monkeypatch.setattr(os, "open", opening)
    monkeypatch.setattr(os, "scandir", failing)
    with pytest.raises(ValueError):
        validate(root, {"parts/a"})
    assert len(opened) == 2
    for descriptor in opened:
        with pytest.raises(OSError):
            os.fstat(descriptor)
