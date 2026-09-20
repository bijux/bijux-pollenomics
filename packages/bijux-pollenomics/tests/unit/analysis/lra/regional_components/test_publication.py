"""Published closure is deterministic for identical authenticated inputs."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.analysis.lra.regional_components import (
    bind_regional_component_set,
)

from .support import component_fixture


def test_scientific_identity_ignores_original_product_locator(tmp_path: Path) -> None:
    input_root, items, batch, plan = component_fixture(tmp_path)
    first = bind_regional_component_set(
        items,
        batch,
        plan,
        input_root=input_root,
        destination=tmp_path / "first",
    )
    second = bind_regional_component_set(
        items,
        batch,
        plan,
        input_root=input_root,
        destination=tmp_path / "second",
    )
    assert first.scientific_content_sha256 == second.scientific_content_sha256
