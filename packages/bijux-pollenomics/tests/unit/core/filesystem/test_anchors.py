"""Directory anchors reject redirected attachments and close their descriptors."""

import os
from pathlib import Path

import pytest

from bijux_pollenomics.core.filesystem.anchors import DirectoryAnchor


def test_parent_replacement_is_detected_and_descriptor_closes(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    parent.mkdir()
    child = parent / "child"
    child.mkdir()
    with DirectoryAnchor(child) as anchor:
        descriptor = anchor.fd
        parent.rename(tmp_path / "displaced")
        parent.mkdir()
        with pytest.raises(ValueError, match="attachment|identity"):
            anchor.check()
    with pytest.raises(OSError):
        os.fstat(descriptor)


def test_symlink_ancestry_is_refused_without_creating_a_child(tmp_path: Path) -> None:
    physical, alias = tmp_path / "physical", tmp_path / "alias"
    physical.mkdir()
    alias.symlink_to(physical, target_is_directory=True)
    with (
        pytest.raises((ValueError, OSError)),
        DirectoryAnchor(alias / "child", create=True),
    ):
        pass
    assert list(physical.iterdir()) == []
