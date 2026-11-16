"""A displaced recovery directory must not lend ownership to its replacement."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.landclim.raw_assets import transaction


def test_replaced_recovery_path_is_explicitly_unverified(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname="landclim-fixture"\n')
    public = tmp_path / "collection"
    public.mkdir()
    (public / "user.txt").write_bytes(b"preserve user work")
    primary = OSError("source generation failed")
    owned = None
    foreign = None
    identity = None

    def produce(candidate: Path) -> None:
        nonlocal owned, foreign, identity
        (candidate / "source.txt").write_bytes(b"owned candidate")
        foreign = candidate.parent
        node = foreign.stat()
        identity = (node.st_dev, node.st_ino)
        owned = foreign.with_name("displaced-owned-recovery")
        foreign.rename(owned)
        foreign.mkdir()
        (foreign / "foreign.txt").write_bytes(b"unrelated replacement")
        raise primary

    with pytest.raises(OSError) as caught:
        transaction.transact(public, produce)
    assert caught.value is primary
    assert foreign is not None and owned is not None and identity is not None
    assert (owned / "candidate/source.txt").read_bytes() == b"owned candidate"
    assert (foreign / "foreign.txt").read_bytes() == b"unrelated replacement"
    assert (public / "user.txt").read_bytes() == b"preserve user work"
    notes = caught.value.__notes__
    assert any("current location unverified" in note for note in notes)
    assert any(str(identity[0]) in note and str(identity[1]) in note for note in notes)
    assert not any(f"state retained at {foreign}" in note for note in notes)
