from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json

from tests.support.repository import REPOSITORY_ROOT
import random
from typing import Any
from unittest.mock import patch

from hypothesis import given
from hypothesis import strategies as st
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
import pytest

from bijux_pollenomics.analysis import (
    classification_events as classification_events_module,
)
from bijux_pollenomics.analysis.classification_events import (
    ClassificationEventContext,
    ClassificationEventDerivationResult,
    derive_classification_events,
)

_REPOSITORY_ROOT = REPOSITORY_ROOT
_EVENT_SCHEMA_PATH = (
    _REPOSITORY_ROOT.parent
    / "bijux-pollenomics-execution-control/contracts/phenomenon-event.schema.json"
)


def _context(**overrides: str) -> ClassificationEventContext:
    values = {
        "source_family": "neotoma",
        "classification_contract_version": "1.0.0",
        "mapping_version": "neotoma-crosswalk.v1",
        "threshold_profile_id": "reported-positive.v1",
        "config_digest": f"sha256:{'c' * 64}",
        "producer_version": "classification-events.v1",
    }
    values.update(overrides)
    return ClassificationEventContext(**values)


def _membership(
    observation_id: str, concept_id: str, status: str = "accepted"
) -> dict[str, object]:
    return {
        "observation_id": observation_id,
        "classification_concept_id": concept_id,
        "mapping_status": status,
        "source_family": "neotoma",
        "classification_contract_version": "1.0.0",
        "source_country_code": "SE",
        "governed_country_code": "SE",
    }


