"""A release becomes visible only after every source member is validated."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .support import NAMES, publish, snapshot


def test_later_asset_failure_preserves_every_prior_release_byte(tmp_path: Path) -> None:
    """A later native fetch failure cannot mix a new asset into an old release."""
    output = tmp_path / "collection"
    publish(output, (b"old-one", b"old-two"))
    before = snapshot(output)
    failure = OSError("generated second asset refusal")
    calls: list[str] = []

    def fetch(url: str, **kwargs: Any) -> bytes:
        calls.append(url)
        if len(calls) == 2:
            raise failure
        return b"new-one"

    with pytest.raises(OSError) as refused:
        publish(output, (b"new-one", b"new-two"), fetch=fetch)
    assert refused.value is failure
    assert len(calls) == 2
    assert snapshot(output) == before


def test_foreign_leaf_alias_refuses_before_fetch_and_preserves_target(
    tmp_path: Path,
) -> None:
    """An existing symbolic annotation destination is never followed."""
    output = tmp_path / "collection"
    publish(output, (b"old-one", b"old-two"))
    leaf = output / "v66" / NAMES[0]
    leaf.unlink()
    foreign = tmp_path / "foreign.txt"
    foreign.write_bytes(b"foreign")
    leaf.symlink_to(foreign)
    calls: list[str] = []

    def fetch(url: str, **kwargs: Any) -> bytes:
        calls.append(url)
        return b"new-one" if len(calls) == 1 else b"new-two"

    with pytest.raises((ValueError, OSError)):
        publish(output, (b"new-one", b"new-two"), fetch=fetch)
    assert calls == []
    assert leaf.is_symlink() and foreign.read_bytes() == b"foreign"


def test_manifest_callback_cannot_follow_a_private_control_alias(
    tmp_path: Path,
) -> None:
    """Callback output has no authority to overwrite a foreign alias target."""
    output = tmp_path / "collection"
    publish(output, (b"old-one", b"old-two"))
    before = snapshot(output)
    foreign = tmp_path / "foreign-control.txt"
    foreign.write_bytes(b"foreign")

    def write(path: Path, payload: object) -> None:
        path.symlink_to(foreign)
        path.write_text("{}", encoding="utf-8")

    with pytest.raises((OSError, ValueError)):
        publish(output, (b"new-one", b"new-two"), write=write)
    assert snapshot(output) == before
    assert foreign.read_bytes() == b"foreign"
