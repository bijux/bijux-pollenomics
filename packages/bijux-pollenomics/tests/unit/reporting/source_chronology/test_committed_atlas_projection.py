"""Real Neotoma denominator and static-publication proof."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import cast

from bijux_pollenomics.reporting.context.points import build_external_point_layer
from bijux_pollenomics.reporting.map_document.evidence_projection.neotoma import (
    _project_neotoma,
)
from bijux_pollenomics.reporting.map_document.static_assets import (
    ATLAS_CHUNK_MAX_BYTES,
    ATLAS_INITIAL_MAX_BYTES,
    ATLAS_INITIAL_MAX_REQUESTS,
    ATLAS_STATIC_ASSETS_MAX_BYTES,
    ATLAS_STATIC_ASSETS_MAX_FILES,
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from .committed_bundle import committed_nordic_inputs
from .static_proof import (
    assert_point_layer_index_coverage,
    decode_static_indexes,
    static_asset_metrics,
)

ROOT = Path(__file__).resolve().parents[6]


def test_committed_source_nodes_reconcile_and_fit_static_budgets(
    tmp_path: Path,
) -> None:
    source_path = ROOT / "data/neotoma/normalized/nordic_pollen_sites.geojson"
    geojson = json.loads(source_path.read_text(encoding="utf-8"))
    base_layer = build_external_point_layer(geojson, source_path=source_path)

    details, accounting, source_layers = _project_neotoma(ROOT / "data", base_layer)

    assert len(details) == 200
    source_accounting = cast(dict[str, object], accounting["source_chronology"])
    assert source_accounting["source_node_count"] == 86_927
    assert source_accounting["layer_counts"] == {
        "source_ecological_code": 8_778,
        "source_sample_presence": 3_569,
        "source_taxon": 74_580,
    }
    assert source_accounting["country_counts"] == {
        "Sweden": 58_055,
        "Denmark": 0,
        "Norway": 26_703,
        "Finland": 2_169,
    }
    layers = {str(layer["node_level"]): layer for layer in source_layers}
    code_facets = cast(
        Mapping[str, object], layers["source_ecological_code"]["facet_metadata"]
    )
    code_counts = {
        str(row["value"]): row["node_count"]
        for row in cast(list[dict[str, object]], code_facets["source_ecological_codes"])
    }
    assert {code: code_counts[code] for code in ("TRSH", "UPHE", "AQVP")} == {
        "TRSH": 3_559,
        "UPHE": 3_511,
        "AQVP": 1_467,
    }
    taxon_features = cast(list[dict[str, object]], layers["source_taxon"]["features"])
    assert all(feature["source_ecological_code"] is None for feature in taxon_features)
    assert all(
        str(feature["record_id"]).startswith("neotoma:site:")
        for feature in taxon_features
    )
    detail_ids = {str(record["record_id"]) for record in details}
    assert {
        str(feature["record_id"])
        for layer in source_layers
        for feature in cast(list[dict[str, object]], layer["features"])
    } <= detail_ids

    assets = write_static_atlas_assets(
        tmp_path,
        slug="neotoma-source-chronology",
        version="committed-snapshot",
        point_layers=source_layers,
        polygon_layers=(),
    )
    assert cast(dict[str, object], assets.manifest["domains"])["nodes"] == {
        "status": "available",
        "record_count": 86_927,
    }
    assert len(assets.asset_paths) <= ATLAS_STATIC_ASSETS_MAX_FILES
    assert sum(path.stat().st_size for path in assets.asset_paths) <= (
        ATLAS_STATIC_ASSETS_MAX_BYTES
    )
    assert max(path.stat().st_size for path in assets.asset_paths) <= (
        ATLAS_CHUNK_MAX_BYTES
    )
    asset_rows = normalize_asset_inventory(assets.manifest["assets"])
    layer_counts = {
        str(layer["key"]): cast(int, layer["count"]) for layer in source_layers
    }
    indexes = decode_static_indexes(assets, asset_rows)
    assert_point_layer_index_coverage(indexes, layer_counts)
    initial_rows = [row for row in asset_rows if row["initial_load"] is True]
    assert len(initial_rows) <= ATLAS_INITIAL_MAX_REQUESTS
    assert sum(cast(int, row["byte_count"]) for row in initial_rows) <= (
        ATLAS_INITIAL_MAX_BYTES
    )
    print(json.dumps({"scope": "source", **static_asset_metrics(assets, asset_rows)}))

    (
        existing_points,
        existing_polygons,
        existing_details,
        existing_signals,
        existing_edges,
        existing_sequences,
    ) = committed_nordic_inputs(ROOT)
    committed_source_layers = {
        str(layer["key"]): layer
        for layer in existing_points
        if layer.get("semantic_role") == "source_chronology_context"
    }
    assert {
        key: cast(int, layer["count"]) for key, layer in committed_source_layers.items()
    } == layer_counts
    assert {
        str(layer["node_level"]): len(cast(list[object], layer["features"]))
        for layer in committed_source_layers.values()
    } == source_accounting["layer_counts"]
    combined_root = tmp_path / "combined"
    combined_root.mkdir()
    combined = write_static_atlas_assets(
        combined_root,
        slug="nordic-combined",
        version="committed-snapshot",
        point_layers=existing_points,
        polygon_layers=existing_polygons,
        detail_records=existing_details,
        scientific_signals=existing_signals,
        edge_records=existing_edges,
        sequence_records=existing_sequences,
    )
    combined_rows = normalize_asset_inventory(combined.manifest["assets"])
    assert_point_layer_index_coverage(
        decode_static_indexes(combined, combined_rows), layer_counts
    )
    combined_initial = [row for row in combined_rows if row["initial_load"] is True]
    assert len(combined_initial) <= ATLAS_INITIAL_MAX_REQUESTS
    assert sum(cast(int, row["byte_count"]) for row in combined_initial) <= (
        ATLAS_INITIAL_MAX_BYTES
    )
    assert sum(path.stat().st_size for path in combined.asset_paths) <= (
        ATLAS_STATIC_ASSETS_MAX_BYTES
    )
    assert max(path.stat().st_size for path in combined.asset_paths) <= (
        ATLAS_CHUNK_MAX_BYTES
    )
    print(
        json.dumps(
            {"scope": "combined", **static_asset_metrics(combined, combined_rows)}
        )
    )
