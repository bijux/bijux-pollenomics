"""SEAD atlas projection fixtures."""

from __future__ import annotations

from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import cast
import pytest
from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
)
from bijux_pollenomics.reporting.map_document.evidence_projection import (
    sead as sead_projection,
)
from .common import _write_json


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
        sead_projection,
        "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
        manifest_sha256,
    )
    monkeypatch.setattr(
        sead_projection,
        "SEAD_GOVERNED_ADMISSION_SHA256",
        admission_sha256,
    )
