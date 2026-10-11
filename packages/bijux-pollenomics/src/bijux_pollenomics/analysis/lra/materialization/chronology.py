"""Retain every sample chronology alternative without choosing an LRA age."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .models import SourceRow

OWNERSHIP_FIELDS = (
    "sample_id",
    "dataset_id",
    "collection_unit_id",
    "site_id",
    "country_code",
)


def chronology_projection(
    sample: Mapping[str, object],
    claims: Sequence[SourceRow],
) -> dict[str, object]:
    """Keep native and normalized age evidence; default does not imply approval."""
    projected = []
    for source in claims:
        claim = source.payload()
        mismatches = [
            field
            for field in OWNERSHIP_FIELDS[1:]
            if claim.get(field) != sample.get(field)
        ]
        if (
            claim.get("subject_id") != sample.get("sample_id")
            or claim.get("subject_type") != "sample"
        ):
            mismatches.append("subject_id")
        projected.append(
            {
                "source_locator": source.locator(),
                "source_claim": claim,
                "ownership_mismatches": sorted(mismatches),
            }
        )
    return {
        "claims": projected,
        "claim_count": len(projected),
        "selected_claim_id": None,
        "lra_age_status": "not_admitted",
        "reason_codes": ["lra_chronology_decision_not_supplied"]
        + ([] if projected else ["sample_has_no_age_claims"]),
    }
