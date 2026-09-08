"""Compatibility and refusal tests for compact asset inventory transport."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    ASSET_TABLE_FIELDS,
    ASSET_TABLE_SCHEMA,
    ASSET_TABLE_STORED_FIELDS,
    PREVIOUS_ASSET_TABLE_SCHEMA,
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
        "schema_version": "atlas-static-asset-table.v3",
        "scope_slug": "nordic",
        "fields": list(ASSET_TABLE_STORED_FIELDS),
        "record_count": len(cast(list[object], inventory["records"])),
        "records": inventory["records"],
    }

    rows = normalize_asset_inventory(inventory)

    assert (
        normalize_asset_inventory(encode_asset_inventory(rows, scope_slug="nordic"))
        == rows
    )
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


def test_checked_in_inventory_reconciles_to_manifest_contract() -> None:
    manifest = json.loads(
        (ROOT / "docs/report/regions/nordic/nordic_map_assets.json").read_text(
            encoding="utf-8"
        )
    )

    rows = normalize_asset_inventory(manifest["assets"])
    inventory = cast(dict[str, object], manifest["assets"])
    domains = cast(dict[str, dict[str, object]], manifest["domains"])

    assert len(rows) == inventory["record_count"]
    assert [row["sequence"] for row in rows] == list(range(len(rows)))
    assert len({row["asset_key"] for row in rows}) == len(rows)
    assert len({row["path"] for row in rows}) == len(rows)
    assert any(row["domain"] == "nodes" for row in rows)
    node_rows = [row for row in rows if row["domain"] == "nodes"]
    if inventory["schema_version"] == PREVIOUS_ASSET_TABLE_SCHEMA:
        assert all(
            row["chronology_absent_record_count"] is None
            and row["refused_chronology_record_count"] is None
            and row["contextual_chronology_record_count"] is None
            for row in node_rows
        )
    else:
        assert inventory["schema_version"] == ASSET_TABLE_SCHEMA
        for row in node_rows:
            chronology_counts = (
                row["chronology_absent_record_count"],
                row["refused_chronology_record_count"],
                row["contextual_chronology_record_count"],
            )
            assert all(
                isinstance(count, int) and not isinstance(count, bool) and count >= 0
                for count in chronology_counts
            )
            assert (
                sum(cast(tuple[int, int, int], chronology_counts))
                == row["untimed_record_count"]
            )
    for domain in ("nodes", "details", "edges", "sequences"):
        assert (
            sum(
                cast(int, row["record_count"])
                for row in rows
                if row["domain"] == domain
            )
            == domains[domain]["record_count"]
        )
    assert all(
        isinstance(row["decoded_byte_count"], int)
        for row in rows
        if row["payload_encoding"] == "gzip_base64"
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("unknown_table_key", "table shape"),
        ("missing_field", "table fields"),
        ("duplicate_field", "table fields"),
        ("count_drift", "table count"),
        ("row_width", "row width"),
        ("invalid_scope", "table scope"),
        ("invalid_digest", "sha256"),
        ("invalid_domain", "domain"),
        ("non_node_selection", "non-node selection"),
        ("negative_time", "BP bounds are invalid"),
        ("reversed_time", "BP bounds are invalid"),
        ("asymmetric_time", "BP bounds are asymmetric"),
        ("untimed_time_contradiction", "contradict untimed records"),
        ("excess_untimed_count", "exceeds record count"),
        ("incomplete_chronology_split", "chronology split is incomplete"),
        ("missing_chronology_split", "chronology split is required"),
        ("inconsistent_chronology_split", "chronology split is inconsistent"),
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
    elif mutation == "invalid_scope":
        inventory["scope_slug"] = "../nordic"
    elif mutation == "invalid_digest":
        records[0][indexes["sha256"]] = "not-a-digest"
    elif mutation == "invalid_domain":
        records[0][indexes["domain"]] = "unknown"
    elif mutation == "non_node_selection":
        non_node = next(
            record for record in records if record[indexes["domain"]] != "nodes"
        )
        non_node[indexes["layer_index"]] = 0
    else:
        node = next(
            record for record in records if record[indexes["domain"]] == "nodes"
        )
        if mutation == "negative_time":
            node[indexes["time_min_bp"]] = -1
        elif mutation == "reversed_time":
            node[indexes["time_min_bp"]] = 200
            node[indexes["time_max_bp"]] = 100
        elif mutation == "asymmetric_time":
            node[indexes["time_min_bp"]] = None
        elif mutation == "excess_untimed_count":
            node[indexes["untimed_record_count"]] = (
                cast(int, node[indexes["record_count"]]) + 1
            )
        elif mutation == "incomplete_chronology_split":
            node[indexes["chronology_absent_record_count"]] = None
        elif mutation == "missing_chronology_split":
            node[indexes["chronology_absent_record_count"]] = None
            node[indexes["refused_chronology_record_count"]] = None
            node[indexes["contextual_chronology_record_count"]] = None
        elif mutation == "inconsistent_chronology_split":
            node[indexes["refused_chronology_record_count"]] = (
                cast(int, node[indexes["refused_chronology_record_count"]]) + 1
            )
        else:
            node[indexes["chronology_absent_record_count"]] = node[
                indexes["record_count"]
            ]
            node[indexes["refused_chronology_record_count"]] = 0
            node[indexes["contextual_chronology_record_count"]] = 0
            node[indexes["untimed_record_count"]] = node[indexes["record_count"]]

    with pytest.raises(ValueError, match=message):
        normalize_asset_inventory(inventory)
