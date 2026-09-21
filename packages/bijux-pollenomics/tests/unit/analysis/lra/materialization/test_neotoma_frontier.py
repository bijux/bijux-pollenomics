"""Source-authenticated Neotoma prerequisite frontier tests."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.api import inspect_neotoma_lra_frontier
from bijux_pollenomics.analysis.lra.materialization.neotoma import (
    MISSING_LRA_EVIDENCE,
)
from bijux_pollenomics.analysis.lra.materialization.neotoma_frontier import (
    assess_neotoma_lra_frontier,
)
from bijux_pollenomics.analysis.lra.materialization.reading import (
    read_neotoma_evidence,
)

from .support import authorities


def test_selected_source_sample_has_exact_refused_prerequisite_partition(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path)
    evidence = read_neotoma_evidence(raw, normalized)
    result = assess_neotoma_lra_frontier(evidence, ("neotoma:sample:100",))
    payload = result.as_dict()

    assert payload["source_denominators"] == {
        "available_samples": 9,
        "available_observations": 45,
        "source_age_claims": 18,
        "source_conflicts": 0,
        "source_orphans": 18,
    }
    selected = payload["selected_denominators"]
    assert selected["samples"] == 1
    assert selected["observations"] == 5
    assert selected["count_candidate_observations"] == 2
    assert selected["refused_count_observations"] == 3
    assert selected["samples_with_count_candidates"] == 1
    assert selected["sites"] == selected["datasets"] == 1
    assert selected["collection_units"] == 1
    assert selected["age_claims"] == 2
    assert selected["samples_with_age_claims"] == 1
    assert selected["samples_with_count_and_age_claims"] == 1
    assert selected["samples_with_count_and_comparable_age_claims"] == 1
    assert payload["schema_version"] == "neotoma-lra-prerequisite-frontier.v3"
    assert (
        sum(
            row["samples_with_count_and_age_claims"]
            for row in payload["country_denominators"].values()
        )
        == 1
    )
    assert (
        sum(
            row["samples_with_count_and_comparable_age_claims"]
            for row in payload["country_denominators"].values()
        )
        == selected["samples_with_count_and_comparable_age_claims"]
    )
    assert (
        sum(row["age_claims"] for row in payload["country_denominators"].values()) == 2
    )
    assert (
        sum(
            sum(row["age_claim_comparability_counts"].values())
            for row in payload["country_denominators"].values()
        )
        == 2
    )
    assert set(payload["country_denominators"]) == {
        "SE",
        "DK",
        "NO",
        "FI",
        "UNASSIGNED",
    }
    assert payload["country_denominators"]["DK"] == {
        "selected_samples": 0,
        "samples_with_count_candidates": 0,
        "samples_without_count_candidates": 0,
        "samples_with_count_and_age_claims": 0,
        "samples_with_count_and_comparable_age_claims": 0,
        "samples_with_age_claims": 0,
        "samples_without_age_claims": 0,
        "age_claims": 0,
        "selected_observations": 0,
        "count_candidate_observations": 0,
        "refused_count_observations": 0,
        "age_claim_comparability_counts": {},
    }
    assert [row["prerequisite"] for row in payload["prerequisites"]] == list(
        MISSING_LRA_EVIDENCE
    )
    assert all(
        row["selected_samples"] == 1
        and row["selected_observations"] == 5
        and row["selected_count_candidate_observations"] == 2
        for row in payload["prerequisites"]
    )
    assert payload["frontier_status"] == "refused"
    assert payload["lra_accepted_samples"] == 0
    assert payload["executable_request"] is None
    assert hashlib.sha256(result.canonical_json).hexdigest() == result.result_digest


def test_selection_order_is_canonical_and_source_values_stay_out_of_request(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path)
    evidence = read_neotoma_evidence(raw, normalized)
    first = assess_neotoma_lra_frontier(
        evidence, ("neotoma:sample:100", "neotoma:sample:200")
    )
    second = assess_neotoma_lra_frontier(
        evidence, ("neotoma:sample:200", "neotoma:sample:100")
    )

    assert first.canonical_json == second.canonical_json
    payload = first.as_dict()
    assert payload["selection"]["sample_ids"] == [
        "neotoma:sample:100",
        "neotoma:sample:200",
    ]
    assert payload["selected_denominators"]["observations"] == 10
    assert payload["selected_denominators"]["count_candidate_observations"] == 4
    assert "scientific_acceptance" in payload["claims_not_made"]
    assert payload["executable_request"] is None


def test_numeric_count_does_not_promote_context_only_age(tmp_path: Path) -> None:
    raw, normalized = authorities(tmp_path, context_only_sample=100)
    evidence = read_neotoma_evidence(raw, normalized)
    selected = assess_neotoma_lra_frontier(evidence, ("neotoma:sample:100",)).as_dict()[
        "selected_denominators"
    ]
    assert selected["count_candidate_observations"] == 2
    assert selected["samples_with_count_and_age_claims"] == 1
    assert selected["age_claim_comparability_counts"] == {"context_only": 1}
    assert selected["samples_with_count_and_comparable_age_claims"] == 0


def test_empty_selection_is_not_misreported_as_scientific_refusal(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path)
    evidence = read_neotoma_evidence(raw, normalized)
    payload = assess_neotoma_lra_frontier(evidence, ()).as_dict()

    assert payload["frontier_status"] == "empty_selection"
    assert payload["reason_codes"] == ["empty_source_sample_selection"]
    assert payload["prerequisites"] == []
    assert payload["selected_denominators"]["samples"] == 0
    assert payload["selected_denominators"]["observations"] == 0
    assert payload["selected_denominators"]["count_candidate_observations"] == 0
    assert payload["selected_denominators"]["samples_with_count_and_age_claims"] == 0
    assert (
        payload["selected_denominators"]["samples_with_count_and_comparable_age_claims"]
        == 0
    )
    assert all(
        row["samples_with_count_and_age_claims"] == 0
        and row["samples_with_count_and_comparable_age_claims"] == 0
        and row["age_claims"] == 0
        for row in payload["country_denominators"].values()
    )
    assert payload["lra_accepted_samples"] == 0
    assert payload["executable_request"] is None


def test_stable_host_facade_reads_the_authenticated_authorities(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path)

    result = inspect_neotoma_lra_frontier(
        raw_root=raw,
        normalized_root=normalized,
        selected_sample_ids=("neotoma:sample:100",),
    )

    payload = result.as_dict()
    assert payload["selected_denominators"]["samples"] == 1
    assert payload["frontier_status"] == "refused"
    assert payload["lra_accepted_samples"] == 0
    assert payload["executable_request"] is None


def test_frontier_rejects_manifest_bytes_detached_from_captured_inventory(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path)
    evidence = read_neotoma_evidence(raw, normalized)
    detached = json.loads(evidence.manifest_bytes)
    detached["build_id"] = "forged-build"
    forged = replace(
        evidence,
        manifest_bytes=json.dumps(detached, sort_keys=True).encode("utf-8"),
    )

    with pytest.raises(ValueError, match="Source authority changed"):
        assess_neotoma_lra_frontier(forged)
