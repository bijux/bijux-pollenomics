"""Atlas detail partitioning tests."""

from __future__ import annotations
import base64
import gzip
import json
from pathlib import Path
from typing import cast
from bijux_pollenomics.core.geospatial.geojson import JsonObject
from bijux_pollenomics.reporting.map_document.static_assets import (
    ATLAS_CHUNK_MAX_BYTES,
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE


def _payload(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    marker = "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push("
    envelope = json.loads(text[text.index(marker) + len(marker) : -3])
    payload_json = (
        gzip.decompress(base64.b64decode(envelope["payload_gzip_base64"])).decode(
            "utf-8"
        )
        if envelope.get("payload_encoding") == "gzip_base64"
        else envelope["payload_json"]
    )
    return cast(dict[str, object], json.loads(payload_json))


def test_high_volume_details_are_lazy_partitioned_and_exactly_indexed(
    tmp_path: Path,
) -> None:
    details: list[JsonObject] = [
        {
            "record_id": f"site:{index:05d}",
            "tabs": {"overview": {"payload": "x" * 6000, "ordinal": index}},
        }
        for index in range(800)
    ]
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()

    first = write_static_atlas_assets(
        first_root,
        slug="evidence",
        version="fixed-point",
        point_layers=[],
        polygon_layers=[],
        detail_records=details,
    )
    second = write_static_atlas_assets(
        second_root,
        slug="evidence",
        version="fixed-point",
        point_layers=[],
        polygon_layers=[],
        detail_records=list(reversed(details)),
    )

    assert first.manifest == second.manifest
    assert [path.read_bytes() for path in first.asset_paths] == [
        path.read_bytes() for path in second.asset_paths
    ]
    asset_rows = cast(list[dict[str, object]], first.manifest["assets"])
    detail_rows = [row for row in asset_rows if row["domain"] == "details"]
    assert len(detail_rows) > 1
    assert all(row["initial_load"] is False for row in detail_rows)
    assert all(
        cast(int, row["byte_count"]) <= ATLAS_CHUNK_MAX_BYTES for row in detail_rows
    )
    max_detail_record_bytes = max(
        len(
            json.dumps(
                record,
                ensure_ascii=True,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        for record in details
    )
    assert max_detail_record_bytes <= ATLAS_CHUNK_MAX_BYTES
    paths_by_key = {
        str(row["asset_key"]): path
        for row, path in zip(asset_rows, first.asset_paths, strict=True)
    }
    index_row = next(row for row in asset_rows if row["domain"] == "indexes")
    index_payload = _payload(paths_by_key[str(index_row["asset_key"])])
    detail_index = cast(dict[str, str], index_payload["detail_record_asset_keys"])
    assert set(detail_index) == {str(row["record_id"]) for row in details}
    reconstructed = {
        str(record["record_id"]): asset_key
        for asset_key, path in paths_by_key.items()
        if asset_key.startswith("details:")
        for record in cast(list[dict[str, object]], _payload(path)["records"])
    }
    assert detail_index == reconstructed
    initial = [row for row in asset_rows if row["initial_load"] is True]
    assert all(row["domain"] != "details" for row in initial)
    assert "detail_chunk_load_failed" in MAP_DOCUMENT_TEMPLATE
    assert "detail_record_asset_keys" in MAP_DOCUMENT_TEMPLATE
