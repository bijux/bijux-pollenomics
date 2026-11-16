"""Destination preflight refuses foreign entries without opening their bodies."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from .support import NAMES, publish


@pytest.mark.parametrize(
    "kind",
    [
        "leaf_alias",
        "parent_alias",
        "root_alias",
        "hardlink",
        "fifo",
        "foreign_file",
        "foreign_directory",
    ],
)
def test_destination_refuses_before_any_binary_fetch(tmp_path: Path, kind: str) -> None:
    """Closed source namespaces are checked before body acquisition."""
    output = tmp_path / "collection"
    publish(output, (b"old-one", b"old-two"))
    leaf = output / "v66" / NAMES[0]
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    marker = foreign / "marker.txt"
    marker.write_bytes(b"foreign")
    if kind == "leaf_alias":
        leaf.unlink()
        leaf.symlink_to(marker)
    elif kind == "parent_alias":
        leaf.parent.rename(tmp_path / "retained-panel")
        leaf.parent.symlink_to(foreign, target_is_directory=True)
    elif kind == "root_alias":
        output.rename(tmp_path / "retained-collection")
        output.symlink_to(foreign, target_is_directory=True)
    elif kind == "hardlink":
        leaf.unlink()
        os.link(marker, leaf)
    elif kind == "fifo":
        leaf.unlink()
        os.mkfifo(leaf)
    elif kind == "foreign_file":
        (output / "v66/unowned.txt").write_bytes(b"unowned")
    else:
        (output / "v66/unowned").mkdir()
    calls: list[str] = []

    def fetch(url: str, **kwargs: Any) -> bytes:
        calls.append(url)
        raise AssertionError("Invalid namespace reached annotation acquisition")

    with pytest.raises((OSError, ValueError)):
        publish(output, (b"new-one", b"new-two"), fetch=fetch)
    assert calls == [] and marker.read_bytes() == b"foreign"


def test_descriptor_capability_unavailable_refuses_before_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unavailable callback capability fails before annotation transport."""
    real_open = os.open
    calls: list[str] = []

    def opened(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        if str(path).startswith("/dev/fd/"):
            raise OSError("generated unavailable descriptor capability")
        return real_open(path, flags, *args, **kwargs)

    def fetch(url: str, **kwargs: Any) -> bytes:
        calls.append(url)
        raise AssertionError("Unavailable capability reached transport")

    monkeypatch.setattr(os, "open", opened)
    # The core compares supported function objects; retain the actual platform set.
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {opened})
    with pytest.raises(OSError, match="unavailable descriptor"):
        publish(tmp_path / "collection", (b"new-one", b"new-two"), fetch=fetch)
    assert calls == []


def test_changed_collection_attachment_cannot_receive_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A foreign collection substituted before core entry receives no candidate."""
    from bijux_pollenomics.core.filesystem import DirectoryAnchor
    import bijux_pollenomics.core.filesystem.replacement as replacement

    output = tmp_path / "collection"
    events: list[str] = []

    class ChangedAnchor(DirectoryAnchor):
        def __init__(self, path: Path, *, create: bool = False) -> None:
            if path == output and not events:
                output.rename(tmp_path / "retained-collection")
                output.mkdir()
                (output / "foreign.txt").write_bytes(b"foreign")
                events.append("foreign_collection_attachment")
            super().__init__(path, create=create)

    monkeypatch.setattr(replacement, "DirectoryAnchor", ChangedAnchor)
    with pytest.raises((OSError, ValueError)):
        publish(output, (b"new-one", b"new-two"))
    assert events == ["foreign_collection_attachment"]
    assert {p.name for p in output.iterdir()} == {"foreign.txt"}
    assert (output / "foreign.txt").read_bytes() == b"foreign"
