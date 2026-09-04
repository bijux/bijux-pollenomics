from __future__ import annotations

import random
from copy import deepcopy
from typing import Any

import pytest
from bijux_pollenomics.analysis.classification_events import (
    ClassificationEventContext,
    derive_classification_events,
)
from hypothesis import given
from hypothesis import strategies as st


def _context() -> ClassificationEventContext:
    return ClassificationEventContext(
        source_family="neotoma",
        classification_contract_version="1.0.0",
        threshold_profile_id="reported-positive.v1",
        config_digest=f"sha256:{'c' * 64}",
    )


def _membership(
    observation_id: str, concept_id: str, status: str = "accepted"
) -> dict[str, object]:
    return {
        "observation_id": observation_id,
        "classification_concept_id": concept_id,
        "mapping_status": status,
        "source_country_code": "SE",
        "governed_country_code": "SE",
    }


def _mapping(
    concept_id: str,
    taxon_id: str,
    *,
    group_id: str = "cultivated_plants",
    subgroup_id: str = "cereals",
    roles: tuple[str, ...] = ("crop_type_qualified",),
    status: str = "accepted",
) -> dict[str, object]:
    return {
        "classification_concept_id": concept_id,
        "mapping_status": status,
        "accepted_taxon_concept_id": taxon_id,
        "taxonomic_qualifier": "exact",
        "primary_group_id": group_id,
        "primary_subgroup_id": subgroup_id,
        "role_ids": list(roles),
        "mapping_version": "neotoma-crosswalk.v1",
        "classification_contract_version": "1.0.0",
        "reviewer_id": "reviewer:fixture",
        "decision_date": "2026-09-04",
        "citation_reference_ids": ["citation:fixture"],
        "review_complete": True,
        "release_eligible": True,
    }


def _observation(
    observation_id: str,
    *,
    sample_id: str = "neotoma:sample:1",
    site_id: str = "neotoma:site:1",
) -> dict[str, object]:
    return {
        "observation_id": observation_id,
        "sample_id": sample_id,
        "site_id": site_id,
        "country_code": "SE",
        "source_element_type": "pollen",
        "source_value": 3,
        "detection_status": "reported_value",
        "source_snapshot_id": f"sha256:{'a' * 64}",
        "build_id": f"sha256:{'b' * 64}",
        "measurement_semantics_id": "count:NISP",
        "evidence_method_id": "source-reported-positive.v1",
        "method_compatibility_key": "neotoma:pollen-count:NISP",
    }


def _site(
    *, latitude: object = 55.605, longitude: object = 13.0038
) -> dict[str, object]:
    return {
        "site_id": "neotoma:site:1",
        "country_code": "SE",
        "latitude": latitude,
        "longitude": longitude,
        "coordinate_quality": "reported",
        "source_snapshot_id": f"sha256:{'a' * 64}",
        "build_id": f"sha256:{'b' * 64}",
    }


def _chronology(
    *,
    comparability_status: str = "comparable",
    younger_bp: object = 5500,
    older_bp: object = 5500,
) -> dict[str, object]:
    return {
        "chronology_claim_id": "neotoma:age-claim:1",
        "source_record_id": "neotoma:sample:1",
        "site_id": "neotoma:site:1",
        "country_code": "SE",
        "selected_for_event": True,
        "comparability_status": comparability_status,
        "younger_bp": younger_bp,
        "older_bp": older_bp,
        "provenance_record_id": f"sha256:{'a' * 64}",
        "source_snapshot_id": f"sha256:{'a' * 64}",
        "build_id": f"sha256:{'b' * 64}",
    }


