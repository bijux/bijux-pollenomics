"""Capacity coherence for the bounded static-atlas bootstrap."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import cast

from bijux_pollenomics.reporting.map_document.static_assets import (
    ATLAS_BOOTSTRAP_MAX_BYTES,
    ATLAS_INITIAL_MAX_BYTES,
    ATLAS_STATIC_ASSETS_MAX_FILES,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    encode_asset_inventory,
)

ROOT = Path(__file__).resolve().parents[7]


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _integrity(digest: str) -> str:
    return "sha256-" + base64.b64encode(bytes.fromhex(digest)).decode("ascii")


def test_bootstrap_budget_can_encode_the_maximum_asset_inventory() -> None:
    rows: list[dict[str, object]] = []
    for sequence in range(ATLAS_STATIC_ASSETS_MAX_FILES):
        wire_digest = _digest(f"wire:{sequence}")
        payload_digest = _digest(f"payload:{sequence}")
        rows.append(
            {
                "asset_key": f"nodes:{sequence}",
                "domain": "nodes",
                "sequence": sequence,
                "path": (
                    "capacity.atlas-nodes."
                    f"{sequence:04d}.{wire_digest[:16]}.js"
                ),
                "sha256": wire_digest,
                "integrity": _integrity(wire_digest),
                "payload_sha256": payload_digest,
                "payload_encoding": "gzip_base64",
                "decoded_byte_count": 1,
                "byte_count": 1,
                "record_count": 1,
                "initial_load": False,
                "layer_index": 0,
                "layer_key": "capacity-layer",
                "layer_kind": "point",
                "country_keys": [],
                "bounds": [0.0, 0.0, 0.0, 0.0],
                "time_min_bp": 0,
                "time_max_bp": 0,
                "untimed_record_count": 0,
                "chronology_absent_record_count": 0,
                "refused_chronology_record_count": 0,
                "contextual_chronology_record_count": 0,
                "scientific_signal_ids": [],
            }
        )

    inventory = encode_asset_inventory(rows, scope_slug="capacity")
    encoded_bootstrap = json.dumps(
        {"assets": inventory},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    records = cast(list[list[object]], inventory["records"])
    assert inventory["record_count"] == ATLAS_STATIC_ASSETS_MAX_FILES
    assert all(
        isinstance(row[1], str)
        and isinstance(row[2], str)
        and len(row[1]) == len(row[2]) == 64
        for row in records
    )
    assert len(encoded_bootstrap) <= ATLAS_BOOTSTRAP_MAX_BYTES
    assert ATLAS_BOOTSTRAP_MAX_BYTES <= ATLAS_INITIAL_MAX_BYTES


def test_committed_nordic_bootstrap_remains_within_budget() -> None:
    manifest_path = ROOT / "docs/report/regions/nordic/nordic_map_assets.json"

    assert manifest_path.is_file()
    assert manifest_path.stat().st_size <= ATLAS_BOOTSTRAP_MAX_BYTES
