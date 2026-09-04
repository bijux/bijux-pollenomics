from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from bijux_pollenomics.core.geojson import JsonObject
from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths
from bijux_pollenomics.reporting.geography import build_published_geography_plan
from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.static_assets import (
    ATLAS_BOOTSTRAP_MAX_BYTES,
    ATLAS_CHUNK_MAX_BYTES,
    ATLAS_DOCUMENT_MAX_BYTES,
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
    for row, path in zip(assets, first.asset_paths, strict=True):
        payload = path.read_bytes()
        assert len(payload) <= ATLAS_CHUNK_MAX_BYTES
        assert row["byte_count"] == len(payload)
        assert row["sha256"] == hashlib.sha256(payload).hexdigest()
        assert str(row["sha256"])[:16] in path.name


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
        + "\nconsole.log(JSON.stringify({nodes:globalThis.__BIJUX_ATLAS_CHUNKS__.nodes.length,edges:globalThis.__BIJUX_ATLAS_CHUNKS__.edges.records.length,sequences:globalThis.__BIJUX_ATLAS_CHUNKS__.sequences.records.length}));"
    )
    result = subprocess.run(
        [node, "-e", probe], check=True, capture_output=True, text=True
    )
    observed = json.loads(result.stdout)
    assert observed["nodes"] >= 2
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
    assert 'id="atlas-static-bootstrap"' in html
    assert "ordered_static_scripts" in html
    assert "evidence-0" not in html
    assert "fetch(" not in html
    for path in assets.asset_paths:
        assert f'<script src="./{path.name}"></script>' in html
        assert not Path(path.name).is_absolute()


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