def _derive(
    *,
    memberships: list[dict[str, object]] | None = None,
    mappings: list[dict[str, object]] | None = None,
    observations: list[dict[str, object]] | None = None,
    sites: list[dict[str, object]] | None = None,
    chronologies: list[dict[str, object]] | None = None,
):
    return derive_classification_events(
        observation_memberships=(
            memberships
            if memberships is not None
            else [_membership("observation:1", "concept:1")]
        ),
        classification_mappings=(
            mappings
            if mappings is not None
            else [_mapping("concept:1", "taxon:triticum")]
        ),
        observations=(
            observations
            if observations is not None
            else [_observation("observation:1")]
        ),
        sites=sites if sites is not None else [_site()],
        chronologies=chronologies if chronologies is not None else [_chronology()],
        context=_context(),
    )


def test_derives_separate_resolution_events_with_union_reconciliation() -> None:
    memberships = [
        _membership("observation:1", "concept:1"),
        _membership("observation:2", "concept:2"),
    ]
    mappings = [
        _mapping("concept:1", "taxon:triticum"),
        _mapping(
            "concept:2",
            "taxon:hordeum",
            roles=("crop_type_qualified", "anthropogenic_indicator"),
        ),
    ]
    observations = [_observation("observation:1"), _observation("observation:2")]

    result = _derive(
        memberships=memberships, mappings=mappings, observations=observations
    )

    by_resolution: dict[str, list[Any]] = {}
    for event in result.events:
        by_resolution.setdefault(event.resolution, []).append(event)
    assert len(by_resolution["whole_pollen"]) == 1
    assert by_resolution["whole_pollen"][0].observation_ids == (
        "observation:1",
        "observation:2",
    )
    assert len(by_resolution["ecological_group"]) == 1
    assert len(by_resolution["ecological_subgroup"]) == 1
    assert len(by_resolution["ecological_role"]) == 2
    assert len(by_resolution["taxon"]) == 2
    assert result.reconciliation.eligible_observation_count == 2
    assert result.reconciliation.role_membership_count == 3
    assert result.reconciliation.role_unique_observation_count == 2
    counts = dict(result.reconciliation.unique_observation_counts_by_resolution)
    assert counts == {
        "whole_pollen": 2,
        "ecological_group": 2,
        "ecological_subgroup": 2,
        "ecological_role": 2,
        "taxon": 2,
    }
    assert result.derivation_status == "materialized"


def test_identical_membership_is_deduplicated_without_double_counting() -> None:
    membership = _membership("observation:1", "concept:1")

    result = _derive(memberships=[membership, deepcopy(membership)])

    assert result.reconciliation.input_membership_count == 2
    assert result.reconciliation.unique_observation_count == 1
    assert result.reconciliation.duplicate_membership_count == 1
    assert result.reconciliation.eligible_observation_count == 1
    assert all(event.observation_ids == ("observation:1",) for event in result.events)


@pytest.mark.parametrize(
    ("status", "reason"),
    (
        ("unmapped", "classification_unmapped"),
        ("contested", "classification_ambiguous"),
        ("refused", "classification_ambiguous"),
        ("not_applicable", "classification_not_applicable"),
    ),
)
def test_nonaccepted_memberships_receive_explicit_refusals(
    status: str, reason: str
) -> None:
    result = _derive(
        memberships=[_membership("observation:1", "concept:1", status)],
        mappings=[],
    )

    assert not result.events
    assert [row.reason_code for row in result.refusals] == [reason]
    assert result.reconciliation.eligible_observation_count == 0
    assert result.reconciliation.refused_observation_count == 1


def test_conflicting_memberships_are_ambiguous_and_never_emit_events() -> None:
    result = _derive(
        memberships=[
            _membership("observation:1", "concept:1"),
            _membership("observation:1", "concept:2"),
        ],
        mappings=[
            _mapping("concept:1", "taxon:triticum"),
            _mapping("concept:2", "taxon:hordeum"),
        ],
    )

    assert not result.events
    assert result.refusals[0].reason_code == "ambiguous_classification_membership"
    assert result.reconciliation.unique_observation_count == 1
    assert result.reconciliation.refused_observation_count == 1


