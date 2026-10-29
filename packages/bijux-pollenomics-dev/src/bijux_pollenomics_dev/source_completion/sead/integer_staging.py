"""Stream native SEAD integer components as individually keyed preparation rows."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import csv
from decimal import Decimal
import json
from typing import Any, TextIO

from bijux_pollenomics.collection.sources.sead.evidence.source_keys.identities import (
    canonical_site_uuid,
)

PARSER_RULE = "native-integer-and-independent-decimal-display-v1"
MAX_CSV_BYTES = 32 * 1024**2
CSV_FIELDS = (
    "analysis_integer_value_id",
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
    "source_unit_id",
    "source_unit_name",
    "unit_status",
    "typed_value_json",
    "typed_value_state",
    "parent_value_json",
    "parent_value_state",
    "parent_numeric_value",
    "parent_parse_state",
    "value_comparison",
    "qualifier_json",
    "qualifier_state",
    "is_variant_json",
    "is_variant_state",
    "chronology_link_status",
    "eligible_claim_count",
    "event_eligibility",
    "event_refusal_reason_codes_json",
)


def source_field(row: Mapping[str, Any], key: str) -> tuple[str, str]:
    """Encode native fields without merging an absent field with JSON null."""
    if key not in row:
        return "", "missing"
    return (
        json.dumps(row[key], ensure_ascii=False, allow_nan=False),
        "source_null" if row[key] is None else "reported",
    )


def project_row(
    integer: Mapping[str, Any],
    parent: Mapping[str, Any],
    observation: Mapping[str, Any],
    entity: Mapping[str, Any],
    site: Mapping[str, Any],
    value_class: Mapping[str, Any],
    value_type: Mapping[str, Any],
    states: tuple[str, str, str],
    unit: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Preserve component, parent and site identities without event admission."""
    for row, keys in (
        (integer, ("analysis_integer_value_id", "analysis_value_id")),
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
            raise ValueError("SEAD integer staging key is invalid")
    if (
        integer["analysis_value_id"] != parent["analysis_value_id"]
        or entity["analysis_entity_id"] != parent["analysis_entity_id"]
        or observation["entity_relation_id"] != entity["entity_relation_id"]
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
        or value_class["value_type_id"] != value_type["value_type_id"]
    ):
        raise ValueError("SEAD integer staging native relation differs")

    # JSON identity preserves native booleans, integers and nullable flags.
    def encode(value: object) -> str:
        return json.dumps(value, sort_keys=True, allow_nan=False)

    if (
        encode(observation["source_components"]["tbl_analysis_integer_values"])
        != encode([integer])
        or encode(observation["source_row"]) != encode(parent)
        or observation["event_eligibility"] != "refused"
        or "source_classification_not_accepted"
        not in observation["event_refusal_reason_codes"]
    ):
        raise ValueError("SEAD integer staging source or refusal differs")
    if (
        (unit is None) != (value_type["unit_id"] is None)
        or (
            unit is not None
            and (
                type(unit.get("unit_id")) is not int
                or unit["unit_id"] != value_type["unit_id"]
            )
        )
        or encode(observation["source_semantics"]["source_unit_id"])
        != encode(value_type["unit_id"])
    ):
        raise ValueError("SEAD integer staging source unit differs")
    typed, typed_state = source_field(integer, "value")
    display, display_state = source_field(parent, "analysis_value")
    qualifier, qualifier_state = source_field(integer, "qualifier")
    variant, variant_state = source_field(integer, "is_variant")
    if typed_state != states[0]:
        raise ValueError("SEAD integer staging typed state differs")
    return {
        "analysis_integer_value_id": integer["analysis_integer_value_id"],
        "component_id": f"sead-analysis-integer-value:{integer['analysis_integer_value_id']}",
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
        "source_unit_id": observation["source_semantics"]["source_unit_id"],
        "source_unit_name": unit["unit_name"] if unit is not None else "",
        "unit_status": observation["source_semantics"]["unit_status"],
        "typed_value_json": typed,
        "typed_value_state": typed_state,
        "parent_value_json": display,
        "parent_value_state": display_state,
        "parent_numeric_value": str(Decimal(str(parent["analysis_value"])))
        if states[1] == "parsed_numeric"
        else "",
        "parent_parse_state": states[1],
        "value_comparison": states[2],
        "qualifier_json": qualifier,
        "qualifier_state": qualifier_state,
        "is_variant_json": variant,
        "is_variant_state": variant_state,
        "chronology_link_status": observation["chronology_link"]["status"],
        "eligible_claim_count": observation["chronology_link"]["eligible_claim_count"],
        "event_eligibility": observation["event_eligibility"],
        "event_refusal_reason_codes_json": json.dumps(
            observation["event_refusal_reason_codes"]
        ),
    }


class IntegerStagingWriter:
    """Bound CSV output and account for every individually keyed component."""

    def __init__(self, stream: TextIO) -> None:
        """Write the header and initialize bounded component-identity accounting."""
        self.stream = stream
        self.byte_count = 0
        self.identities: set[int] = set()
        self.parents: set[int] = set()
        self.states: dict[str, Counter[str]] = {
            key: Counter()
            for key in (
                "typed_value_state",
                "parent_value_state",
                "parent_parse_state",
                "value_comparison",
                "qualifier_state",
                "is_variant_state",
            )
        }
        self.writer = csv.DictWriter(self, CSV_FIELDS, lineterminator="\n")
        self.writer.writeheader()

    def write(self, text: str) -> int:
        """Stop before writing bytes beyond the declared preparation budget."""
        size = len(text.encode("utf-8"))
        if self.byte_count + size > MAX_CSV_BYTES:
            raise ValueError("SEAD integer staged CSV exceeds 32 MiB")
        result = self.stream.write(text)
        self.byte_count += size
        return result

    def write_row(self, row: Mapping[str, Any]) -> None:
        """Reject duplicate components and parent fan-out before row publication."""
        key, parent = row["analysis_integer_value_id"], row["analysis_value_id"]
        if key in self.identities:
            raise ValueError("SEAD integer staging duplicate component key")
        if parent in self.parents:
            raise ValueError("SEAD integer staging parent fan-out")
        self.writer.writerow(row)
        self.identities.add(key)
        self.parents.add(parent)
        for field, counts in self.states.items():
            counts[row[field]] += 1

    def summary(
        self, count: int, extra_table_digests: Mapping[str, str]
    ) -> dict[str, Any]:
        """Describe successful row accounting without duplicating raw sources."""
        if len(self.identities) != count:
            raise ValueError("SEAD integer staging row population differs")
        return {
            "parser_rule": PARSER_RULE,
            "columns": CSV_FIELDS,
            "row_count": count,
            "distinct_component_primary_keys": len(self.identities),
            "additional_source_table_sha256": dict(extra_table_digests),
            "csv_byte_count": self.byte_count,
            "field_states": {
                key: dict(sorted(counts.items())) for key, counts in self.states.items()
            },
            "relationship_review_ledgers": {
                "duplicate_component_keys": [],
                "orphan_components": [],
                "missing_entity_parents": [],
                "missing_site_parents": [],
                "fan_out_parents": [],
            },
            "interpretation": "Native typed integers, uninterpreted nullable flags and independently parsed parent displays remain distinct. Missing required source values, broken relations or inaccessible inputs refuse publication; none become fabricated nulls or accepted events.",
        }
