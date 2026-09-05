from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.core.geojson import JsonObject
from bijux_pollenomics.reporting.context.artifacts import stage_context_point_layers
from bijux_pollenomics.reporting.map_document import evidence_projection
from bijux_pollenomics.reporting.map_document.evidence_projection import (
    build_map_evidence_projection,
)
from bijux_pollenomics.reporting.map_document.static_assets import (
    ATLAS_CHUNK_MAX_BYTES,
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE


def _write_json(path: Path, value: object) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path.write_bytes(payload)
    return payload


def _decode_sead_claim_table(table: dict[str, object]) -> list[dict[str, object]]:
    fields = cast(list[str], table["fields"])
    dictionaries = cast(dict[str, list[object]], table["column_dictionaries"])
    list_fields = set(cast(list[str], table["list_dictionary_fields"]))
    list_dictionary = cast(list[str], table["list_value_dictionary"])
    age_columns = cast(
        dict[str, list[str]], table["source_age_value_columns_by_claim_type"]
    )
    inherited = cast(
        dict[str, dict[str, str]],
        table["source_age_value_inherited_fields_by_claim_type"],
    )
    age_dictionaries = cast(
        dict[str, dict[str, list[object]]],
        table["source_age_value_dictionaries_by_claim_type"],
    )
    relation_dictionary = cast(
        list[list[list[str]]], table["source_relation_path_dictionary"]
    )
    common = cast(dict[str, object], table["common_fields"])
    decoded: list[dict[str, object]] = []
    for encoded in cast(list[list[object]], table["records"]):
        row = dict(zip(fields, encoded, strict=True))
        for field, dictionary in dictionaries.items():
            row[field] = dictionary[cast(int, row[field])]
        for field in list_fields:
            row[field] = [
                list_dictionary[index] for index in cast(list[int], row[field])
            ]
        claim_type = cast(str, row["claim_type"])
        source_age_value: dict[str, object] = {}
        for field, encoded_value in zip(
            age_columns[claim_type],
            cast(list[object], row["source_age_value"]),
            strict=True,
        ):
            age_dictionary = age_dictionaries[claim_type].get(field)
            source_age_value[field] = (
                age_dictionary[cast(int, encoded_value)]
                if age_dictionary is not None
                else encoded_value
            )
        for source_field, claim_field in inherited[claim_type].items():
            source_age_value[source_field] = row[claim_field]
        row["source_age_value"] = source_age_value
        relation_shape = relation_dictionary[cast(int, row["source_relation_path"])]
        row["source_relation_path"] = [
            {
                "table": table_name,
                "key": key,
                "value": (
                    common["source_site_id"]
                    if value_field == "common_fields.source_site_id"
                    else row[value_field]
                ),
            }
            for table_name, key, value_field in relation_shape
        ]
        decoded.append({**common, **row})
    return decoded


def _neotoma_fixture(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    relational = root / "neotoma" / "relational"
    build_id = "sha256:" + "b" * 64
    snapshot_id = "sha256:" + "s" * 64
    surfaces: dict[str, object] = {}
    surface_rows: dict[str, list[dict[str, object]]] = {
        "sites": [
            {
                "site_id": "neotoma:site:10",
                "country_code": "SE",
                "country_decision_status": "assigned",
            }
        ],
        "collection_units": [
            {
                "site_id": "neotoma:site:10",
                "collection_unit_id": "neotoma:collection-unit:20",
                "source_collection_unit_id": 20,
                "source_payload": {"collunittype": "Core", "location": None},
            }
        ],
        "datasets": [
            {
                "site_id": "neotoma:site:10",
                "dataset_id": "neotoma:dataset:30",
                "collection_unit_id": "neotoma:collection-unit:20",
                "source_dataset_id": 30,
                "source_payload": {"datasettype": "pollen", "doi": []},
            }
        ],
        "samples": [
            {
                "site_id": "neotoma:site:10",
                "sample_id": "neotoma:sample:40",
                "collection_unit_id": "neotoma:collection-unit:20",
                "dataset_id": "neotoma:dataset:30",
                "source_sample_id": 40,
                "source_analysis_unit_id": 41,
                "source_payload": {"depth": 12, "thickness": None},
            }
        ],
        "age_claims": [
            {
                "site_id": "neotoma:site:10",
                "chronology_claim_id": "neotoma:age-claim:40:1",
                "subject_type": "sample",
                "subject_id": "neotoma:sample:40",
                "source_record_id": "neotoma:sample:40",
                "chronology_id": "neotoma:chronology:20:1",
                "chronology_name": "Default",
                "collection_unit_id": "neotoma:collection-unit:20",
                "dataset_id": "neotoma:dataset:30",
                "source_age_type": "Calibrated radiocarbon years BP",
                "source_age_unit": "year",
                "source_age_value": 125.5,
                "source_age_younger": None,
                "source_age_older": None,
                "younger_bp": 125.5,
                "older_bp": 125.5,
                "calibration_status": "calibrated",
                "comparability_status": "comparable",
                "admission_reason": None,
                "refusal_reason": None,
                "is_default_chronology": True,
                "provenance_record_id": snapshot_id,
                "source_relation_path": "neotoma:dataset:30/neotoma:sample:40/ages/1",
            }
        ],
        "variables": [
            {
                "variable_id": "neotoma:variable:50",
                "source_taxon_id": 50,
                "source_reported_name": "Triticum",
                "source_semantics": [{"source_element": "pollen"}],
                "source_units": ["NISP"],
            }
        ],
        "observations": [
            {
                "site_id": "neotoma:site:10",
                "observation_id": "neotoma:observation:40:50:1",
                "sample_id": "neotoma:sample:40",
                "variable_id": "neotoma:variable:50",
                "source_value": 3,
                "source_unit": "NISP",
                "source_denominator": None,
                "denominator_status": "not_provided_by_source",
                "detection_status": "reported_value",
                "source_context": None,
                "source_taxon_id": 50,
                "source_reported_name": "Triticum",
                "source_ecological_group": "CROP",
                "source_element": "pollen",
                "source_element_type": "pollen",
                "aggregation_key": "neotoma:exact-unit:NISP",
                "unit_family": "count",
            }
        ],
    }
    for name, rows in surface_rows.items():
        relative = f"surfaces/{name}/part-00001.json"
        payload = _write_json(
            relational / relative,
            {"row_count": len(rows), "rows": rows},
        )
        surfaces[name] = {
            "row_count": len(rows),
            "parts": [
                {"path": relative, "sha256": hashlib.sha256(payload).hexdigest()}
            ],
        }
    manifest = {
        "source_snapshot_id": snapshot_id,
        "build_id": build_id,
        "materialization_sha256": "m" * 64,
        "surfaces": surfaces,
    }
    monkeypatch.setattr(
        evidence_projection,
        "validate_neotoma_relational_materialization",
        lambda _root: manifest,
    )


def _sead_fixture(root: Path) -> None:
    run_id = "sead-fixture"
    build_id = "sha256:" + "c" * 64
    acquisition = root / "sead" / "raw" / "acquisitions" / run_id
    countries = (("1", "Sweden"), ("2", "Denmark"), ("3", "Norway"), ("4", "Finland"))
    site_payload = _write_json(
        acquisition / "payloads" / "tbl_sites.json",
        {
            "table": "tbl_sites",
            "rows": [{"site_id": int(site_id)} for site_id, _ in countries],
        },
    )
    manifest_payload = _write_json(
        acquisition / "manifest.json", {"status": "complete"}
    )
    country_codes = {
        "Sweden": "SE",
        "Denmark": "DK",
        "Norway": "NO",
        "Finland": "FI",
    }
    decisions_payload = _write_json(
        acquisition / "country-decisions.json",
        {
            "decisions": [
                {
                    "site_id": int(site_id),
                    "governed_country_code": country_codes[country],
                    "decision": {"decision_status": "assigned"},
                }
                for site_id, country in countries
            ]
        },
    )
    copied = []
    for relative, payload in (
        ("manifest.json", manifest_payload),
        ("country-decisions.json", decisions_payload),
        ("payloads/tbl_sites.json", site_payload),
    ):
        copied.append(
            {
                "path": relative,
                "byte_count": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    acquisition_manifest_sha256 = hashlib.sha256(manifest_payload).hexdigest()
    country_decisions_sha256 = hashlib.sha256(decisions_payload).hexdigest()
    acquisition_bundle_sha256 = "sha256:" + "d" * 64
    _write_json(
        acquisition / "admission.json",
        {
            "schema_version": "sead-acquisition-admission.v1",
            "source_family": "sead",
            "run_id": run_id,
            "build_id": build_id,
            "acquisition_manifest_sha256": acquisition_manifest_sha256,
            "acquisition_bundle_sha256": acquisition_bundle_sha256,
            "release_status": "refused",
            "copied_files": copied,
        },
    )
    claim = {
        "chronology_claim_id": "sead:site-2:dating_range:9",
        "source_family": "sead",
        "source_site_id": "2",
        "site_uuid": "site-2",
        "country_code": "DK",
        "latitude_dd": 55.0,
        "longitude_dd": 10.0,
        "country_assignment_method": "strict_boundary_containment",
        "source_table": "tbl_analysis_dating_ranges",
        "source_record_id": "9",
        "source_native_record_id": "9",
        "subject_type": "analysis_entity",
        "subject_id": "90",
        "sample_group_id": 20,
        "physical_sample_id": 21,
        "analysis_entity_id": 90,
        "analysis_value_id": 91,
        "dataset_id": 30,
        "claim_type": "dating_range",
        "source_age_type": "AD",
        "source_age_value": {
            "analysis_entity_id": 90,
            "physical_sample_id": 21,
            "sample_group_id": 20,
            "dataset_id": 30,
            "analysis_dating_range_id": 9,
            "analysis_value_id": 91,
            "age_type_id": 1,
            "dating_uncertainty_id": None,
            "age_type": "AD",
            "age_type_description": "Anno Domini",
            "low_value": 1850,
            "high_value": None,
            "low_qualifier": "",
            "high_qualifier": "",
            "low_is_uncertain": False,
            "high_is_uncertain": False,
            "uncertainty_label": "",
            "uncertainty_description": "",
            "time_start_bp": 100,
            "time_end_bp": 100,
        },
        "source_age_unit": "calendar_year",
        "calibration_status": "not_applicable",
        "younger_bp": 100,
        "older_bp": 100,
        "comparability_status": "comparable",
        "chronology_eligibility": "eligible",
        "propagation_eligibility": "refused",
        "propagation_reason_codes": ["observation_link_not_materialized"],
        "publication_role": "chronology_display_only",
        "reason_codes": [],
        "transformation_id": "sead-calendar-year-to-cal-bp-1950-v1",
        "original_interval_orientation": "point",
        "selection_status": "retained_unselected",
        "selection_rule_version": "sead-retain-all-source-chronologies-v1",
        "provenance_record_id": "sead-acquisition-manifest:fixture",
        "build_id": build_id,
        "source_relation_path": [
            {"table": "tbl_sites", "key": "site_id", "value": "2"},
            {
                "table": "tbl_sample_groups",
                "key": "sample_group_id",
                "value": 20,
            },
            {
                "table": "tbl_physical_samples",
                "key": "physical_sample_id",
                "value": 21,
            },
            {
                "table": "tbl_analysis_entities",
                "key": "analysis_entity_id",
                "value": 90,
            },
            {"table": "tbl_datasets", "key": "dataset_id", "value": 30},
            {
                "table": "tbl_analysis_values",
                "key": "analysis_value_id",
                "value": 91,
            },
            {
                "table": "tbl_analysis_dating_ranges",
                "key": "analysis_dating_range_id",
                "value": "9",
            },
        ],
        "schema_version": "sead-chronology-claim.v1",
        "source_payload_sha256": "e" * 64,
        "acquisition_manifest_sha256": acquisition_manifest_sha256,
    }
    _write_json(
        root / "sead" / "normalized" / "chronology_claims.json",
        {
            "schema_version": "sead-chronology-claim-bundle.v1",
            "source_family": "sead",
            "source_run_id": run_id,
            "source_build_id": build_id,
            "acquisition_manifest_sha256": acquisition_manifest_sha256,
            "acquisition_bundle_sha256": acquisition_bundle_sha256,
            "country_decisions_sha256": country_decisions_sha256,
            "table_payload_sha256": {
                "tbl_sites": hashlib.sha256(site_payload).hexdigest()
            },
            "claim_count": 1,
            "claims": [claim],
            "propagation_status": "refused",
            "propagation_reason_code": "observation_relations_not_captured",
        },
    )
    features = []
    for site_id, country in countries:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [10, 55]},
                "properties": {
                    "source": "SEAD",
                    "layer_key": "sead-sites",
                    "record_id": site_id,
                    "name": f"Site {site_id}",
                    "country": country,
                    "source_url": f"https://example.test/{site_id}",
                },
            }
        )
    _write_json(
        root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
        {"type": "FeatureCollection", "features": features},
    )


def _projection_layers() -> list[dict[str, object]]:
    return [
        {
            "key": "neotoma-pollen",
            "features": [{"evidence_row_id": "10", "country": "Sweden"}],
        },
        {
            "key": "sead-sites",
            "features": [
                {"evidence_row_id": str(index), "country": country}
                for index, country in enumerate(
                    ("Sweden", "Denmark", "Norway", "Finland"), start=1
                )
            ],
        },
        {
            "key": "sweden-archaeology-site-discovery",
            "features": [
                {"evidence_row_id": "1:unresolved:discovery", "country": "Sweden"}
            ],
        },
    ]


def test_projection_is_fixed_point_lossless_and_four_country_reconciled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.absolute()
    _neotoma_fixture(root, monkeypatch)
    _sead_fixture(root)
    first_layers = _projection_layers()
    second_layers = _projection_layers()

    first = build_map_evidence_projection(root, first_layers)
    second = build_map_evidence_projection(root, second_layers)

    assert first == second
    assert first_layers == second_layers
    assert [str(row["record_id"]) for row in first.detail_records] == sorted(
        str(row["record_id"]) for row in first.detail_records
    )
    assert first.reconciliation["source_feature_count"] == 6
    assert first.reconciliation["detail_record_count"] == 5
    assert first.reconciliation["repeated_feature_reference_count"] == 1
    sources = cast(dict[str, object], first.reconciliation["sources"])
    neotoma = cast(dict[str, object], sources["neotoma"])
    assert cast(dict[str, int], neotoma["detail_row_counts"])["variables"] == 1
    sead = cast(dict[str, object], sources["sead"])
    assert sead["country_site_counts"] == {
        "Denmark": 1,
        "Finland": 1,
        "Norway": 1,
        "Sweden": 1,
    }
    assert sead["bbox_site_denominator"] == 4
    assert sead["assigned_site_count"] == 4
    assert sead["excluded_site_count"] == 0
    details = {str(row["record_id"]): row for row in first.detail_records}
    neotoma_tabs = cast(dict[str, object], details["neotoma:site:10"]["tabs"])
    samples = cast(dict[str, object], neotoma_tabs["samples"])
    assert cast(dict[str, object], samples["samples"])["record_count"] == 1
    chronology = cast(dict[str, object], neotoma_tabs["chronology"])
    assert chronology["interval_semantics"] == "[younger_bp, older_bp]"
    age_row = dict(
        zip(
            cast(list[str], chronology["fields"]),
            cast(list[list[object]], chronology["records"])[0],
            strict=True,
        )
    )
    assert age_row["source_age_younger"] is None
    assert age_row["source_age_older"] is None
    assert age_row["younger_bp"] == age_row["older_bp"] == 125.5
    age_prefixes = cast(dict[str, str], chronology["identifier_prefixes"])
    assert (
        age_prefixes["collection_unit_id"] + str(age_row["collection_unit_id"])
        == "neotoma:collection-unit:20"
    )
    assert age_prefixes["dataset_id"] + str(age_row["dataset_id"]) == (
        "neotoma:dataset:30"
    )
    assert age_row["provenance_record_id"] == "sha256:" + "s" * 64
    composition = cast(dict[str, object], neotoma_tabs["pollen_composition"])
    assert composition["record_count"] == 1
    assert composition["aggregation_posture"] == (
        "source rows retained without cross-unit summing"
    )
    observation_row = dict(
        zip(
            cast(list[str], composition["fields"]),
            cast(list[list[object]], composition["records"])[0],
            strict=True,
        )
    )
    assert observation_row["source_unit"] == "NISP"
    assert observation_row["source_denominator"] is None
    assert observation_row["denominator_status"] == "not_provided_by_source"
    assert observation_row["source_part_number"] == 1
    variable_table = cast(dict[str, object], composition["variables"])
    variable_row = dict(
        zip(
            cast(list[str], variable_table["fields"]),
            cast(list[list[object]], variable_table["records"])[0],
            strict=True,
        )
    )
    assert variable_row["source_reported_name"] == "Triticum"
    assert variable_row["source_taxon_id"] == 50
    assert cast(dict[str, object], neotoma_tabs["classification"]) == {
        "status": "unavailable",
        "reason_code": "accepted_scientific_classification_not_available",
    }
    sead_tabs = cast(dict[str, object], details["sead:site:2"]["tabs"])
    sead_chronology = cast(dict[str, object], sead_tabs["chronology"])
    assert sead_chronology["chronology_claim_count"] == 1
    assert sead_chronology["record_count"] == 1
    assert sead_chronology["encoding"] == "sead-chronology-claim-table.v1"
    decoded_claim = _decode_sead_claim_table(sead_chronology)[0]
    assert decoded_claim["chronology_claim_id"] == "sead:site-2:dating_range:9"
    assert decoded_claim["source_record_id"] == "9"
    assert decoded_claim["source_native_record_id"] == "9"
    assert decoded_claim["site_uuid"] == "site-2"
    assert decoded_claim["source_age_type"] == "AD"
    assert decoded_claim["source_age_unit"] == "calendar_year"
    assert decoded_claim["source_age_value"] == {
        "age_type": "AD",
        "age_type_description": "Anno Domini",
        "age_type_id": 1,
        "analysis_dating_range_id": 9,
        "analysis_entity_id": 90,
        "analysis_value_id": 91,
        "dataset_id": 30,
        "dating_uncertainty_id": None,
        "high_is_uncertain": False,
        "high_qualifier": "",
        "high_value": None,
        "low_is_uncertain": False,
        "low_qualifier": "",
        "low_value": 1850,
        "physical_sample_id": 21,
        "sample_group_id": 20,
        "time_end_bp": 100,
        "time_start_bp": 100,
        "uncertainty_description": "",
        "uncertainty_label": "",
    }
    assert decoded_claim["younger_bp"] == decoded_claim["older_bp"] == 100
    assert decoded_claim["original_interval_orientation"] == "point"
    assert decoded_claim["propagation_eligibility"] == "refused"
    assert decoded_claim["propagation_reason_codes"] == [
        "observation_link_not_materialized"
    ]
    assert decoded_claim["selection_rule_version"] == (
        "sead-retain-all-source-chronologies-v1"
    )
    assert decoded_claim["provenance_record_id"] == (
        "sead-acquisition-manifest:fixture"
    )
    source_relation_path = cast(
        list[dict[str, object]], decoded_claim["source_relation_path"]
    )
    assert source_relation_path[-1] == {
        "table": "tbl_analysis_dating_ranges",
        "key": "analysis_dating_range_id",
        "value": "9",
    }
    assert decoded_claim["source_payload_sha256"] == "e" * 64
    assert decoded_claim["build_id"] == "sha256:" + "c" * 64
    assert (
        decoded_claim["acquisition_manifest_sha256"]
        == hashlib.sha256(b'{"status":"complete"}\n').hexdigest()
    )
    assert (
        cast(dict[str, object], sead_tabs["provenance"])["acquisition_release_status"]
        == "refused"
    )


def test_projection_refuses_changed_governed_surface_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.absolute()
    _neotoma_fixture(root, monkeypatch)
    _sead_fixture(root)
    path = root / "neotoma" / "relational" / "surfaces" / "sites" / "part-00001.json"
    path.write_text(path.read_text() + " ", encoding="utf-8")

    with pytest.raises(ValueError, match="surface digest changed"):
        build_map_evidence_projection(root, _projection_layers())


def test_projection_refuses_sead_claim_lineage_that_disagrees_with_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.absolute()
    _neotoma_fixture(root, monkeypatch)
    _sead_fixture(root)
    path = root / "sead" / "normalized" / "chronology_claims.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["claims"][0]["source_relation_path"][-1]["value"] = "forged"
    _write_json(path, payload)

    with pytest.raises(
        ValueError,
        match="chronology relation analysis_dating_range_id disagrees",
    ):
        build_map_evidence_projection(root, _projection_layers())


def test_discovery_keeps_nordic_sead_sites_without_bulk_temporal_duplicates(
    tmp_path: Path,
) -> None:
    root = tmp_path / "data"
    output = tmp_path / "output"
    output.mkdir()
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [10, 55]},
        "properties": {"layer_key": "fixture"},
    }
    for relative in (
        "sead/normalized/nordic_environmental_sites.geojson",
        "sead/normalized/nordic_temporal_evidence.geojson",
        "sead/derived/sweden_archaeology_site_discovery.geojson",
    ):
        _write_json(
            root / relative, {"type": "FeatureCollection", "features": [feature]}
        )

    layers, _artifacts = stage_context_point_layers(
        scope_key="nordic",
        context_root=root,
        output_dir=output,
        build_external_point_layer_fn=lambda _geojson, source_path: {
            "key": source_path.name
        },
    )

    assert [layer["key"] for layer in layers] == [
        "nordic_environmental_sites.geojson",
        "sweden_archaeology_site_discovery.geojson",
    ]


