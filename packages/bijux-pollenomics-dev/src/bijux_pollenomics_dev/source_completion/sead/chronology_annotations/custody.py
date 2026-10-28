"""Bind physical and reference owners while retaining native annotation differences."""

from __future__ import annotations

import copy
import hashlib
from typing import Any

from .comparison import canonical, compare_field, same
from .source import SOURCES


def lookup(
    tables: dict[str, dict[int, dict[str, Any]]],
    table: str,
    value: object,
    *,
    nullable: bool = False,
) -> dict[str, Any] | None:
    """Resolve a typed native parent while preserving allowed nulls."""
    if value is None and nullable:
        return None
    if type(value) is not int or value not in tables[table]:
        raise ValueError("Missing or invalid native parent: " + table)
    return tables[table][value]


def reference_links(
    tables: dict[str, dict[int, dict[str, Any]]],
) -> dict[str, dict[int, list[int | None]]]:
    """Preserve separately declared native reference roles without merging ownership."""
    result: dict[str, dict[int, list[int | None]]] = {}
    for table, parent in [
        ("tbl_site_references", "site_id"),
        ("tbl_sample_group_references", "sample_group_id"),
        ("tbl_relative_age_refs", "relative_age_id"),
    ]:
        grouped: dict[int, list[int | None]] = {}
        for row in tables[table].values():
            value = row[parent]
            if type(value) is not int:
                raise ValueError("Invalid reference parent identifier")
            biblio = row["biblio_id"]
            lookup(tables, "tbl_biblio", biblio, nullable=True)
            grouped.setdefault(value, []).append(biblio)
        result[table] = grouped
    return result


