"""Source authorities cannot be contaminated through lexical or symlink paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.materialization.paths import (
    checked_output_directory,
)


def test_overlap_is_refused_before_any_directory_creation(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    with pytest.raises(ValueError, match="overlap"):
        checked_output_directory(
            tmp_path / "bridge" / ".." / "raw" / "nested", input_roots=(raw,)
        )
    assert list(raw.iterdir()) == []
    assert not (tmp_path / "bridge").exists()
    with pytest.raises(ValueError, match="overlap"):
        checked_output_directory(tmp_path, input_roots=(raw,))


def test_symlink_and_existing_targets_refuse(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(raw, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        checked_output_directory(alias / ".." / "new", input_roots=(raw,))
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        checked_output_directory(existing, input_roots=(raw,))
