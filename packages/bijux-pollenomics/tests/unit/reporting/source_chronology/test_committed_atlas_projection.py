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
    ATLAS_BOOTSTRAP_MAX_BYTES,
    ATLAS_CHUNK_MAX_BYTES,
    ATLAS_DOCUMENT_MAX_BYTES,
    ATLAS_INITIAL_MAX_BYTES,
    ATLAS_INITIAL_MAX_REQUESTS,
    ATLAS_STATIC_ASSETS_MAX_BYTES,
    ATLAS_STATIC_ASSETS_MAX_FILES,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from .committed_bundle import committed_nordic_inputs
from .static_proof import (
    assert_point_layer_index_coverage,
    decode_committed_static_indexes,
)

ROOT = Path(__file__).resolve().parents[6]
SOURCE_COUNTRIES = {"Sweden", "Denmark", "Norway", "Finland"}


def _assert_committed_source_chronology_contract(
    layers: Mapping[str, Mapping[str, object]],
) -> None:
    expected_refusal_reasons = {
        "source_sample_presence": "reviewed_pollen_sum_not_available",
        "source_ecological_code": "source_ecological_equivalence_not_reviewed",
        "source_taxon": "source_taxon_equivalence_not_reviewed",
    }
    for layer in layers.values():
        facets = cast(Mapping[str, object], layer["facet_metadata"])
        features = cast(list[dict[str, object]], layer["features"])
        assert layer["applies_time_filter"] is True
        assert layer["temporal_direction"] == "oldest_to_present"
        assert layer["interval_semantics"] == "[younger_bp, older_bp]"
        assert layer["propagation_status"] == "refused"
        assert layer["edge_count"] == 0
        assert facets["schema_version"] == "neotoma-source-chronology-facets.v3"
        assert facets["time_min_bp"] == 0
        assert facets["time_max_bp"] == 22_911
        assert {
            cast(str, row["value"])
            for row in cast(list[dict[str, object]], facets["country_counts"])
        } == SOURCE_COUNTRIES
        assert all(feature["propagation_eligible"] is False for feature in features)
        assert all(
            feature["candidate_generation_status"] == "refused" for feature in features
        )
        assert {feature["candidate_refusal_reason"] for feature in features} == {
            expected_refusal_reasons[cast(str, layer["node_level"])]
        }
        intervals = [
            (cast(float, feature["time_end_bp"]), cast(float, feature["time_start_bp"]))
            for feature in features
        ]
        assert all(0 <= younger <= older for older, younger in intervals)
        oldest_bounds = [older for older, _younger in intervals]
        assert oldest_bounds == sorted(oldest_bounds, reverse=True)

    code_facets = cast(
        Mapping[str, object], layers["neotoma-source-ecological-code"]["facet_metadata"]
    )
    code_rows = {
        cast(str, row["value"]): row
        for row in cast(list[dict[str, object]], code_facets["source_ecological_codes"])
    }
    assert {
        code: (
            code_rows[code]["node_count"],
            code_rows[code]["observation_denominator"],
            code_rows[code]["time_min_bp"],
            code_rows[code]["time_max_bp"],
        )
        for code in code_rows
    } == {
        "AQVP": (4_991, 9_666, 0, 19_190),
        "SEED": (108, 108, 31, 10_282),
        "TRSH": (9_978, 114_225, 0, 22_911),
        "UNID": (160, 165, 19, 9_815),
        "UPHE": (9_928, 91_739, 0, 22_911),
    }
    taxon_facets = cast(
        Mapping[str, object], layers["neotoma-source-exact-taxon"]["facet_metadata"]
    )
    taxa = cast(list[dict[str, object]], taxon_facets["source_taxa"])
    assert len(taxa) == 972
    assert len({cast(str, row["value"]) for row in taxa}) == 972