def audit_claim(
    claim: dict[str, Any],
    tables: dict[str, dict[int, dict[str, Any]]],
    references: dict[str, dict[int, list[int | None]]] | None = None,
) -> dict[str, Any]:
    """Bind every native age field and its physical, method and bibliography owners."""
    kind = claim.get("claim_type")
    if not isinstance(kind, str) or kind not in SOURCES:
        raise ValueError("Unknown native chronology kind")
    table, key = SOURCES[kind]
    identifier = claim.get("source_record_id")
    if (
        not isinstance(identifier, str)
        or not identifier.isdecimal()
        or str(int(identifier)) != identifier
    ):
        raise ValueError("Noncanonical source record identifier")
    native = lookup(tables, table, int(identifier))
    assert native is not None
    if (
        claim.get("source_table") != table
        or claim.get("source_native_record_id") != identifier
    ):
        raise ValueError("Source table or native identifier differs")
    source = claim.get("source_age_value")
    if not isinstance(source, dict):
        raise ValueError("Native source age object absent")
    comparisons = [
        compare_field(field, value, source) for field, value in native.items()
    ]
    if kind == "dating_range":
        value_row = lookup(tables, "tbl_analysis_values", native["analysis_value_id"])
        assert value_row is not None
        entity_id = value_row["analysis_entity_id"]
        same(
            claim.get("analysis_value_id"),
            native["analysis_value_id"],
            "analysis_value_id",
        )
    else:
        entity_id = native["analysis_entity_id"]
    entity = lookup(tables, "tbl_analysis_entities", entity_id)
    assert entity is not None
    physical = lookup(tables, "tbl_physical_samples", entity["physical_sample_id"])
    assert physical is not None
    group = lookup(tables, "tbl_sample_groups", physical["sample_group_id"])
    assert group is not None
    site = lookup(tables, "tbl_sites", group["site_id"])
    dataset = lookup(tables, "tbl_datasets", entity["dataset_id"])
    assert site is not None and dataset is not None
    if (
        claim.get("chronology_claim_id")
        != f"sead:{site['site_uuid']}:{kind}:{identifier}"
    ):
        raise ValueError("Native composite chronology identity differs")
    expected = {
        "analysis_entity_id": entity_id,
        "physical_sample_id": entity["physical_sample_id"],
        "sample_group_id": physical["sample_group_id"],
        "dataset_id": entity["dataset_id"],
        "site_uuid": site["site_uuid"],
        "source_site_id": str(group["site_id"]),
    }
    for field, value in expected.items():
        same(claim.get(field), value, field)
        if field in {
            "analysis_entity_id",
            "physical_sample_id",
            "sample_group_id",
            "dataset_id",
        }:
            if field not in source:
                raise ValueError("Enriched native ownership field omitted: " + field)
            same(source[field], value, "source_age_value/" + field)
    if "site_id" in source:
        same(source["site_id"], group["site_id"], "source_age_value/site_id")
    path = [
        ("tbl_sites", "site_id", group["site_id"]),
        ("tbl_sample_groups", "sample_group_id", physical["sample_group_id"]),
        ("tbl_physical_samples", "physical_sample_id", entity["physical_sample_id"]),
        ("tbl_analysis_entities", "analysis_entity_id", entity_id),
        ("tbl_datasets", "dataset_id", entity["dataset_id"]),
    ]
    if kind == "dating_range":
        path.append(
            ("tbl_analysis_values", "analysis_value_id", native["analysis_value_id"])
        )
    path.append((table, key, native[key]))
    # Native relative-date identifiers are retained as source strings in the path.
    actual_path = claim.get("source_relation_path")
    if not isinstance(actual_path, list) or len(actual_path) != len(path):
        raise ValueError("Native chronology relation path differs")
    for actual, (name, field, value) in zip(actual_path, path, strict=True):
        if (
            actual.get("table") != name
            or actual.get("key") != field
            or str(actual.get("value")) != str(value)
            or type(actual.get("value")) is bool
        ):
            raise ValueError("Native chronology relation path differs")
    uncertainty_id = native.get("dating_uncertainty_id")
    uncertainty = lookup(
        tables, "tbl_dating_uncertainty", uncertainty_id, nullable=True
    )
    lookup_comparisons: list[dict[str, Any]] = []
    if "dating_uncertainty_id" in native:
        lookup_comparisons.extend(
            compare_field(field, value, source)
            for field, value in [
                (
                    "uncertainty_label",
                    uncertainty["uncertainty"] if uncertainty is not None else None,
                ),
                (
                    "uncertainty_description",
                    uncertainty["description"] if uncertainty is not None else None,
                ),
            ]
        )
    method_id = dataset.get("method_id")
    method = lookup(tables, "tbl_methods", method_id, nullable=True)
    bibliography_id = dataset.get("biblio_id")
    bibliography = lookup(tables, "tbl_biblio", bibliography_id, nullable=True)
    direct_method_id = native.get("method_id")
    direct_method = lookup(tables, "tbl_methods", direct_method_id, nullable=True)
    if "method_id" in native:
        lookup_comparisons.append(
            compare_field(
                "method_name",
                direct_method["method_name"] if direct_method is not None else None,
                source,
            )
        )
    if (
        claim.get("propagation_eligibility") != "refused"
        or claim.get("selection_status") != "retained_unselected"
    ):
        raise ValueError("Native annotation audit cannot admit selected events")
    expected_calibration = {
        "dating_range": "not_applicable",
        "dendrochronology": "not_applicable",
        "relative_period": "not_calibrated",
        "geochronology": "unknown",
        "analysis_entity_age": "unknown",
    }[kind]
    if claim.get("calibration_status") != expected_calibration:
        raise ValueError("Native calibration posture absent or promoted")
    if references is None:
        references = reference_links(tables)
    reference_ids = {
        "dataset": [bibliography_id] if bibliography is not None else [],
        "site": references["tbl_site_references"].get(group["site_id"], []),
        "sample_group": references["tbl_sample_group_references"].get(
            physical["sample_group_id"], []
        ),
        "relative_age": references["tbl_relative_age_refs"].get(
            native.get("relative_age_id", -1), []
        )
        if kind == "relative_period"
        else [],
    }
    representations = [
        {
            "field": "source_record_id",
            "raw_type": "integer",
            "stored_type": "string",
            "rule": "canonical decimal identifier",
            "mathematical_identifier_equal": True,
        }
    ]
    for actual, (_name, _field, value) in zip(actual_path, path, strict=True):
        if type(actual["value"]) is not type(value):
            representations.append(
                {
                    "field": "source_relation_path/" + actual["table"],
                    "raw_type": "integer",
                    "stored_type": "string",
                    "rule": "canonical decimal identifier",
                    "mathematical_identifier_equal": True,
                }
            )
    return {
        "raw_annotations": copy.deepcopy(native),
        "stored_native_annotation_fields": {
            field: copy.deepcopy(source[field]) for field in native if field in source
        },
        "field_comparisons": comparisons,
        "lookup_comparisons": lookup_comparisons,
        "raw_uncertainty_definition_sha256": hashlib.sha256(
            canonical(uncertainty)
        ).hexdigest()
        if uncertainty is not None
        else None,
        "raw_dataset_method_definition_sha256": hashlib.sha256(
            canonical(method)
        ).hexdigest()
        if method is not None
        else None,
        "raw_direct_method_definition_sha256": hashlib.sha256(
            canonical(direct_method)
        ).hexdigest()
        if direct_method is not None
        else None,
        "identifier_representations": representations,
        "all_stored_native_fields_exact": all(
            row["category"] == "exact" for row in comparisons
        ),
        "scientific_normalization_approved": False,
        "source_table": table,
        "source_record_id": identifier,
        "source_age_type": claim.get("source_age_type"),
        "source_age_unit": claim.get("source_age_unit"),
        "chronology_eligibility": claim.get("chronology_eligibility"),
        "publication_role": claim.get("publication_role"),
        "reference_ids": reference_ids,
        "chronology_claim_id": claim["chronology_claim_id"],
        "claim_type": kind,
        "native_field_count": len(native),
        "native_null_fields": sum(v is None for v in native.values()),
        "uncertainty_id": uncertainty_id,
        "uncertainty_label": uncertainty["uncertainty"]
        if uncertainty is not None
        else None,
        "dataset_method_id": method_id,
        "dataset_method_name": method["method_name"] if method is not None else None,
        "dataset_biblio_id": bibliography_id,
        "bibliography_status": "linked" if bibliography is not None else "source_null",
        "direct_method_id": direct_method_id,
        "source_chronology_id": native.get("chronology_id"),
        "calibration_status": claim["calibration_status"],
        "eligible_event": False,
    }
