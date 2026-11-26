"""Source chronology-reference refusal shared by evidence consumers."""

from __future__ import annotations

from collections.abc import Mapping


def invalid_chronology_reference(claim: Mapping[str, object]) -> bool:
    """Refuse recorded invalid or malformed source reference evidence."""
    if (
        "chronology_reference_status" in claim
        and claim["chronology_reference_status"] != "not_recorded"
    ):
        return True
    payload = claim.get("source_payload")
    return isinstance(payload, Mapping) and isinstance(
        payload.get("chronologyid"), (Mapping, list)
    )
