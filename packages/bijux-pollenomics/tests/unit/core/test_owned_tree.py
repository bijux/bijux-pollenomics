"""Exclusive publication preserves competitors and leaves failed staging intact."""

from __future__ import annotations

import errno
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.core import owned_tree


def test_new_tree_publication_is_exclusive_and_preserves_existing_empty_directory(
    tmp_path: Path,
) -> None:
    stage, destination = tmp_path / "stage", tmp_path / "output"
    stage.mkdir()
    (stage / "result.txt").write_text("complete")
    owned_tree.publish_new_output_tree(
        final_output_root=destination, staging_output_root=stage
    )
    assert (destination / "result.txt").read_text() == "complete"
    assert not stage.exists()
    stage.mkdir()
    competitor = tmp_path / "competitor"
    competitor.mkdir()
    identity = competitor.stat().st_ino
    with pytest.raises(FileExistsError):
        owned_tree.publish_new_output_tree(
            final_output_root=competitor, staging_output_root=stage
        )
    assert competitor.stat().st_ino == identity and list(competitor.iterdir()) == []
    assert stage.is_dir()


def test_unsupported_platform_refuses_without_replacing_output(tmp_path: Path) -> None:
    stage = tmp_path / "stage"
    stage.mkdir()
    with (
        patch.object(sys, "platform", "unsupported-test-platform"),
        pytest.raises(OSError) as error,
    ):
        owned_tree.publish_new_output_tree(
            final_output_root=tmp_path / "output", staging_output_root=stage
        )
    assert error.value.errno == errno.ENOTSUP
    assert stage.is_dir() and not (tmp_path / "output").exists()


def test_nul_path_refuses_before_filesystem_call(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="NUL"):
        owned_tree.publish_new_output_tree(
            final_output_root=tmp_path / "bad\x00path",
            staging_output_root=tmp_path / "stage",
        )
