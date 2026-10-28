"""Keep serialized candidate/selection boundaries real under byte tampering."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.products import (
    reopen,
    write,
)


def test_changed_closed_bytes_refuse_even_if_valid_json(tmp_path: Path) -> None:
    pin = write(tmp_path, "candidates.json", {"pollen": [0.25, 0.75]}, 1024)
    assert reopen(tmp_path, pin) == {"pollen": [0.25, 0.75]}
    (tmp_path / "candidates.json").write_text('{"pollen":[0.75,0.25]}\n')
    with pytest.raises(ValueError, match="changed"):
        reopen(tmp_path, pin)


@pytest.mark.parametrize(
    "name", ["../selection.json", "/selection.json", "..", ".", ""]
)
def test_member_cannot_escape_its_freeze_directory(tmp_path: Path, name: str) -> None:
    with pytest.raises(ValueError, match="Direct member"):
        write(tmp_path, name, {}, 1024)
    with pytest.raises(ValueError, match="Direct member"):
        reopen(tmp_path, {"path": name})


def test_existing_member_is_never_overwritten(tmp_path: Path) -> None:
    pin = write(tmp_path, "choices.json", {"choice": 20}, 1024)
    with pytest.raises(FileExistsError):
        write(tmp_path, "choices.json", {"choice": 100}, 1024)
    assert reopen(tmp_path, pin) == {"choice": 20}


def test_redirected_member_is_refused(tmp_path: Path) -> None:
    pin = write(tmp_path, "choices.json", {"choice": 20}, 1024)
    original = tmp_path / "choices.json"
    original.rename(tmp_path / "elsewhere.json")
    original.symlink_to(tmp_path / "elsewhere.json")
    with pytest.raises(ValueError, match="Ordinary"):
        reopen(tmp_path, pin)


def test_oversized_member_leaves_no_partial_output(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="ceiling"):
        write(tmp_path, "choices.json", {"payload": "x" * 1024}, 128)
    assert not (tmp_path / "choices.json").exists()
