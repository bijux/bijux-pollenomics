from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import pytest

from .support import (
    _chronology,
    _derive,
    _mapping,
    _membership,
    _observation,
    _site,
)


def test_self_declared_review_metadata_cannot_replace_product_authority() -> None:
    authorized = _mapping("concept:1", "taxon:triticum")
    forged = deepcopy(authorized)
    forged.update(
        {
            "reviewer_id": "reviewer:forged",
            "decision_date": "2099-01-01",
            "citation_reference_ids": ["citation:forged"],
            "review_complete": True,
            "release_eligible": True,
        }
    )

    result = _derive(mappings=[forged], authority_mappings=[authorized])

    assert not result.events
    assert result.refusals[0].reason_code == "classification_mapping_not_authorized"


def test_membership_cannot_reassign_observation_to_another_authorized_mapping() -> None:
    triticum = _mapping(
        "concept:triticum",
        "taxon:triticum",
        source_variable_id="neotoma:variable:triticum",
        source_taxon_id=101,
        source_reported_name="Triticum",
    )
    hordeum = _mapping(
        "concept:hordeum",
        "taxon:hordeum",
        source_variable_id="neotoma:variable:hordeum",
        source_taxon_id=202,
        source_reported_name="Hordeum",
    )
    observation = _observation(
        "observation:1",
        source_variable_id="neotoma:variable:triticum",
        source_taxon_id=101,
        source_reported_name="Triticum",
    )
    reassigned = _membership("observation:1", "concept:hordeum")

    result = _derive(
        memberships=[reassigned],
        mappings=[triticum, hordeum],
        observations=[observation],
    )

    assert not result.events
    assert result.refusals[0].reason_code == "classification_source_identity_mismatch"


def test_shared_source_identity_across_authorized_mappings_is_ambiguous() -> None:
    concept_a = _mapping("concept:a", "taxon:triticum")
    concept_b = _mapping("concept:b", "taxon:hordeum")

    result = _derive(
        memberships=[_membership("observation:1", "concept:b")],
        mappings=[concept_a, concept_b],
    )

    assert not result.events
    assert [row.reason_code for row in result.refusals] == [
        "ambiguous_authorized_classification_mapping"
    ]
    assert result.reconciliation.eligible_observation_count == 0
    assert result.reconciliation.refused_observation_count == 1


def test_authorized_mapping_subset_cannot_hide_source_identity_ambiguity() -> None:
    concept_a = _mapping("concept:a", "taxon:triticum")
    concept_b = _mapping("concept:b", "taxon:hordeum")

    result = _derive(
        memberships=[_membership("observation:1", "concept:b")],
        mappings=[concept_b],
        authority_mappings=[concept_a, concept_b],
    )

    assert not result.events
    assert [row.reason_code for row in result.refusals] == [
        "incomplete_classification_authority_universe"
    ]


def test_extra_accepted_mapping_invalidates_authority_universe() -> None:
    authorized = _mapping("concept:a", "taxon:triticum")
    extra = _mapping("concept:extra", "taxon:hordeum")

    result = _derive(
        memberships=[_membership("observation:1", "concept:a")],
        mappings=[authorized, extra],
        authority_mappings=[authorized],
    )

    assert not result.events
    assert [row.reason_code for row in result.refusals] == [
        "extra_classification_authority_mapping"
    ]


def test_duplicate_accepted_mapping_invalidates_authority_universe() -> None:
    authorized = _mapping("concept:a", "taxon:triticum")

    result = _derive(
        memberships=[_membership("observation:1", "concept:a")],
        mappings=[authorized, deepcopy(authorized)],
        authority_mappings=[authorized],
    )

    assert not result.events
    assert [row.reason_code for row in result.refusals] == [
        "duplicate_classification_authority_mapping"
    ]


def test_conflicting_accepted_mapping_invalidates_authority_universe() -> None:
    authorized = _mapping("concept:a", "taxon:triticum")
    conflicting = {**authorized, "accepted_taxon_concept_id": "taxon:hordeum"}

    result = _derive(
        memberships=[_membership("observation:1", "concept:a")],
        mappings=[authorized, conflicting],
        authority_mappings=[authorized],
    )

    assert not result.events
    assert [row.reason_code for row in result.refusals] == [
        "conflicting_classification_authority_mapping"
    ]


