"""Governed crossing edges discover their exact lazy point-node chunks."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.static_assets import nodes
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.edges import (
    edge_endpoint_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)
from bijux_pollenomics.reporting.map_document.static_assets.validation import (
    _validate_static_payloads,
)
from bijux_pollenomics.reporting.map_document.static_assets.writer import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE


def published(
    root: Path,
    *,
    missing: bool = False,
    faraway: bool = False,
    left_latitude: object = 0,
) -> tuple[dict[str, Any], dict[str, Any]]:
    features = [
        {
            "record_id": record,
            "country": country,
            "latitude": left_latitude if record == "left" else 0,
            "longitude": longitude,
            "title": record,
            "scientific_signal_ids": ["whole"],
        }
        for record, country, longitude in (
            ("left", "Sweden", -20),
            ("right", "Norway", 20),
            ("unrelated", "Denmark", 0),
        )
    ]
    if faraway:
        features.extend(
            [
                {
                    "record_id": record,
                    "country": country,
                    "latitude": 50,
                    "longitude": longitude,
                    "title": record,
                    "scientific_signal_ids": ["whole"],
                }
                for record, country, longitude in (
                    ("far-left", "Sweden", -20),
                    ("far-right", "Norway", 20),
                )
            ]
        )
    edges = [
        {
            "edge_id": "crossing",
            "signal_id": "whole",
            "source_record_id": "left",
            "target_record_id": "right",
            "source_country": "Sweden",
            "target_country": "Norway",
            "status": "possible_candidate",
            "predicates": [],
        }
    ]
    if faraway:
        edges.append(
            {
                **edges[0],
                "edge_id": "faraway",
                "source_record_id": "far-left",
                "target_record_id": "far-right",
            }
        )
    if missing:
        features = [feature for feature in features if feature["record_id"] != "right"]
    assets = write_static_atlas_assets(
        root,
        slug="crossing",
        version="discovery",
        point_layers=[
            {
                "key": "points",
                "label": "Points",
                "features": features,
                "applies_country_filter": True,
                "scientific_selection_enabled": True,
            }
        ],
        polygon_layers=[],
        scientific_signals=[
            {
                "signal_id": "whole",
                "feature_key": "whole",
                "label": "Whole",
                "resolution": "whole",
                "status": "accepted",
            }
        ],
        edge_records=edges,
    )
    rows = cast(
        list[dict[str, Any]], normalize_asset_inventory(assets.manifest["assets"])
    )
    payloads = {
        row["asset_key"]: decode_chunk_script(
            path.read_bytes(),
            expected_asset_key=row["asset_key"],
            expected_payload_sha256=row["payload_sha256"],
            expected_payload_encoding=row["payload_encoding"],
            expected_decoded_byte_count=row["decoded_byte_count"],
        )
        for row, path in zip(rows, assets.asset_paths, strict=True)
    }
    return {**assets.manifest, "assets": rows}, payloads


def block(start: str, end: str) -> str:
    offset = MAP_DOCUMENT_TEMPLATE.index(start)
    return MAP_DOCUMENT_TEMPLATE[offset : MAP_DOCUMENT_TEMPLATE.index(end, offset)]


def browser(
    manifest: dict[str, Any], payloads: dict[str, Any], change: str = ""
) -> dict[str, Any]:
    node = shutil.which("node")
    assert node is not None
    script = (
        "const STATIC_ATLAS_BOOTSTRAP=" + json.dumps(manifest) + ";"
        "const payloads="
        + json.dumps(payloads)
        + ";"
        + "const STATIC_ATLAS_INLINE=false, STATIC_ATLAS_CHUNKS={nodes:[]};"
        + "for(const row of STATIC_ATLAS_BOOTSTRAP.assets)if(row.initial_load)"
        + "STATIC_ATLAS_CHUNKS[row.domain]=payloads[row.asset_key];"
        + "const staticAtlasLoadedAssets=new Set(STATIC_ATLAS_BOOTSTRAP.assets"
        + ".filter(row=>row.initial_load).map(row=>row.asset_key));"
        + "const staticAtlasSearchFeatureKeys=new WeakMap();"
        + "const POINT_LAYERS=STATIC_ATLAS_CHUNKS.provenance.layers.map(row=>"
        + "({...row.layer,features:[]})), POLYGON_LAYERS=[];"
        + "const ALL_LAYERS=POINT_LAYERS, activeLayerKeys=new Set(['points']);"
        + "const activeCountries=new Set(['Sweden']);"
        + "const activeScientificSignalIds=new Set(['whole']),TIME_HAS_DATA=false;"
        + "const SCIENTIFIC_SIGNALS=[{signal_id:'whole'}],SCOPE_KEY='nordic';"
        + "const activeAnimalSpecies='all',activeAnimalScope='all';"
        + "function isAnimalLayer(){return false;}"
        + "function isAnimalSourceChronologyLayer(){return false;}"
        + "const map={_loaded:true,getBounds:()=>({getSouth:()=>-1,"
        + "getNorth:()=>1,getWest:()=>-1,getEast:()=>1}),"
        + "latLngToContainerPoint:p=>({x:p[1]+10,y:10-p[0]}),"
        + "getSize:()=>({x:20,y:20})};"
        + "function visibleGovernedEdges(){return STATIC_ATLAS_CHUNKS.edges.records"
        + ".filter(edge=>atlasEdgeVisible(edge,activeCountries,'all',false,activeScientificSignalIds));}"
        + block("function atlasCountryPairKey", "function atlasFilterStateSnapshot")
        + "const retainedNeighborRecordCountries=atlasRetainedNeighborRecordCountries("
        + "visibleGovernedEdges(),activeCountries);"
        + block(
            "function staticAtlasFailure", "function staticAtlasNullableFiniteNumber"
        )
        + block(
            "function validateStaticAtlasEdgeAssets",
            "function validateStaticAtlasPayload",
        )
        + block("function hydrateStaticAtlasLayers", "const SCOPE_KEY")
        + block("function staticAtlasLayerForRow", "const countryColors")
        + block("function finiteCoordinateValue", "function coordinateLabel")
        + block("function atlasEdgeIntersectsViewport", "function renderEdgeLayers")
        + "const requested=[];function beginStaticAtlasSelection(){return {throwIfAborted(){}};}"
        + "async function waitForStaticAtlasSelection(value){return value;}"
        + "async function loadStaticAtlasAsset(row){requested.push(row.asset_key);"
        + "staticAtlasLoadedAssets.add(row.asset_key);if(row.domain==='nodes')"
        + "STATIC_ATLAS_CHUNKS.nodes.push(payloads[row.asset_key]);}"
        + "const pair=featureCoordinatePair;"
        + "(async()=>{try{validateStaticAtlasEdgeAssets(STATIC_ATLAS_CHUNKS.edges);"
        + change
        + ";await ensureStaticAtlasSelectionLoaded();"
        + "const entries=new Map(POINT_LAYERS.flatMap(layer=>layer.features.map(feature=>"
        + "[feature.record_id,{layer,feature}])));"
        + "const rendered=atlasEdgeRenderSelection(visibleGovernedEdges(),entries,0,pair,"
        + "coordinates=>atlasEdgeIntersectsViewport(map,coordinates));"
        + "console.log(JSON.stringify({requested,rows:rendered.rows.map(row=>row.edge.edge_id),"
        + "viewport_count:rendered.viewport_count,admitted_count:STATIC_ATLAS_CHUNKS.edges.records.length,features:[...entries.keys()]}));"
        + "}catch(error){console.log(JSON.stringify({error:error.message,requested}));}})();"
    )
    result = subprocess.run(
        [node, "-"], input=script, text=True, capture_output=True, check=True
    )
    observed = json.loads(result.stdout)
    assert isinstance(observed, dict)
    return observed


def test_crossing_edge_loads_only_its_exact_endpoint_chunks(tmp_path: Path) -> None:
    manifest, payloads = published(tmp_path)
    edges = next(
        payload for payload in payloads.values() if "endpoint_node_assets" in payload
    )
    expected = sorted(
        {key for keys in edges["endpoint_node_assets"].values() for key in keys}
    )
    observed = browser(manifest, payloads)
    assert observed["rows"] == ["crossing"]
    assert observed["viewport_count"] == 1
    assert (
        sorted(key for key in observed["requested"] if key.startswith("nodes:"))
        == expected
    )
    assert sorted(observed["features"]) == ["left", "right"]
    assert all(payloads[key]["country_keys"] != ["Denmark"] for key in expected)


@pytest.mark.parametrize(
    "mutation", ["missing", "foreign", "duplicate", "empty", "extra", "wrong_record"]
)
def test_endpoint_membership_corruption_refuses(tmp_path: Path, mutation: str) -> None:
    manifest, payloads = published(tmp_path)
    edges = next(
        payload for payload in payloads.values() if "endpoint_node_assets" in payload
    )
    references = edges["endpoint_node_assets"]
    if mutation == "missing":
        del references["left"]
    elif mutation == "foreign":
        references["left"] = ["provenance:0"]
    elif mutation == "duplicate":
        references["left"] *= 2
    elif mutation == "empty":
        references["left"] = []
    elif mutation == "extra":
        references["foreign"] = references["left"]
    else:
        references["left"] = references["right"]
    with pytest.raises(ValueError, match="endpoint assets"):
        _validate_static_payloads(manifest, manifest["assets"], payloads)
    observed = browser(manifest, payloads)
    assert "error" in observed
    if mutation != "wrong_record":
        assert observed["requested"] == []


@pytest.mark.parametrize("kind", ["requests", "bytes"])
def test_endpoint_union_budget_refuses_before_requests(
    tmp_path: Path, kind: str
) -> None:
    manifest, payloads = published(tmp_path)
    observed = browser(manifest, payloads)
    rows = [
        row for row in manifest["assets"] if row["asset_key"] in observed["requested"]
    ]
    bound = len(rows) if kind == "requests" else sum(row["byte_count"] for row in rows)
    key = f"interaction_max_{kind}"
    manifest["budgets"][key] = bound
    assert browser(manifest, payloads)["rows"] == ["crossing"]
    manifest["budgets"][key] = bound - 1
    refused = browser(manifest, payloads)
    assert "budget" in refused["error"]
    assert refused["requested"] == []


@pytest.mark.parametrize(
    "change",
    [
        "activeLayerKeys.clear()",
        "activeScientificSignalIds.clear()",
        "activeCountries.clear()",
    ],
)
def test_existing_filter_exclusions_prevent_endpoint_requests(
    tmp_path: Path, change: str
) -> None:
    manifest, payloads = published(tmp_path)
    observed = browser(manifest, payloads, change)
    assert observed["rows"] == []
    assert not any(key.startswith("nodes:") for key in observed["requested"])


def test_legacy_edge_payload_has_explicit_compatible_path(tmp_path: Path) -> None:
    manifest, payloads = published(tmp_path)
    manifest["compatibility"]["edge_schema"] = "atlas-edges-chunk.v1"
    edges = next(
        payload for payload in payloads.values() if "endpoint_node_assets" in payload
    )
    edges["schema_version"] = "atlas-edges-chunk.v1"
    del edges["endpoint_node_assets"]
    del edges["endpoint_node_geometry"]
    _validate_static_payloads(manifest, manifest["assets"], payloads)
    assert "error" not in browser(manifest, payloads)
    edges["endpoint_node_assets"] = {}
    with pytest.raises(ValueError, match="Legacy"):
        _validate_static_payloads(manifest, manifest["assets"], payloads)
    assert "error" in browser(manifest, payloads)


def test_all_representations_retained_and_missing_endpoint_refuses() -> None:
    records = [{"source_record_id": "left", "target_record_id": "right"}]
    nodes = {
        key: {
            "layer_kind": "point",
            "feature_indexes": [0],
            "features": [{"record_id": record}],
        }
        for key, record in (
            ("nodes:1", "left"),
            ("nodes:2", "right"),
            ("nodes:3", "left"),
        )
    }
    assert edge_endpoint_assets(records, nodes) == {
        "left": ["nodes:1", "nodes:3"],
        "right": ["nodes:2"],
    }
    del nodes["nodes:2"]
    with pytest.raises(ValueError, match="no published point node"):
        edge_endpoint_assets(records, nodes)


def test_node_reordering_does_not_change_endpoint_identity(tmp_path: Path) -> None:
    manifest, payloads = published(tmp_path)
    swapped = deepcopy(manifest)
    swapped["assets"].reverse()
    observed = browser(swapped, payloads)
    assert observed["rows"] == ["crossing"]
    assert sorted(observed["features"]) == ["left", "right"]


def test_publisher_refuses_endpoint_missing_from_all_point_chunks(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="no published point node"):
        published(tmp_path, missing=True)
    assert list(tmp_path.iterdir()) == []


def test_same_active_country_faraway_edge_does_not_load_its_chunks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(nodes, "ATLAS_COMPRESSED_CHUNK_TARGET_BYTES", 1)
    manifest, payloads = published(tmp_path, faraway=True)
    edges = next(
        payload for payload in payloads.values() if "endpoint_node_assets" in payload
    )
    expected = sorted(
        {
            key
            for record in ("left", "right")
            for key in edges["endpoint_node_assets"][record]
        }
    )
    observed = browser(manifest, payloads)
    assert observed["rows"] == ["crossing"]
    assert observed["admitted_count"] == 2
    assert observed["viewport_count"] == 1
    assert (
        sorted(key for key in observed["requested"] if key.startswith("nodes:"))
        == expected
    )
    assert sorted(observed["features"]) == ["left", "right"]


@pytest.mark.parametrize("latitude", [None, True, "", 91])
def test_missing_or_refused_coordinates_never_acquire_zero_geometry(
    tmp_path: Path, latitude: object
) -> None:
    manifest, payloads = published(tmp_path, left_latitude=latitude)
    observed = browser(manifest, payloads)
    assert observed["rows"] == []
    assert observed["admitted_count"] == 1


@pytest.mark.parametrize("latitude", ["0", "0x0"])
def test_raw_numeric_strings_use_original_javascript_coordinate_semantics(
    tmp_path: Path, latitude: object
) -> None:
    manifest, payloads = published(tmp_path, left_latitude=latitude)
    assert browser(manifest, payloads)["rows"] == ["crossing"]


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "foreign", "coordinate"])
def test_geometry_hint_corruption_refuses(tmp_path: Path, mutation: str) -> None:
    manifest, payloads = published(tmp_path)
    edges = next(
        payload for payload in payloads.values() if "endpoint_node_assets" in payload
    )
    geometry = edges["endpoint_node_geometry"]
    if mutation == "missing":
        del geometry["left"]
    elif mutation == "duplicate":
        geometry["left"] *= 2
    elif mutation == "foreign":
        geometry["left"][0]["asset_key"] = "provenance:0"
    else:
        geometry["left"][0]["latitude"] = 0.5
    with pytest.raises(ValueError, match="endpoint assets or geometry"):
        _validate_static_payloads(manifest, manifest["assets"], payloads)
    assert "error" in browser(manifest, payloads)
