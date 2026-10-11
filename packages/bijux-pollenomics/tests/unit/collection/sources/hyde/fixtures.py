from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.hyde import (
    DeclaredGridLayer,
    load_declared_grid,
)


@pytest.fixture
def declared_payload() -> dict[str, Any]:
    return {
        "schema_version": "hyde-declared-grid.v1",
        "source": {
            "kind": "synthetic_fixture",
            "release_claim": "synthetic-fixture",
            "url": None,
            "citation": None,
            "license_claim": None,
        },
        "grid": {
            "columns": 2,
            "rows": 2,
            "west": 10,
            "south": 60,
            "longitude_step": 1,
            "latitude_step": 1,
            "row_order": "north_to_south",
            "crs": "EPSG:4326",
        },
        "time": {
            "start": {"year": 2000, "era": "CE"},
            "end": {"year": 2000, "era": "CE"},
            "kind": "instant",
            "convention": "calendar-year-start-no-year-zero.v1",
        },
        "variable": {
            "source_label": "fixture managed land",
            "category_key": "fixture:managed_land",
            "scenario": "fixture:baseline",
            "quantity": "land_fraction",
            "units": "1",
        },
        "nodata_value": -9999,
        "values": [[0, 0.5], [-9999, 1]],
        "land_fractions": [[1, 0.5], [1, 1]],
    }


def write_layer(
    tmp_path: Path, payload: dict[str, Any], name: str = "layer.json"
) -> DeclaredGridLayer:
    path = tmp_path / name
    content = json.dumps(payload).encode()
    path.write_bytes(content)
    return load_declared_grid(path, expected_sha256=hashlib.sha256(content).hexdigest())
