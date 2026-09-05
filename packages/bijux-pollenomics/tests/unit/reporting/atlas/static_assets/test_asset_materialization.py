from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess


from bijux_pollenomics.core.geospatial.geojson import JsonObject
from bijux_pollenomics.reporting.map_document.evidence import DETAIL_TAB_KEYS
from bijux_pollenomics.reporting.map_document.static_assets import (
    ATLAS_BOOTSTRAP_MAX_BYTES,
    ATLAS_CHUNK_MAX_BYTES,
    ATLAS_CHUNK_TARGET_BYTES,
    ATLAS_INITIAL_MAX_BYTES,
    ATLAS_INITIAL_MAX_REQUESTS,
    ATLAS_INTERACTION_MAX_BYTES,
    validate_static_atlas_assets,
    write_static_atlas_assets,
)

from .fixtures.layers import build_point_layers, build_polygon_layers
from .fixtures.scientific_evidence import (
    build_detail_records,
    build_edge_records,
    build_scientific_point_layers,
    build_scientific_signals,
)
from .payloads import read_static_asset_payload


def test_static_assets_are_deterministic_hashed_and_domain_accounted(
    tmp_path: Path,
) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first = write_static_atlas_assets(
        first_root,
        slug="nordic",
        version="v66",
        point_layers=build_point_layers(large=True),
        polygon_layers=build_polygon_layers(),
    )
    second = write_static_atlas_assets(
        second_root,
        slug="nordic",
        version="v66",
        point_layers=build_point_layers(large=True),
        polygon_layers=build_polygon_layers(),
    )

    assert first.manifest == second.manifest
    assert first.manifest_path.read_bytes() == second.manifest_path.read_bytes()
    assert [path.name for path in first.asset_paths] == [
        path.name for path in second.asset_paths
    ]
    assert len(first.manifest_path.read_bytes()) <= ATLAS_BOOTSTRAP_MAX_BYTES
    assert str(first.manifest["build_id"]).startswith("atlas-")
    assert first.manifest["load_strategy"] == "selection_aware_static_scripts"
    assert first.manifest["transport_integrity"] == {
        "http_https": "subresource_integrity_plus_payload_sha256",
        "file": "payload_sha256_after_script_registration",
        "file_pre_execution_sri": False,
    }
    domains = first.manifest["domains"]
    assert isinstance(domains, dict)
    assert domains["nodes"]["status"] == "available"
    assert domains["edges"] == {
        "status": "unavailable",
        "record_count": 0,
        "reason_code": "governed_map_edge_model_not_available",
    }
    assert domains["sequences"] == {
        "status": "unavailable",
        "record_count": 0,
        "reason_code": "governed_sequence_detail_model_not_available",
    }
    assert domains["provenance"]["status"] == "layer_metadata_only"
    assert domains["details"] == {
        "status": "unavailable",
        "record_count": 0,
        "reason_code": "record_level_evidence_not_available",
    }
    assert domains["classifications"] == {
        "status": "unavailable",
        "record_count": 0,
        "reason_code": "accepted_scientific_classifications_not_available",
    }
    assets = first.manifest["assets"]
    assert isinstance(assets, list)
    node_assets = [row for row in assets if row["domain"] == "nodes"]
    assert len(node_assets) > 1
    assert {tuple(row["country_keys"]) for row in node_assets} >= {
        ("Norway",),
        ("Sweden",),
    }
    assert all(row["initial_load"] is False for row in node_assets)
    initial_assets = [row for row in assets if row["initial_load"] is True]
    assert len(initial_assets) <= ATLAS_INITIAL_MAX_REQUESTS
    assert sum(row["byte_count"] for row in initial_assets) <= ATLAS_INITIAL_MAX_BYTES
    budgets = first.manifest["budgets"]
    assert isinstance(budgets, dict)
    assert budgets["interaction_max_bytes"] == ATLAS_INTERACTION_MAX_BYTES
    for row, path in zip(assets, first.asset_paths, strict=True):
        payload = path.read_bytes()
        assert len(payload) <= ATLAS_CHUNK_MAX_BYTES
        assert row["byte_count"] == len(payload)
        assert row["sha256"] == hashlib.sha256(payload).hexdigest()
        assert str(row["sha256"])[:16] in path.name


