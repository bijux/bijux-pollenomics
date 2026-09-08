from __future__ import annotations

import pytest

from .support import _derive, _mapping, _membership, _observation


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
