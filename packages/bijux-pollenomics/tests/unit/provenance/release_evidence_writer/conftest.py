"""Trusted gate specification for release-evidence writer tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.provenance import gates as gate_module

from .support import _fixture_specification


@pytest.fixture(autouse=True)
def _trusted_writer_gate_specification(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    if not Path(request.node.path).is_relative_to(Path(__file__).parent):
        return
    monkeypatch.setattr(
        gate_module,
        "build_product_gate_specification",
        _fixture_specification,
    )