def test_accepted_scientific_fixture_populates_truthful_atlas_domains(
    tmp_path: Path,
) -> None:
    point_layers = build_scientific_point_layers()
    signals = build_scientific_signals()
    details = build_detail_records()
    edges = build_edge_records()
    sequences: list[JsonObject] = [
        {
            "sequence_id": "sequence:1",
            "signal_id": "pollen:whole",
            "record_ids": ["site:1", "site:2"],
        }
    ]
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()

    first = write_static_atlas_assets(
        first_root,
        slug="nordic",
        version="v66",
        point_layers=point_layers,
        polygon_layers=[],
        detail_records=details,
        scientific_signals=signals,
        edge_records=edges,
        sequence_records=sequences,
    )
    second = write_static_atlas_assets(
        second_root,
        slug="nordic",
        version="v66",
        point_layers=point_layers,
        polygon_layers=[],
        detail_records=list(reversed(details)),
        scientific_signals=list(reversed(signals)),
        edge_records=list(reversed(edges)),
        sequence_records=list(reversed(sequences)),
    )

    assert first.manifest == second.manifest
    asset_rows = first.manifest["assets"]
    assert isinstance(asset_rows, list)
    assert all(
        row["payload_encoding"]
        == ("gzip_base64" if row["domain"] == "details" else "json")
        for row in asset_rows
    )
    domains = first.manifest["domains"]
    assert isinstance(domains, dict)
    assert domains["classifications"] == {
        "status": "available",
        "record_count": 4,
        "reason_code": None,
    }
    assert domains["details"] == {
        "status": "available",
        "record_count": 1,
        "reason_code": None,
    }
    assert domains["edges"] == {
        "status": "available",
        "record_count": 2,
        "reason_code": None,
    }
    assert domains["sequences"] == {
        "status": "available",
        "record_count": 1,
        "reason_code": None,
    }
    payloads = {
        read_static_asset_payload(path)["schema_version"]: read_static_asset_payload(
            path
        )
        for path in first.asset_paths
    }
    provenance = payloads["atlas-provenance-chunk.v3"]
    assert provenance["details_status"] == "available"
    assert provenance["classifications_status"] == "available"
    details_payload = payloads["atlas-details-chunk.v1"]
    detail_tabs = details_payload["records"][0]["tabs"]
    assert set(detail_tabs) == set(DETAIL_TAB_KEYS)
    observed_signals = provenance["scientific_signals"]
    assert [row["signal_id"] for row in observed_signals] == sorted(
        row["signal_id"] for row in signals
    )
    assert len({row["color"] for row in observed_signals}) == len(observed_signals)
    assert all(row["non_color_cue"] for row in observed_signals)
    assert payloads["atlas-edges-chunk.v1"]["records"][0]["cross_border"] is True


def test_compressed_details_use_the_decoded_chunk_budget_without_eager_loading(
    tmp_path: Path,
) -> None:
    details: list[JsonObject] = []
    for index in range(6):
        payload = random.Random(index).randbytes(225_000).hex()
        details.append(
            {
                "record_id": f"site:{index:03d}",
                "tabs": {"overview": {"source_payload": payload}},
            }
        )

    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="v66",
        point_layers=build_point_layers(),
        polygon_layers=[],
        detail_records=details,
    )

    rows = assets.manifest["assets"]
    assert isinstance(rows, list)
    detail_rows = [row for row in rows if row["domain"] == "details"]
    assert len(detail_rows) == 1
    assert detail_rows[0]["initial_load"] is False
    detail_path = assets.asset_paths[rows.index(detail_rows[0])]
    decoded_payload = read_static_asset_payload(detail_path)
    decoded_bytes = len(
        json.dumps(
            decoded_payload,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    assert ATLAS_CHUNK_TARGET_BYTES < decoded_bytes <= ATLAS_CHUNK_MAX_BYTES
    assert detail_path.stat().st_size <= ATLAS_CHUNK_MAX_BYTES
    indexes = next(
        read_static_asset_payload(path)
        for row, path in zip(rows, assets.asset_paths, strict=True)
        if row["domain"] == "indexes"
    )
    detail_record_asset_keys = indexes["detail_record_asset_keys"]
    assert isinstance(detail_record_asset_keys, dict)
    assert set(detail_record_asset_keys.values()) == {detail_rows[0]["asset_key"]}
    assert len(assets.manifest_path.read_bytes()) <= ATLAS_BOOTSTRAP_MAX_BYTES
    validate_static_atlas_assets(assets)


def test_static_node_chunks_preserve_every_source_feature_exactly_once(
    tmp_path: Path,
) -> None:
    point_layers = build_point_layers(large=True)
    polygon_layers = build_polygon_layers()
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="v66",
        point_layers=point_layers,
        polygon_layers=polygon_layers,
    )
    reconstructed: dict[int, list[tuple[int, object]]] = {}
    manifest_assets = assets.manifest["assets"]
    assert isinstance(manifest_assets, list)
    for row, path in zip(manifest_assets, assets.asset_paths, strict=True):
        assert isinstance(row, dict)
        if row["domain"] != "nodes":
            continue
        payload = read_static_asset_payload(path)
        indexes = payload["feature_indexes"]
        features = payload["features"]
        assert isinstance(indexes, list)
        assert isinstance(features, list)
        assert len(indexes) == len(features) == row["record_count"]
        layer_index = payload["layer_index"]
        assert isinstance(layer_index, int)
        reconstructed.setdefault(layer_index, []).extend(
            zip(indexes, features, strict=True)
        )

    point_features = point_layers[0]["features"]
    polygon_geojson = polygon_layers[0]["geojson"]
    assert isinstance(polygon_geojson, dict)
    polygon_features = polygon_geojson["features"]
    assert isinstance(point_features, list)
    assert isinstance(polygon_features, list)
    expected_layers = [point_features, polygon_features]
    domains = assets.manifest["domains"]
    assert isinstance(domains, dict)
    nodes = domains["nodes"]
    assert isinstance(nodes, dict)
    assert nodes["record_count"] == sum(len(features) for features in expected_layers)
    for layer_index, expected in enumerate(expected_layers):
        assert isinstance(expected, list)
        indexed = sorted(reconstructed[layer_index])
        assert [index for index, _feature in indexed] == list(range(len(expected)))
        assert [feature for _index, feature in indexed] == expected


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
    assert "country_feature_indexes" in scripts
    assert "spatial_degree_feature_indexes" in scripts
    assert "time_interval_feature_indexes" in scripts
    assert "signal_layer_indexes" in scripts
    assert "fetch(" not in scripts

    node = shutil.which("node")
    assert node is not None
    probe = (
        scripts
        + "\nconst payloads=globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.map((row)=>JSON.parse(row.payload_json));"
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
