"""Reusable authenticated static-atlas reconciliation helpers."""

from __future__ import annotations

from typing import cast

from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (
    decode_index_bundle,
)
from bijux_pollenomics.reporting.map_document.static_assets.models import (
    StaticAtlasAssets,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)


def decode_static_indexes(
    assets: StaticAtlasAssets, rows: list[dict[str, object]]
) -> dict[str, object]:
    """Authenticate and decode the unique physical index bundle."""
    index_rows = [row for row in rows if row["domain"] == "indexes"]
    if len(index_rows) != 1:
        raise AssertionError("static atlas must contain exactly one index asset")
    row = index_rows[0]
    payload = decode_chunk_script(
        assets.asset_paths[rows.index(row)].read_bytes(),
        expected_asset_key=cast(str, row["asset_key"]),
        expected_payload_sha256=cast(str, row["payload_sha256"]),
        expected_payload_encoding=cast(str, row["payload_encoding"]),
        expected_decoded_byte_count=cast(int, row["decoded_byte_count"]),
    )
    return decode_index_bundle(payload)


def assert_point_layer_index_coverage(
    indexes: dict[str, object], layer_counts: dict[str, int]
) -> None:
    """Assert exact country, spatial, and time coverage for selected layers."""
    expected_total = sum(layer_counts.values())
    for index_name in (
        "country_feature_indexes",
        "spatial_degree_feature_indexes",
    ):
        nested = cast(dict[str, dict[str, list[int]]], indexes[index_name])
        by_layer = {
            layer_key: sorted(
                feature_index
                for layer_rows in nested.values()
                for feature_index in layer_rows.get(layer_key, [])
            )
            for layer_key in layer_counts
        }
        assert sum(len(rows) for rows in by_layer.values()) == expected_total
        assert all(
            by_layer[layer_key] == list(range(count))
            for layer_key, count in layer_counts.items()
        )
    time_rows = cast(list[list[object]], indexes["time_interval_feature_indexes"])
    selected_time_rows = [row for row in time_rows if row[2] in layer_counts]
    assert len(selected_time_rows) == expected_total
    for layer_key, count in layer_counts.items():
        assert sorted(
            cast(int, row[3]) for row in time_rows if row[2] == layer_key
        ) == list(range(count))


def static_asset_metrics(
    assets: StaticAtlasAssets, rows: list[dict[str, object]]
) -> dict[str, int]:
    """Return physical, decoded, bootstrap, and initial-load measurements."""
    initial = [row for row in rows if row["initial_load"] is True]
    return {
        "asset_count": len(assets.asset_paths),
        "bootstrap_bytes": assets.manifest_path.stat().st_size,
        "total_bytes": sum(path.stat().st_size for path in assets.asset_paths),
        "max_chunk_bytes": max(path.stat().st_size for path in assets.asset_paths),
        "max_decoded_chunk_bytes": max(
            cast(int, row["decoded_byte_count"]) for row in rows
        ),
        "initial_requests": len(initial),
        "initial_bytes": sum(cast(int, row["byte_count"]) for row in initial),
    }


__all__ = [
    "assert_point_layer_index_coverage",
    "decode_static_indexes",
    "static_asset_metrics",
]
