"""Expose literal variable qualifiers without asserting a native foreign key."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from copy import deepcopy
import json

from ..records import _row_table

OBSERVATION_FIELDS = (
    "observation_id",
    "sample_id",
    "variable_id",
    "source_taxon_id",
    "source_value",
    "source_unit",
    "source_denominator",
    "denominator_status",
    "detection_status",
    "source_context",
    "source_ecological_group",
    "source_element",
    "source_element_type",
    "aggregation_key",
    "unit_family",
    "source_part_number",
    "source_variable_provenance",
)


def observation_variable_provenance(
    rows: Iterable[Mapping[str, object]],
) -> Iterator[dict[str, object]]:
    """Keep absent source fields distinct from explicit null and unknown values."""
    for row in rows:
        payload = row.get("source_payload")
        provenance = (
            {
                field: deepcopy(payload[field])
                for field in ("variableid", "symmetry", "taphonomics", "variablename")
                if field in payload
            }
            if isinstance(payload, Mapping)
            else None
        )
        if provenance is not None and isinstance(payload, Mapping):
            provenance["source_reported_name_status"] = (
                "reported" if "variablename" in payload else "not_provided_by_source"
            )
        yield {**row, "source_variable_provenance": provenance}


def observation_table(
    fields: tuple[str, ...], rows: Sequence[Sequence[object]], variable_prefix: str
) -> dict[str, object]:
    """Dictionary-encode literal provenance without collapsing JSON value types."""
    index = fields.index("source_variable_provenance")
    encoded_values = [
        json.dumps(row[index], sort_keys=True, ensure_ascii=True, allow_nan=False)
        for row in rows
    ]
    keys = sorted(set(encoded_values))
    positions = {value: number for number, value in enumerate(keys)}
    encoded_rows = [list(row) for row in rows]
    for row, key in zip(encoded_rows, encoded_values, strict=True):
        row[index] = positions[key]
    return {
        **_row_table(
            fields,
            encoded_rows,
            identifier_prefixes={
                "observation_id": "neotoma:observation:",
                "sample_id": "neotoma:sample:",
                "variable_id": variable_prefix,
                "aggregation_key": "neotoma:exact-unit:",
            },
        ),
        "column_dictionaries": {
            "source_variable_provenance": [json.loads(value) for value in keys]
        },
    }
