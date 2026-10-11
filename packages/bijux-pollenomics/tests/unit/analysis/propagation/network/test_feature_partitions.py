"""Resolution and accepted-concept universe separation."""

from __future__ import annotations

from dataclasses import replace
from typing import TypedDict

import pytest

from bijux_pollenomics.analysis.propagation.candidates import (
    DEFAULT_PROPAGATION_SCENARIO,
)
from bijux_pollenomics.analysis.propagation.network import (
    EventValidationError,
    PropagationCandidate,
    PropagationPairRefusal,
    evaluate_propagation_pair,
    generate_propagation_network,
)

from .support import event, scenario


def test_signal_resolution_and_role_universes_remain_separate() -> None:
    taxon_a = event("taxon-a")
    taxon_b = event(
        "taxon-b", latitude=55.7, longitude=13.19, younger_bp=5500, older_bp=5500
    )
    role_a = event(
        "role-a",
        resolution="ecological_role",
        feature_key="role:cereal_indicator",
    )
    role_b = event(
        "role-b",
        resolution="ecological_role",
        feature_key="role:cereal_indicator",
        latitude=55.7,
        longitude=13.19,
        younger_bp=5500,
        older_bp=5500,
    )

    result = scenario(
        generate_propagation_network((taxon_a, role_b, taxon_b, role_a)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )

    assert {row.feature_key for row in result.evaluated_pairs} == {
        "taxon:triticum_aestivum",
        "role:cereal_indicator",
    }
    assert all(
        row.source_event_id.startswith("event:")
        and row.target_event_id.startswith("event:")
        for row in result.evaluated_pairs
    )
    assert len(result.evaluated_pairs) == 4


@pytest.mark.parametrize("_fixture_id", ["MATCH-006"])
def test_taxon_universe_requires_the_same_accepted_concept(_fixture_id: str) -> None:
    accepted_a = event("accepted-a")
    accepted_b = event(
        "accepted-b",
        latitude=55.7,
        longitude=13.19,
        younger_bp=5500,
        older_bp=5500,
        accepted_taxon_concept_id="accepted-taxon-2",
    )

    result = scenario(
        generate_propagation_network((accepted_a, accepted_b)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )
    direct = evaluate_propagation_pair(accepted_a, accepted_b)

    assert not result.evaluated_pairs
    assert isinstance(direct, PropagationPairRefusal)
    assert direct.reason_code == "incompatible_feature"


@pytest.mark.parametrize(
    ("resolution", "feature", "accepted"),
    [
        ("taxon", "taxon:pinus-sylvestris", "accepted:pinus-sylvestris"),
        ("ecological_subgroup", "subgroup:coniferous_trees", "unused"),
    ],
    ids=["MATCH-001", "MATCH-003"],
)
def test_same_reviewed_taxon_or_subgroup_remains_comparable(
    resolution: str, feature: str, accepted: str
) -> None:
    source = event(
        "source",
        resolution=resolution,
        feature_key=feature,
        accepted_taxon_concept_id=accepted,
    )
    target = event(
        "target",
        resolution=resolution,
        feature_key=feature,
        accepted_taxon_concept_id=accepted,
        younger_bp=5500,
        older_bp=5500,
        latitude=55.61,
        longitude=13.01,
    )
    assert isinstance(evaluate_propagation_pair(source, target), PropagationCandidate)


@pytest.mark.parametrize(
    "mismatch",
    ["qualifier", "subgroup", "crosswalk"],
    ids=["MATCH-002", "MATCH-004", "MATCH-003-crosswalk"],
)
def test_mismatched_qualifier_subgroup_or_crosswalk_is_refused(mismatch: str) -> None:
    source = event("source")
    target = event("target", younger_bp=5500, older_bp=5500)
    if mismatch == "qualifier":
        target = replace(target, taxonomic_qualifier="undifferentiated", event_id="")
    elif mismatch == "subgroup":
        source = event(
            "source",
            resolution="ecological_subgroup",
            feature_key="subgroup:coniferous_trees",
        )
        target = event(
            "target",
            resolution="ecological_subgroup",
            feature_key="subgroup:broadleaved_deciduous_trees",
            younger_bp=5500,
            older_bp=5500,
        )
    else:
        target = replace(
            target, classification_contract_version="other-crosswalk.v1", event_id=""
        )
    refused = evaluate_propagation_pair(source, target)
    assert (
        isinstance(refused, PropagationPairRefusal)
        and refused.reason_code == "incompatible_feature"
    )
    result = generate_propagation_network((source, target)).scenario_results[0]
    assert not result.evaluated_pairs and not result.directed_candidates


class InvalidEventOverrides(TypedDict, total=False):
    resolution: str
    feature_key: str
    classification_contract_version: str | None


@pytest.mark.parametrize(
    "overrides",
    [
        {"resolution": "ecological_group", "feature_key": "taxon:123"},
        {"classification_contract_version": None},
        {"resolution": "source", "feature_key": "source:coverage"},
    ],
    ids=["MATCH-009", "MATCH-010", "MATCH-011-event"],
)
def test_event_resolution_schema_refuses_wrong_prefix_missing_version_and_coverage_sentinel(
    overrides: InvalidEventOverrides,
) -> None:
    with pytest.raises(EventValidationError) as refused:
        event("invalid", **overrides)
    assert refused.value.reason_code == "invalid_event_schema"


@pytest.mark.parametrize("_fixture_id", ["SOURCE-005"])
def test_cross_source_shared_underlying_observation_is_not_independent_evidence(
    _fixture_id: str,
) -> None:
    source = replace(
        event("source"),
        source_family="sead",
        observation_ids=("published-core:sample-1",),
        event_id="",
    )
    target = replace(
        event(
            "target", younger_bp=5500, older_bp=5500, latitude=55.61, longitude=13.01
        ),
        source_family="neotoma",
        observation_ids=source.observation_ids,
        event_id="",
    )
    result = generate_propagation_network((source, target)).scenario_results[0]
    assert not result.evaluated_pairs and not result.directed_candidates
    assert len(result.refusals) == 2
    assert {row.reason_code for row in result.refusals} == {
        "duplicate_underlying_observation"
    }
    assert result.reconciliation.refused_pair_count == 2
    reverse = generate_propagation_network((target, source)).scenario_results[0]
    assert result.as_dict() == reverse.as_dict()