def _payload(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    marker = "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push("
    envelope = json.loads(text[text.index(marker) + len(marker) : -3])
    payload_json = (
        gzip.decompress(base64.b64decode(envelope["payload_gzip_base64"])).decode(
            "utf-8"
        )
        if envelope.get("payload_encoding") == "gzip_base64"
        else envelope["payload_json"]
    )
    return cast(dict[str, object], json.loads(payload_json))


def test_high_volume_details_are_lazy_partitioned_and_exactly_indexed(
    tmp_path: Path,
) -> None:
    details: list[JsonObject] = [
        {
            "record_id": f"site:{index:05d}",
            "tabs": {"overview": {"payload": "x" * 6000, "ordinal": index}},
        }
        for index in range(800)
    ]
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()

    first = write_static_atlas_assets(
        first_root,
        slug="evidence",
        version="fixed-point",
        point_layers=[],
        polygon_layers=[],
        detail_records=details,
    )
    second = write_static_atlas_assets(
        second_root,
        slug="evidence",
        version="fixed-point",
        point_layers=[],
        polygon_layers=[],
        detail_records=list(reversed(details)),
    )

    assert first.manifest == second.manifest
    assert [path.read_bytes() for path in first.asset_paths] == [
        path.read_bytes() for path in second.asset_paths
    ]
    asset_rows = cast(list[dict[str, object]], first.manifest["assets"])
    detail_rows = [row for row in asset_rows if row["domain"] == "details"]
    assert len(detail_rows) > 1
    assert all(row["initial_load"] is False for row in detail_rows)
    assert all(
        cast(int, row["byte_count"]) <= ATLAS_CHUNK_MAX_BYTES for row in detail_rows
    )
    max_detail_record_bytes = max(
        len(
            json.dumps(
                record,
                ensure_ascii=True,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        for record in details
    )
    assert max_detail_record_bytes <= ATLAS_CHUNK_MAX_BYTES
    paths_by_key = {
        str(row["asset_key"]): path
        for row, path in zip(asset_rows, first.asset_paths, strict=True)
    }
    index_row = next(row for row in asset_rows if row["domain"] == "indexes")
    index_payload = _payload(paths_by_key[str(index_row["asset_key"])])
    detail_index = cast(dict[str, str], index_payload["detail_record_asset_keys"])
    assert set(detail_index) == {str(row["record_id"]) for row in details}
    reconstructed = {
        str(record["record_id"]): asset_key
        for asset_key, path in paths_by_key.items()
        if asset_key.startswith("details:")
        for record in cast(list[dict[str, object]], _payload(path)["records"])
    }
    assert detail_index == reconstructed
    initial = [row for row in asset_rows if row["initial_load"] is True]
    assert all(row["domain"] != "details" for row in initial)
    assert "detail_chunk_load_failed" in MAP_DOCUMENT_TEMPLATE
    assert "detail_record_asset_keys" in MAP_DOCUMENT_TEMPLATE