def _assert_committed_static_publication_budgets() -> None:
    bundle_root = ROOT / "docs/report/regions/nordic"
    manifest_path = bundle_root / "nordic_map_assets.json"
    manifest = cast(
        dict[str, object], json.loads(manifest_path.read_text(encoding="utf-8"))
    )
    rows = normalize_asset_inventory(manifest["assets"])
    paths = [bundle_root / cast(str, row["path"]) for row in rows]
    assert len(rows) == 232
    assert len(paths) <= ATLAS_STATIC_ASSETS_MAX_FILES
    assert all(path.is_file() for path in paths)
    assert all(
        path.stat().st_size == cast(int, row["byte_count"])
        for path, row in zip(paths, rows, strict=True)
    )
    assert sum(path.stat().st_size for path in paths) <= ATLAS_STATIC_ASSETS_MAX_BYTES
    assert max(path.stat().st_size for path in paths) <= ATLAS_CHUNK_MAX_BYTES
    assert manifest_path.stat().st_size <= ATLAS_BOOTSTRAP_MAX_BYTES
    initial_rows = [row for row in rows if row["initial_load"] is True]
    assert len(initial_rows) <= ATLAS_INITIAL_MAX_REQUESTS
    assert sum(cast(int, row["byte_count"]) for row in initial_rows) <= (
        ATLAS_INITIAL_MAX_BYTES
    )
    index_rows = [row for row in rows if row["domain"] == "indexes"]
    assert len(index_rows) == 1
    assert index_rows[0]["initial_load"] is False
    map_document = (bundle_root / "nordic_map.html").read_text(encoding="utf-8")
    assert len(map_document.encode("utf-8")) <= ATLAS_DOCUMENT_MAX_BYTES
    assert "function sourceChronologyPlaybackSelection()" in map_document
    assert "const selection = sourceChronologyPlaybackSelection();" in map_document
    assert "return selection || globalTimePlaybackExtent();" in map_document


def test_committed_source_nodes_reconcile() -> None:
    source_path = ROOT / "data/neotoma/normalized/nordic_pollen_sites.geojson"
    geojson = json.loads(source_path.read_text(encoding="utf-8"))
    base_layer = build_external_point_layer(geojson, source_path=source_path)

    details, accounting, source_layers = _project_neotoma(ROOT / "data", base_layer)

    assert len(details) == 193
    source_accounting = cast(dict[str, object], accounting["source_chronology"])
    assert source_accounting["source_node_count"] == 250_904
    assert source_accounting["layer_counts"] == {
        "source_ecological_code": 25_165,
        "source_sample_presence": 9_988,
        "source_taxon": 215_751,
    }
    assert source_accounting["country_counts"] == {
        "Sweden": 118_704,
        "Denmark": 3_769,
        "Norway": 93_727,
        "Finland": 34_704,
    }
    layers = {str(layer["node_level"]): layer for layer in source_layers}
    code_facets = cast(
        Mapping[str, object], layers["source_ecological_code"]["facet_metadata"]
    )
    code_rows = {
        str(row["value"]): row
        for row in cast(list[dict[str, object]], code_facets["source_ecological_codes"])
    }
    assert {
        code: (
            code_rows[code]["label"],
            code_rows[code]["source_code"],
            code_rows[code]["node_count"],
            code_rows[code]["observation_denominator"],
        )
        for code in ("TRSH", "UPHE", "AQVP")
    } == {
        "TRSH": ("Trees and Shrubs", "TRSH", 9_978, 114_225),
        "UPHE": ("Upland Herbs", "UPHE", 9_928, 91_739),
        "AQVP": ("Aquatic Vascular Plants", "AQVP", 4_991, 9_666),
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

    layer_counts = {
        str(layer["key"]): cast(int, layer["count"]) for layer in source_layers
    }
    existing_points = committed_nordic_inputs(ROOT)[0]
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
    _assert_committed_source_chronology_contract(committed_source_layers)


def test_committed_static_bundle_fits_budgets_and_indexes() -> None:
    _assert_committed_static_publication_budgets()
    bundle_root = ROOT / "docs/report/regions/nordic"
    manifest = cast(
        dict[str, object],
        json.loads((bundle_root / "nordic_map_assets.json").read_text("utf-8")),
    )
    rows = normalize_asset_inventory(manifest["assets"])
    layer_counts = {
        "neotoma-source-ecological-code": 25_165,
        "neotoma-source-sample-pollen-context": 9_988,
        "neotoma-source-exact-taxon": 215_751,
    }
    assert_point_layer_index_coverage(
        decode_committed_static_indexes(bundle_root, rows), layer_counts
    )
