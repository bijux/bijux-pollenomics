"""Source-owned Neotoma candidate series preserve review and refusal evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.materialization.neotoma.series import (
    MAX_SAMPLES,
    build_neotoma_candidate_series,
    source_element_status,
)
from bijux_pollenomics.analysis.lra.materialization.reading import (
    read_neotoma_evidence,
)

from ...support import authorities


@pytest.mark.parametrize(
    ("element", "element_type", "expected"),
    [
        ("pollen", "spore", "source_element_labels_disagree"),
        ("pollen", None, "source_element_type_missing"),
        (None, "pollen", "source_element_missing"),
        ("pollen", "pollen", "source_label_pollen"),
    ],
)
def test_pollen_lead_requires_both_source_element_labels(
    element: object, element_type: object, expected: str
) -> None:
    assert source_element_status(element, element_type) == expected


def test_candidate_series_keeps_owned_values_units_and_age_alternatives(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path)
    evidence = read_neotoma_evidence(raw, normalized)
    result = build_neotoma_candidate_series(evidence, ("neotoma:sample:100",))
    payload = result.as_dict()

    assert payload["source_denominators"] == {
        "available_samples": 9,
        "available_observations": 45,
        "source_age_claims": 18,
    }
    assert payload["selected_denominators"] == {
        "samples": 1,
        "lra_refused_samples": 1,
        "observations": 5,
        "count_candidate_observations": 2,
        "pollen_labelled_count_candidates": 2,
        "age_claims": 2,
    }
    sample = payload["series"][0]
    assert sample["sample_id"] == "neotoma:sample:100"
    assert sample["source_sample"]["source_sample_id"] == 100
    assert sample["chronology"]["selected_claim_id"] is None
    claims = sample["chronology"]["claims"]
    assert {claim["source_claim"]["source_age_type"] for claim in claims} == {
        "Calendar years BP",
        "Radiocarbon years BP",
    }
    assert {claim["source_claim"]["comparability_status"] for claim in claims} == {
        "comparable",
        "context_only",
    }
    rows = sample["observations"]
    assert all(
        row["source_observation"]["sample_id"] == sample["sample_id"] for row in rows
    )
    assert all(row["source_locator"]["row_sha256"] for row in rows)
    assert any(
        row["source_observation"]["source_value"] == 0
        and row["typed_count"] == 0
        and row["pollen_count_review_candidate"]
        for row in rows
    )
    assert any(
        row["source_observation"]["source_value"] is None
        and row["typed_count"] is None
        and not row["pollen_count_review_candidate"]
        for row in rows
    )
    assert any(
        row["source_observation"]["source_unit"] == "percent"
        and "source_unit_is_not_count" in row["pollen_review_reason_codes"]
        for row in rows
    )
    assert sample["lra_admission_status"] == "refused"
    assert payload["lra_accepted_samples"] == 0
    assert payload["executable_request"] is None
    assert hashlib.sha256(result.canonical_json).hexdigest() == result.result_digest


def test_selection_order_and_country_partition_are_deterministic(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path)
    evidence = read_neotoma_evidence(raw, normalized)
    first = build_neotoma_candidate_series(
        evidence, ("neotoma:sample:200", "neotoma:sample:100")
    )
    second = build_neotoma_candidate_series(
        evidence, ("neotoma:sample:100", "neotoma:sample:200")
    )

    assert first.canonical_json == second.canonical_json
    payload = first.as_dict()
    assert payload["selection"]["sample_ids"] == [
        "neotoma:sample:100",
        "neotoma:sample:200",
    ]
    assert payload["country_denominators"]["UNASSIGNED"]["samples"] == 2
    assert payload["country_denominators"]["UNASSIGNED"]["observations"] == 10
    assert (
        payload["country_denominators"]["UNASSIGNED"]["count_candidate_observations"]
        == 4
    )
    assert set(payload["country_denominators"]) == {
        "SE",
        "DK",
        "NO",
        "FI",
        "UNASSIGNED",
    }
    assert sum(row["samples"] for row in payload["country_denominators"].values()) == 2


def test_numeric_count_with_context_only_age_still_refuses_admission(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path, context_only_sample=100)
    evidence = read_neotoma_evidence(raw, normalized)
    payload = build_neotoma_candidate_series(
        evidence, ("neotoma:sample:100",)
    ).as_dict()

    assert payload["series"][0]["pollen_labelled_count_candidates"] == 2
    assert payload["series"][0]["chronology"]["claim_count"] == 1
    assert (
        payload["series"][0]["chronology"]["claims"][0]["source_claim"][
            "comparability_status"
        ]
        == "context_only"
    )
    assert "no_comparable_sample_age_claim" in payload["series"][0]["lra_reason_codes"]
    assert payload["lra_accepted_samples"] == 0


def test_series_requires_explicit_bounded_source_ids(tmp_path: Path) -> None:
    raw, normalized = authorities(tmp_path)
    evidence = read_neotoma_evidence(raw, normalized)

    with pytest.raises(ValueError, match="Select between"):
        build_neotoma_candidate_series(evidence, ())
    with pytest.raises(ValueError, match="Select between"):
        build_neotoma_candidate_series(
            evidence, tuple(f"sample:{i}" for i in range(MAX_SAMPLES + 1))
        )
    with pytest.raises(ValueError, match="absent from the source inventory"):
        build_neotoma_candidate_series(evidence, ("neotoma:sample:missing",))
