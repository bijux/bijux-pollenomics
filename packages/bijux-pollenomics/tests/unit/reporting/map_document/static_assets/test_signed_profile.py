"""Complete signed static transport keeps profile, node and index identities joined."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.core.calendar_support import SIGNED_CALENDAR_PROFILE
from bijux_pollenomics.reporting.map_document.native_lra import bind_native_view
from bijux_pollenomics.reporting.map_document.static_assets import (
    validate_static_atlas_assets,
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (
    decode_index_bundle,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)

from ..lra_products.signed_support import signed_fixture


@pytest.mark.parametrize("bounds", [(-50.75, -49.25), (-0.5, 0.25), (0, 0), (10, 20)])
def test_actual_signed_encoder_reconciles_every_typed_transport(
    tmp_path: Path, bounds: tuple[int | float, int | float]
) -> None:
    view, layers = signed_fixture(*bounds)
    assets = write_static_atlas_assets(
        tmp_path,
        slug="synthetic",
        version="v0.2.0",
        point_layers=layers,
        polygon_layers=[],
        temporal_profile=SIGNED_CALENDAR_PROFILE,
        native_lra=view,
    )
    validate_static_atlas_assets(assets)
    assert assets.manifest["schema_version"] == "atlas-static-bootstrap.v3"
    assert assets.manifest["native_view_sha256"] == bind_native_view(view)["sha256"]
    assert isinstance(assets.manifest["assets"], dict)
    assert assets.manifest["assets"]["schema_version"] == "atlas-static-asset-table.v4"
    rows = normalize_asset_inventory(assets.manifest["assets"])
    for row, path in zip(rows, assets.asset_paths, strict=True):
        decoded_count = row["decoded_byte_count"]
        assert isinstance(decoded_count, int)
        payload = decode_chunk_script(
            path.read_bytes(),
            expected_asset_key=str(row["asset_key"]),
            expected_payload_sha256=str(row["payload_sha256"]),
            expected_payload_encoding=str(row["payload_encoding"]),
            expected_decoded_byte_count=decoded_count,
        )
        assert (
            payload["temporal_profile"] == SIGNED_CALENDAR_PROFILE
            and payload["temporal_axis"] == "BP1950"
        )
        if row["domain"] == "nodes":
            assert payload["schema_version"] == "atlas-node-chunk.v2"
            assert (row["time_min_bp"], row["time_max_bp"]) == bounds
            assert row["untimed_record_count"] == 0
        if row["domain"] == "indexes":
            assert payload["schema_version"] == "atlas-static-indexes.v4"
            assert payload["shard_schema"] == "atlas-static-index-shard.v2"
            indexes = decode_index_bundle(payload)
            assert indexes["schema_version"] == "atlas-static-signed-indexes.v1"
            assert indexes["time_interval_feature_indexes"] == [
                [*bounds, "layer-l", 0],
                [*bounds, "layer-r", 0],
            ]
    changed = copy.deepcopy(assets.manifest["assets"])
    changed["temporal_axis"] = "CE"
    with pytest.raises(ValueError):
        normalize_asset_inventory(changed)
    changed = copy.deepcopy(assets.manifest["assets"])
    changed["schema_version"] = "atlas-static-asset-table.v3"
    with pytest.raises(ValueError):
        normalize_asset_inventory(changed)


@pytest.mark.parametrize(
    "case",
    [
        "no_view",
        "no_profile",
        "wrong_profile",
        "source_layer",
        "polygon",
        "edge",
        "sequence",
        "wrong_view",
    ],
)
def test_signed_writer_refuses_incomplete_authorization_before_writes(
    tmp_path: Path, case: str
) -> None:
    view, layers = signed_fixture()
    kwargs: dict[str, Any] = {
        "slug": "synthetic",
        "version": "v0.2.0",
        "point_layers": layers,
        "polygon_layers": [],
        "temporal_profile": SIGNED_CALENDAR_PROFILE,
        "native_lra": view,
    }
    if case == "no_view":
        kwargs["native_lra"] = None
    elif case == "no_profile":
        kwargs["temporal_profile"] = None
    elif case == "wrong_profile":
        kwargs["temporal_profile"] = "unknown"
    elif case == "source_layer":
        layers[0]["semantic_role"] = "source_chronology"
    elif case == "polygon":
        kwargs["polygon_layers"] = [{"key": "source", "geojson": {}}]
    elif case == "edge":
        kwargs["edge_records"] = [{"record_id": "source-edge"}]
    elif case == "sequence":
        kwargs["sequence_records"] = [{"record_id": "source-sequence"}]
    else:
        view["product_manifest_sha256"] = "f" * 64
    with pytest.raises(ValueError):
        write_static_atlas_assets(tmp_path, **kwargs)
    assert list(tmp_path.iterdir()) == []


def test_legacy_writer_does_not_acquire_signed_time_from_feature_fields(
    tmp_path: Path,
) -> None:
    _, layers = signed_fixture()
    assets = write_static_atlas_assets(
        tmp_path,
        slug="legacy",
        version="v0.2.0",
        point_layers=layers,
        polygon_layers=[],
    )
    assert assets.manifest["schema_version"] == "atlas-static-bootstrap.v2"
    assert "temporal_profile" not in assets.manifest
    for row in normalize_asset_inventory(assets.manifest["assets"]):
        if row["domain"] == "nodes":
            assert row["time_min_bp"] is None and row["time_max_bp"] is None
            assert row["refused_chronology_record_count"] == row["record_count"]


@pytest.mark.parametrize(
    "case", ["index_interval", "node_interval", "shard_axis", "node_age_type"]
)
def test_fully_rehashed_temporal_contradictions_refuse(
    tmp_path: Path, case: str
) -> None:
    import base64
    import gzip
    from hashlib import sha256
    import json

    from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
        encode_asset_inventory,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (
        build_index_bundle,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.models import (
        StaticAtlasAssets,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.nodes import (
        node_asset_selection,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
        canonical_json,
        chunk_script_bytes,
    )

    view, layers = signed_fixture()
    assets = write_static_atlas_assets(
        tmp_path,
        slug="synthetic",
        version="v0.2.0",
        point_layers=layers,
        polygon_layers=[],
        temporal_profile=SIGNED_CALENDAR_PROFILE,
        native_lra=view,
    )
    rows = normalize_asset_inventory(assets.manifest["assets"])
    paths = list(assets.asset_paths)
    target_domain = "indexes" if case.startswith(("index", "shard")) else "nodes"
    position = next(
        index for index, row in enumerate(rows) if row["domain"] == target_domain
    )
    row = rows[position]
    decoded_count = row["decoded_byte_count"]
    assert isinstance(decoded_count, int)
    payload: Any = decode_chunk_script(
        paths[position].read_bytes(),
        expected_asset_key=str(row["asset_key"]),
        expected_payload_sha256=str(row["payload_sha256"]),
        expected_payload_encoding=str(row["payload_encoding"]),
        expected_decoded_byte_count=decoded_count,
    )
    if case == "index_interval":
        indexes: Any = decode_index_bundle(payload)
        indexes["time_interval_feature_indexes"][0][0] = -50.5
        payload = {**build_index_bundle(indexes), "asset_key": payload["asset_key"]}
    elif case == "shard_axis":
        envelope = payload["shards"][0]
        shard = json.loads(
            gzip.decompress(base64.b64decode(envelope["payload_gzip_base64"]))
        )
        shard["temporal_axis"] = "CE"
        encoded = canonical_json(shard).encode()
        envelope.update(
            payload_sha256=sha256(encoded).hexdigest(),
            decoded_byte_count=len(encoded),
            payload_gzip_base64=base64.b64encode(
                gzip.compress(encoded, mtime=0)
            ).decode(),
        )
    elif case == "node_age_type":
        payload["features"][0]["age_type"] = "radiocarbon_bp"
    else:
        feature = payload["features"][0]
        feature["time_start_bp"] = -50.5
        feature["source_age_support_bp"][0][0] = -50.5
        for key in ("source_calendar_support", "declared_calendar_support"):
            feature[key]["younger_bp"] = -50.5
        row.update(node_asset_selection(payload))
    encoded_json = canonical_json(payload)
    payload_sha = sha256(encoded_json.encode()).hexdigest()
    raw = chunk_script_bytes(
        asset_key=str(row["asset_key"]),
        payload_sha256=payload_sha,
        payload_json=encoded_json,
        payload_encoding=str(row["payload_encoding"]),
    )
    digest = sha256(raw).hexdigest()
    name = f"synthetic.atlas-{row['domain']}.{row['sequence']:04d}.{digest[:16]}.js"
    path = tmp_path / name
    path.write_bytes(raw)
    paths[position] = path
    row.update(
        path=name,
        sha256=digest,
        integrity="sha256-" + base64.b64encode(sha256(raw).digest()).decode(),
        payload_sha256=payload_sha,
        byte_count=len(raw),
        decoded_byte_count=len(encoded_json.encode()),
    )
    manifest = copy.deepcopy(assets.manifest)
    manifest["assets"] = encode_asset_inventory(
        rows, scope_slug="synthetic", temporal_profile=SIGNED_CALENDAR_PROFILE
    )
    assets.manifest_path.write_text(canonical_json(manifest) + "\n")
    forged = StaticAtlasAssets(assets.manifest_path, manifest, tuple(paths))
    with pytest.raises(ValueError):
        validate_static_atlas_assets(forged)
