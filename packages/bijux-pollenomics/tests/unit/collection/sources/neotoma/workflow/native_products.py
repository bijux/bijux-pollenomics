"""Local source callbacks for complete collection publication controls."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import collection


@pytest.fixture
def source(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []

    def inventory(*args: Any) -> list[dict[str, object]]:
        calls.append("inventory")
        return [{"site": {"datasets": [{"datasetid": 201}]}}]

    monkeypatch.setattr(collection, "fetch_neotoma_dataset_inventory_rows", inventory)
    monkeypatch.setattr(
        collection, "filter_neotoma_dataset_inventory_rows", lambda rows, **_: rows
    )
    monkeypatch.setattr(
        collection,
        "fetch_neotoma_dataset_download_rows",
        lambda _: [{"site": {"dataset": {"datasetid": 201}}}],
    )
    monkeypatch.setattr(
        collection, "build_neotoma_site_rows_from_downloads", lambda _: []
    )
    monkeypatch.setattr(collection, "normalize_neotoma_rows", lambda *_, **__: [])
    return calls


def collect(path: Path) -> collection.NeotomaDataReport:
    return collection.collect_neotoma_data(path, {}, (4, 54, 35, 72))
