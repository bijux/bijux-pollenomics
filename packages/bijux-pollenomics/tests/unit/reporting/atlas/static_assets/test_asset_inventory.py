"""Compatibility and refusal tests for compact asset inventory transport."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    ASSET_TABLE_FIELDS,
    encode_asset_inventory,
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.writer import (
    write_static_atlas_assets,
)

from .fixtures.layers import build_point_layers

ROOT = Path(__file__).resolve().parents[7]


def _inventory(tmp_path: Path) -> dict[str, object]:
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="fixture",
        point_layers=build_point_layers(),
        polygon_layers=[],
    )
    return cast(dict[str, object], deepcopy(assets.manifest["assets"]))


def test_columnar_inventory_reconstructs_exact_ordered_rows(tmp_path: Path) -> None:
    inventory = _inventory(tmp_path)
    assert inventory == {
        "schema_version": "atlas-static-asset-table.v1",
        "fields": list(ASSET_TABLE_FIELDS),
        "record_count": len(cast(list[object], inventory["records"])),
        "records": inventory["records"],
    }

    rows = normalize_asset_inventory(inventory)

    assert normalize_asset_inventory(encode_asset_inventory(rows)) == rows
    assert [row["sequence"] for row in rows] == list(range(len(rows)))
    assert len({row["asset_key"] for row in rows}) == len(rows)
    assert len({row["path"] for row in rows}) == len(rows)
    assert all(
        set(row) == set(ASSET_TABLE_FIELDS) for row in rows if row["domain"] == "nodes"
    )
    assert all(
        set(row) == set(ASSET_TABLE_FIELDS[:12])
        for row in rows
        if row["domain"] != "nodes"
    )


def test_checked_in_v1_inventory_remains_normalizable() -> None:
    manifest = json.loads(
        (ROOT / "docs/report/regions/nordic/nordic_map_assets.json").read_text(
            encoding="utf-8"
        )
    )

    rows = normalize_asset_inventory(manifest["assets"])

    assert len(rows) == 110
    assert [row["sequence"] for row in rows] == list(range(110))
    assert any(row["domain"] == "nodes" for row in rows)
    assert all("decoded_byte_count" not in row for row in rows)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("unknown_table_key", "table shape"),
        ("missing_field", "table fields"),
        ("duplicate_field", "table fields"),
        ("count_drift", "table count"),
        ("row_width", "row width"),
        ("duplicate_asset_key", "duplicated"),
        ("duplicate_path", "duplicated"),
        ("duplicate_sequence", "duplicated"),
        ("invalid_sequence_type", "sequence is invalid"),
    ],
)
def test_columnar_inventory_refuses_structural_drift(
    tmp_path: Path, mutation: str, message: str
) -> None:
    inventory = _inventory(tmp_path)
    records = cast(list[list[object]], inventory["records"])
    fields = cast(list[str], inventory["fields"])
    indexes = {field: index for index, field in enumerate(fields)}
    if mutation == "unknown_table_key":
        inventory["unexpected"] = True
    elif mutation == "missing_field":
        fields.pop()
    elif mutation == "duplicate_field":
        fields[-1] = fields[0]
    elif mutation == "count_drift":
        inventory["record_count"] = len(records) + 1
    elif mutation == "row_width":
        records[0].pop()
    elif mutation == "duplicate_asset_key":
        records[1][indexes["asset_key"]] = records[0][indexes["asset_key"]]
    elif mutation == "duplicate_path":
        records[1][indexes["path"]] = records[0][indexes["path"]]
    elif mutation == "duplicate_sequence":
        records[1][indexes["sequence"]] = records[0][indexes["sequence"]]
    else:
        records[0][indexes["sequence"]] = "zero"

    with pytest.raises(ValueError, match=message):
        normalize_asset_inventory(inventory)
