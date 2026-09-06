from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from .support import (
    EVENT_SCHEMA_PATH as _EVENT_SCHEMA_PATH,
)
from .support import (
    _chronology,
    _derive,
    _mapping,
    _membership,
    _observation,
    _site,
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
            roles=("direct_crop_confirmed", "cultivated"),
            source_variable_id="neotoma:variable:hordeum",
            source_taxon_id=2,
            source_reported_name="Hordeum",
        ),
    ]
    observations = [
        _observation("observation:1"),
        _observation(
            "observation:2",
            source_variable_id="neotoma:variable:hordeum",
            source_taxon_id=2,
            source_reported_name="Hordeum",
        ),
    ]

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


def test_published_events_validate_against_normative_json_schema() -> None:
    schema = json.loads(_EVENT_SCHEMA_PATH.read_bytes())
    validator = Draft202012Validator(schema)
    published_events = _derive().as_dict()["events"]
    assert isinstance(published_events, list)

    errors = [
        error.message
        for event in published_events
        for error in validator.iter_errors(event)
    ]

    assert not errors
    assert all(
        not {
            "measurement_semantics_id",
            "evidence_method_id",
            "method_compatibility_key",
            "subject_granularity",
            "preaggregation_valid",
            "role_membership_explicit",
            "temporal_contract_version",
        }
        & set(event)
        for event in published_events
        if isinstance(event, dict)
    )


def test_unreferenced_lookup_rows_do_not_change_observation_derived_result() -> None:
    baseline = _derive()
    unused_site = {
        **_site(),
        "site_id": "neotoma:site:unused",
        "latitude": 60.0,
    }
    unused_chronology = {
        **_chronology(),
        "chronology_claim_id": "neotoma:age-claim:unused",
        "source_record_id": "neotoma:sample:unused",
        "site_id": "neotoma:site:unused",
    }

    with_unused_lookups = _derive(
        sites=[_site(), unused_site],
        chronologies=[_chronology(), unused_chronology],
    )

    assert with_unused_lookups == baseline


def test_identical_membership_is_deduplicated_without_double_counting() -> None:
    membership = _membership("observation:1", "concept:1")

    result = _derive(memberships=[membership, deepcopy(membership)])

    assert result.reconciliation.input_membership_count == 2
    assert result.reconciliation.unique_observation_count == 1
    assert result.reconciliation.duplicate_membership_count == 1
    assert result.reconciliation.identical_duplicate_membership_count == 1
    assert result.reconciliation.conflicting_duplicate_membership_count == 0
    assert result.reconciliation.eligible_observation_count == 1
    assert all(event.observation_ids == ("observation:1",) for event in result.events)


def test_identical_duplicate_source_observation_is_counted_and_refused() -> None:
    observation = _observation("observation:1")

    result = _derive(observations=[observation, deepcopy(observation)])

    assert not result.events
    assert [row.reason_code for row in result.refusals] == [
        "duplicate_source_observation"
    ]
    assert result.reconciliation.input_source_observation_count == 2
    assert result.reconciliation.duplicate_source_observation_count == 1
    assert result.reconciliation.identical_duplicate_source_observation_count == 1
    assert result.reconciliation.unique_observation_count == 1
    assert result.reconciliation.refused_observation_count == 1


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
    assert result.reconciliation.input_membership_count == 2
    assert result.reconciliation.duplicate_membership_count == 1
    assert result.reconciliation.identical_duplicate_membership_count == 0
    assert result.reconciliation.conflicting_duplicate_membership_count == 1


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
