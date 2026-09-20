"""Typed reopen authenticates every retained child and claim field."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.regional_components import (
    bind_regional_component_set,
    read_regional_component_set,
)

from .support import component_fixture


def test_child_mutation_is_refused_even_without_external_bundle_pin(
    tmp_path: Path,
) -> None:
    input_root, items, batch, plan = component_fixture(tmp_path)
    product = bind_regional_component_set(
        items,
        batch,
        plan,
        input_root=input_root,
        destination=tmp_path / "bundle",
    )
    child = product.directory / "components/000000/request.json"
    child.write_text(child.read_text() + " ")
    with pytest.raises(LRARefusal) as error:
        read_regional_component_set(product.directory)
    assert error.value.reason_code == "invalid_regional_component_set"


def test_claim_promotion_is_refused(tmp_path: Path) -> None:
    input_root, items, batch, plan = component_fixture(tmp_path)
    product = bind_regional_component_set(
        items,
        batch,
        plan,
        input_root=input_root,
        destination=tmp_path / "bundle",
    )
    path = product.directory / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["aggregation_performed"] = True
    path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n")
    with pytest.raises(LRARefusal):
        read_regional_component_set(product.directory)
