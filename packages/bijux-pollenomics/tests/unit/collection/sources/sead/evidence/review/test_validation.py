from __future__ import annotations

from collections.abc import Callable
import copy
import json
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.sead.evidence.review.validation import (
    validate_sead_scientific_classification_review,
)
from tests.support.repository import REPOSITORY_ROOT

pytestmark = pytest.mark.generated_artifacts

_PACKET_PATH = (
    REPOSITORY_ROOT / "data/sead/review/scientific_classification_review.json"
)
JsonObject = dict[str, object]
Mutation = Callable[[JsonObject], None]


@pytest.fixture(scope="module")
def packet() -> JsonObject:
    """Load the checked-in review packet once for adversarial validation."""
    value = json.loads(_PACKET_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return cast(JsonObject, value)


def _mapping(value: object) -> JsonObject:
    assert isinstance(value, dict)
    return cast(JsonObject, value)


def _rows(value: object) -> list[JsonObject]:
    assert isinstance(value, list)
    assert all(isinstance(row, dict) for row in value)
    return cast(list[JsonObject], value)


def _change_lineage(packet: JsonObject) -> None:
    _mapping(packet["lineage"])["source_run_id"] = "coordinated-but-ungoverned"


def _accept_posture(packet: JsonObject) -> None:
    _mapping(packet["review_posture"])["accepted_mapping_count"] = 1


def _prefill_candidate(packet: JsonObject) -> None:
    _rows(packet["candidates"])[0]["proposed_accepted_taxon_concept_id"] = "taxon:1"


def _permit_candidate_propagation(packet: JsonObject) -> None:
    _rows(packet["candidates"])[0]["propagation_allowed"] = True


def _add_hidden_acceptance(packet: JsonObject) -> None:
    _rows(packet["candidates"])[0]["accepted_taxon_concept_id"] = "taxon:1"


def _misclassify_review_priority(packet: JsonObject) -> None:
    candidates = _rows(packet["candidates"])
    candidate = next(
        row
        for row in candidates
        if row["source_ecocode_count"]
        and row["review_priority"] == "source_taxon_candidate"
    )
    candidate["review_priority"] = "plant_ecocode_candidate"


def _coordinate_false_ecocode_total(packet: JsonObject) -> None:
    inventory = _mapping(packet["ecocode_inventory"])
    systems = _rows(inventory["systems"])
    systems[0]["ecocode_row_count"] = 2_534
    systems[1]["ecocode_row_count"] = 6_553


def _change_citation_authority(packet: JsonObject) -> None:
    citation = _mapping(packet["citation_audit"])
    plant = _rows(citation["systems"])[2]
    plant["citation_title"] = "Arnolds and van der Maarel plant authority"


def _flatten_nested_chronology_reason(packet: JsonObject) -> None:
    chronology = _mapping(packet["chronology_authority_gaps"])
    reasons = _mapping(chronology["refusal_reason_counts"])
    reasons["chronology_not_comparable"] = (
        sum(
            cast(int, reasons[key])
            for key in (
                "analysis_entity_age_basis_unspecified",
                "geochronology_calibration_posture_unknown",
                "relative_period_requires_governed_mapping",
            )
        )
        + 1
    )


def _change_event_refusal_overlap(packet: JsonObject) -> None:
    events = _mapping(packet["event_refusal_posture"])
    reasons = _mapping(events["refusal_reason_counts"])
    reasons["source_taxon_unavailable"] = 154_106


@pytest.mark.parametrize(
    "mutation",
    [
        _change_lineage,
        _accept_posture,
        _prefill_candidate,
        _permit_candidate_propagation,
        _add_hidden_acceptance,
        _misclassify_review_priority,
        _coordinate_false_ecocode_total,
        _change_citation_authority,
        _flatten_nested_chronology_reason,
        _change_event_refusal_overlap,
    ],
)
def test_review_validation_rejects_coordinated_false_claims(
    packet: JsonObject,
    mutation: Mutation,
) -> None:
    candidate = copy.deepcopy(packet)
    mutation(candidate)

    with pytest.raises((TypeError, ValueError)):
        validate_sead_scientific_classification_review(candidate)


def test_checked_in_packet_is_valid_and_entirely_pending(packet: JsonObject) -> None:
    validate_sead_scientific_classification_review(packet)

    candidates = _rows(packet["candidates"])
    assert len(candidates) == 1_974
    assert all(
        row["review_status"] == "pending_qualified_scientific_review"
        for row in candidates
    )
    assert all(
        row["current_classification_status"] == "not_accepted" for row in candidates
    )
    assert all(row["propagation_allowed"] is False for row in candidates)
