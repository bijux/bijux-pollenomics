"""Explicitly reviewed synthetic context categories retain scientific boundaries."""

from copy import deepcopy
from typing import cast

import pytest

from bijux_pollenomics.analysis.classification.events import (
    assess_classification_eligibility,
)
from bijux_pollenomics.analysis.classification.review import (
    assess_reviewed_context,
)
from bijux_pollenomics.evidence.classification.audit_outputs.queues import queue_row

from .test_classification_events.support import (
    _derive,
    _mapping,
    _membership,
    _observation,
)
from .test_classification_events.test_eligibility import _context, _fixture_authority

# These declarations are reviewed contract examples, not admitted provider
# records or a native-name crosswalk. Product authority remains empty.
_CONTEXT_CASES: list[tuple[str, str, str, str, bool]] = [
    ("Sphagnum spore", "spore", "non_pollen_evidence", "spores", False),
    ("Microcharcoal", "charcoal", "charcoal_combustion", "microcharcoal", False),
    ("Unidentified pollen", "pollen", "other_pollen", "taxon_unidentified", True),
    (
        "Loss on ignition",
        "laboratory",
        "laboratory_or_excluded",
        "laboratory_measurement",
        False,
    ),
]


def _context_mapping(
    name: str, element: str, group: str, subgroup: str, *, concept: str = "concept:1"
) -> dict[str, object]:
    mapping = _mapping(
        concept,
        "unused",
        source_reported_name=name,
        group_id=group,
        subgroup_id=subgroup,
        roles=(),
        status="accepted_qualified",
        qualifier="unknown",
    )
    mapping.update(
        source_element_type=element,
        source_taxon_id=None if group == "other_pollen" else 1,
        accepted_taxon_concept_id=None,
        accepted_rank=None,
        crosswalk_version=mapping["mapping_version"],
        evidence_reference_ids=mapping["citation_reference_ids"],
        observation_count=1,
    )
    projected = queue_row(mapping)
    mapping["review_complete"] = projected["review_complete"]
    mapping["context_review_complete"] = projected["context_review_complete"]
    mapping["context_release_eligible"] = projected["context_release_eligible"]
    mapping["release_eligible"] = projected["release_eligible"]
    return mapping


def _context_observation(
    mapping: dict[str, object], observation_id: str = "observation:1"
) -> dict[str, object]:
    return {
        **_observation(observation_id),
        **{
            field: mapping[field]
            for field in (
                "source_variable_id",
                "source_taxon_id",
                "source_reported_name",
                "source_element_type",
            )
        },
        "source_unit": "native-unit",
        "source_value": 9007199254740993,
    }


def _assess(
    mappings: list[dict[str, object]],
    observations: list[dict[str, object]],
    memberships: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return assess_reviewed_context(
        classification_mappings=mappings,
        observations=observations,
        observation_memberships=memberships
        if memberships is not None
        else [
            _membership(
                str(row["observation_id"]),
                str(mapping["classification_concept_id"]),
                str(mapping["mapping_status"]),
            )
            for mapping, row in zip(mappings, observations, strict=True)
        ],
        context=_context(),
    ).as_dict()


def _rows(payload: dict[str, object]) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], payload["rows"])


@pytest.mark.parametrize(
    ("name", "element", "group", "subgroup", "pollen"),
    _CONTEXT_CASES,
    ids=["ECO007", "ECO008", "ECO009", "ECO010"],
)
def test_reviewed_context_retains_positive_category_without_a_taxon_or_event(
    name: str, element: str, group: str, subgroup: str, pollen: bool
) -> None:
    mapping = _context_mapping(name, element, group, subgroup)
    observation = _context_observation(mapping)
    original = deepcopy((mapping, observation))
    assert mapping["context_review_complete"] is True
    assert mapping["review_complete"] is False
    assert mapping["release_eligible"] is False
    assert mapping["context_release_eligible"] is True
    with _fixture_authority([mapping]):
        payload = _assess([mapping], [observation])
        old_review = assess_classification_eligibility(
            classification_mappings=[mapping],
            observations=[observation],
            observation_memberships=[
                _membership("observation:1", "concept:1", "accepted_qualified")
            ],
            context=_context(),
        ).as_dict()
    row = _rows(payload)[0]
    assert row["review_eligibility"] == "eligible"
    assert row["participates_in_whole_pollen_category"] is pollen
    assert payload["category_counts"] == [
        {
            "primary_group_id": group,
            "primary_subgroup_id": subgroup,
            "unique_observation_count": 1,
        }
    ]
    assert payload["whole_pollen_category_observation_count"] == int(pollen)
    assert payload["scope"] == "reviewed_source_context_only"
    assert "pollen_event_admission" in cast(list[str], payload["unassessed"])
    native = cast(dict[str, object], row["source_observation"])
    assert native == observation
    assert native["source_taxon_id"] == mapping["source_taxon_id"]
    if group == "other_pollen":
        assert native["source_taxon_id"] is None
    assert type(native["source_value"]) is int
    reviewed = cast(dict[str, object], row["classification_mapping"])
    assert reviewed["accepted_taxon_concept_id"] is None
    assert _rows(old_review)[0]["review_eligibility"] == "refused"
    derived = _derive(
        mappings=[mapping],
        observations=[observation],
        memberships=[_membership("observation:1", "concept:1", "accepted_qualified")],
    )
    assert not derived.events and derived.reconciliation.refused_observation_count == 1
    assert (mapping, observation) == original


