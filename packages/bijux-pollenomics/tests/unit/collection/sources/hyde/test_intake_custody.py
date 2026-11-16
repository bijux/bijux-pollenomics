"""Declared-grid identity must belong to one ordinary, literal source file."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.hyde import load_declared_grid
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal


@pytest.mark.parametrize("alias_kind", ["parent", "hardlink", "changed_leaf"])
def test_matching_bytes_do_not_admit_an_aliased_or_substituted_source(
    tmp_path: Path,
    declared_payload: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    alias_kind: str,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    content = json.dumps(declared_payload).encode()
    original = source / "grid.json"
    original.write_bytes(content)
    selected = original
    if alias_kind == "parent":
        alias = tmp_path / "alias"
        alias.symlink_to(source, target_is_directory=True)
        selected = alias / original.name
    elif alias_kind == "hardlink":
        selected = source / "linked.json"
        selected.hardlink_to(original)
    else:
        other = source / "other.json"
        other.write_bytes(content)
        ordinary = Path.is_file

        def substitute_after_classification(path: Path) -> bool:
            result = ordinary(path)
            if path == selected:
                path.unlink()
                path.symlink_to(other)
            return result

        monkeypatch.setattr(Path, "is_file", substitute_after_classification)
    with pytest.raises(IntakeRefusal, match="hyde_local_asset"):
        load_declared_grid(
            selected, expected_sha256=hashlib.sha256(content).hexdigest()
        )
    assert original.read_bytes() == content


def test_selected_file_does_not_inventory_or_read_unrelated_siblings(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    content = json.dumps(declared_payload).encode()
    selected = tmp_path / "grid.json"
    selected.write_bytes(content)
    unrelated = tmp_path / "unrelated"
    unrelated.symlink_to(tmp_path / "missing")
    layer = load_declared_grid(
        selected,
        expected_sha256=hashlib.sha256(content).hexdigest(),
        maximum_bytes=len(content),
    )
    assert list(layer.values) == [0.0, 0.5, None, 1.0]
    assert layer.native_hyde_admission_verified is False
    assert unrelated.is_symlink()
