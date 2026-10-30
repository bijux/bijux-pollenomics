"""SEAD country-decision state and geometry refusal tests."""

from __future__ import annotations

from typing import cast

import pytest

from bijux_pollenomics.governance.country_coverage.evidence.sead_decisions.records import (
    _parse_decision_identity,
)

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

    with pytest.raises(
        ValueError, match=rf"{message}|retained SEAD country decisions identity changed"
    ):
        _build()


@pytest.mark.parametrize("identity_field", ("site_id", "site_uuid"))
def test_duplicate_sead_decision_identity_is_refused(
    monkeypatch: pytest.MonkeyPatch, identity_field: str
) -> None:
    record: dict[str, object] = {
        "site_id": 1,
        "site_uuid": "00000000-0000-4000-8000-000000000001",
        "latitude_dd": 1.0,
        "longitude_dd": 1.0,
        "governed_country_code": "SE",
        "decision": {
            "decision_status": "assigned",
            "decision_method": "strict_boundary_containment",
            "raw_country": None,
            "refusal_reason": None,
        },
    }
    second = dict(
        record,
        site_id=2,
        site_uuid="00000000-0000-4000-8000-000000000002",
    )
    seen_site_ids: set[int] = set()
    seen_site_uuids: set[str] = set()
    baseline = _parse_decision_identity(
        record,
        bbox=(0.0, 0.0, 4.0, 4.0),
        seen_site_ids=seen_site_ids,
        seen_site_uuids=seen_site_uuids,
    )
    assert baseline.site_id == 1
    assert (
        _parse_decision_identity(
            second,
            bbox=(0.0, 0.0, 4.0, 4.0),
            seen_site_ids=set(),
            seen_site_uuids=set(),
        ).site_id
        == 2
    )
    second[identity_field] = record[identity_field]
    with pytest.raises(ValueError, match="duplicate identity"):
        _parse_decision_identity(
            second,
            bbox=(0.0, 0.0, 4.0, 4.0),
            seen_site_ids=seen_site_ids,
            seen_site_uuids=seen_site_uuids,
        )

    def duplicate_identity(document: dict[str, object]) -> None:
        decisions = cast(list[dict[str, object]], document["decisions"])
        decisions[2][identity_field] = decisions[0][identity_field]

    _replace_input_document(
        monkeypatch,
        _SEAD_DECISIONS_PATH,
        duplicate_identity,
    )

    with pytest.raises(
        ValueError, match="^retained SEAD country decisions identity changed$"
    ):
        _build()


def test_coherent_sead_country_reassignment_is_refused(
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

    with pytest.raises(
        ValueError,
        match="governed geometry|retained SEAD country decisions identity changed",
    ):
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
    record: dict[str, object] = {
        "site_id": 1,
        "site_uuid": "00000000-0000-4000-8000-000000000001",
        "latitude_dd": 1.0,
        "longitude_dd": 1.0,
        "governed_country_code": "SE",
        "decision": {
            "decision_status": "assigned",
            "decision_method": "strict_boundary_containment",
            "raw_country": None,
            "refusal_reason": None,
        },
    }
    baseline = _parse_decision_identity(
        record,
        bbox=(0.0, 0.0, 4.0, 4.0),
        seen_site_ids=set(),
        seen_site_uuids=set(),
    )
    assert (baseline.latitude, baseline.longitude) == (1.0, 1.0)
    record[field] = value
    with pytest.raises(ValueError, match="finite coordinate"):
        _parse_decision_identity(
            record,
            bbox=(0.0, 0.0, 4.0, 4.0),
            seen_site_ids=set(),
            seen_site_uuids=set(),
        )

    def corrupt_coordinate(document: dict[str, object]) -> None:
        decisions = cast(list[dict[str, object]], document["decisions"])
        decisions[0][field] = value

    _replace_input_document(monkeypatch, _SEAD_DECISIONS_PATH, corrupt_coordinate)

    with pytest.raises(
        ValueError, match="^retained SEAD country decisions identity changed$"
    ):
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

    with pytest.raises(
        ValueError,
        match="governed geometry|retained SEAD country decisions identity changed",
    ):
        _build()
