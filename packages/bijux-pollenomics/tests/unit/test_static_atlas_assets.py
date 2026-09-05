from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

import pytest

from bijux_pollenomics.core.geojson import JsonObject
from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths
from bijux_pollenomics.reporting.geography import build_published_geography_plan
from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.evidence import DETAIL_TAB_KEYS
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
from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE
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


def _scientific_signals() -> list[JsonObject]:
    return [
        {
            "signal_id": "pollen:taxon:triticum",
            "feature_key": "taxon:triticum",
            "label": "Triticum",
            "resolution": "taxon",
            "parent_signal_id": "pollen:group:cereals",
            "status": "accepted",
        },
        {
            "signal_id": "pollen:whole",
            "feature_key": "whole:pollen",
            "label": "All accepted pollen",
            "resolution": "whole",
            "status": "accepted",
        },
        {
            "signal_id": "pollen:group:cereals",
            "feature_key": "group:cereals",
            "label": "Cereals",
            "resolution": "group",
            "parent_signal_id": "pollen:whole",
            "status": "accepted",
        },
        {
            "signal_id": "pollen:role:direct-crop",
            "feature_key": "role:direct-crop",
            "label": "Direct crop evidence",
            "resolution": "role",
            "parent_signal_id": "pollen:group:cereals",
            "status": "accepted",
        },
    ]


def _scientific_point_layers() -> list[JsonObject]:
    layers = _point_layers()
    layer = layers[0]
    layer["scientific_selection_enabled"] = True
    features = layer["features"]
    assert isinstance(features, list)
    for index, feature in enumerate(features):
        assert isinstance(feature, dict)
        feature["record_id"] = f"site:{index + 1}"
        feature["scientific_signal_ids"] = [
            "pollen:whole",
            "pollen:group:cereals",
            "pollen:role:direct-crop",
            "pollen:taxon:triticum",
        ]
    return layers


def _detail_records() -> list[JsonObject]:
    return [
        {
            "record_id": "site:1",
            "tabs": {
                "overview": {"site_id": "site:1", "dataset_id": "dataset:1"},
                "samples": [{"sample_id": "sample:1", "depth_cm": 10}],
                "chronology": {
                    "age_basis": "cal BP",
                    "younger_bp": 100,
                    "older_bp": 200,
                },
                "pollen_composition": [
                    {"feature_key": "taxon:triticum", "value": 4, "unit": "count"}
                ],
                "relation": {"status": "no_selected_relation"},
                "classification": {
                    "feature_key": "taxon:triticum",
                    "mapping_version": "fixture-1",
                },
                "provenance": {
                    "source_snapshot": "snapshot:1",
                    "raw_locator": "raw/sites.json#site:1",
                    "build_id": "fixture-build",
                    "sha256": "0" * 64,
                },
            },
        }
    ]


def _edge_records() -> list[JsonObject]:
    return [
        {
            "edge_id": "edge:se-no",
            "signal_id": "pollen:whole",
            "source_record_id": "site:1",
            "target_record_id": "site:2",
            "source_country": "Sweden",
            "target_country": "Norway",
            "status": "definite_candidate",
            "predicates": [
                {"predicate": "distance_within_threshold", "status": "pass"}
            ],
        },
        {
            "edge_id": "edge:se-se",
            "signal_id": "pollen:group:cereals",
            "source_record_id": "site:1",
            "target_record_id": "site:1",
            "source_country": "Sweden",
            "target_country": "Sweden",
            "status": "possible_candidate",
            "predicates": [],
        },
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
    point_layers = _scientific_point_layers()
    signals = _scientific_signals()
    details = _detail_records()
    edges = _edge_records()
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
        _payload(path)["schema_version"]: _payload(path) for path in first.asset_paths
    }
    provenance = payloads["atlas-provenance-chunk.v2"]
    assert provenance["details_status"] == "available"
    assert provenance["classifications_status"] == "available"
    detail_tabs = provenance["detail_records"][0]["tabs"]
    assert set(detail_tabs) == set(DETAIL_TAB_KEYS)
    observed_signals = provenance["scientific_signals"]
    assert [row["signal_id"] for row in observed_signals] == sorted(
        row["signal_id"] for row in signals
    )
    assert len({row["color"] for row in observed_signals}) == len(observed_signals)
    assert all(row["non_color_cue"] for row in observed_signals)
    assert payloads["atlas-edges-chunk.v1"]["records"][0]["cross_border"] is True


def test_scientific_fixture_refuses_unaccepted_or_unknown_signals(
    tmp_path: Path,
) -> None:
    signals = _scientific_signals()
    signals[0]["status"] = "review"
    with pytest.raises(ValueError, match="not accepted"):
        write_static_atlas_assets(
            tmp_path,
            slug="nordic",
            version="v66",
            point_layers=_scientific_point_layers(),
            polygon_layers=[],
            scientific_signals=signals,
        )

    point_layers = _scientific_point_layers()
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
            scientific_signals=_scientific_signals(),
        )


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


def test_scientific_atlas_document_exposes_comparison_relations_and_detail_drawer(
    tmp_path: Path,
) -> None:
    point_layers = _scientific_point_layers()
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="v66",
        point_layers=point_layers,
        polygon_layers=[],
        detail_records=_detail_records(),
        scientific_signals=_scientific_signals(),
        edge_records=_edge_records(),
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


def test_browser_filter_helpers_preserve_eligibility_and_restore_exact_state() -> None:
    node = shutil.which("node")
    assert node is not None

    start = MAP_DOCUMENT_TEMPLATE.index("function atlasCountryPairKey")
    end = MAP_DOCUMENT_TEMPLATE.index("function clampTimeInterval", start)
    helper_source = MAP_DOCUMENT_TEMPLATE[start:end]
    probe = (
        helper_source
        + """
const edges = [
  {edge_id:'cross', source_country:'Sweden', target_country:'Norway', signal_id:'whole'},
  {edge_id:'domestic', source_country:'Sweden', target_country:'Sweden', signal_id:'group'},
];
const allCountries = new Set(['Sweden', 'Norway']);
const allSignals = new Set(['whole', 'group']);
const defaults = atlasFilterStateSnapshot(allCountries, allSignals, 'all', false);
const changed = atlasFilterStateSnapshot(new Set(['Sweden']), new Set(['group']), 'Sweden|Sweden', true);
const restored = atlasFilterStateSnapshot(new Set(['Norway', 'Sweden']), new Set(['group', 'whole']), 'all', false);
console.log(JSON.stringify({
  eligibility: edges.length,
  all: edges.filter((edge) => atlasEdgeVisible(edge, allCountries, 'all', false, allSignals)).length,
  cross: edges.filter((edge) => atlasEdgeVisible(edge, allCountries, 'all', true, allSignals)).length,
  pair: edges.filter((edge) => atlasEdgeVisible(edge, allCountries, 'Norway|Sweden', false, allSignals)).length,
  sweden: edges.filter((edge) => atlasEdgeVisible(edge, new Set(['Sweden']), 'all', false, allSignals)).length,
  defaults_equal_restored: atlasFilterStateEquals(defaults, restored),
  defaults_equal_changed: atlasFilterStateEquals(defaults, changed),
}));
"""
    )
    result = subprocess.run(
        [node, "-e", probe], check=True, capture_output=True, text=True
    )

    assert json.loads(result.stdout) == {
        "eligibility": 2,
        "all": 2,
        "cross": 1,
        "pair": 1,
        "sweden": 1,
        "defaults_equal_restored": True,
        "defaults_equal_changed": False,
    }


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
