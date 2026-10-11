from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json
from typing import cast
from unittest.mock import patch

import pytest

from bijux_pollenomics.analysis.classification.events import (
    ClassificationReviewContext,
    assess_classification_eligibility,
    authority,
)

from .support import _derive, _mapping, _membership, _observation


def _context() -> ClassificationReviewContext:
    return ClassificationReviewContext("neotoma", "1.0.0", "neotoma-crosswalk.v1")


@contextmanager
def _fixture_authority(mappings: list[dict[str, object]]) -> Iterator[None]:
    entries = tuple(
        sorted(
            (
                str(row["classification_concept_id"]),
                "sha256:"
                + hashlib.sha256(
                    json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            )
            for row in mappings
        )
    )
    receipt = replace(
        authority._CLASSIFICATION_AUTHORITY,
        source_snapshot_id=f"sha256:{'a' * 64}",
        build_id=f"sha256:{'b' * 64}",
        accepted_mapping_count=len(entries),
        accepted_mapping_sha256_by_concept=entries,
    )
    with patch.object(authority, "_CLASSIFICATION_AUTHORITY", receipt):
        yield


def _review(
    observations: list[dict[str, object]],
    *,
    memberships: list[dict[str, object]] | None = None,
    mappings: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return assess_classification_eligibility(
        observation_memberships=(
            memberships
            if memberships is not None
            else [
                _membership(str(row["observation_id"]), "concept:1")
                for row in observations
            ]
        ),
        classification_mappings=mappings
        if mappings is not None
        else [_mapping("concept:1", "taxon:1")],
        observations=observations,
        context=_context(),
    ).as_dict()


def _rows(payload: dict[str, object]) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], payload["rows"])


@pytest.mark.parametrize("value", [0, 0.0, None, -1, 9007199254740993])
def test_review_preserves_native_value_without_admitting_a_detection(
    value: object,
) -> None:
    observation = {**_observation("observation:1"), "source_value": value}
    mapping = _mapping("concept:1", "taxon:1")
    with _fixture_authority([mapping]):
        reviewed = _review([observation])
    row = _rows(reviewed)[0]
    assert row["review_eligibility"] == "eligible"
    retained = cast(dict[str, object], row["source_observation"])["source_value"]
    assert type(retained) is type(value)
    assert retained == value
    assert reviewed["scope"] == "reviewed_source_taxon_membership_only"
    assert "chronology" in cast(list[str], reviewed["unassessed"])
    if value is None or cast(float, value) <= 0:
        event_result = _derive(observations=[observation], mappings=[mapping])
        assert not event_result.events
        assert event_result.refusals[0].reason_code == "non_positive_observation"


def test_absent_value_stays_absent_and_results_do_not_alias_inputs() -> None:
    observation = _observation("observation:1")
    observation.pop("source_value")
    with _fixture_authority([_mapping("concept:1", "taxon:1")]):
        result = assess_classification_eligibility(
            observation_memberships=[_membership("observation:1", "concept:1")],
            classification_mappings=[_mapping("concept:1", "taxon:1")],
            observations=[observation],
            context=_context(),
        )
    observation["source_value"] = 7
    row = _rows(result.as_dict())[0]
    assert "source_value" not in cast(dict[str, object], row["source_observation"])
    row["review_eligibility"] = "changed"
    assert _rows(result.as_dict())[0]["review_eligibility"] == "eligible"
    assert (
        hashlib.sha256(result.canonical_json.encode()).hexdigest()
        == result.result_digest
    )


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("source_taxon_id", True, "classification_source_identity_mismatch"),
        ("source_reported_name", "other", "classification_source_identity_mismatch"),
        (
            "source_snapshot_id",
            f"sha256:{'d' * 64}",
            "classification_authority_lineage_mismatch",
        ),
        ("build_id", f"sha256:{'d' * 64}", "classification_authority_lineage_mismatch"),
        ("country_code", "NO", "source_lineage_mismatch"),
        ("source_family", "sead", "source_lineage_mismatch"),
    ],
)
def test_source_identity_and_lineage_remain_required(
    field: str, value: object, reason: str
) -> None:
    observation = {**_observation("observation:1"), field: value, "source_value": 0}
    with _fixture_authority([_mapping("concept:1", "taxon:1")]):
        assert _rows(_review([observation]))[0]["reason_code"] == reason