@pytest.mark.parametrize(
    "mutation",
    (
        {"accepted_mapping_count": True},
        {"accepted_mapping_count": 1.0},
        {"accepted_mapping_count": "1"},
        {"accepted_mapping_count": -1},
        {"accepted_mapping_count": 0},
        {"manifest_sha256": 1},
        {"manifest_sha256": "sha256:not-a-bare-digest"},
        {"source_family": 1},
        {"source_family": " "},
        {"source_snapshot_id": 1},
        {"source_snapshot_id": "invalid"},
        {"build_id": 1},
        {"build_id": "invalid"},
        {"contract_version": 1},
        {"contract_version": " "},
        {"contract_digest": 1},
        {"contract_digest": "invalid"},
        {"producer_id": 1},
        {"producer_id": " "},
        {"producer_version": 1},
        {"producer_version": " "},
        {"producer_digest": 1},
        {"producer_digest": "invalid"},
        {"accepted_mapping_sha256_by_concept": []},
        {"accepted_mapping_sha256_by_concept": None},
        {"accepted_mapping_sha256_by_concept": "concept:1"},
        {"accepted_mapping_sha256_by_concept": (["concept:1", f"sha256:{'a' * 64}"],)},
        {"accepted_mapping_sha256_by_concept": (("concept:1",),)},
        {
            "accepted_mapping_sha256_by_concept": (
                ("concept:1", f"sha256:{'a' * 64}", "extra"),
            )
        },
        {"accepted_mapping_sha256_by_concept": ((1, f"sha256:{'a' * 64}"),)},
        {"accepted_mapping_sha256_by_concept": ((" ", f"sha256:{'a' * 64}"),)},
        {"accepted_mapping_sha256_by_concept": (("concept:1", 1),)},
        {"accepted_mapping_sha256_by_concept": (("concept:1", "invalid"),)},
    ),
)
def test_malformed_authority_receipt_fails_closed_without_runtime_coercion(
    mutation: dict[str, object],
) -> None:
    result = _derive(authority_overrides=mutation)

    assert not result.events
    assert [row.reason_code for row in result.refusals] == [
        "invalid_classification_authority_receipt"
    ]
    assert result.reason_codes == ("invalid_classification_authority_receipt",)
    assert isinstance(result.classification_authority_manifest_sha256, str)


def test_duplicate_concepts_in_authority_receipt_fail_closed() -> None:
    mapping = _mapping("concept:1", "taxon:triticum")
    digest = (
        "sha256:"
        + hashlib.sha256(
            json.dumps(mapping, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )

    result = _derive(
        authority_overrides={
            "accepted_mapping_count": 2,
            "accepted_mapping_sha256_by_concept": (
                ("concept:1", digest),
                ("concept:1", digest),
            ),
        }
    )

    assert not result.events
    assert [row.reason_code for row in result.refusals] == [
        "invalid_classification_authority_receipt"
    ]


def test_mixed_mapping_version_is_refused_against_context_crosswalk() -> None:
    memberships = [
        _membership("observation:1", "concept:1"),
        _membership("observation:2", "concept:2"),
    ]
    mappings = [
        _mapping("concept:1", "taxon:triticum"),
        _mapping("concept:2", "taxon:hordeum", mapping_version="other-crosswalk.v1"),
    ]

    result = _derive(
        memberships=memberships,
        mappings=mappings,
        observations=[_observation("observation:1"), _observation("observation:2")],
    )

    assert result.derivation_status == "materialized_with_refusals"
    assert {row.observation_id for row in result.refusals} == {"observation:2"}
    assert result.refusals[0].reason_code == "classification_mapping_version_mismatch"
    assert all(event.observation_ids == ("observation:1",) for event in result.events)
    assert result.context.mapping_version == "neotoma-crosswalk.v1"


def test_product_zero_accepted_receipt_rejects_coherent_fabricated_mapping() -> None:
    result = _derive(use_product_authority=True)

    assert not result.events
    assert result.refusals[0].reason_code == "classification_mapping_not_authorized"


def test_source_lineage_cannot_substitute_for_authority_snapshot_and_build() -> None:
    observation = _observation("observation:1")
    site = _site()
    chronology = _chronology()
    for record in (observation, site, chronology):
        record["source_snapshot_id"] = f"sha256:{'d' * 64}"
        record["build_id"] = f"sha256:{'e' * 64}"

    result = _derive(
        observations=[observation], sites=[site], chronologies=[chronology]
    )

    assert not result.events
    assert result.refusals[0].reason_code == "classification_authority_lineage_mismatch"


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
