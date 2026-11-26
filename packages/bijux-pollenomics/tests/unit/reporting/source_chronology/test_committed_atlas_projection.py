"""Committed source denominators and static-publication proof."""

from __future__ import annotations

import base64
from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import cast

import pytest

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
pytestmark = pytest.mark.generated_artifacts


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
        assert facets["schema_version"] == "neotoma-source-chronology-facets.v4"
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
    published = json.loads((bundle_root / "nordic_bundle.json").read_text("utf-8"))
    published_assets = [
        row["filename"]
        for row in published["artifacts"]["extra_files"]
        if row["label"] == "Static atlas data chunk"
    ]
    assert len(published_assets) == len(set(published_assets))
    assert set(published_assets) == {row["path"] for row in rows}
    assert set(published_assets) == {
        path.relative_to(bundle_root).as_posix()
        for path in bundle_root.glob(f"{manifest['scope_slug']}.atlas-*.js")
    }
    raa_rows = [row for row in rows if row.get("layer_key") == "raa-archaeology"]
    assert len(raa_rows) == 1
    assert raa_rows[0]["domain"] == "nodes"
    assert raa_rows[0]["record_count"] == 106
    assert raa_rows[0]["country_keys"] == ["Sweden"]
    assert raa_rows[0]["chronology_absent_record_count"] == 106
    assert raa_rows[0]["scientific_signal_ids"] == []
    map_document = (bundle_root / "nordic_map.html").read_text(encoding="utf-8")
    bootstraps = re.findall(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        map_document,
        re.S,
    )
    assert len(bootstraps) == 1
    bootstrap = json.loads(bootstraps[0])
    assert {
        key: value for key, value in bootstrap.items() if key != "runtime"
    } == manifest
    runtime = bootstrap["runtime"]
    runtime_path = (bundle_root / runtime["path"]).resolve(strict=True)
    assert runtime_path.is_relative_to(bundle_root.resolve())
    runtime_bytes = runtime_path.read_bytes()
    assert len(runtime_bytes) == runtime["byte_count"]
    runtime_integrity = "sha256-" + base64.b64encode(
        hashlib.sha256(runtime_bytes).digest()
    ).decode("ascii")
    assert runtime_integrity == runtime["integrity"]
    runtime_document = runtime_bytes.decode("utf-8")
    assert "const TIME_MIN_BP = 0;" in runtime_document
    sead_rows = [row for row in rows if row.get("layer_key") == "sead-sites"]
    assert sum(cast(int, row["record_count"]) for row in sead_rows) == 2_069
    assert sum(cast(int, row["untimed_record_count"]) for row in sead_rows) == 1_219
    assert all(
        cast(float, row["time_min_bp"]) >= 0
        for row in sead_rows
        if row["time_min_bp"] is not None
    )
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
    assert index_rows and all(row["initial_load"] is False for row in index_rows)
    map_document = (bundle_root / "nordic_map.html").read_text(encoding="utf-8")
    assert len(map_document.encode("utf-8")) <= ATLAS_DOCUMENT_MAX_BYTES
    assert "function sourceChronologyPlaybackSelection()" in runtime_document
    assert "const selection = sourceChronologyPlaybackSelection();" in runtime_document
    assert "return selection || globalTimePlaybackExtent();" in runtime_document


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

    current_chronology = {
        str(layer["key"]): layer
        for layer in source_layers
        if layer.get("semantic_role") == "source_chronology_context"
    }
    charcoal_layers = [
        layer
        for layer in source_layers
        if layer.get("semantic_role") == "native_charcoal_source_context"
    ]
    assert len(current_chronology) == 3
    assert len(charcoal_layers) == 1
    assert len(current_chronology) + len(charcoal_layers) == len(source_layers)
    charcoal = charcoal_layers[0]
    charcoal_features = cast(list[dict[str, object]], charcoal["features"])
    assert charcoal["key"] == "neotoma-native-charcoal-context"
    assert charcoal["source_name"] == "Neotoma"
    assert charcoal["contribution_role"] == "display_only"
    assert charcoal["count"] == len(charcoal_features) == 2_900
    assert charcoal["default_enabled"] is False
    assert charcoal["candidate_ranking_eligible"] is False
    assert charcoal["scientific_classification_eligible"] is False
    assert charcoal["scientific_selection_enabled"] is False
    assert charcoal["propagation_status"] == "refused"
    assert charcoal["edge_count"] == 0
    assert all(
        row["candidate_generation_status"] == "refused"
        and row["candidate_refusal_reason"]
        == "literal_source_observation_not_scientific_event"
        and row["propagation_eligible"] is False
        and row["source_family"] == "neotoma"
        and row["source_ecological_group"] == "CHAR"
        and row["source_snapshot_id"] == accounting["source_snapshot_id"]
        and row["build_id"] == accounting["build_id"]
        and row["node_id"] == f"neotoma:native-charcoal:{row['observation_id']}"
        and row["source_observation_locator"]
        == f"surfaces/observations/part-{row['source_part_number']:05d}.json#observation_id={row['observation_id']}"
        for row in charcoal_features
    )
    charcoal_account = cast(dict[str, object], accounting["native_charcoal"])
    assert charcoal_account["source_snapshot_id"] == accounting["source_snapshot_id"]
    assert charcoal_account["build_id"] == accounting["build_id"]
    assert charcoal_account["published_observation_count"] == len(charcoal_features)
    assert charcoal_account["scientific_event_count"] == 0
    assert charcoal_account["propagation_eligible_event_count"] == 0
    source_charcoal = {}
    observation_parts = ROOT / "data/neotoma/relational/surfaces/observations"
    for path in sorted(observation_parts.glob("part-*.json")):
        part = json.loads(path.read_bytes())
        actual_part_number = int(path.stem.removeprefix("part-"))
        assert part["part_number"] == actual_part_number
        for row in part["rows"]:
            if row.get("source_ecological_group") == "CHAR":
                assert row["observation_id"] not in source_charcoal
                source_charcoal[row["observation_id"]] = (row, actual_part_number)
    exclusions = cast(
        list[dict[str, object]], charcoal_account["excluded_observations"]
    )
    assert len(source_charcoal) == charcoal_account["native_charcoal_observation_count"]
    feature_ids = {row["observation_id"] for row in charcoal_features}
    excluded_ids = {row["observation_id"] for row in exclusions}
    assert len(feature_ids) == len(charcoal_features)
    assert len(excluded_ids) == len(exclusions)
    assert charcoal_account["excluded_observation_count"] == len(exclusions)
    assert all(
        isinstance(row["reason_code"], str) and row["reason_code"] for row in exclusions
    )
    assert charcoal_account["excluded_reason_counts"] == dict(
        sorted(Counter(str(row["reason_code"]) for row in exclusions).items())
    )
    assert not feature_ids & excluded_ids
    assert feature_ids | excluded_ids == set(source_charcoal)
    assert all(
        feature["source_part_number"] == source_charcoal[feature["observation_id"]][1]
        for feature in charcoal_features
    )
    assert all(
        all(
            json.dumps(feature[field], sort_keys=True, allow_nan=False)
            == json.dumps(
                source_charcoal[feature["observation_id"]][0].get(field),
                sort_keys=True,
                allow_nan=False,
            )
            for field in (
                "observation_id",
                "sample_id",
                "variable_id",
                "source_taxon_id",
                "source_reported_name",
                "source_ecological_group",
                "source_element",
                "source_element_type",
                "source_value",
                "source_unit",
                "source_denominator",
                "denominator_status",
                "detection_status",
                "unit_family",
                "source_context",
            )
        )
        for feature in charcoal_features
    )
    layer_counts = {
        key: cast(int, layer["count"]) for key, layer in current_chronology.items()
    }
    existing_points = committed_nordic_inputs(ROOT)[0]
    assert not any(
        layer.get("semantic_role") == "native_charcoal_source_context"
        or layer.get("key") == "neotoma-native-charcoal-context"
        for layer in existing_points
    )
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
        decode_committed_static_indexes(bundle_root, rows, manifest=manifest),
        layer_counts,
    )


@pytest.mark.parametrize("damage", ["missing", "duplicate", "reordered"])
def test_committed_index_parts_refuse_inventory_damage(damage: str) -> None:
    bundle_root = ROOT / "docs/report/regions/nordic"
    manifest = json.loads((bundle_root / "nordic_map_assets.json").read_text("utf-8"))
    assert (
        manifest["compatibility"]["index_transport_schema"]
        == "atlas-static-index-part.v1"
    )
    rows = normalize_asset_inventory(manifest["assets"])
    positions = [index for index, row in enumerate(rows) if row["domain"] == "indexes"]
    assert len(positions) > 1
    damaged = deepcopy(rows)
    if damage == "missing":
        damaged.pop(positions[-1])
    elif damage == "duplicate":
        damaged.append(deepcopy(damaged[positions[0]]))
    else:
        first, last = positions[0], positions[-1]
        damaged[first], damaged[last] = damaged[last], damaged[first]
    with pytest.raises(ValueError, match="index"):
        decode_committed_static_indexes(bundle_root, damaged, manifest=manifest)
