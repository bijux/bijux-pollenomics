from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.core.geojson import JsonObject
from bijux_pollenomics.collection.sources.sead.evidence.reader import (
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
)
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


def _decode_dictionary_table(table: dict[str, object]) -> list[dict[str, object]]:
    fields = cast(list[str], table["fields"])
    dictionaries = cast(dict[str, list[object]], table["column_dictionaries"])
    list_fields = set(cast(list[str], table["list_dictionary_fields"]))
    list_dictionary = cast(list[str], table["list_value_dictionary"])
    decoded: list[dict[str, object]] = []
    for encoded in cast(list[list[object]], table["records"]):
        row = dict(zip(fields, encoded, strict=True))
        for field, dictionary in dictionaries.items():
            row[field] = dictionary[cast(int, row[field])]
        for field in list_fields:
            row[field] = [
                list_dictionary[index] for index in cast(list[int], row[field])
            ]
        decoded.append(row)
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


def _write_sead_evidence_fixture(
    root: Path,
    *,
    run_id: str,
    build_id: str,
    acquisition_manifest_sha256: str,
    acquisition_bundle_sha256: str,
    country_decisions_sha256: str,
    table_payload_sha256: str,
    parent_admission_sha256: str,
    claim: dict[str, object],
    observation_entity_id: str,
) -> str:
    claim_id = cast(str, claim["chronology_claim_id"])
    dimension_relation_id = "sead-dimension-relation:fixture"
    observations: list[dict[str, object]] = [
        {
            "schema_version": "sead-source-native-observation.v1",
            "source_family": "sead",
            "observation_id": "sead-observation:zero",
            "source_table": "tbl_abundances",
            "source_record_id": "7",
            "entity_relation_id": observation_entity_id,
            "country_code": "DK",
            "source_value": 0,
            "source_value_field": "abundance",
            "source_value_state": "reported",
            "source_semantics": {
                "dataset_semantics_id": "sead-dataset:30",
                "dataset_semantics_status": "source_native_linked",
                "source_unit_id": None,
                "unit_status": "not_exposed_by_relation",
                "value_semantics_id": None,
            },
            "taxon_relation_id": "sead-taxon:5",
            "taxon_status": "source_native_linked",
            "dimension_relation_ids": [dimension_relation_id],
            "dimension_status": "source_native_linked",
            "chronology_link": {
                "entity_relation_id": "sead-analysis-entity:90",
                "status": "direct_analysis_entity_eligible_claim",
                "claim_count": 1,
                "eligible_claim_count": 1,
                "selection_rule": "same_analysis_entity_only",
            },
            "event_eligibility": "refused",
            "event_refusal_reason_codes": [
                "source_classification_not_accepted",
                "source_unit_unavailable",
            ],
            "source_payload_sha256": "1" * 64,
            "acquisition_manifest_sha256": acquisition_manifest_sha256,
            "build_id": build_id,
        },
        {
            "schema_version": "sead-source-native-observation.v1",
            "source_family": "sead",
            "observation_id": "sead-observation:null",
            "source_table": "tbl_analysis_values",
            "source_record_id": "8",
            "entity_relation_id": "sead-analysis-entity:90",
            "country_code": "DK",
            "source_value": None,
            "source_value_field": "analysis_value",
            "source_value_state": "source_null",
            "source_semantics": {
                "dataset_semantics_id": "sead-dataset:30",
                "dataset_semantics_status": "source_native_linked",
                "source_unit_id": 8,
                "unit_status": "source_native_linked",
                "value_semantics_id": "sead-value-class:12",
            },
            "taxon_relation_id": None,
            "taxon_status": "not_exposed_for_observation_type",
            "dimension_relation_ids": [dimension_relation_id],
            "dimension_status": "source_native_linked",
            "chronology_link": {
                "entity_relation_id": "sead-analysis-entity:90",
                "status": "direct_analysis_entity_eligible_claim",
                "claim_count": 1,
                "eligible_claim_count": 1,
                "selection_rule": "same_analysis_entity_only",
            },
            "event_eligibility": "refused",
            "event_refusal_reason_codes": ["source_classification_not_accepted"],
            "source_payload_sha256": "2" * 64,
            "acquisition_manifest_sha256": acquisition_manifest_sha256,
            "build_id": build_id,
        },
    ]
    entity_relations = [
        {
            "entity_relation_id": "sead-analysis-entity:90",
            "analysis_entity_id": 90,
            "physical_sample_id": 21,
            "sample_group_id": 20,
            "dataset_id": 30,
            "site_id": 2,
            "site_uuid": "site-2",
            "country_code": "DK",
            "latitude_dd": 55.0,
            "longitude_dd": 10.0,
            "chronology_link": {
                "selection_rule": "same_analysis_entity_only",
                "claim_ids": [claim_id],
                "eligible_claim_ids": [claim_id],
            },
        }
    ]
    taxon_relations = [
        {
            "taxon_relation_id": "sead-taxon:5",
            "taxon_id": 5,
            "taxon": {"taxon_id": 5, "species": "aestivum"},
            "genus": {"genus_name": "Triticum"},
            "family": {"family_name": "Poaceae"},
            "order": {"order_name": "Poales"},
            "author": {"author_name": "L."},
            "source_ecocodes": [
                {
                    "ecocode_definition_id": 10,
                    "abbreviation": "CR",
                    "name": "cultivated resource",
                }
            ],
            "derived_classification_status": "not_accepted",
        }
    ]
    dimension_relations = [
        {
            "dimension_relation_id": dimension_relation_id,
            "dimension_semantics_id": "sead-dimension:2",
            "dimension_status": "source_native_linked",
            "owner_id": 21,
            "owner_kind": "physical_sample",
            "source_record_id": "3",
            "source_table": "tbl_sample_dimensions",
            "source_row": {"dimension_value": 0.0, "qualifier_id": None},
            "unit_status": "source_native_linked",
        }
    ]
    dimension_semantics = [
        {
            "dimension_semantics_id": "sead-dimension:2",
            "dimension_id": 2,
            "source_dimension": {
                "dimension_name": "Lower boundary depth",
                "dimension_abbrev": None,
                "dimension_description": "Depth from source reference",
            },
            "source_unit_id": 1,
            "source_unit": {
                "unit_id": 1,
                "unit_name": "metres",
                "unit_abbrev": "m",
                "description": "Distance measure SI unit",
            },
            "unit_status": "source_native_linked",
        }
    ]
    dataset_semantics = [
        {
            "dataset_semantics_id": "sead-dataset:30",
            "dataset": {
                "dataset_id": 30,
                "dataset_uuid": "dataset-30",
                "dataset_name": "Fixture dataset",
                "data_type_id": 8,
            },
            "source_data_type": {
                "data_type_id": 8,
                "data_type_name": "Continuous",
            },
            "source_data_type_group": {"data_type_group_name": "Continuous"},
        }
    ]
    value_semantics = [
        {
            "value_semantics_id": "sead-value-class:12",
            "value_class": {
                "value_class_id": 12,
                "name": "Inferred year",
                "description": "Source-native inferred year",
            },
            "source_value_type": {
                "value_type_id": 6,
                "name": "Year",
                "base_type": "integer",
            },
            "source_unit": {
                "unit_id": 8,
                "unit_name": "Years",
                "unit_abbrev": "yrs",
                "description": "Calendar years",
            },
        }
    ]
    refusals = [
        {
            "observation_id": cast(str, observation["observation_id"]),
            "status": "refused",
            "eligible_chronology_claim_count": 1,
            "reason_codes": observation["event_refusal_reason_codes"],
        }
        for observation in observations
    ]
    documents: dict[str, dict[str, object]] = {
        "chronology_claims.json": {
            "schema_version": "sead-chronology-claim-bundle.v1",
            "source_family": "sead",
            "source_run_id": run_id,
            "source_build_id": build_id,
            "acquisition_manifest_sha256": acquisition_manifest_sha256,
            "acquisition_bundle_sha256": acquisition_bundle_sha256,
            "country_decisions_sha256": country_decisions_sha256,
            "table_payload_sha256": {"tbl_sites": table_payload_sha256},
            "claim_count": 1,
            "country_counts": {"DK": 1},
            "claims": [claim],
            "propagation_status": "refused",
            "propagation_reason_code": "source_classification_not_accepted",
        },
        "source_native_observations.json": {
            "schema_version": "sead-source-native-evidence-bundle.v1",
            "source_family": "sead",
            "source_run_id": run_id,
            "build_id": build_id,
            "acquisition_manifest_sha256": acquisition_manifest_sha256,
            "observation_count": len(observations),
            "country_counts": {"DK": 2},
            "observation_table_counts": {
                "tbl_abundances": 1,
                "tbl_analysis_values": 1,
            },
            "observations": observations,
        },
        "observation_relation_index.json": {
            "schema_version": "sead-evidence-relation-index.v1",
            "source_family": "sead",
            "source_run_id": run_id,
            "build_id": build_id,
            "acquisition_manifest_sha256": acquisition_manifest_sha256,
            "entity_relation_count": len(entity_relations),
            "taxon_relation_count": len(taxon_relations),
            "dimension_relation_count": len(dimension_relations),
            "dimension_semantic_count": len(dimension_semantics),
            "dataset_semantic_count": len(dataset_semantics),
            "value_semantic_count": len(value_semantics),
            "entity_relations": entity_relations,
            "taxon_relations": taxon_relations,
            "dimension_relations": dimension_relations,
            "dimension_semantics": dimension_semantics,
            "dataset_semantics": dataset_semantics,
            "value_semantics": value_semantics,
        },
        "evidence_events.json": {
            "schema_version": "sead-evidence-event-bundle.v1",
            "source_family": "sead",
            "source_run_id": run_id,
            "build_id": build_id,
            "acquisition_manifest_sha256": acquisition_manifest_sha256,
            "observation_denominator": len(observations),
            "eligible_event_count": 0,
            "refused_event_count": len(refusals),
            "country_observation_counts": {"DK": 2},
            "country_eligible_event_counts": {"DK": 0},
            "refusal_reason_counts": {
                "source_classification_not_accepted": 2,
                "source_unit_unavailable": 1,
            },
            "events": [],
            "refusals": refusals,
        },
    }
    evidence_root = root / "sead" / "normalized" / "acquisitions" / run_id
    file_records: dict[str, dict[str, object]] = {}
    multipart_documents: dict[str, dict[str, object]] = {}
    for document_name, document in documents.items():
        partitioned_fields = [
            field
            for field in (
                "claims",
                "observations",
                "entity_relations",
                "taxon_relations",
                "dimension_relations",
                "dimension_semantics",
                "dataset_semantics",
                "value_semantics",
                "refusals",
            )
            if field in document
        ]
        part_paths: list[str] = []
        partition_index: dict[str, object] = {}
        for field in sorted(partitioned_fields):
            rows = cast(list[object], document.pop(field))
            part_path = f"{document_name.removesuffix('.json')}/{field}-00001.json"
            part_payload = _write_json(
                evidence_root / part_path,
                {
                    "schema_version": "sead-evidence-multipart.v1",
                    "logical_document": document_name,
                    "field": field,
                    "part_number": 1,
                    "row_start": 0,
                    "row_end": len(rows),
                    field: rows,
                },
            )
            part_record = {
                "path": part_path,
                "byte_count": len(part_payload),
                "sha256": hashlib.sha256(part_payload).hexdigest(),
                "part_number": 1,
                "row_start": 0,
                "row_end": len(rows),
                "row_count": len(rows),
            }
            partition_index[field] = {
                "part_count": 1,
                "row_count": len(rows),
                "parts": [part_record],
            }
            file_records[part_path] = {
                key: part_record[key] for key in ("path", "byte_count", "sha256")
            }
            part_paths.append(part_path)
        document["partitioned_fields"] = partition_index
        payload = _write_json(evidence_root / document_name, document)
        file_records[document_name] = {
            "path": document_name,
            "byte_count": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
        multipart_documents[document_name] = {
            "part_count": len(part_paths),
            "partitioned_fields": sorted(partitioned_fields),
            "parts": sorted(part_paths),
        }
    digest_rows = [
        f"{path}:{row['sha256']}:{row['byte_count']}"
        for path, row in sorted(file_records.items())
    ]
    file_set_sha256 = hashlib.sha256(
        (json.dumps(digest_rows, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()
    manifest_payload = _write_json(
        evidence_root / "evidence_materialization_manifest.json",
        {
            "schema_version": "sead-evidence-materialization-manifest.v1",
            "source_family": "sead",
            "source_run_id": run_id,
            "build_id": build_id,
            "acquisition_manifest_sha256": acquisition_manifest_sha256,
            "acquisition_bundle_sha256": acquisition_bundle_sha256,
            "file_set_sha256": file_set_sha256,
            "parent_admission_sha256": parent_admission_sha256,
            "chronology_claim_count": 1,
            "observation_count": len(observations),
            "eligible_event_count": 0,
            "refused_event_count": len(refusals),
            "maximum_file_byte_count": 50 * 1024 * 1024,
            "files": [file_records[path] for path in sorted(file_records)],
            "multipart_documents": multipart_documents,
        },
    )
    return hashlib.sha256(manifest_payload).hexdigest()


def _sead_fixture(
    root: Path, *, observation_entity_id: str = "sead-analysis-entity:90"
) -> tuple[str, str]:
    run_id = SEAD_GOVERNED_EVIDENCE_RUN_ID
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
    admission_payload = _write_json(
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
        "propagation_reason_codes": ["source_classification_not_accepted"],
        "publication_role": "chronology_display_only",
        "reason_codes": [],
        "transformation_id": "sead-calendar-year-to-cal-bp-1950-v1",
        "original_interval_orientation": "point",
        "selection_status": "retained_unselected",
        "selection_rule_version": "sead-retain-all-source-chronologies-v1",
        "observation_link_status": "linked_at_analysis_entity",
        "observation_relation_id": "sead-analysis-entity:90",
        "linked_source_native_observation_count": 2,
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
    evidence_manifest_sha256 = _write_sead_evidence_fixture(
        root,
        run_id=run_id,
        build_id=build_id,
        acquisition_manifest_sha256=acquisition_manifest_sha256,
        acquisition_bundle_sha256=acquisition_bundle_sha256,
        country_decisions_sha256=country_decisions_sha256,
        table_payload_sha256=hashlib.sha256(site_payload).hexdigest(),
        parent_admission_sha256=hashlib.sha256(admission_payload).hexdigest(),
        claim=claim,
        observation_entity_id=observation_entity_id,
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
    return evidence_manifest_sha256, hashlib.sha256(admission_payload).hexdigest()


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


def _install_sead_fixture(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    observation_entity_id: str = "sead-analysis-entity:90",
) -> None:
    manifest_sha256, admission_sha256 = _sead_fixture(
        root, observation_entity_id=observation_entity_id
    )
    monkeypatch.setattr(
        evidence_projection,
        "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
        manifest_sha256,
    )
    monkeypatch.setattr(
        evidence_projection,
        "SEAD_GOVERNED_ADMISSION_SHA256",
        admission_sha256,
    )


def test_projection_is_fixed_point_lossless_and_four_country_reconciled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.absolute()
    _neotoma_fixture(root, monkeypatch)
    _install_sead_fixture(root, monkeypatch)
    first_layers = _projection_layers()
    second_layers = _projection_layers()

    first = build_map_evidence_projection(root, first_layers)
    second = build_map_evidence_projection(root, second_layers)

    assert first == second
    assert first_layers == second_layers
    assert first.reconciliation["schema_version"] == "atlas-evidence-projection.v2"
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
    assert sead["source_claim_denominator"] == 1
    assert sead["source_observation_denominator"] == 2
    assert sead["source_taxon_relation_denominator"] == 1
    assert sead["source_dimension_relation_denominator"] == 1
    assert sead["source_event_refusal_denominator"] == 2
    assert sead["projected_site_observation_count"] == 2
    assert sead["projected_unique_taxon_relation_count"] == 1
    assert sead["projected_dimension_relation_count"] == 1
    assert sead["unprojected_dimension_relation_count"] == 0
    assert sead["eligible_event_count"] == 0
    assert sead["claim_country_counts"] == {"DK": 1}
    assert sead["observation_country_counts"] == {"DK": 2}
    assert sead["eligible_event_country_counts"] == {"DK": 0}
    assert sead["propagation_status"] == "refused"
    assert sead["propagation_reason_code"] == "source_classification_not_accepted"
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
        "source_classification_not_accepted"
    ]
    assert decoded_claim["observation_link_status"] == "linked_at_analysis_entity"
    assert decoded_claim["observation_relation_id"] == "sead-analysis-entity:90"
    assert decoded_claim["linked_source_native_observation_count"] == 2
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
    sead_composition = cast(dict[str, object], sead_tabs["pollen_composition"])
    assert sead_composition["record_count"] == 2
    assert sead_composition["encoding"] == "sead-source-native-observation-table.v1"
    observation_rows = _decode_dictionary_table(sead_composition)
    values_by_id = {
        cast(str, row["observation_id"]): (
            row["source_value"],
            row["source_value_state"],
        )
        for row in observation_rows
    }
    assert values_by_id == {
        "sead-observation:null": (None, "source_null"),
        "sead-observation:zero": (0, "reported"),
    }
    zero = next(
        row
        for row in observation_rows
        if row["observation_id"] == "sead-observation:zero"
    )
    assert zero["analysis_entity_id"] == 90
    assert zero["physical_sample_id"] == 21
    assert zero["sample_group_id"] == 20
    assert zero["dataset_id"] == 30
    assert zero["taxon_relation_id"] == "sead-taxon:5"
    assert zero["dimension_relation_ids"] == ["sead-dimension-relation:fixture"]
    assert "source_classification_not_accepted" in cast(
        list[str], zero["event_refusal_reason_codes"]
    )
    taxa = cast(dict[str, object], sead_composition["taxa"])
    taxon_row = dict(
        zip(
            cast(list[str], taxa["fields"]),
            cast(list[list[object]], taxa["records"])[0],
            strict=True,
        )
    )
    assert taxon_row["genus_name"] == "Triticum"
    assert taxon_row["source_ecocodes"] == [
        {
            "ecocode_definition_id": 10,
            "abbreviation": "CR",
            "name": "cultivated resource",
        }
    ]
    dimensions = cast(dict[str, object], sead_composition["dimensions"])
    dimension_row = dict(
        zip(
            cast(list[str], dimensions["fields"]),
            cast(list[list[object]], dimensions["records"])[0],
            strict=True,
        )
    )
    assert dimension_row["dimension_value"] == 0.0
    value_semantics = cast(dict[str, object], sead_composition["value_semantics"])
    assert value_semantics["record_count"] == 1
    relation = cast(dict[str, object], sead_tabs["relation"])
    assert relation["status"] == "refused"
    assert relation["reason_code"] == "source_classification_not_accepted"
    assert relation["eligible_event_count"] == 0
    assert relation["refused_observation_count"] == 2
    provenance = cast(dict[str, object], sead_tabs["provenance"])
    assert provenance["evidence_bundle_path"] == (
        "data/sead/normalized/acquisitions/" + SEAD_GOVERNED_EVIDENCE_RUN_ID
    )
    assert len(cast(str, provenance["evidence_file_set_sha256"])) == 64


def test_projection_refuses_changed_governed_surface_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.absolute()
    _neotoma_fixture(root, monkeypatch)
    _install_sead_fixture(root, monkeypatch)
    path = root / "neotoma" / "relational" / "surfaces" / "sites" / "part-00001.json"
    path.write_text(path.read_text() + " ", encoding="utf-8")

    with pytest.raises(ValueError, match="surface digest changed"):
        build_map_evidence_projection(root, _projection_layers())


def test_projection_refuses_tampered_sead_multipart_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.absolute()
    _neotoma_fixture(root, monkeypatch)
    _install_sead_fixture(root, monkeypatch)
    path = (
        root
        / "sead"
        / "normalized"
        / "acquisitions"
        / SEAD_GOVERNED_EVIDENCE_RUN_ID
        / "chronology_claims"
        / "claims-00001.json"
    )
    path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")

    with pytest.raises(ValueError, match="evidence (byte count|digest) changed"):
        build_map_evidence_projection(root, _projection_layers())


def test_projection_refuses_self_consistent_evidence_with_unknown_entity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.absolute()
    _neotoma_fixture(root, monkeypatch)
    _install_sead_fixture(
        root,
        monkeypatch,
        observation_entity_id="sead-analysis-entity:forged",
    )

    with pytest.raises(ValueError, match="unknown entity relation"):
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
