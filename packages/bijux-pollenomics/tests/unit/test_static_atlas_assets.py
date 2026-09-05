from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from bijux_pollenomics.core.geojson import JsonObject
from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths
from bijux_pollenomics.reporting.geography import build_published_geography_plan
from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.payload import serialize_json_for_script
from bijux_pollenomics.reporting.map_document.static_assets import (
    ATLAS_BOOTSTRAP_MAX_BYTES,
    ATLAS_CHUNK_MAX_BYTES,
    ATLAS_DOCUMENT_MAX_BYTES,
    ATLAS_INITIAL_MAX_BYTES,
    ATLAS_INITIAL_MAX_REQUESTS,
    ATLAS_INTERACTION_MAX_BYTES,
    validate_static_atlas_assets,
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_publication import resolve_map_scope_policy


def _point_layers(*, large: bool = False) -> list[JsonObject]:
    description = "x" * 30_000 if large else "source-owned point"
    count = 100 if large else 2
    return [
        {
            "key": "pollen-sites",
            "label": "Pollen sites",
            "group": "environmental-context",
            "source_name": "Example source",
            "default_enabled": True,
            "features": [
                {
                    "title": f"evidence-{index}",
                    "country": "Sweden" if index % 2 == 0 else "Norway",
                    "latitude": 59.0 + index / 1000,
                    "longitude": 18.0 + index / 1000,
                    "time_start_bp": index,
                    "time_end_bp": index + 100,
                    "description": description,
                }
                for index in range(count)
            ],
        }
    ]


def _polygon_layers() -> list[JsonObject]:
    return [
        {
            "key": "country-boundaries",
            "label": "Country boundaries",
            "group": "orientation",
            "source_name": "Boundary source",
            "default_enabled": True,
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [17.0, 58.0],
                                    [19.0, 58.0],
                                    [19.0, 60.0],
                                    [17.0, 60.0],
                                    [17.0, 58.0],
                                ]
                            ],
                        },
                        "properties": {"country": "Sweden"},
                    }
                ],
            },
        }
    ]


def _payload(path: Path) -> dict[str, object]:
    script = path.read_text(encoding="utf-8")
    marker = "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push("
    start = script.index(marker) + len(marker)
    assert script.endswith(");\n")
    envelope = json.loads(script[start:-3])
    payload_json = envelope["payload_json"]
    assert isinstance(payload_json, str)
    assert (
        envelope["payload_sha256"]
        == hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    )
    payload = json.loads(payload_json)
    assert isinstance(payload, dict)
    return payload


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
        point_layers=_point_layers(large=True),
        polygon_layers=_polygon_layers(),
    )
    second = write_static_atlas_assets(
        second_root,
        slug="nordic",
        version="v66",
        point_layers=_point_layers(large=True),
        polygon_layers=_polygon_layers(),
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


def test_static_node_chunks_preserve_every_source_feature_exactly_once(
    tmp_path: Path,
) -> None:
    point_layers = _point_layers(large=True)
    polygon_layers = _polygon_layers()
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
        payload = _payload(path)
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
        point_layers=_point_layers(),
        polygon_layers=_polygon_layers(),
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


def test_static_map_document_is_small_relative_only_and_offline_loadable(
    tmp_path: Path,
) -> None:
    point_layers = _point_layers()
    polygon_layers = _polygon_layers()
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="v66",
        point_layers=point_layers,
        polygon_layers=polygon_layers,
    )
    policy = resolve_map_scope_policy(
        next(
            scope
            for scope in build_published_geography_plan(
                ("Sweden", "Norway")
            ).regional_scopes
            if scope.key == "nordic"
        )
    )
    html = render_multi_country_map_html(
        "Nordic",
        "v66",
        "2026-09-04",
        ("Sweden", "Norway"),
        policy,
        point_layers,
        polygon_layers,
        "./_map_assets",
        static_assets=assets,
    )

    assert len(html.encode("utf-8")) <= ATLAS_DOCUMENT_MAX_BYTES
    assert all(line == line.rstrip() for line in html.splitlines())
    assert 'id="atlas-static-bootstrap"' in html
    assert "selection_aware_static_scripts" in html
    assert "evidence-0" not in html
    assert "fetch(" not in html
    manifest_assets = assets.manifest["assets"]
    assert isinstance(manifest_assets, list)
    for _row, path in zip(manifest_assets, assets.asset_paths, strict=True):
        expected_tag = f'<script src="./{path.name}"></script>'
        assert expected_tag not in html
        assert not Path(path.name).is_absolute()
    assert "await loadStaticAtlasAsset(row)" in html
    assert "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__ =" in html
    assert "script.integrity = row.integrity" in html
    assert "file:// cannot reliably enforce transport SRI" in html
    assert "staticAtlasLoadGeneration" in html
    assert "requiredStaticAtlasNodeAssets" in html
    assert "payload integrity mismatch" in html
    assert "redeploy the HTML and hashed assets from the same build" in html
    assert "compatibility declaration mismatch" in html
    assert "path is invalid" in html
    assert "aria-busy" in html


