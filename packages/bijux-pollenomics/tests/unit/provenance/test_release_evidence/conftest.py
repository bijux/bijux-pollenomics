"""Release-evidence fixture registration."""

from __future__ import annotations

import pytest

from bijux_pollenomics.provenance import gates as gate_module

from .support.gates import _fixture_specification


@pytest.fixture(autouse=True)
def _trusted_fixture_gate_specification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gate_module,
        "build_product_gate_specification",
        _fixture_specification,
    )
