from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (
    decode_index_bundle,
)

from .fixtures.layers import build_point_layers, build_polygon_layers
from .payloads import read_static_asset_payload


def test_static_assets_ship_build_time_indexes_and_execute_without_fetch(
    tmp_path: Path,
) -> None:
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="v66",
        point_layers=build_point_layers(),
        polygon_layers=build_polygon_layers(),
    )
    scripts = "\n".join(path.read_text(encoding="utf-8") for path in assets.asset_paths)
    rows = normalize_asset_inventory(assets.manifest["assets"])
    index_path = next(
        path
        for row, path in zip(rows, assets.asset_paths, strict=True)
        if row["domain"] == "indexes"
    )
    indexes = decode_index_bundle(read_static_asset_payload(index_path))
    assert set(indexes) >= {
        "country_feature_indexes",
        "spatial_degree_feature_indexes",
        "time_interval_feature_indexes",
        "signal_layer_indexes",
    }
    assert "fetch(" not in scripts

    node = shutil.which("node")
    assert node is not None
    probe = (
        scripts
        + "\nconst zlib=require('node:zlib');"
        + "const payloads=globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.map((row)=>JSON.parse(row.payload_encoding==='gzip_base64'?zlib.gunzipSync(Buffer.from(row.payload_gzip_base64,'base64')).toString('utf8'):row.payload_json));"
        + "const nodes=payloads.filter((row)=>row.schema_version==='atlas-node-chunk.v1');"
        + "const edges=payloads.find((row)=>row.schema_version==='atlas-edges-chunk.v1');"
        + "const sequences=payloads.find((row)=>row.schema_version==='atlas-sequences-chunk.v1');"
        + "console.log(JSON.stringify({nodes:nodes.length,records:nodes.reduce((total,row)=>total+row.features.length,0),edges:edges.records.length,sequences:sequences.records.length}));"
    )
    result = subprocess.run(
        [node, "-e", probe], check=True, capture_output=True, text=True
    )
    observed = json.loads(result.stdout)
    assert observed["nodes"] >= 2
    assert observed["records"] == 3
    assert observed["edges"] == 0
    assert observed["sequences"] == 0