def test_product_authority_does_not_accept_fixture_review_claims() -> None:
    assert (
        _rows(_review([_observation("observation:1")]))[0]["reason_code"]
        == "classification_mapping_not_authorized"
    )


@pytest.mark.parametrize(
    ("identity", "eligible"), [(1, True), (True, False), (1.0, False)]
)
def test_exact_source_taxon_scalar_type_avoids_python_equality_collision(
    identity: object, eligible: bool
) -> None:
    mapping = _mapping("concept:1", "taxon:1", source_taxon_id=1)
    observation = _observation("observation:1", source_taxon_id=identity)
    with _fixture_authority([mapping]):
        row = _rows(_review([observation], mappings=[mapping]))[0]
    assert (row["review_eligibility"] == "eligible") is eligible
    if not eligible:
        assert row["reason_code"] == "classification_source_identity_mismatch"
        event_result = _derive(observations=[observation], mappings=[mapping])
        assert (
            event_result.refusals[0].reason_code
            == "classification_source_identity_mismatch"
        )


def test_missing_review_and_extra_authorized_universe_cannot_be_bypassed() -> None:
    incomplete = {**_mapping("concept:1", "taxon:1"), "reviewer_id": None}
    with _fixture_authority([incomplete]):
        assert (
            _rows(_review([_observation("observation:1")], mappings=[incomplete]))[0][
                "reason_code"
            ]
            == "classification_review_incomplete"
        )
    with _fixture_authority(
        [_mapping("concept:1", "taxon:1"), _mapping("concept:2", "taxon:2")]
    ):
        assert (
            _rows(_review([_observation("observation:1")]))[0]["reason_code"]
            == "incomplete_classification_authority_universe"
        )


def test_union_duplicates_and_missing_rows_are_accounted() -> None:
    observation = _observation("observation:1")
    members = [
        _membership("observation:1", "concept:1"),
        _membership("missing", "concept:1"),
    ]
    with _fixture_authority([_mapping("concept:1", "taxon:1")]):
        result = _review(
            [observation, dict(observation), _observation("unmapped")],
            memberships=members,
        )
    assert {row["observation_id"]: row["reason_code"] for row in _rows(result)} == {
        "observation:1": "duplicate_source_observation",
        "missing": "missing_source_observation",
        "unmapped": "classification_membership_missing",
    }
    counts = cast(dict[str, int], result["reconciliation"])
    assert (
        counts["unique_observation_count"] == counts["refused_observation_count"] == 3
    )
    assert counts["duplicate_source_observation_count"] == 1


def test_permutation_preserves_identity_and_value_changes_bind_input_digest() -> None:
    observations = [
        _observation("first"),
        {**_observation("second"), "source_value": 0},
    ]
    with _fixture_authority([_mapping("concept:1", "taxon:1")]):
        baseline = _review(observations)
        assert baseline == _review(list(reversed(observations)))
        observations[1]["source_value"] = None
        assert _review(observations)["input_digest"] != baseline["input_digest"]


def test_conflicting_duplicate_permutation_cannot_change_refused_projection() -> None:
    observations = [
        _observation("duplicate"),
        {**_observation("duplicate"), "source_value": 0},
    ]
    with _fixture_authority([_mapping("concept:1", "taxon:1")]):
        result = _review(observations)
        assert result == _review(list(reversed(observations)))
    assert _rows(result)[0]["reason_code"] == "conflicting_source_observation"
    counts = cast(dict[str, int], result["reconciliation"])
    assert counts["input_observation_count"] == 2
    assert (
        counts["unique_observation_count"] == counts["refused_observation_count"] == 1
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_native_json_is_refused_before_projection(value: float) -> None:
    with pytest.raises(ValueError, match="Out of range float values"):
        _review([{**_observation("invalid"), "source_value": value}])
