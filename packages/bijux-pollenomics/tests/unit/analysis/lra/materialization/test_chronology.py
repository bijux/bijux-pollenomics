"""Source chronology preservation does not manufacture an LRA age choice."""

from __future__ import annotations

from bijux_pollenomics.analysis.lra.materialization.chronology import (
    chronology_projection,
)
from bijux_pollenomics.analysis.lra.materialization.models import (
    SourceRow,
    canonical_bytes,
)


def test_signed_native_claim_and_mismatched_subject_remain_visible() -> None:
    sample = {
        "sample_id": "sample-1",
        "dataset_id": "dataset-1",
        "site_id": "site-1",
        "collection_unit_id": "unit-1",
        "country_code": "SE",
    }
    claim = {
        **sample,
        "subject_id": "sample-other",
        "subject_type": "sample",
        "source_age_type": "Calendar years BP",
        "source_age_value": -50,
        "source_age_younger": None,
        "source_age_older": None,
        "comparability_status": "refused",
        "admission_reason": "negative_bp",
    }
    source = SourceRow(
        "age_claims", "surfaces/age_claims/part-00001.json", 0, canonical_bytes(claim)
    )
    projection = chronology_projection(sample, [source])
    assert projection["selected_claim_id"] is None
    assert projection["claims"] == [
        {
            "source_locator": source.locator(),
            "source_claim": claim,
            "ownership_mismatches": ["subject_id"],
        }
    ]
    assert chronology_projection(sample, [])["reason_codes"] == [
        "lra_chronology_decision_not_supplied",
        "sample_has_no_age_claims",
    ]
