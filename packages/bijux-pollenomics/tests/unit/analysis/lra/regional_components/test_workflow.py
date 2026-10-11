"""Heterogeneous component execution remains distinct from aggregation."""

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


def test_complete_component_set_copies_children_without_aggregation(
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
    reopened = read_regional_component_set(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    manifest = json.loads((product.directory / "manifest.json").read_text())
    rows = [
        json.loads(line)
        for line in (product.directory / "components.jsonl").read_text().splitlines()
    ]
    assert reopened.component_execution_status == "complete"
    assert [row["geometry"]["diameter_m"] for row in rows] == [300.0, 400.0]
    assert [row["site_id"] for row in rows] == ["site-1", "site-2"]
    assert all((product.directory / row["product_path"]).is_dir() for row in rows)
    assert manifest["aggregation_performed"] is False
    assert manifest["aggregation_profile"] is None
    assert manifest["regional_estimate"] is None
    assert manifest["regional_uncertainty"] is None
    assert manifest["publication_profile"] is None


def test_partial_component_set_preserves_refusal_denominator(tmp_path: Path) -> None:
    input_root, items, batch, plan = component_fixture(
        tmp_path, second_status="refused"
    )
    product = bind_regional_component_set(
        items,
        batch,
        plan,
        input_root=input_root,
        destination=tmp_path / "bundle",
    )
    assert product.component_execution_status == "partial"
    assert product.counts["completed"] == 1
    assert product.counts["refused"] == 1
    read_regional_component_set(product.directory)


def test_order_and_external_batch_pin_are_enforced(tmp_path: Path) -> None:
    input_root, items, batch, plan = component_fixture(tmp_path)
    with pytest.raises(LRARefusal) as error:
        bind_regional_component_set(
            tuple(reversed(items)),
            batch,
            plan,
            input_root=input_root,
            destination=tmp_path / "bundle",
        )
    assert error.value.reason_code == "regional_component_item_order_mismatch"
