"""SEAD country-decision state and geometry refusal tests."""

from __future__ import annotations

from typing import cast

import pytest

from ..fixtures import (
    _SEAD_DECISIONS_PATH,
    _build,
    _replace_input_document,
)


@pytest.mark.parametrize(
    ("status", "country_code", "refusal_reason", "message"),
    (
        ("fabricated", "SE", None, "governed geometry"),
        ("assigned", "UNASSIGNED", None, "governed country"),
        ("review", "UNASSIGNED", "outside_governed_boundaries", "governed geometry"),
        ("unassigned", "UNASSIGNED", None, "governed geometry"),
    ),
)
def test_invalid_sead_decision_state_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    status: str,
    country_code: str,
    refusal_reason: str | None,
    message: str,
) -> None:
    def corrupt_decision(document: dict[str, object]) -> None:
        decisions = cast(list[dict[str, object]], document["decisions"])
        record = decisions[0]
        record["governed_country_code"] = country_code
        decision = cast(dict[str, object], record["decision"])
        decision["decision_status"] = status
        decision["refusal_reason"] = refusal_reason

    _replace_input_document(
        monkeypatch,
        _SEAD_DECISIONS_PATH,
        corrupt_decision,
    )

    with pytest.raises(ValueError, match=message):
        _build()


@pytest.mark.parametrize("identity_field", ("site_id", "site_uuid"))
def test_duplicate_sead_decision_identity_is_refused(
    monkeypatch: pytest.MonkeyPatch, identity_field: str
) -> None:
    def duplicate_identity(document: dict[str, object]) -> None:
        decisions = cast(list[dict[str, object]], document["decisions"])
        decisions[2][identity_field] = decisions[0][identity_field]

    _replace_input_document(
        monkeypatch,
        _SEAD_DECISIONS_PATH,
        duplicate_identity,
    )

    with pytest.raises(ValueError, match="duplicate identity"):
        _build()


def test_coherent_sead_country_reassignment_is_refused_by_geometry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reassign(document: dict[str, object]) -> None:
        decisions = cast(list[dict[str, object]], document["decisions"])
        record = decisions[0]
        record["governed_country_code"] = "DK"
        decision = cast(dict[str, object], record["decision"])
        decision["derived_country"] = "Denmark"
        decision["candidate_countries"] = ["Denmark"]
        country_counts = cast(dict[str, int], document["country_counts"])
        country_counts["SE"] -= 1
        country_counts["DK"] += 1

    _replace_input_document(monkeypatch, _SEAD_DECISIONS_PATH, reassign)

    with pytest.raises(ValueError, match="governed geometry"):
        _build()


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("latitude_dd", 999),
        ("longitude_dd", -999),
    ),
)
def test_sead_decision_coordinates_are_validated(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    def corrupt_coordinate(document: dict[str, object]) -> None:
        decisions = cast(list[dict[str, object]], document["decisions"])
        decisions[0][field] = value

    _replace_input_document(monkeypatch, _SEAD_DECISIONS_PATH, corrupt_coordinate)

    with pytest.raises(ValueError, match="finite coordinate"):
        _build()


@pytest.mark.parametrize(
    ("status", "field", "value"),
    (
        ("assigned", "derived_country", "Denmark"),
        ("review", "ambiguity_reason", None),
        ("unassigned", "refusal_reason", None),
    ),
)
def test_sead_decision_detail_must_equal_geometry_result(
    monkeypatch: pytest.MonkeyPatch, status: str, field: str, value: object
) -> None:
    def corrupt_detail(document: dict[str, object]) -> None:
        decisions = cast(list[dict[str, object]], document["decisions"])
        record = next(
            row
            for row in decisions
            if cast(dict[str, object], row["decision"])["decision_status"] == status
        )
        cast(dict[str, object], record["decision"])[field] = value

    _replace_input_document(monkeypatch, _SEAD_DECISIONS_PATH, corrupt_detail)

    with pytest.raises(ValueError, match="governed geometry"):
        _build()
