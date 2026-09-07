"""SEAD atlas projection fixtures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

from bijux_pollenomics.collection.sources.sead.evidence.source_keys.contract import (
    SOURCE_KEY_LEDGER_SCHEMA_VERSION,
    SOURCE_KEY_RANGE_ENCODING,
    SOURCE_KEY_TABLE_CONTRACT_SCHEMA_VERSION,
    source_key_table_contract_rows,
    source_key_table_contract_sha256,
)
from bijux_pollenomics.collection.sources.sead.evidence.source_keys.ranges import (
    positive_integer_key_set_sha256,
    positive_integer_ranges_sha256,
)
from bijux_pollenomics.collection.sources.sead.evidence.source_keys.serialization import (
    canonical_bytes,
    canonical_sha256,
)
from bijux_pollenomics.collection.sources.sead.evidence.source_keys.validation import (
    validate_sead_source_key_ledger,
)


def _source_key_ledger_fixture(
    *,
    run_id: str,
    build_id: str,
    acquisition_manifest_sha256: str,
    acquisition_bundle_sha256: str,
    country_decisions_sha256: str,
    parent_admission_sha256: str,
) -> dict[str, object]:
    """Build a small, complete ledger for a projection-only materialization."""
    contract_rows = source_key_table_contract_rows()
    table_rows: list[dict[str, object]] = []
    payload_inventory: list[dict[str, object]] = []
    receipt_inventory: list[dict[str, object]] = []
    key_inventory: list[dict[str, object]] = []
    empty_key_sha256 = positive_integer_key_set_sha256([])
    empty_ranges_sha256 = positive_integer_ranges_sha256([])

    for contract_row in contract_rows:
        table = cast(str, contract_row["table"])
        primary_key = cast(str, contract_row["primary_key"])
        payload_bytes = canonical_bytes({"rows": [], "table": table})
        payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
        receipt_bytes = canonical_bytes(
            {
                "content_sha256": payload_sha256,
                "receipt_id": f"sead-fixture-receipt:{table}",
                "row_count": 0,
                "status": "complete",
                "table": table,
            }
        )
        receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()
        payload_identity = {
            "path": f"payloads/{table}.json",
            "byte_count": len(payload_bytes),
            "sha256": payload_sha256,
        }
        receipt_identity = {
            "path": f"receipts/{table}.json",
            "byte_count": len(receipt_bytes),
            "sha256": receipt_sha256,
            "receipt_id": f"sead-fixture-receipt:{table}",
            "status": "complete",
            "row_count": 0,
            "content_sha256": payload_sha256,
        }
        table_row: dict[str, object] = {
            **contract_row,
            "row_count": 0,
            "distinct_primary_key_count": 0,
            "duplicate_primary_key_count": 0,
            "minimum_primary_key": None,
            "maximum_primary_key": None,
            "key_encoding": SOURCE_KEY_RANGE_ENCODING,
            "key_ranges": [],
            "key_range_count": 0,
            "key_set_sha256": empty_key_sha256,
            "key_ranges_sha256": empty_ranges_sha256,
            "payload": payload_identity,
            "receipt": receipt_identity,
        }
        table_row["table_record_sha256"] = canonical_sha256(table_row)
        table_rows.append(table_row)
        payload_inventory.append(
            {
                "table": table,
                "byte_count": len(payload_bytes),
                "sha256": payload_sha256,
            }
        )
        receipt_inventory.append(
            {
                "table": table,
                "byte_count": len(receipt_bytes),
                "sha256": receipt_sha256,
            }
        )
        key_inventory.append(
            {
                "table": table,
                "primary_key": primary_key,
                "row_count": 0,
                "key_set_sha256": empty_key_sha256,
            }
        )

    site_country_bindings: dict[str, object] = {
        "fields": [
            "site_id",
            "site_uuid",
            "country_code_index",
            "assignment_method_index",
        ],
        "country_codes": ["DK", "FI", "NO", "SE"],
        "assignment_methods": ["fixture_projection_only"],
        "rows": [],
    }
    ledger: dict[str, object] = {
        "schema_version": SOURCE_KEY_LEDGER_SCHEMA_VERSION,
        "source_family": "sead",
        "source_run_id": run_id,
        "scope_id": "sha256:"
        + hashlib.sha256(f"sead-fixture-scope:{run_id}".encode()).hexdigest(),
        "build_id": build_id,
        "acquisition_manifest_sha256": acquisition_manifest_sha256,
        "acquisition_bundle_sha256": acquisition_bundle_sha256,
        "parent_admission_sha256": parent_admission_sha256,
        "country_decisions_sha256": country_decisions_sha256,
        "table_contract_schema_version": SOURCE_KEY_TABLE_CONTRACT_SCHEMA_VERSION,
        "table_contract_sha256": source_key_table_contract_sha256(contract_rows),
        "table_count": len(table_rows),
        "source_row_count": 0,
        "distinct_primary_key_count": 0,
        "key_range_count": 0,
        "empty_table_count": len(table_rows),
        "payload_set_sha256": canonical_sha256(payload_inventory),
        "receipt_set_sha256": canonical_sha256(receipt_inventory),
        "source_key_set_sha256": canonical_sha256(key_inventory),
        "site_identity_sha256": canonical_sha256([]),
        "site_country_binding_sha256": canonical_sha256(site_country_bindings),
        "site_country_bindings": site_country_bindings,
        "country_binding_accountability": {
            "country_decisions_sha256": country_decisions_sha256,
            "bbox_site_count": 0,
            "assigned_site_count": 0,
            "review_site_count": 0,
            "unassigned_site_count": 0,
            "excluded_site_count": 0,
            "country_counts": {"DK": 0, "FI": 0, "NO": 0, "SE": 0},
            "decision_status_counts": {"assigned": 0},
        },
        "tables": table_rows,
    }
    return validate_sead_source_key_ledger(ledger)


def _write_json(path: Path, value: object) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path.write_bytes(payload)
    return payload


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
        "source_key_ledger.json": _source_key_ledger_fixture(
            run_id=run_id,
            build_id=build_id,
            acquisition_manifest_sha256=acquisition_manifest_sha256,
            acquisition_bundle_sha256=acquisition_bundle_sha256,
            country_decisions_sha256=country_decisions_sha256,
            parent_admission_sha256=parent_admission_sha256,
        ),
    }
    evidence_root = root / "sead" / "normalized" / "acquisitions" / run_id
    file_records: dict[str, dict[str, object]] = {}
    multipart_documents: dict[str, dict[str, object]] = {}
    for document_name, document in documents.items():
        if document_name == "source_key_ledger.json":
            payload = _write_json(evidence_root / document_name, document)
            file_records[document_name] = {
                "path": document_name,
                "byte_count": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            continue
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
