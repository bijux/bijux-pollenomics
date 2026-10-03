"""Retain reviewed ecological concepts without stronger biological claims."""

from __future__ import annotations

import pytest

from ..test_ecological_classification import (
    _build,
    _snapshot,
)
from ..test_ecological_classification import (
    _observation as _native_observation,
)
from .support import (
    _derive,
    _mapping,
    _membership,
    _observation,
)


@pytest.mark.parametrize(
    ("label", "accepted", "rank", "group", "subgroup", "roles"),
    [
        (
            "Pinus sylvestris",
            "accepted:pinus-sylvestris",
            "species",
            "forest_woodland",
            "coniferous_trees",
            ("conifer", "arboreal"),
        ),
        (
            "Quercus sp.",
            "accepted:quercus",
            "genus",
            "forest_woodland",
            "broadleaved_deciduous_trees",
            ("broadleaved_deciduous", "arboreal"),
        ),
        (
            "Secale cereale",
            "accepted:secale-cereale",
            "species",
            "cultivated_plants",
            "cereals",
            ("direct_crop_confirmed",),
        ),
        (
            "Plantago lanceolata",
            "accepted:plantago-lanceolata",
            "species",
            "open_ground",
            "grassland_meadow",
            ("anthropogenic_indicator",),
        ),
        (
            "Rumex acetosella",
            "accepted:rumex-acetosella",
            "species",
            "open_ground",
            "open_ground_other",
            (),
        ),
    ],
    ids=["ECO-001", "ECO-002", "ECO-004", "ECO-005", "ECO-006"],
)
def test_reviewed_ecological_hierarchy_and_roles_are_preserved(
    label: str,
    accepted: str,
    rank: str,
    group: str,
    subgroup: str,
    roles: tuple[str, ...],
) -> None:
    mapping = _mapping(
        "concept:1",
        accepted,
        source_reported_name=label,
        accepted_rank=rank,
        group_id=group,
        subgroup_id=subgroup,
        roles=roles,
    )
    result = _derive(
        mappings=[mapping],
        observations=[_observation("observation:1", source_reported_name=label)],
    )
    assert not result.refusals
    assert {
        event.feature_key
        for event in result.events
        if event.resolution == "ecological_group"
    } == {"group:" + group}
    assert {
        event.feature_key
        for event in result.events
        if event.resolution == "ecological_subgroup"
    } == {"subgroup:" + subgroup}
    assert {
        event.feature_key
        for event in result.events
        if event.resolution == "ecological_role"
    } == {"role:" + role for role in roles}
    taxa = [event for event in result.events if event.resolution == "taxon"]
    assert len(taxa) == 1 and taxa[0].accepted_taxon_concept_id == accepted
    assert taxa[0].taxonomic_qualifier == "exact"
    assert result.reconciliation.eligible_observation_count == 1
    if rank == "genus":
        assert "robur" not in taxa[0].feature_key
    if group != "cultivated_plants":
        assert "role:direct_crop_confirmed" not in {
            event.feature_key for event in result.events
        }


@pytest.mark.parametrize(
    ("label", "qualifier", "rank", "roles"),
    [
        pytest.param(
            "Poaceae (Cerealia-type)",
            "type",
            "type",
            ("crop_type_qualified", "cultivated"),
            id="ECO-003",
        ),
        pytest.param(
            "cf. Avena sativa", "cf", "species", ("cultivated",), id="ECO-011"
        ),
    ],
)
def test_reviewed_qualified_crop_preserves_qualification_without_direct_crop_role(
    label: str,
    qualifier: str,
    rank: str,
    roles: tuple[str, ...],
) -> None:
    mapping = _mapping(
        "concept:1",
        "accepted:cerealia-type" if qualifier == "type" else "accepted:avena-sativa",
        source_reported_name=label,
        status="accepted_qualified",
        qualifier=qualifier,
        accepted_rank=rank,
        roles=roles,
    )
    result = _derive(
        memberships=[_membership("observation:1", "concept:1", "accepted_qualified")],
        mappings=[mapping],
        observations=[_observation("observation:1", source_reported_name=label)],
    )
    assert not result.refusals
    taxa = [event for event in result.events if event.resolution == "taxon"]
    assert len(taxa) == 1 and taxa[0].taxonomic_qualifier == qualifier
    assert {
        event.feature_key
        for event in result.events
        if event.resolution == "ecological_role"
    } == {"role:" + role for role in roles}
    assert "role:direct_crop_confirmed" not in {
        event.feature_key for event in result.events
    }


@pytest.mark.parametrize("_fixture_id", ["ECO-012-MATCH-007"])
def test_two_indicator_roles_share_one_observation_union(_fixture_id: str) -> None:
    result = _derive(
        mappings=[
            _mapping(
                "concept:1",
                "accepted:plantago",
                group_id="open_ground",
                subgroup_id="pastoral_associated",
                roles=("anthropogenic_indicator", "pastoral_indicator"),
            )
        ]
    )
    assert not result.refusals
    role_events = [
        event for event in result.events if event.resolution == "ecological_role"
    ]
    assert len(role_events) == 2
    assert {event.observation_ids for event in role_events} == {("observation:1",)}
    assert result.reconciliation.role_membership_count == 2
    assert result.reconciliation.role_unique_observation_count == 1
    assert (
        dict(result.reconciliation.unique_observation_counts_by_resolution)[
            "whole_pollen"
        ]
        == 1
    )
    assert result.reconciliation.eligible_observation_count == 1


@pytest.mark.parametrize(
    ("name", "element", "group", "expected_status"),
    [
        ("Sphagnum", "spore", "UPHE", "unmapped"),
        ("Microcharcoal", "charcoal", "UPHE", "unmapped"),
        ("Loss on ignition", "laboratory", "LABO", "not_applicable"),
    ],
    ids=["ECO-007-MATCH-008", "ECO-008", "ECO-010"],
)
def test_non_pollen_source_elements_are_retained_without_pollen_admission(
    name: str, element: str, group: str, expected_status: str
) -> None:
    native = _native_observation(
        "observation:1",
        variable_id="neotoma:variable:1",
        taxon_id=1,
        name=name,
        element=element,
        element_type=element,
        ecological_group=group,
    )
    payload = _build(_snapshot([native]))
    concept = payload["concepts"][0]
    assert concept["source_element_type"] == element
    assert concept["source_evidence_universe"] != "source_pollen"
    assert concept["mapping_status"] == expected_status
    assert concept["accepted_taxon_concept_id"] is None
    assert payload["reconciliation"]["unique_observation_count"] == 1
    mapping = _mapping("concept:1", "accepted:fixture")
    mapping["source_element_type"] = element
    observation = _observation("observation:1")
    observation["source_element_type"] = element
    derived = _derive(mappings=[mapping], observations=[observation])
    assert not derived.events
    assert derived.reconciliation.refused_observation_count == 1


@pytest.mark.parametrize("_fixture_id", ["ECO-009"])
def test_unidentified_pollen_keeps_its_accounting_denominator_without_an_invented_taxon(
    _fixture_id: str,
) -> None:
    native = _native_observation(
        "observation:unidentified",
        variable_id="neotoma:variable:1",
        taxon_id=1,
        name="Unidentified pollen",
    )
    payload = _build(_snapshot([native]))
    concept = payload["concepts"][0]
    assert concept["source_evidence_universe"] == "source_pollen"
    assert concept["accepted_taxon_concept_id"] is None
    assert concept["mapping_status"] == "unmapped"
    assert payload["reconciliation"]["unique_observation_count"] == 1
    assert payload["reconciliation"]["concept_observation_count_sum"] == 1
