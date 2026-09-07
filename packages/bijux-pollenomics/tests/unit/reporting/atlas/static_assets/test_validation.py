from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics.reporting.map_document.static_assets import (
    ATLAS_CHUNK_MAX_BYTES,
    validate_static_atlas_assets,
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    canonical_json,
    chunk_script_bytes,
    decode_chunk_script,
)

from .fixtures.layers import build_point_layers
from .fixtures.scientific_evidence import (
    build_scientific_point_layers,
    build_scientific_signals,
)


def test_scientific_fixture_refuses_unaccepted_or_unknown_signals(
    tmp_path: Path,
) -> None:
    signals = build_scientific_signals()
    signals[0]["status"] = "review"
    with pytest.raises(ValueError, match="not accepted"):
        write_static_atlas_assets(
            tmp_path,
            slug="nordic",
            version="v66",
            point_layers=build_scientific_point_layers(),
            polygon_layers=[],
            scientific_signals=signals,
        )

    point_layers = build_scientific_point_layers()
    features = point_layers[0]["features"]
    assert isinstance(features, list)
    assert isinstance(features[0], dict)
    features[0]["scientific_signal_ids"] = ["pollen:unreviewed"]
    with pytest.raises(ValueError, match="unaccepted scientific signals"):
        write_static_atlas_assets(
            tmp_path,
            slug="nordic",
            version="v66",
            point_layers=point_layers,
            polygon_layers=[],
            scientific_signals=build_scientific_signals(),
        )


def test_static_asset_validation_detects_tampering(tmp_path: Path) -> None:
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="v66",
        point_layers=build_point_layers(),
        polygon_layers=[],
    )
    assets.asset_paths[0].write_text("changed", encoding="utf-8")

    with pytest.raises(ValueError, match="byte count changed|digest changed"):
        validate_static_atlas_assets(assets)


@pytest.mark.parametrize(
    ("schema", "inventory", "message"),
    [
        ("atlas-static-bootstrap.unknown", {}, "bootstrap schema"),
        ("atlas-static-bootstrap.v1", {}, "v1 asset inventory"),
        ("atlas-static-bootstrap.v2", [], "v2 asset inventory"),
    ],
)
def test_bootstrap_schema_and_inventory_encoding_must_agree(
    tmp_path: Path, schema: str, inventory: object, message: str
) -> None:
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="v66",
        point_layers=build_point_layers(),
        polygon_layers=[],
    )
    assets.manifest["schema_version"] = schema
    assets.manifest["assets"] = inventory
    assets.manifest_path.write_text(
        canonical_json(assets.manifest) + "\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match=message):
        validate_static_atlas_assets(assets)


def test_single_unbounded_feature_is_refused(tmp_path: Path) -> None:
    layers = build_point_layers()
    features = layers[0]["features"]
    assert isinstance(features, list)
    assert isinstance(features[0], dict)
    features[0]["description"] = "x" * (ATLAS_CHUNK_MAX_BYTES + 1)

    with pytest.raises(ValueError, match="one static atlas feature"):
        write_static_atlas_assets(
            tmp_path,
            slug="nordic",
            version="v66",
            point_layers=layers,
            polygon_layers=[],
        )


def test_compressed_payload_refuses_over_budget_expansion() -> None:
    payload_json = '"' + "x" * (ATLAS_CHUNK_MAX_BYTES + 1) + '"'
    digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    script = chunk_script_bytes(
        asset_key="nodes:1",
        payload_sha256=digest,
        payload_json=payload_json,
        payload_encoding="gzip_base64",
    )

    with pytest.raises(ValueError, match="exceeds its decoded budget"):
        decode_chunk_script(
            script,
            expected_asset_key="nodes:1",
            expected_payload_sha256=digest,
            expected_payload_encoding="gzip_base64",
            expected_decoded_byte_count=len(payload_json),
        )


def test_compressed_payload_uses_platform_neutral_gzip_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    platform_gzip_compress = gzip.compress

    def compress_with_platform_header(
        payload: bytes, *, compresslevel: int, mtime: int
    ) -> bytes:
        compressed = bytearray(
            platform_gzip_compress(
                payload,
                compresslevel=compresslevel,
                mtime=mtime,
            )
        )
        compressed[9] = 19
        return bytes(compressed)

    monkeypatch.setattr(gzip, "compress", compress_with_platform_header)
    payload_json = canonical_json({"records": [{"id": "sample"}]})
    script = chunk_script_bytes(
        asset_key="nodes:1",
        payload_sha256=hashlib.sha256(payload_json.encode()).hexdigest(),
        payload_json=payload_json,
        payload_encoding="gzip_base64",
    )
    envelope = json.loads(script.decode().split(".push(", maxsplit=1)[1][:-3])
    compressed = base64.b64decode(envelope["payload_gzip_base64"])

    assert compressed[9] == 255
    assert gzip.decompress(compressed).decode() == payload_json


def test_compressed_payload_normalizes_truncated_gzip_failure() -> None:
    envelope = {
        "asset_key": "nodes:1",
        "payload_sha256": "0" * 64,
        "payload_encoding": "gzip_base64",
        "payload_gzip_base64": base64.b64encode(b"not-gzip").decode("ascii"),
    }
    script = (
        "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__="
        "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__||[];"
        f"globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push({json.dumps(envelope)});\n"
    ).encode()

    with pytest.raises(ValueError, match="compressed payload is invalid"):
        decode_chunk_script(
            script,
            expected_asset_key="nodes:1",
            expected_payload_sha256="0" * 64,
            expected_payload_encoding="gzip_base64",
        )