@pytest.mark.parametrize("measurement", [0, None, "absent"])
def test_context_review_preserves_measurement_absence(measurement: object) -> None:
    mapping = _context_mapping(*_CONTEXT_CASES[2][:4])
    observation = _context_observation(mapping)
    if measurement == "absent":
        observation.pop("source_value")
    else:
        observation["source_value"] = measurement
    with _fixture_authority([mapping]):
        payload = _assess([mapping], [observation])
    assert (
        cast(dict[str, object], _rows(payload)[0]["source_observation"]) == observation
    )
    assert payload["whole_pollen_category_observation_count"] == 1


def test_context_union_accounts_missing_duplicates_and_unmapped_without_inflation() -> (
    None
):
    mappings = [
        _context_mapping(*case[:4], concept=f"concept:{index}")
        for index, case in enumerate(_CONTEXT_CASES)
    ]
    observations = [
        _context_observation(mapping, f"observation:{index}")
        for index, mapping in enumerate(mappings)
    ]
    memberships = [
        _membership(f"observation:{index}", f"concept:{index}", "accepted_qualified")
        for index in range(4)
    ]
    observations.extend([deepcopy(observations[0]), _observation("unmapped")])
    memberships.append(_membership("missing", "concept:0", "accepted_qualified"))
    with _fixture_authority(mappings):
        payload = _assess(mappings, observations, memberships)
        reverse = _assess(
            list(reversed(mappings)),
            list(reversed(observations)),
            list(reversed(memberships)),
        )
    assert payload == reverse
    counts = cast(dict[str, int], payload["reconciliation"])
    assert counts["unique_observation_count"] == 6
    assert (
        counts["eligible_observation_count"] == counts["refused_observation_count"] == 3
    )
    assert payload["whole_pollen_category_observation_count"] == 1
    assert (
        sum(
            cast(int, category["unique_observation_count"])
            for category in cast(list[dict[str, object]], payload["category_counts"])
        )
        == 3
    )
    assert {
        row["observation_id"]: row["reason_code"]
        for row in _rows(payload)
        if row["review_eligibility"] == "refused"
    } == {
        "observation:0": "duplicate_source_observation",
        "unmapped": "classification_membership_missing",
        "missing": "missing_source_observation",
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("reviewer_id", None),
        ("context_review_complete", False),
        ("context_release_eligible", False),
        ("citation_reference_ids", []),
        ("source_element_type", "pollen"),
        ("source_element_type", "charcoal"),
        ("source_element_type", "unknown"),
        ("accepted_taxon_concept_id", "invented:taxon"),
        ("accepted_taxon_name", "Invented accepted name"),
        ("accepted_rank", "species"),
        ("role_ids", ["direct_crop_confirmed"]),
    ],
)
def test_reviewed_context_refuses_incomplete_or_incompatible_review(
    field: str, value: object
) -> None:
    mapping = _context_mapping(*_CONTEXT_CASES[0][:4])
    mapping[field] = value
    with _fixture_authority([mapping]):
        payload = _assess([mapping], [_context_observation(mapping)])
    assert _rows(payload)[0]["review_eligibility"] == "refused"
    assert not payload["category_counts"]
    assert payload["whole_pollen_category_observation_count"] == 0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_taxon_id", False),
        ("source_reported_name", "substituted"),
        ("source_snapshot_id", "sha256:" + "c" * 64),
        ("build_id", "sha256:" + "c" * 64),
    ],
)
def test_context_authority_requires_exact_native_identity_and_lineage(
    field: str, value: object
) -> None:
    mapping = _context_mapping(*_CONTEXT_CASES[0][:4])
    observation = {**_context_observation(mapping), field: value}
    with _fixture_authority([mapping]):
        payload = _assess([mapping], [observation])
    assert _rows(payload)[0]["review_eligibility"] == "refused"


def test_no_product_authority_or_incomplete_universe_cannot_create_context_review() -> (
    None
):
    mapping = _context_mapping(*_CONTEXT_CASES[0][:4])
    assert (
        _rows(_assess([mapping], [_context_observation(mapping)]))[0][
            "review_eligibility"
        ]
        == "refused"
    )
    other = _context_mapping(*_CONTEXT_CASES[1][:4], concept="concept:other")
    with _fixture_authority([mapping, other]):
        assert (
            _rows(_assess([mapping], [_context_observation(mapping)]))[0]["reason_code"]
            == "incomplete_classification_authority_universe"
        )


