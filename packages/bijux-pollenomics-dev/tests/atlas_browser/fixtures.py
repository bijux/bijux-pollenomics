"""Small content-bound atlas fixtures that never launch a browser."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
    AtlasCandidate,
    AtlasScope,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
BUILD_ID = f"atlas-{'d' * 64}"


def candidate() -> AtlasCandidate:
    """Return a valid immutable candidate identity."""
    return AtlasCandidate(SHA_A, SHA_B, SHA_C, BUILD_ID)


def write_static_atlas(root: Path) -> AtlasScope:
    """Write one minimal atlas manifest, document, and bound script."""
    output = root / "docs/report/regions/nordic"
    output.mkdir(parents=True)
    payload = b"globalThis.fixtureAtlas = true;\n"
    digest = hashlib.sha256(payload).hexdigest()
    asset = f"nordic.atlas-provenance.0000.{digest[:16]}.js"
    (output / asset).write_bytes(payload)
    document = (
        "<!doctype html><script>const tile='https://tile.openstreetmap.org/"
        "{z}/{x}/{y}.png'; const build='"
        + BUILD_ID
        + "';</script><script src=\""
        + asset
        + '"></script>\n'
    )
    (output / "nordic_map.html").write_text(document, encoding="utf-8")
    fields = [
        "domain",
        "sha256",
        "payload_sha256",
        "decoded_byte_count",
        "byte_count",
        "record_count",
        "layer_index",
        "layer_key",
        "layer_kind",
        "country_keys",
        "bounds",
        "time_min_bp",
        "time_max_bp",
        "untimed_record_count",
        "scientific_signal_ids",
    ]
    manifest = {
        "schema_version": "atlas-static-bootstrap.v2",
        "scope_slug": "nordic",
        "build_id": BUILD_ID,
        "budgets": {
            "static_assets_max_files": 2,
            "static_assets_max_bytes": 4096,
        },
        "assets": {
            "fields": fields,
            "record_count": 1,
            "records": [
                [
                    "provenance",
                    digest,
                    digest,
                    len(payload),
                    len(payload),
                    1,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ]
            ],
        },
    }
    (output / "nordic_map_assets.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    return AtlasScope(
        "nordic",
        "docs/report/regions/nordic/nordic_map.html",
        "docs/report/regions/nordic/nordic_map_assets.json",
    )
