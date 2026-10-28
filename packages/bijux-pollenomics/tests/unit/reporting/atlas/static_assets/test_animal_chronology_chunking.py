"""Animal source chronology remains contextual in static atlas chunks."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.core.geospatial.geojson import JsonObject
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)

from .payloads import mapping_rows, read_static_asset_payload


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
    for feature in admitted:
        feature["temporal_semantics"] = {
            "comparability_posture": "numeric_interval_with_caveat",
            "evidence_class": "direct_numeric_sample_date",
            "precision_posture": "sample_precise_interval",
        }
    inadmissible: list[JsonObject] = [
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
    provenance_layers = mapping_rows(provenance["layers"])
    assert len(provenance_layers) == 1
    layer_metadata = provenance_layers[0]["layer"]
    assert isinstance(layer_metadata, dict)
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