def _mapping(
    concept_id: str,
    taxon_id: str,
    *,
    group_id: str = "cultivated_plants",
    subgroup_id: str = "cereals",
    roles: tuple[str, ...] = ("direct_crop_confirmed",),
    status: str = "accepted",
    qualifier: str = "exact",
    source_variable_id: str = "neotoma:variable:fixture",
    source_taxon_id: object = 1,
    source_reported_name: str = "Fixture pollen",
    mapping_version: str = "neotoma-crosswalk.v1",
    accepted_rank: str = "species",
) -> dict[str, object]:
    return {
        "classification_concept_id": concept_id,
        "source_family": "neotoma",
        "source_variable_id": source_variable_id,
        "source_taxon_id": source_taxon_id,
        "source_reported_name": source_reported_name,
        "source_element_type": "pollen",
        "mapping_status": status,
        "accepted_taxon_concept_id": taxon_id,
        "taxonomic_qualifier": qualifier,
        "primary_group_id": group_id,
        "primary_subgroup_id": subgroup_id,
        "role_ids": list(roles),
        "accepted_rank": accepted_rank,
        "classification_confidence": "high",
        "mapping_version": mapping_version,
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
    source_variable_id: str = "neotoma:variable:fixture",
    source_taxon_id: object = 1,
    source_reported_name: str = "Fixture pollen",
) -> dict[str, object]:
    return {
        "observation_id": observation_id,
        "sample_id": sample_id,
        "site_id": site_id,
        "country_code": "SE",
        "source_family": "neotoma",
        "source_variable_id": source_variable_id,
        "source_taxon_id": source_taxon_id,
        "source_reported_name": source_reported_name,
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
    context: ClassificationEventContext | None = None,
    authority_mappings: list[dict[str, object]] | None = None,
    authority_overrides: dict[str, object] | None = None,
    use_product_authority: bool = False,
) -> ClassificationEventDerivationResult:
    resolved_mappings = (
        mappings if mappings is not None else [_mapping("concept:1", "taxon:triticum")]
    )
    resolved_context = context if context is not None else _context()

    def invoke() -> ClassificationEventDerivationResult:
        return derive_classification_events(
            observation_memberships=(
                memberships
                if memberships is not None
                else [_membership("observation:1", "concept:1")]
            ),
            classification_mappings=resolved_mappings,
            observations=(
                observations
                if observations is not None
                else [_observation("observation:1")]
            ),
            sites=sites if sites is not None else [_site()],
            chronologies=chronologies if chronologies is not None else [_chronology()],
            context=resolved_context,
        )

    if use_product_authority:
        return invoke()
    authorized = (
        authority_mappings if authority_mappings is not None else resolved_mappings
    )
    entries = tuple(
        sorted(
            (
                str(mapping["classification_concept_id"]),
                "sha256:"
                + hashlib.sha256(
                    json.dumps(mapping, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            )
            for mapping in authorized
        )
    )
    manifest_sha256 = hashlib.sha256(
        json.dumps(
            {
                "source_family": resolved_context.source_family,
                "contract_version": resolved_context.classification_contract_version,
                "entries": entries,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    authority = replace(
        classification_events_module._CLASSIFICATION_AUTHORITY,
        manifest_sha256=manifest_sha256,
        source_family=resolved_context.source_family,
        source_snapshot_id=f"sha256:{'a' * 64}",
        build_id=f"sha256:{'b' * 64}",
        contract_version=resolved_context.classification_contract_version,
        accepted_mapping_count=len(entries),
        accepted_mapping_sha256_by_concept=entries,
    )
    if authority_overrides is not None:
        for field_name, value in authority_overrides.items():
            object.__setattr__(authority, field_name, value)
    with patch.object(
        classification_events_module, "_CLASSIFICATION_AUTHORITY", authority
    ):
        return invoke()


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


@pytest.mark.parametrize(
    ("mutation", "reason"),
    (
        ({"review_complete": False}, "classification_review_incomplete"),
        ({"release_eligible": False}, "classification_review_incomplete"),
        ({"reviewer_id": None}, "classification_review_incomplete"),
        ({"citation_reference_ids": []}, "classification_review_incomplete"),
        ({"citation_reference_ids": None}, "classification_review_incomplete"),
        ({"primary_group_id": None}, "classification_hierarchy_incomplete"),
        ({"mapping_version": None}, "classification_mapping_version_mismatch"),
        ({"source_variable_id": None}, "classification_source_identity_incomplete"),
        ({"source_taxon_id": None}, "classification_source_identity_incomplete"),
        ({"source_taxon_id": True}, "classification_source_identity_incomplete"),
        ({"source_reported_name": None}, "classification_source_identity_incomplete"),
        (
            {"source_element_type": "charcoal"},
            "classification_source_identity_incomplete",
        ),
        ({"accepted_rank": None}, "classification_source_identity_incomplete"),
        ({"classification_confidence": None}, "classification_confidence_invalid"),
        (
            {"classification_confidence": "unresolved"},
            "classification_confidence_invalid",
        ),
        ({"classification_contract_version": None}, "classification_version_mismatch"),
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


@pytest.mark.parametrize("record", ("membership", "mapping", "observation"))
def test_every_classification_source_family_is_bound_to_context(record: str) -> None:
    membership = _membership("observation:1", "concept:1")
    mapping = _mapping("concept:1", "taxon:triticum")
    observation = _observation("observation:1")
    selected = {
        "membership": membership,
        "mapping": mapping,
        "observation": observation,
    }[record]
    selected["source_family"] = "sead"

    result = _derive(
        memberships=[membership], mappings=[mapping], observations=[observation]
    )

    assert not result.events
    assert result.refusals[0].reason_code == (
        "source_lineage_mismatch"
        if record == "observation"
        else "classification_source_family_mismatch"
    )


def test_membership_contract_version_is_required() -> None:
    membership = _membership("observation:1", "concept:1")
    membership.pop("classification_contract_version")

    result = _derive(memberships=[membership])

    assert not result.events
    assert result.refusals[0].reason_code == "classification_version_mismatch"


@pytest.mark.parametrize(
    ("status", "qualifier"),
    (("accepted", "type"), ("accepted_qualified", "exact")),
)
def test_mapping_status_cannot_masquerade_as_an_incompatible_qualifier(
    status: str, qualifier: str
) -> None:
    result = _derive(
        memberships=[_membership("observation:1", "concept:1", status)],
        mappings=[
            _mapping(
                "concept:1",
                "taxon:triticum",
                status=status,
                qualifier=qualifier,
                roles=(),
            )
        ],
    )

    assert not result.events
    assert result.refusals[0].reason_code == "classification_qualifier_status_mismatch"


def test_qualified_crop_type_requires_a_qualified_mapping() -> None:
    result = _derive(
        memberships=[_membership("observation:1", "concept:1", "accepted_qualified")],
        mappings=[
            _mapping(
                "concept:1",
                "taxon:cerealia-type",
                status="accepted_qualified",
                qualifier="type",
                accepted_rank="type",
                roles=("crop_type_qualified", "cultivated"),
            )
        ],
    )

    assert result.events


def test_qualified_source_identity_cannot_be_promoted_to_species_rank() -> None:
    result = _derive(
        memberships=[_membership("observation:1", "concept:1", "accepted_qualified")],
        mappings=[
            _mapping(
                "concept:1",
                "taxon:cerealia-type",
                status="accepted_qualified",
                qualifier="type",
                accepted_rank="species",
                roles=("crop_type_qualified",),
            )
        ],
    )

    assert not result.events
    assert result.refusals[0].reason_code == "classification_rank_qualifier_mismatch"


def test_group_qualified_mapping_does_not_leak_into_taxon_events() -> None:
    result = _derive(
        memberships=[_membership("observation:1", "concept:1", "accepted_qualified")],
        mappings=[
            _mapping(
                "concept:1",
                "taxon:poaceae-group",
                status="accepted_qualified",
                qualifier="group",
                accepted_rank="group",
                roles=(),
            )
        ],
    )

    assert result.events
    assert {event.resolution for event in result.events} == {
        "whole_pollen",
        "ecological_group",
        "ecological_subgroup",
    }
    assert (
        dict(result.reconciliation.unique_observation_counts_by_resolution)["taxon"]
        == 0
    )


def test_nordic_source_and_governed_country_conflict_is_explicitly_refused() -> None:
    membership = _membership("observation:1", "concept:1")
    membership["source_country_code"] = "DK"

    result = _derive(memberships=[membership])

    assert not result.events
    assert result.refusals[0].reason_code == "source_governed_country_conflict"
    assert dict(result.reconciliation.source_governed_country_relation_counts) == {
        "DK->SE": 1
    }


def test_unreported_source_country_can_use_governed_country_with_accounting() -> None:
    membership = _membership("observation:1", "concept:1")
    membership["source_country_code"] = "UNASSIGNED"

    result = _derive(memberships=[membership])

    assert result.events
    assert dict(result.reconciliation.source_governed_country_relation_counts) == {
        "UNASSIGNED->SE": 1
    }


@pytest.mark.parametrize(
    ("group_id", "subgroup_id", "roles"),
    (
        (
            "cultivated_plants",
            "cereals",
            ("direct_crop_confirmed", "anthropogenic_indicator"),
        ),
        ("cultivated_plants", "cereals", ("arboreal",)),
        ("open_ground", "pastoral_associated", ("ruderal_disturbance_indicator",)),
    ),
)
def test_roles_cannot_invent_incompatible_hierarchy_or_evidence_classes(
    group_id: str, subgroup_id: str, roles: tuple[str, ...]
) -> None:
    result = _derive(
        mappings=[
            _mapping(
                "concept:1",
                "taxon:fixture",
                group_id=group_id,
                subgroup_id=subgroup_id,
                roles=roles,
            )
        ]
    )

    assert not result.events
    assert result.refusals[0].reason_code == "classification_role_incompatible"


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


def test_empty_result_digest_is_bound_to_full_derivation_context() -> None:
    baseline = _derive(memberships=[], mappings=[], observations=[])
    variants = (
        _context(source_family="sead"),
        _context(mapping_version="neotoma-crosswalk.v2"),
        _context(threshold_profile_id="reported-positive.v2"),
        _context(config_digest=f"sha256:{'d' * 64}"),
        _context(producer_version="classification-events.v2"),
    )

    variant_digests = {
        _derive(
            memberships=[], mappings=[], observations=[], context=context
        ).result_digest
        for context in variants
    }

    assert baseline.context == _context()
    assert baseline.classification_authority_manifest_sha256
    assert baseline.result_digest not in variant_digests
    assert len(variant_digests) == len(variants)


@given(st.integers(min_value=0, max_value=2**32 - 1))
def test_input_order_does_not_change_events_reconciliation_or_digest(seed: int) -> None:
    memberships = [
        _membership("observation:1", "concept:1"),
        _membership("observation:2", "concept:2"),
    ]
    mappings = [
        _mapping("concept:1", "taxon:triticum"),
        _mapping(
            "concept:2",
            "taxon:hordeum",
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
