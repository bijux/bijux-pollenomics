"""Source taxon identity refusals shared by Neotoma evidence consumers."""

from __future__ import annotations

from collections.abc import Mapping


def invalid_source_taxon_identifier(row: Mapping[str, object]) -> bool:
    """Retain malformed taxon IDs as invalid rather than treating them as absent."""
    if (
        "source_taxon_identifier_status" in row
        and row["source_taxon_identifier_status"] != "not_recorded"
    ):
        return True
    if isinstance(row.get("source_taxon_id"), (Mapping, list)):
        return True
    payload = row.get("source_payload")
    return isinstance(payload, Mapping) and isinstance(
        payload.get("taxonid"), (Mapping, list)
    )
