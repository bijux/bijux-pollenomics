"""Genuine finite source products and I/O observations for preflight batches."""

from __future__ import annotations

from collections import Counter
import importlib
from pathlib import Path
from typing import Any

import pytest

from ...linked_evidence.native_products import (
    scoped_inputs as scoped_inputs,
)
from ...linked_evidence.native_products import (
    scoped_selection_products as scoped_selection_products,
)
from ..native_products import facet_row as facet_row
from ..native_products import selected_products as selected_products


def api() -> Any:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection.batch"
    )


def observe(monkeypatch: pytest.MonkeyPatch, products: dict[str, Any]) -> Counter[Path]:
    roots = [products[key] for key in ("capsule", "facet_capsule") if key in products]
    original = Path.open
    counts: Counter[Path] = Counter()

    def opened(path: Path, *args: Any, **kwargs: Any) -> Any:
        assert not (
            path.suffix == ".body" and any(root in path.parents for root in roots)
        ), f"Preflight opened native entity {path}"
        counts[path] += 1
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", opened)
    return counts


def scoped_arguments(products: dict[str, Any]) -> dict[str, Any]:
    return {**products["kwargs"], "evidence_sources": products["evidence_sources"]}


def linked_rows(
    products: dict[str, Any], native: int
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    row = next(
        row
        for row in products["view"].observations
        if row["kind"] == "linked"
        and row["identity"]["kind"] == "taxon"
        and row["identity"]["native_id"] == native
    )
    return row, [
        value
        for value in products["view"].linked_occurrences
        if value["observation_id"] == row["observation_id"]
    ]
