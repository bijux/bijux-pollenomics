"""Reusable authenticated static-atlas reconciliation helpers."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from pathlib import Path
from typing import cast

from bijux_pollenomics.reporting.map_document.static_assets.index_transport import (
    decode_index_payloads,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)


def decode_committed_static_indexes(
    bundle_root: Path,
    rows: list[dict[str, object]],
    *,
    manifest: Mapping[str, object],
) -> dict[str, object]:
    """Authenticate every declared physical part before logical index restoration."""
    index_rows = [row for row in rows if row["domain"] == "indexes"]
    payloads = {}
    for row in index_rows:
        body = (bundle_root / cast(str, row["path"])).read_bytes()
        assert len(body) == row["byte_count"]
        assert hashlib.sha256(body).hexdigest() == row["sha256"]
        key = cast(str, row["asset_key"])
        payloads[key] = decode_chunk_script(
            body,
            expected_asset_key=key,
            expected_payload_sha256=cast(str, row["payload_sha256"]),
            expected_payload_encoding=cast(str, row["payload_encoding"]),
            expected_decoded_byte_count=cast(int, row["decoded_byte_count"]),
        )
    return decode_index_payloads(index_rows, payloads, manifest=manifest)


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


__all__ = [
    "assert_point_layer_index_coverage",
    "decode_committed_static_indexes",
]
