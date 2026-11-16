"""Publication retains the authored tree even after its staging name is moved."""

from __future__ import annotations

import os
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.owned_tree import publish_new_output_tree


def test_authenticates_both_root_names_without_retargeting_writer(
    tmp_path: Path,
) -> None:
    stage, final = tmp_path / "stage", tmp_path / "published"
    with OwnedTreeWriter(stage, max_bytes=100, max_files=3) as writer:
        writer.write_bytes("raw/one", b"literal source")
        writer.write_bytes("two", b"second source")
        writer.validate_publication_attachment(stage)
        publish_new_output_tree(final_output_root=final, staging_output_root=stage)
        writer.validate_publication_attachment(final)
        assert writer.root == stage
    with pytest.raises(ValueError, match="closed"):
        writer.validate_publication_attachment(final)


@pytest.mark.parametrize(
    "mutation", ["child", "leaf", "contents", "restored_mtime", "symlink", "hardlink"]
)
def test_refuses_changed_authored_members(tmp_path: Path, mutation: str) -> None:
    stage = tmp_path / "stage"
    with OwnedTreeWriter(stage, max_bytes=100, max_files=1) as writer:
        writer.write_bytes("raw/one", b"literal source")
        target = stage / "raw/one"
        if mutation == "child":
            saved = tmp_path / "saved-raw"
            target.parent.rename(saved)
            shutil.copytree(saved, stage / "raw")
        elif mutation == "leaf":
            target.rename(stage / "raw/saved")
            target.write_bytes(b"literal source")
        elif mutation in {"contents", "restored_mtime"}:
            original = target.stat()
            target.write_bytes(b"changed source")
            if mutation == "restored_mtime":
                os.utime(target, ns=(original.st_atime_ns, original.st_mtime_ns))
        elif mutation == "symlink":
            saved = tmp_path / "original-leaf"
            target.rename(saved)
            target.symlink_to(saved)
        else:
            os.link(target, tmp_path / "linked-leaf")
        with pytest.raises(ValueError, match="identity"):
            writer.validate_publication_attachment(stage)


def test_refuses_an_equal_byte_foreign_root_and_directory_alias(tmp_path: Path) -> None:
    stage, foreign = tmp_path / "stage", tmp_path / "foreign"
    with OwnedTreeWriter(stage, max_bytes=100, max_files=1) as writer:
        writer.write_bytes("raw/one", b"literal source")
        shutil.copytree(stage, foreign)
        with pytest.raises(ValueError, match="identity"):
            writer.validate_publication_attachment(foreign)
        alias = tmp_path / "alias"
        alias.symlink_to(stage, target_is_directory=True)
        with pytest.raises(ValueError, match="redirected"):
            writer.validate_publication_attachment(alias)
