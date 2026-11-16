"""Expose literal variable qualifiers without asserting a native foreign key."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from copy import deepcopy

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
                for field in ("variableid", "symmetry", "taphonomics")
                if field in payload
            }
            if isinstance(payload, Mapping)
            else None
        )
        yield {**row, "source_variable_provenance": provenance}
