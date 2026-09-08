from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random

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
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (
    decode_index_bundle,
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
    assets = normalize_asset_inventory(first.manifest["assets"])
    node_assets = [row for row in assets if row["domain"] == "nodes"]
    assert len(node_assets) > 1
    assert {tuple(row["country_keys"]) for row in node_assets} >= {
        ("Norway",),
        ("Sweden",),
    }
    assert all(row["initial_load"] is False for row in node_assets)
    index_assets = [row for row in assets if row["domain"] == "indexes"]
    assert len(index_assets) == 1
    assert index_assets[0]["initial_load"] is False
    initial_assets = [row for row in assets if row["initial_load"] is True]
    assert {row["domain"] for row in initial_assets} == {
        "provenance",
        "edges",
        "sequences",
    }
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
    asset_rows = normalize_asset_inventory(first.manifest["assets"])
    assert all(
        isinstance(row["decoded_byte_count"], int)
        and row["decoded_byte_count"] <= ATLAS_CHUNK_MAX_BYTES
        for row in asset_rows
    )
    assert all(
        row["payload_encoding"]
        == (
            "gzip_base64"
            if row["domain"] in {"nodes", "details", "provenance"}
            else "json"
        )
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

    rows = normalize_asset_inventory(assets.manifest["assets"])
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
    detail_record_asset_keys = decode_index_bundle(indexes)["detail_record_asset_keys"]
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
    manifest_assets = normalize_asset_inventory(assets.manifest["assets"])
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


def test_animal_chronology_contract_and_admitted_bounds_survive_static_chunking(
    tmp_path: Path,
) -> None:
    layer_posture: JsonObject = {
        "group": "animal-chronology-context",
        "semantic_role": "animal_source_chronology_context",
        "contribution_role": "display_only",
        "default_enabled": False,
        "applies_country_filter": True,
        "applies_time_filter": True,
        "candidate_ranking_eligible": False,
        "scientific_classification_eligible": False,
        "scientific_selection_enabled": False,
        "propagation_status": "refused",
        "propagation_reason_code": "display_only_source_chronology",
        "edge_count": 0,
        "circle_enabled": False,
    }
    feature_posture: JsonObject = {
        "semantic_role": "animal_source_chronology_context",
        "contribution_role": "display_only",
        "candidate_ranking_eligible": False,
        "scientific_classification_eligible": False,
        "scientific_selection_enabled": False,
        "propagation_status": "refused",
        "propagation_reason_code": "display_only_source_chronology",
        "edge_count": 0,
    }
    admitted = [
        {
            **feature_posture,
            "feature_id": "animal-sample:PRJEB81815:cat-1",
            "record_id": "animal-sample:PRJEB81815:cat-1",
            "project_accession": "PRJEB81815",
            "repo_stable_sample_id": "cat-1",
            "project_species_latin_name": "Felis catus",
            "project_species_common_name": "cat",
            "species_attribution_basis": "governed_project_registry",
            "country": "Sweden",
            "latitude": 59.0,
            "longitude": 18.0,
            "time_start_bp": 340,
            "time_end_bp": 527,
        },
        {
            **feature_posture,
            "feature_id": "animal-sample:PRJEB81815:cat-2",
            "record_id": "animal-sample:PRJEB81815:cat-2",
            "project_accession": "PRJEB81815",
            "repo_stable_sample_id": "cat-2",
            "project_species_latin_name": "Felis catus",
            "project_species_common_name": "cat",
            "species_attribution_basis": "governed_project_registry",
            "country": "Sweden",
            "latitude": 60.0,
            "longitude": 19.0,
            "time_start_bp": 1000,
            "time_end_bp": 8173,
        },
    ]
    inadmissible = [
        {"time_start_bp": None, "time_end_bp": None},
        {"time_start_bp": 100, "time_end_bp": None},
        {"time_start_bp": -1, "time_end_bp": 50},
        {"time_start_bp": 900, "time_end_bp": 800},
        {
            "time_start_bp": 1,
            "time_end_bp": 999_999,
            "temporal_semantics": {
                "comparability_posture": "refused",
                "refusal_reason_code": "source_age_system_not_comparable",
            },
        },
    ]
    features: list[JsonObject] = [*admitted]
    for index, chronology in enumerate(inadmissible):
        features.append(
            {
                **feature_posture,
                "feature_id": f"animal-sample:refused:{index}",
                "record_id": f"animal-sample:refused:{index}",
                "project_accession": "PRJEB81815",
                "repo_stable_sample_id": f"refused-{index}",
                "project_species_latin_name": "Felis catus",
                "project_species_common_name": "cat",
                "species_attribution_basis": "governed_project_registry",
                "country": "Sweden",
                "latitude": 61.0,
                "longitude": 20.0,
                **chronology,
            }
        )
    layer: JsonObject = {
        "key": "animal-source-chronology-felis-catus",
        "label": "Cat source-sample chronology",
        "project_species_latin_name": "Felis catus",
        "project_species_common_name": "cat",
        "species_attribution_basis": "governed_project_registry",
        **layer_posture,
        "features": features,
    }

    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="v66",
        point_layers=[layer],
        polygon_layers=[],
    )
    rows = normalize_asset_inventory(assets.manifest["assets"])
    node_row = next(row for row in rows if row["domain"] == "nodes")
    assert node_row["time_min_bp"] == 340
    assert node_row["time_max_bp"] == 8173
    assert node_row["untimed_record_count"] == 5
    assert node_row["chronology_absent_record_count"] == 1
    assert node_row["refused_chronology_record_count"] == 4
    assert node_row["contextual_chronology_record_count"] == 0

    payloads = [read_static_asset_payload(path) for path in assets.asset_paths]
    provenance = next(
        payload
        for payload in payloads
        if payload["schema_version"] == "atlas-provenance-chunk.v3"
    )
    layer_metadata = provenance["layers"][0]["layer"]
    for field, expected in layer_posture.items():
        assert layer_metadata[field] == expected
    assert layer_metadata["project_species_latin_name"] == "Felis catus"
    assert layer_metadata["project_species_common_name"] == "cat"
    assert layer_metadata["species_attribution_basis"] == "governed_project_registry"

    nodes = next(
        payload
        for payload in payloads
        if payload["schema_version"] == "atlas-node-chunk.v1"
    )
    observed = nodes["features"]
    assert observed == features
    assert [feature["feature_id"] for feature in observed[:2]] == [
        "animal-sample:PRJEB81815:cat-1",
        "animal-sample:PRJEB81815:cat-2",
    ]
    assert observed[0]["project_species_latin_name"] == "Felis catus"
    assert observed[1]["project_species_latin_name"] == "Felis catus"
    assert observed[0]["project_accession"] == "PRJEB81815"
    assert observed[0]["repo_stable_sample_id"] == "cat-1"