def test_ambiguous_context_concepts_for_one_native_identity_are_refused() -> None:
    mapping = _context_mapping(*_CONTEXT_CASES[0][:4])
    other = {**mapping, "classification_concept_id": "concept:other"}
    with _fixture_authority([mapping, other]):
        payload = _assess(
            [mapping, other],
            [
                _context_observation(mapping),
                _context_observation(other, "observation:other"),
            ],
        )
    assert all(
        row["reason_code"] == "ambiguous_authorized_classification_mapping"
        for row in _rows(payload)
    )


def test_crop_and_indicator_display_retains_separate_counts_and_qualified_wording() -> (
    None
):
    direct = _mapping("direct", "fixture:secale", roles=("direct_crop_confirmed",))
    qualified = _mapping(
        "qualified",
        "fixture:cerealia-type",
        source_variable_id="fixture:qualified",
        roles=("crop_type_qualified",),
        status="accepted_qualified",
        qualifier="type",
        accepted_rank="type",
    )
    indicators = _mapping(
        "indicators",
        "fixture:plantago",
        source_variable_id="fixture:indicator",
        group_id="open_ground",
        subgroup_id="pastoral_associated",
        roles=("anthropogenic_indicator", "pastoral_indicator"),
    )
    mappings = [direct, qualified, indicators]
    observations = [
        _context_observation(mapping, str(mapping["classification_concept_id"]))
        for mapping in mappings
    ]
    with _fixture_authority(mappings):
        payload = _assess(mappings, observations)
    totals = cast(list[dict[str, object]], payload["crop_indicator_totals"])
    assert [
        (row["role_id"], row["label"], row["unique_observation_count"])
        for row in totals
    ] == [
        ("direct_crop_confirmed", "Direct crop taxon evidence", 1),
        ("crop_type_qualified", "Qualified crop-type evidence", 1),
        ("anthropogenic_indicator", "Anthropogenic or land-use indicator", 1),
        ("pastoral_indicator", "Pastoral-associated indicator", 1),
        (
            "ruderal_disturbance_indicator",
            "Ruderal or disturbance-associated indicator",
            0,
        ),
    ]
    assert all(row["pollen_alone_proves"] is False for row in totals)
    assert payload["crop_indicator_union_observation_count"] == 3
    assert sum(cast(int, row["unique_observation_count"]) for row in totals) == 4
    assert payload["whole_pollen_category_observation_count"] == 3
    row = next(row for row in _rows(payload) if row["observation_id"] == "qualified")
    display = cast(list[dict[str, object]], row["role_display"])[0]
    assert display["taxonomic_qualifier"] == "type"
    assert display["unproven_claim"] == "local cultivation"


@pytest.mark.parametrize(
    ("mapping_has_taxon", "source_has_taxon"),
    [(False, True), (True, False), (False, False)],
)
def test_native_null_and_absent_taxon_identifiers_remain_distinct(
    mapping_has_taxon: bool, source_has_taxon: bool
) -> None:
    mapping = _context_mapping(*_CONTEXT_CASES[2][:4])
    observation = _context_observation(mapping)
    assert mapping["source_taxon_id"] is observation["source_taxon_id"] is None
    if not mapping_has_taxon:
        mapping.pop("source_taxon_id")
    if not source_has_taxon:
        observation.pop("source_taxon_id")
    with _fixture_authority([mapping]):
        payload = _assess([mapping], [observation])
    row = _rows(payload)[0]
    expected = mapping_has_taxon == source_has_taxon
    assert (row["review_eligibility"] == "eligible") is expected
    assert payload["whole_pollen_category_observation_count"] == int(expected)
    assert (row["reason_code"] is None) is expected
    if not expected:
        assert row["reason_code"] == "classification_source_identity_mismatch"
    native = cast(dict[str, object], row["source_observation"])
    reviewed = cast(dict[str, object], row["classification_mapping"])
    assert ("source_taxon_id" in native) is source_has_taxon
    assert ("source_taxon_id" in reviewed) is mapping_has_taxon
    assert reviewed["accepted_taxon_concept_id"] is None


@pytest.mark.parametrize("flag", [True, False, 1, 0, "true", "false", None])
def test_context_release_requires_explicit_boolean_authority(flag: object) -> None:
    concept = {
        "classification_concept_id": "context:unidentified",
        "mapping_status": "accepted_qualified",
        "taxonomic_qualifier": "unknown",
        "source_element_type": "pollen",
        "primary_group_id": "other_pollen",
        "primary_subgroup_id": "taxon_unidentified",
        "accepted_taxon_concept_id": None,
        "accepted_taxon_name": None,
        "accepted_rank": None,
        "crosswalk_version": "fixture:review",
        "reviewer_id": "fixture:reviewer",
        "decision_date": "2026-10-03",
        "evidence_reference_ids": ["fixture:citation"],
        "role_ids": [],
        "observation_count": 1,
        "release_eligible": flag,
    }
    original = deepcopy(concept)
    row = queue_row(concept)
    assert row["context_review_complete"] is True
    assert row["context_release_eligible"] is (flag is True)
    assert row["review_complete"] is False
    assert row["release_eligible"] is False
    assert concept == original
