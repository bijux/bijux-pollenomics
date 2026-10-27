"""Separate a freshly recomputed decision from its historical authority identity."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.boundaries.review import (
    _build_boundary_review,
    build_point_country_decision,
)
from bijux_pollenomics.collection.sources.boundaries.review.decisions import (
    _prior_decision_comparison,
)
from bijux_pollenomics.collection.spatial.country_classification import (
    CountryAttributionDecision,
)

from .test_boundary_country_review import _authority, _point


def _geometric() -> CountryAttributionDecision:
    return CountryAttributionDecision(
        derived_country="Sweden",
        decision_status="assigned",
        decision_method="strict_boundary_containment",
        ambiguity_reason=None,
        refusal_reason=None,
        raw_country="SE",
        raw_country_comparison="agrees",
        candidate_countries=("Sweden",),
        boundary_artifact_digest="sha256:" + "4" * 64,
        boundary_version="natural-earth:5.1.1",
    )


def _prior() -> dict[str, Any]:
    return {
        "decision_status": "assigned",
        "decision_method": "strict_boundary_containment",
        "derived_country": "Sweden",
        "boundary_artifact_digest": "sha256:" + "3" * 64,
    }


def test_new_authority_preserves_same_decision_and_both_authorities_without_approval() -> (
    None
):
    prior = _prior()
    original = deepcopy(prior)
    point = replace(
        _point(
            longitude=1.0, latitude=1.0, raw_country="SE", published_country="Sweden"
        ),
        prior_decision=prior,
    )
    authority = _authority()
    row = build_point_country_decision(point, authority=authority)
    assert row["prior_country_decision_comparison"] == "agrees_authority_changed"
    assert row["prior_boundary_artifact_digest"] == prior["boundary_artifact_digest"]
    assert row["boundary_artifact_digest"] == authority.artifact_digest
    assert row["country_decision_status"] == "assigned"
    assert row["review_reason_codes"] == []
    assert row["raw_country"] == "SE"
    assert row["published_country"] == "Sweden"
    assert row["source_native_lineage"] == list(point.lineage)
    assert row["qualified_review_status"] == "not_required"
    assert row["qualified_reviewer"] is None
    assert row["qualified_reviewed_at"] is None
    assert prior == original
    review = _build_boundary_review(authority)
    assert review["qualified_review_status"] == "pending"
    assert review["release_status"] == "blocked_pending_qualified_boundary_review"
    countries = review["countries"]
    assert isinstance(countries, list)
    assert len(countries) == 4
    assert all(
        isinstance(country, dict) and country["qualified_review_status"] == "pending"
        for country in countries
    )


def test_exact_authority_and_complete_decision_agree() -> None:
    prior = {
        **_prior(),
        "boundary_artifact_digest": _geometric().boundary_artifact_digest,
    }
    assert _prior_decision_comparison(prior, _geometric()) == "agrees"
    assert _prior_decision_comparison(None, _geometric()) == "not_supplied"
    row = build_point_country_decision(
        _point(longitude=1.0, latitude=1.0), authority=_authority()
    )
    assert row["prior_country_decision_comparison"] == "not_supplied"
    assert "prior_boundary_artifact_digest" not in row


@pytest.mark.parametrize(
    "field,value",
    [
        ("decision_status", "review"),
        ("decision_method", "no_boundary_containment"),
        ("derived_country", "Finland"),
        ("derived_country", None),
    ],
)
def test_actual_decision_differences_still_require_review(
    field: str, value: object
) -> None:
    prior = {**_prior(), field: value}
    row = build_point_country_decision(
        replace(_point(longitude=1.0, latitude=1.0), prior_decision=prior),
        authority=_authority(),
    )
    assert row["prior_country_decision_comparison"] == "conflicts"
    assert row["country_decision_status"] == "review"
    assert row["review_reason_codes"] == ["prior_country_decision_conflict"]
    assert row["qualified_review_status"] == "pending"


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "digest",
        "a" * 64,
        "sha1:" + "a" * 40,
        "sha256:" + "a" * 63,
        "sha256:" + "g" * 64,
        "sha256:" + "A" * 64,
        True,
        42,
    ],
)
def test_malformed_prior_or_current_authority_does_not_agree(value: object) -> None:
    assert (
        _prior_decision_comparison(
            {**_prior(), "boundary_artifact_digest": value}, _geometric()
        )
        == "conflicts"
    )
    malformed_current = replace(_geometric(), boundary_artifact_digest=cast(Any, value))
    assert _prior_decision_comparison(_prior(), malformed_current) == "conflicts"
    assert (
        _prior_decision_comparison(
            {**_prior(), "boundary_artifact_digest": value}, malformed_current
        )
        == "conflicts"
    )


def test_missing_prior_fields_are_not_inferred_from_current_decision() -> None:
    for field in _prior():
        prior = _prior()
        del prior[field]
        assert _prior_decision_comparison(prior, _geometric()) == "conflicts"
    row = build_point_country_decision(
        replace(_point(longitude=1.0, latitude=1.0), prior_decision={}),
        authority=_authority(),
    )
    assert row["prior_boundary_artifact_digest"] is None
    assert row["country_decision_status"] == "review"


def test_changed_authority_does_not_clear_genuine_geometric_review() -> None:
    point = replace(
        _point(longitude=0.0, latitude=1.0),
        prior_decision={
            **_prior(),
            "decision_status": "review",
            "decision_method": "point_on_boundary",
            "derived_country": None,
        },
    )
    row = build_point_country_decision(point, authority=_authority())
    assert row["prior_country_decision_comparison"] == "agrees_authority_changed"
    assert row["country_decision_status"] == "review"
    assert row["review_reason_codes"] == ["point_on_boundary"]
    assert row["qualified_review_status"] == "pending"


def test_previous_unassigned_country_to_finland_remains_an_explicit_conflict() -> None:
    """Construct the country transition observed for the four changed source rows."""
    prior = {
        **_prior(),
        "decision_status": "unassigned",
        "decision_method": "no_boundary_containment",
        "derived_country": None,
    }
    point = replace(
        _point(longitude=13.0, latitude=1.0, raw_country="FI"),
        prior_decision=prior,
    )
    row = build_point_country_decision(point, authority=_authority())
    assert row["derived_country_code"] == "FI"
    assert row["boundary_decision_status"] == "assigned"
    assert row["prior_country_decision_comparison"] == "conflicts"
    assert row["country_decision_status"] == "review"
    assert row["review_reason_codes"] == ["prior_country_decision_conflict"]
    assert row["prior_boundary_artifact_digest"] == prior["boundary_artifact_digest"]
    assert row["qualified_review_status"] == "pending"
