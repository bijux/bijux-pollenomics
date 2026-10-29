"""Lossless categorical component rows on the existing SEAD source relations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import csv
import io
import json
from typing import Any

from bijux_pollenomics.collection.sources.sead.evidence.source_keys.identities import (
    canonical_site_uuid,
)

PARSER_RULE = "source-native-category-identity-and-nullable-fields-v1"
CSV_FIELDS = (
    "analysis_categorical_value_id",
    "component_id",
    "analysis_value_id",
    "observation_id",
    "site_id",
    "site_uuid",
    "country_code",
    "sample_group_id",
    "physical_sample_id",
    "analysis_entity_id",
    "dataset_id",
    "value_class_id",
    "value_class_name",
    "value_type_id",
    "value_type_name",
    "value_type_base_type",
    "value_type_unit_id",
    "value_type_item_id",
    "item_name_json",
    "item_key_parse_state",
    "typed_value_json",
    "typed_value_state",
    "typed_value_parse_state",
    "is_variant_json",
    "is_variant_state",
    "parent_value_json",
    "parent_value_state",
    "parent_parse_state",
    "parent_display_vs_item_name",
    "source_unit_id",
    "unit_status",
    "chronology_link_status",
    "eligible_claim_count",
    "event_eligibility",
    "event_refusal_reason_codes_json",
)


def field_value(row: Mapping[str, Any], key: str) -> tuple[str, str]:
    """Retain JSON null and an absent field as different source states."""
    if key not in row:
        return "", "missing"
    return (
        json.dumps(row[key], ensure_ascii=False, allow_nan=False),
        "source_null" if row[key] is None else "reported",
    )


def project_row(
    component: Mapping[str, Any],
    parent: Mapping[str, Any],
    observation: Mapping[str, Any],
    entity: Mapping[str, Any],
    site: Mapping[str, Any],
    item: Mapping[str, Any],
    value_class: Mapping[str, Any],
    value_type: Mapping[str, Any],
) -> dict[str, Any]:
    """Expose native identity without translating an item into an observed value.

    The linked item is parsed only as an exact native foreign-key relation.
    Neither its name nor the free parent display supplies a missing component
    value. Reported component values have no additional interpretation rule.
    Missing source files and broken relations refuse the source consumer; they
    never become fabricated null-valued rows or ecological exclusions.
    """
    keys = (
        (component, "analysis_categorical_value_id"),
        (component, "analysis_value_id"),
        (component, "value_type_item_id"),
        (parent, "analysis_value_id"),
        (parent, "analysis_entity_id"),
        (parent, "value_class_id"),
        (entity, "site_id"),
        (entity, "sample_group_id"),
        (entity, "physical_sample_id"),
        (entity, "analysis_entity_id"),
        (entity, "dataset_id"),
        (site, "site_id"),
        (item, "value_type_item_id"),
        (item, "value_type_id"),
        (value_class, "value_class_id"),
        (value_class, "value_type_id"),
        (value_type, "value_type_id"),
    )
    if any(type(row.get(key)) is not int or row[key] <= 0 for row, key in keys):
        raise ValueError("SEAD categorical staging key parse_failed")
    if (
        component["analysis_value_id"] != parent["analysis_value_id"]
        or parent["analysis_entity_id"] != entity["analysis_entity_id"]
        or entity["entity_relation_id"] != observation["entity_relation_id"]
        or entity["entity_relation_id"]
        != f"sead-analysis-entity:{parent['analysis_entity_id']}"
        or entity["site_id"] != site["site_id"]
        or entity["site_uuid"] != site["site_uuid"]
        or canonical_site_uuid(entity["site_uuid"])
        != canonical_site_uuid(site["site_uuid"])
        or entity["country_code"] != observation["country_code"]
        or observation["source_semantics"]["dataset_semantics_id"]
        != f"sead-dataset:{entity['dataset_id']}"
        or parent["value_class_id"] != value_class["value_class_id"]
        or component["value_type_item_id"] != item["value_type_item_id"]
        or item["value_type_id"] != value_class["value_type_id"]
        or item["value_type_id"] != value_type["value_type_id"]
        or value_type["base_type"] != "category"
    ):
        raise ValueError("SEAD categorical staging native relation differs")
    value, value_state = field_value(component, "value")
    variant, variant_state = field_value(component, "is_variant")
    display, display_state = field_value(parent, "analysis_value")
    return {
        "analysis_categorical_value_id": component["analysis_categorical_value_id"],
        "component_id": f"sead-analysis-categorical-value:{component['analysis_categorical_value_id']}",
        "analysis_value_id": parent["analysis_value_id"],
        "observation_id": observation["observation_id"],
        **{
            key: entity[key]
            for key in (
                "site_id",
                "site_uuid",
                "country_code",
                "sample_group_id",
                "physical_sample_id",
                "analysis_entity_id",
                "dataset_id",
            )
        },
        "value_class_id": value_class["value_class_id"],
        "value_class_name": value_class["name"],
        "value_type_id": value_type["value_type_id"],
        "value_type_name": value_type["name"],
        "value_type_base_type": value_type["base_type"],
        "value_type_unit_id": value_type["unit_id"],
        "value_type_item_id": item["value_type_item_id"],
        "item_name_json": json.dumps(item["name"], ensure_ascii=False),
        "item_key_parse_state": "resolved_native_foreign_key",
        "typed_value_json": value,
        "typed_value_state": value_state,
        "typed_value_parse_state": value_state
        if value_state != "reported"
        else "reported_uninterpreted",
        "is_variant_json": variant,
        "is_variant_state": variant_state,
        "parent_value_json": display,
        "parent_value_state": display_state,
        "parent_parse_state": display_state
        if display_state != "reported"
        else "source_display_not_interpreted",
        "parent_display_vs_item_name": "equal"
        if parent.get("analysis_value") == item["name"]
        else "different",
        "source_unit_id": observation["source_semantics"]["source_unit_id"],
        "unit_status": observation["source_semantics"]["unit_status"],
        "chronology_link_status": observation["chronology_link"]["status"],
        "eligible_claim_count": observation["chronology_link"]["eligible_claim_count"],
        "event_eligibility": observation["event_eligibility"],
        "event_refusal_reason_codes_json": json.dumps(
            observation["event_refusal_reason_codes"]
        ),
    }


def render_rows(rows: Sequence[Mapping[str, Any]]) -> str:
    """Write one deterministic row per distinct component, preserving source IDs."""
    identities = [row["analysis_categorical_value_id"] for row in rows]
    if len(identities) != len(set(identities)):
        raise ValueError("SEAD categorical staging duplicate primary key")
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(sorted(rows, key=lambda row: row["analysis_categorical_value_id"]))
    return output.getvalue()
