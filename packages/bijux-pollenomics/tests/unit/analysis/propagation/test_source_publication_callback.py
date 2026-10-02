"""Source checks at the propagation bundle commit boundary."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.propagation.outputs.publication import (
    _publish_atomically,
)


def test_source_callback_refuses_before_create_and_unchanged_reuse(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "propagation"
    expected = {"manifest.json": b"exact bytes"}

    def refuse() -> None:
        raise RuntimeError("source changed")

    with pytest.raises(RuntimeError, match="source changed"):
        _publish_atomically(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            expected_files=expected,
            before_commit=refuse,
        )
    assert not output_root.exists()
    assert not tuple(tmp_path.glob(".propagation.staging-*"))
    assert not (tmp_path / ".propagation.materialization.lock").exists()

    assert (
        _publish_atomically(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            expected_files=expected,
        )
        == "created"
    )
    with pytest.raises(RuntimeError, match="source changed"):
        _publish_atomically(
            output_root=output_root,
            allowed_output_parent=tmp_path,
            expected_files=expected,
            before_commit=refuse,
        )
    assert (output_root / "manifest.json").read_bytes() == b"exact bytes"
    assert not (tmp_path / ".propagation.materialization.lock").exists()