def test_source_observation_without_membership_is_never_silently_omitted() -> None:
    result = _derive(
        memberships=[], mappings=[], observations=[_observation("observation:1")]
    )

    assert not result.events
    assert result.refusals[0].reason_code == "classification_membership_missing"
    assert result.reason_codes == ("classification_membership_missing",)
    assert result.reconciliation.input_membership_count == 0
    assert result.reconciliation.input_source_observation_count == 1
    assert result.reconciliation.unique_observation_count == 1


@pytest.mark.parametrize(
    ("site", "chronology", "reason"),
    (
        (_site(latitude=None), _chronology(), "missing_or_invalid_coordinates"),
        (
            _site(),
            _chronology(
                comparability_status="context_only", younger_bp=None, older_bp=None
            ),
            "non_comparable_chronology",
        ),
        (
            _site(),
            _chronology(younger_bp=5600, older_bp=5500),
            "non_comparable_chronology",
        ),
        (
            _site(),
            _chronology(younger_bp=-1, older_bp=0),
            "non_comparable_chronology",
        ),
    ),
)
def test_missing_coordinates_and_noncomparable_time_fail_closed(
    site: dict[str, object], chronology: dict[str, object], reason: str
) -> None:
    result = _derive(sites=[site], chronologies=[chronology])

    assert not result.events
    assert result.refusals[0].reason_code == reason


def test_zero_bp_is_preserved_as_a_valid_canonical_interval() -> None:
    result = _derive(chronologies=[_chronology(younger_bp=0, older_bp=0)])

    assert result.events
    assert all(event.younger_bp == 0 and event.older_bp == 0 for event in result.events)


@pytest.mark.parametrize(
    ("mutation", "reason"),
    (
        ({"review_complete": False}, "classification_review_incomplete"),
        ({"release_eligible": False}, "classification_review_incomplete"),
        ({"reviewer_id": None}, "classification_review_incomplete"),
        ({"citation_reference_ids": []}, "classification_review_incomplete"),
        ({"citation_reference_ids": None}, "classification_review_incomplete"),
        ({"primary_group_id": None}, "classification_hierarchy_incomplete"),
        ({"mapping_version": None}, "classification_review_incomplete"),
        (
            {"classification_contract_version": "2.0.0"},
            "classification_version_mismatch",
        ),
        (
            {"primary_subgroup_id": "forest_understory"},
            "classification_hierarchy_incompatible",
        ),
        ({"role_ids": ["invented_role"]}, "classification_hierarchy_incompatible"),
    ),
)
def test_accepted_label_without_governed_evidence_is_refused(
    mutation: dict[str, object], reason: str
) -> None:
    mapping = _mapping("concept:1", "taxon:triticum")
    mapping.update(mutation)

    result = _derive(mappings=[mapping])

    assert not result.events
    assert result.refusals[0].reason_code == reason


def test_empty_production_authority_is_a_deterministic_release_refusal() -> None:
    first = _derive(memberships=[], mappings=[], observations=[])
    second = _derive(memberships=[], mappings=[], observations=[])

    assert first == second
    assert first.derivation_status == "refused"
    assert first.reason_codes == ("accepted_classification_not_available",)
    assert not first.events
    assert not first.refusals
    assert first.reconciliation.unique_observation_count == 0
    assert first.reconciliation.event_count == 0


@given(st.integers(min_value=0, max_value=2**32 - 1))
def test_input_order_does_not_change_events_reconciliation_or_digest(seed: int) -> None:
    memberships = [
        _membership("observation:1", "concept:1"),
        _membership("observation:2", "concept:2"),
    ]
    mappings = [
        _mapping("concept:1", "taxon:triticum"),
        _mapping("concept:2", "taxon:hordeum"),
    ]
    observations = [_observation("observation:1"), _observation("observation:2")]
    expected = _derive(
        memberships=memberships,
        mappings=mappings,
        observations=observations,
    )
    random.Random(seed).shuffle(memberships)
    random.Random(seed + 1).shuffle(mappings)
    random.Random(seed + 2).shuffle(observations)

    actual = _derive(
        memberships=memberships,
        mappings=mappings,
        observations=observations,
    )

    assert actual == expected
