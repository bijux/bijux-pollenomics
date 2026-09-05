from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess

import pytest

from bijux_pollenomics.reporting.geography import build_published_geography_plan
from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.payload import serialize_json_for_script
from bijux_pollenomics.reporting.map_document.static_assets import (
    ATLAS_DOCUMENT_MAX_BYTES,
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_publication import resolve_map_scope_policy

from .fixtures.layers import build_point_layers, build_polygon_layers
from .fixtures.scientific_evidence import (
    build_detail_records,
    build_edge_records,
    build_scientific_point_layers,
    build_scientific_signals,
)


def test_static_map_document_is_small_relative_only_and_offline_loadable(
    tmp_path: Path,
) -> None:
    point_layers = build_point_layers()
    polygon_layers = build_polygon_layers()
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
    manifest_assets = normalize_asset_inventory(assets.manifest["assets"])
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
    assert "new DecompressionStream('gzip')" in html
    assert "decoded payload exceeds its byte budget" in html
    assert "redeploy the HTML and hashed assets from the same build" in html
    assert "compatibility declaration mismatch" in html
    assert "path is invalid" in html
    assert "aria-busy" in html


def test_scientific_atlas_document_exposes_comparison_relations_and_detail_drawer(
    tmp_path: Path,
) -> None:
    point_layers = build_scientific_point_layers()
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="v66",
        point_layers=point_layers,
        polygon_layers=[],
        detail_records=build_detail_records(),
        scientific_signals=build_scientific_signals(),
        edge_records=build_edge_records(),
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
        "2026-09-05",
        ("Sweden", "Norway"),
        policy,
        point_layers,
        [],
        "./_map_assets",
        static_assets=assets,
    )

    for element_id in (
        "scientific-filters",
        "country-pair-filter",
        "cross-border-only",
        "focus-tabs",
        "focus-detail",
    ):
        assert f'id="{element_id}"' in html
    for label in (
        "Overview",
        "Samples",
        "Chronology",
        "Pollen/composition",
        "Relation",
        "Classification",
        "Provenance",
    ):
        assert label in html
    assert "accepted_scientific_classifications_not_available" in html
    assert "record_level_evidence_not_available" in html
    assert "not proof of migration or causation" in html
    assert "atlas-scientific-marker" in html
    assert "edge) => Object.freeze({ ...edge })" in html
    assert "resetRestoredVisibleEdges" in html
    assert "STATIC_ATLAS_CHUNKS.edges?.status !== 'unavailable'" not in html
    inline_scripts = re.findall(r"<script(?: [^>]*)?>(.*?)</script>", html, re.DOTALL)
    assert inline_scripts
    node = shutil.which("node")
    assert node is not None
    subprocess.run(
        [node, "--check", "-"],
        input=inline_scripts[-1],
        check=True,
        capture_output=True,
        text=True,
    )


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

    hostile_layers = build_point_layers()
    hostile_features = hostile_layers[0]["features"]
    assert isinstance(hostile_features, list)
    assert isinstance(hostile_features[0], dict)
    hostile_features[0]["title"] = hostile
    hostile_polygons = build_polygon_layers()
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
        build_point_layers(),
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
            point_layers=build_point_layers(),
            polygon_layers=[],
        )

    with pytest.raises(ValueError, match="safe release identifier"):
        render_multi_country_map_html(
            "Nordic",
            hostile,
            "2026-09-04",
            ("Sweden", "Norway"),
            policy,
            build_point_layers(),
            [],
            "./_map_assets",
        )


def test_static_loader_suppresses_obsolete_selection_generations(
    tmp_path: Path,
) -> None:
    point_layers = build_point_layers()
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
