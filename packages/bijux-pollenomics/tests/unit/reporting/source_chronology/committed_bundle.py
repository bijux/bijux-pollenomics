"""Read the checked Nordic bundle as inputs for combined-budget proof."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from bijux_pollenomics.core.geospatial.geojson import JsonObject
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)


def committed_nordic_inputs(
    root: Path,
) -> tuple[
    list[JsonObject],
    list[JsonObject],
    list[JsonObject],
    list[JsonObject],
    list[JsonObject],
    list[JsonObject],
]:
    """Authenticate and hydrate every checked Nordic static-atlas domain."""
    bundle_root = root / "docs/report/regions/nordic"
    manifest = cast(
        dict[str, object],
        json.loads((bundle_root / "nordic_map_assets.json").read_text("utf-8")),
    )
    asset_rows = normalize_asset_inventory(manifest["assets"])
    payloads = {
        cast(str, row["asset_key"]): decode_chunk_script(
            (bundle_root / cast(str, row["path"])).read_bytes(),
            expected_asset_key=cast(str, row["asset_key"]),
            expected_payload_sha256=cast(str, row["payload_sha256"]),
            expected_payload_encoding=cast(str, row["payload_encoding"]),
        )
        for row in asset_rows
    }
    provenance = next(
        payloads[cast(str, row["asset_key"])]
        for row in asset_rows
        if row["domain"] == "provenance"
    )
    node_payloads = [
        payloads[cast(str, row["asset_key"])]
        for row in asset_rows
        if row["domain"] == "nodes"
    ]
    point_layers: list[JsonObject] = []
    polygon_layers: list[JsonObject] = []
    for raw_entry in cast(list[dict[str, object]], provenance["layers"]):
        layer_index = cast(int, raw_entry["layer_index"])
        layer_kind = cast(str, raw_entry["layer_kind"])
        layer = dict(cast(Mapping[str, object], raw_entry["layer"]))
        indexed_features = sorted(
            (
                cast(int, feature_index),
                cast(JsonObject, feature),
            )
            for payload in node_payloads
            if payload["layer_index"] == layer_index
            for feature_index, feature in zip(
                cast(list[object], payload["feature_indexes"]),
                cast(list[object], payload["features"]),
                strict=True,
            )
        )
        features = [feature for _index, feature in indexed_features]
        if layer_kind == "point":
            layer["features"] = features
            point_layers.append(layer)
        else:
            geojson = dict(cast(Mapping[str, object], layer["geojson"]))
            geojson["features"] = features
            layer["geojson"] = geojson
            polygon_layers.append(layer)
    details = _domain_records(asset_rows, payloads, "details")
    edges = _domain_records(asset_rows, payloads, "edges")
    sequences = _domain_records(asset_rows, payloads, "sequences")
    signals = cast(list[JsonObject], provenance["scientific_signals"])
    return point_layers, polygon_layers, details, signals, edges, sequences


def _domain_records(
    rows: list[dict[str, object]],
    payloads: Mapping[str, Mapping[str, object]],
    domain: str,
) -> list[JsonObject]:
    return [
        cast(JsonObject, record)
        for row in rows
        if row["domain"] == domain
        for record in cast(
            list[object], payloads[cast(str, row["asset_key"])]["records"]
        )
    ]


__all__ = ["committed_nordic_inputs"]
