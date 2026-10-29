"""Individually keyed native Boolean components, without display interpretation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import csv
import io
import json
from typing import Any, TextIO

from bijux_pollenomics.collection.sources.sead.evidence.source_keys.identities import (
    canonical_site_uuid,
)

PARSER_RULE = "native-boolean-with-independent-display-and-type-metadata-v1"
MAX_CSV_BYTES = 16 * 1024**2
CSV_FIELDS = (
    "analysis_boolean_value_id",
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
    "storage_vs_declared_base_type",
    "source_unit_id",
    "source_unit_name",
    "unit_status",
    "typed_value_json",
    "typed_value_state",
    "typed_value_parse_state",
    "qualifier_json",
    "qualifier_state",
    "parent_value_json",
    "parent_value_state",
    "parent_boolean_value_json",
    "parent_boolean_value_state",
    "parent_boolean_comparison",
    "chronology_link_status",
    "eligible_claim_count",
    "event_eligibility",
    "event_refusal_reason_codes_json",
)


def source_field(row: Mapping[str, Any], key: str) -> tuple[str, str]:
    """Encode absent fields, literal nulls and reported source values distinctly."""
    if key not in row:
        return "", "missing"
    return (
        json.dumps(row[key], ensure_ascii=False, allow_nan=False),
        "source_null" if row[key] is None else "reported",
    )


def boolean_field(row: Mapping[str, Any], key: str) -> tuple[str, str, str]:
    """Parse only native JSON Booleans; integer or textual substitutes refuse."""
    encoded, state = source_field(row, key)
    if state != "reported":
        return encoded, state, state
    if type(row[key]) is not bool:
        raise ValueError("SEAD Boolean value parse_failed: native bool required")
    return encoded, state, "true" if row[key] else "false"


def project_row(
    component: Mapping[str, Any],
    parent: Mapping[str, Any],
    observation: Mapping[str, Any],
    entity: Mapping[str, Any],
    site: Mapping[str, Any],
    value_class: Mapping[str, Any],
    value_type: Mapping[str, Any],
    units: Mapping[int, Mapping[str, Any]],
) -> dict[str, Any]:
    """Preserve actual storage separately from native class/type declarations.

    A native Count declaration can accompany Boolean storage. It is diagnostic,
    not permission to cast the flag to an integer or repair its source metadata.
    Parent display text and qualifiers supply no Boolean or ecological meaning.
    Broken relations refuse preparation rather than inventing excluded rows.
    """
    for row, keys in (
        (component, ("analysis_boolean_value_id", "analysis_value_id")),
        (parent, ("analysis_value_id", "analysis_entity_id", "value_class_id")),
        (
            entity,
            (
                "site_id",
                "sample_group_id",
                "physical_sample_id",
                "analysis_entity_id",
                "dataset_id",
            ),
        ),
        (site, ("site_id",)),
        (value_class, ("value_class_id", "value_type_id")),
        (value_type, ("value_type_id",)),
    ):
        if any(type(row.get(key)) is not int or row[key] <= 0 for key in keys):
            raise ValueError("SEAD Boolean staging key parse_failed")
    semantics, link = observation["source_semantics"], observation["chronology_link"]
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
        or semantics["dataset_semantics_id"] != f"sead-dataset:{entity['dataset_id']}"
        or semantics["value_semantics_id"]
        != f"sead-value-class:{parent['value_class_id']}"
        or parent["value_class_id"] != value_class["value_class_id"]
        or value_class["value_type_id"] != value_type["value_type_id"]
    ):
        raise ValueError("SEAD Boolean staging native relation differs")
    unit_id = value_type["unit_id"]
    if unit_id is not None and (
        type(unit_id) is not int or unit_id <= 0 or unit_id not in units
    ):
        raise ValueError("SEAD Boolean staging missing unit parent")
    unit_status = (
        "source_native_linked" if unit_id is not None else "not_exposed_by_relation"
    )
    if (
        type(semantics["source_unit_id"]) is not type(unit_id)
        or semantics["source_unit_id"] != unit_id
        or semantics["unit_status"] != unit_status
        or (
            unit_id is not None
            and (
                type(units[unit_id]["unit_id"]) is not int
                or units[unit_id]["unit_id"] != unit_id
            )
        )
    ):
        raise ValueError("SEAD Boolean staging unit semantics differ")
    eligible, claims = link["eligible_claim_count"], link["claim_count"]
    if (
        type(eligible) is not int
        or type(claims) is not int
        or not 0 <= eligible <= claims
    ):
        raise ValueError("SEAD Boolean staging chronology counts are invalid")
    status = (
        "direct_analysis_entity_eligible_claim"
        if eligible
        else "direct_analysis_entity_context_only"
        if claims
        else "unavailable_at_analysis_entity"
    )
    if (
        link["entity_relation_id"] != entity["entity_relation_id"]
        or link["selection_rule"] != "same_analysis_entity_only"
        or link["status"] != status
        or observation["event_eligibility"] != "refused"
        or "source_classification_not_accepted"
        not in observation["event_refusal_reason_codes"]
    ):
        raise ValueError("SEAD Boolean staging chronology or refusal differs")
    typed, typed_state, parsed = boolean_field(component, "value")
    qualifier, qualifier_state = source_field(component, "qualifier")
    display, display_state = source_field(parent, "analysis_value")
    parent_boolean, parent_state, _ = boolean_field(parent, "boolean_value")
    return {
        "analysis_boolean_value_id": component["analysis_boolean_value_id"],
        "component_id": f"sead-analysis-boolean-value:{component['analysis_boolean_value_id']}",
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
        "storage_vs_declared_base_type": "boolean_storage_boolean_declaration"
        if value_type["base_type"] == "boolean"
        else "boolean_storage_other_declaration",
        "source_unit_id": unit_id,
        "source_unit_name": units[unit_id]["unit_name"] if unit_id is not None else "",
        "unit_status": unit_status,
        "typed_value_json": typed,
        "typed_value_state": typed_state,
        "typed_value_parse_state": parsed,
        "qualifier_json": qualifier,
        "qualifier_state": qualifier_state,
        "parent_value_json": display,
        "parent_value_state": display_state,
        "parent_boolean_value_json": parent_boolean,
        "parent_boolean_value_state": parent_state,
        "parent_boolean_comparison": "equal_native_boolean"
        if typed_state == parent_state == "reported" and typed == parent_boolean
        else "different_native_boolean"
        if typed_state == parent_state == "reported"
        else "not_both_reported",
        "chronology_link_status": status,
        "eligible_claim_count": eligible,
        "event_eligibility": observation["event_eligibility"],
        "event_refusal_reason_codes_json": json.dumps(
            observation["event_refusal_reason_codes"]
        ),
    }


class BooleanStagingWriter:
    """Bound one CSV while accounting for every independently keyed component."""

    def __init__(self, stream: TextIO) -> None:
        """Initialize bounded CSV output and native component-state counters."""
        self.stream = stream
        self.byte_count = 0
        self.identities: set[int] = set()
        self.parents: Counter[int] = Counter()
        self.states: dict[str, Counter[str]] = {
            key: Counter()
            for key in (
                "typed_value_state",
                "typed_value_parse_state",
                "qualifier_state",
                "parent_value_state",
                "parent_boolean_value_state",
                "parent_boolean_comparison",
                "storage_vs_declared_base_type",
            )
        }
        self._write(None)

    def _write(self, row: Mapping[str, Any] | None) -> None:
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, CSV_FIELDS, lineterminator="\n")
        writer.writeheader() if row is None else writer.writerow(row)
        encoded = buffer.getvalue()
        if self.byte_count + len(encoded.encode()) > MAX_CSV_BYTES:
            raise ValueError("SEAD Boolean staged table exceeds sixteen MiB")
        self.stream.write(encoded)
        self.byte_count += len(encoded.encode())

    def append(self, row: Mapping[str, Any]) -> None:
        """Refuse repeated primary keys instead of silently merging source rows."""
        identity = row["analysis_boolean_value_id"]
        if identity in self.identities:
            raise ValueError("SEAD Boolean staging duplicate component primary key")
        self._write(row)
        self.identities.add(identity)
        self.parents[row["analysis_value_id"]] += 1
        for key, counts in self.states.items():
            counts[row[key]] += 1

    def account(self) -> dict[str, Any]:
        """Describe actual source preparation; intake errors are not fabricated rows."""
        return {
            "parser_rule": PARSER_RULE,
            "columns": CSV_FIELDS,
            "row_count": len(self.identities),
            "distinct_component_primary_keys": len(self.identities),
            "distinct_parent_primary_keys": len(self.parents),
            "field_states": {
                key: dict(sorted(counts.items())) for key, counts in self.states.items()
            },
            "relationship_review_ledgers": {
                "duplicate_component_keys": [],
                "orphan_components": [],
                "missing_entity_parents": [],
                "missing_site_parents": [],
                "fan_out_parents": [
                    {"analysis_value_id": key, "component_count": count}
                    for key, count in sorted(self.parents.items())
                    if count > 1
                ],
            },
            "interpretation": "Native Boolean storage, declared type metadata, qualifier and parent display remain separate. Broken relations, inaccessible sources and parse failures refuse publication; they never become null or excluded rows. No ecological or event interpretation is admitted.",
        }
