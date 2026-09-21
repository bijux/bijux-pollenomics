"""Full-source Neotoma prerequisite screen retains refusals and source identity."""

from __future__ import annotations

import hashlib
from pathlib import Path

from bijux_pollenomics.analysis.lra.materialization.neotoma_pollen_screen import (
    _comparable_owned_claim,
    assess_neotoma_pollen_screen,
)
from bijux_pollenomics.analysis.lra.materialization.reading import (
    read_neotoma_evidence,
)

from .support import authorities


def test_screen_covers_every_sample_and_keeps_refusal_only_status(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path)
    result = assess_neotoma_pollen_screen(read_neotoma_evidence(raw, normalized))
    payload = result.as_dict()

    assert payload["source_denominators"]["available_samples"] == 9
    assert payload["source_denominators"]["available_observations"] == 45
    assert payload["screen_denominators"]["count_candidate_observations"] == 18
    assert payload["screen_denominators"]["pollen_count_observations"] == 18
    assert payload["screen_denominators"]["samples_with_count_and_comparable_age"] == 9
    assert payload["screen_denominators"]["necessary_candidate_samples"] == 9
    assert payload["screen_denominators"]["refused_samples"] == 0
    assert len(payload["sample_decisions"]) == 9
    assert len(payload["candidate_sample_ids"]) == 9
    assert all(
        decision["screen_status"] == "necessary_candidate"
        and decision["lra_admission_status"] == "refused"
        and decision["source_locator"]["row_sha256"]
        for decision in payload["sample_decisions"]
    )
    assert payload["lra_accepted_samples"] == 0
    assert payload["executable_request"] is None
    assert hashlib.sha256(result.canonical_json).hexdigest() == result.result_digest
    assert (
        sum(
            country["screen_candidate_samples"]
            for country in payload["country_denominators"].values()
        )
        == 9
    )


def test_context_only_age_refuses_a_pollen_count_sample(tmp_path: Path) -> None:
    raw, normalized = authorities(tmp_path, context_only_sample=100)
    payload = assess_neotoma_pollen_screen(
        read_neotoma_evidence(raw, normalized)
    ).as_dict()

    assert payload["screen_denominators"]["samples_with_count_and_comparable_age"] == 8
    assert payload["screen_denominators"]["necessary_candidate_samples"] == 8
    assert payload["screen_denominators"]["refused_samples"] == 1
    sample = next(
        row
        for row in payload["sample_decisions"]
        if row["sample_id"] == "neotoma:sample:100"
    )
    assert sample["pollen_count_observations"] == 2
    assert sample["owned_comparable_age_claim_ids"] == []
    assert sample["reason_codes"] == ["no_sample_owned_comparable_typed_age"]
    assert sample["sample_id"] not in payload["candidate_sample_ids"]


def test_comparable_claim_requires_owner_type_and_ordered_numeric_bounds() -> None:
    claim = {
        "source_claim": {
            "comparability_status": "comparable",
            "source_age_type": "Calendar years BP",
            "younger_bp": 100,
            "older_bp": 200,
        },
        "ownership_mismatches": [],
    }
    assert _comparable_owned_claim(claim)
    assert not _comparable_owned_claim({**claim, "ownership_mismatches": ["site_id"]})
    assert not _comparable_owned_claim(
        {**claim, "source_claim": {**claim["source_claim"], "source_age_type": None}}
    )
    assert not _comparable_owned_claim(
        {**claim, "source_claim": {**claim["source_claim"], "younger_bp": 300}}
    )
    assert not _comparable_owned_claim(
        {**claim, "source_claim": {**claim["source_claim"], "older_bp": True}}
    )
