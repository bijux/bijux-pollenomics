"""Durable publication of the real-source prerequisite projection."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from bijux_pollenomics_dev.taxa_review.lra_prerequisites.__main__ import _publish_new


def test_publish_is_exact_and_refuses_replacement(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "projection.json"
    _publish_new(output, b"exact\n")
    assert output.read_bytes() == b"exact\n"
    with pytest.raises(ValueError, match="Refusing to replace"):
        _publish_new(output, b"different\n")
    assert output.read_bytes() == b"exact\n"
    assert not list(output.parent.glob(".*.stage"))


def test_publish_failure_leaves_no_partial_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "projection.json"

    def fail_link(_source: Path, _target: Path) -> None:
        raise OSError("simulated publication failure")

    monkeypatch.setattr(os, "link", fail_link)
    with pytest.raises(OSError, match="simulated publication failure"):
        _publish_new(output, b"never visible\n")
    assert not output.exists()
    assert not list(tmp_path.glob(".*.stage"))
