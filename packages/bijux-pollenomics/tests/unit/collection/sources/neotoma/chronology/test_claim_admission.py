from __future__ import annotations

import copy
import unittest

import pytest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from tests.support.neotoma import download_row
from tests.support.neotoma.relational_shapes import mapping, nested, rows


class NeotomaChronologyClaimAdmissionTests(unittest.TestCase):
    def test_refuses_negative_bp_without_turning_missing_age_into_zero(self) -> None:
        row = download_row()
        sample = rows(nested(row, "site", "collectionunit", "dataset")["samples"])[0]
        sample["ages"] = [
            {
                "age": -2,
                "ageyounger": None,
                "ageolder": None,
                "agetype": "Calendar years BP",
                "chronologyid": 7001,
            },
            {
                "age": None,
                "ageyounger": None,
                "ageolder": None,
                "agetype": None,
                "chronologyid": None,
            },
            {
                "age": 0,
                "ageyounger": None,
                "ageolder": None,
                "agetype": "Calendar years BP",
                "chronologyid": 7001,
            },
        ]

        payload = build_neotoma_relational_snapshot(
            [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
        )
        by_status = mapping(payload["reconciliation"])["age_comparability_counts"]
        self.assertEqual(by_status, {"comparable": 1, "refused": 1, "unresolved": 1})
        zero = next(
            claim
            for claim in rows(payload["age_claims"])
            if claim["source_age_value"] == 0
        )
        missing = next(
            claim
            for claim in rows(payload["age_claims"])
            if claim["source_age_value"] is None
        )
        self.assertEqual((zero["younger_bp"], zero["older_bp"]), (0, 0))
        self.assertIsNone(missing["younger_bp"])
        self.assertIsNone(missing["older_bp"])


@pytest.mark.parametrize(
    ("younger", "older"),
    [
        (True, False),
        ("1150", "1250"),
        ([1150], {"age": 1250}),
        (True, 1250),
        (None, "1250"),
    ],
)
def test_explicit_malformed_interval_cannot_fall_back_to_a_comparable_point(
    younger: object, older: object
) -> None:
    row = download_row()
    sample = rows(nested(row, "site", "collectionunit", "dataset")["samples"])[0]
    age = mapping(rows(sample["ages"])[0])
    age.update(age=1200, ageyounger=younger, ageolder=older)
    raw = copy.deepcopy(age)
    original = copy.deepcopy(row)
    payload = build_neotoma_relational_snapshot(
        [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
    )
    claims = rows(payload["age_claims"])
    claim = next(
        claim
        for claim in claims
        if claim["source_age_type"] == "Calibrated radiocarbon years BP"
    )
    assert len(claims) == 2
    assert claim["comparability_status"] == "refused"
    assert (
        claim["admission_reason"] == claim["refusal_reason"] == "invalid_interval_bound"
    )
    assert claim["younger_bp"] is claim["older_bp"] is None
    assert claim["source_age_value"] == 1200
    assert claim["source_age_younger"] == younger and claim["source_age_older"] == older
    assert type(claim["source_age_younger"]) is type(younger)
    assert type(claim["source_age_older"]) is type(older)
    assert claim["source_payload"] == raw
    assert claim["is_default_chronology"] is True
    reconciliation = mapping(payload["reconciliation"])
    assert mapping(reconciliation["source_row_counts"])["age_claim_rows"] == 2
    assert mapping(reconciliation["normalized_row_counts"])["age_claims"] == 2
    assert mapping(reconciliation["age_comparability_counts"])["refused"] == 1
    assert mapping(reconciliation["age_reason_counts"])["invalid_interval_bound"] == 1
    assert row == original


@pytest.mark.parametrize("bounds", ["absent", "null", "numeric"])
def test_legitimate_point_and_interval_age_sources_keep_their_original_posture(
    bounds: str,
) -> None:
    row = download_row()
    sample = rows(nested(row, "site", "collectionunit", "dataset")["samples"])[0]
    age = mapping(rows(sample["ages"])[0])
    age["age"] = 0 if bounds != "numeric" else 1200
    if bounds == "absent":
        age.pop("ageyounger")
        age.pop("ageolder")
    elif bounds == "null":
        age.update(ageyounger=None, ageolder=None)
    payload = build_neotoma_relational_snapshot(
        [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
    )
    claim = next(
        claim
        for claim in rows(payload["age_claims"])
        if claim["source_age_type"] == "Calibrated radiocarbon years BP"
    )
    assert claim["comparability_status"] == "comparable"
    assert claim["admission_reason"] is None
    assert (claim["younger_bp"], claim["older_bp"]) == (
        (1150, 1250) if bounds == "numeric" else (0, 0)
    )
    assert claim["source_payload"] == age