def test_script_json_escaping_round_trips_and_hostile_versions_are_refused(
    tmp_path: Path,
) -> None:
    hostile = "v66</script><script>globalThis.executed=true</script>&\u2028\u2029"
    serialized = serialize_json_for_script(hostile)
    assert json.loads(serialized) == hostile
    assert "<" not in serialized
    assert ">" not in serialized
    assert "&" not in serialized
    assert "\u2028" not in serialized
    assert "\u2029" not in serialized
    assert "\\u2028" in serialized
    assert "\\u2029" in serialized

    hostile_layers = _point_layers()
    hostile_features = hostile_layers[0]["features"]
    assert isinstance(hostile_features, list)
    assert isinstance(hostile_features[0], dict)
    hostile_features[0]["title"] = hostile
    hostile_polygons = _polygon_layers()
    hostile_geojson = hostile_polygons[0]["geojson"]
    assert isinstance(hostile_geojson, dict)
    hostile_polygon_features = hostile_geojson["features"]
    assert isinstance(hostile_polygon_features, list)
    assert isinstance(hostile_polygon_features[0], dict)
    hostile_properties = hostile_polygon_features[0]["properties"]
    assert isinstance(hostile_properties, dict)
    hostile_properties["country"] = hostile
    policy = resolve_map_scope_policy(
        next(
            scope
            for scope in build_published_geography_plan(
                ("Sweden", "Norway")
            ).regional_scopes
            if scope.key == "nordic"
        )
    )
    normal_html = render_multi_country_map_html(
        "Nordic",
        "v66",
        "2026-09-04",
        ("Sweden", "Norway"),
        policy,
        _point_layers(),
        [],
        "./_map_assets",
    )
    hostile_html = render_multi_country_map_html(
        hostile,
        "v66",
        "2026-09-04",
        (hostile, "Norway"),
        policy,
        hostile_layers,
        hostile_polygons,
        "./_map_assets",
    )
    assert hostile_html.count("<script") == normal_html.count("<script")
    assert "<script>globalThis.executed" not in hostile_html
    point_json = hostile_html.split("const POINT_LAYERS = ", 1)[1].split(";", 1)[0]
    round_tripped_layers = json.loads(point_json)
    assert round_tripped_layers[0]["features"][0]["title"] == hostile
    country_json = hostile_html.split("const COUNTRIES = ", 1)[1].split(";", 1)[0]
    assert json.loads(country_json)[0] == hostile
    polygon_json = hostile_html.split("const POLYGON_LAYERS = ", 1)[1].split(";", 1)[0]
    round_tripped_polygons = json.loads(polygon_json)
    assert (
        round_tripped_polygons[0]["geojson"]["features"][0]["properties"]["country"]
        == hostile
    )

    with pytest.raises(ValueError, match="safe release identifier"):
        write_static_atlas_assets(
            tmp_path,
            slug="nordic",
            version=hostile,
            point_layers=_point_layers(),
            polygon_layers=[],
        )

    with pytest.raises(ValueError, match="safe release identifier"):
        render_multi_country_map_html(
            "Nordic",
            hostile,
            "2026-09-04",
            ("Sweden", "Norway"),
            policy,
            _point_layers(),
            [],
            "./_map_assets",
        )


def test_static_loader_suppresses_obsolete_selection_generations(
    tmp_path: Path,
) -> None:
    point_layers = _point_layers()
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="v66",
        point_layers=point_layers,
        polygon_layers=[],
    )
    policy = resolve_map_scope_policy(
        next(
            scope
            for scope in build_published_geography_plan(
                ("Sweden", "Norway")
            ).regional_scopes
            if scope.key == "nordic"
        )
    )
    html = render_multi_country_map_html(
        "Nordic",
        "v66",
        "2026-09-04",
        ("Sweden", "Norway"),
        policy,
        point_layers,
        [],
        "./_map_assets",
        static_assets=assets,
    )

    generation_start = html.index("const generation = ++staticAtlasLoadGeneration")
    load_await = html.index(
        "await ensureStaticAtlasSelectionLoaded()", generation_start
    )
    stale_guard = html.index(
        "if (generation !== staticAtlasLoadGeneration) return", load_await
    )
    render = html.index("renderLoadedMapState()", stale_guard)
    assert generation_start < load_await < stale_guard < render
    assert "if (generation === staticAtlasLoadGeneration)" in html


def test_static_asset_validation_detects_tampering(tmp_path: Path) -> None:
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="v66",
        point_layers=_point_layers(),
        polygon_layers=[],
    )
    assets.asset_paths[0].write_text("changed", encoding="utf-8")

    with pytest.raises(ValueError, match="byte count changed|digest changed"):
        validate_static_atlas_assets(assets)


def test_single_unbounded_feature_is_refused(tmp_path: Path) -> None:
    layers = _point_layers()
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


def test_bundle_paths_own_static_asset_manifest(tmp_path: Path) -> None:
    paths = build_atlas_bundle_paths(tmp_path, "Nordic Atlas", "v66")
    assert paths.map_static_assets_manifest_path == (
        tmp_path / "nordic-atlas_map_assets.json"
    )
