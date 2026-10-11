"""All native claims remain at their owner and no chronology is selected."""

from __future__ import annotations

from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.materialization.sead.chronology import (
    ChronologyAccounting,
)

from .support import source_row
from .test_observations import accounting


def claim(identity: str) -> dict[str, Any]:
    return {
        "chronology_claim_id": identity,
        "observation_relation_id": "entity:1",
        "analysis_entity_id": 1,
        "physical_sample_id": 2,
        "sample_group_id": 3,
        "dataset_id": 1,
        "site_uuid": "site",
        "country_code": "SE",
        "comparability_status": "comparable",
        "source_age_type": "AD",
        "source_age_value": {"value": 1951},
        "younger_bp": -1,
        "older_bp": -1,
    }


def test_multiple_native_claims_and_post1950_bp_are_retained() -> None:
    owner = accounting()
    ledger = ChronologyAccounting(owner)
    for name in ("claim:1", "claim:2"):
        record = ledger.claim(source_row(claim(name)))
        assert record["source_claim"]["younger_bp"] == -1
        assert record["selected"] is False
    entity = ledger.entity(owner.entities["entity:1"])
    assert entity["multiple_claims_retained"] is True
    assert entity["selected_chronology_claim"] is None
    with pytest.raises(ValueError, match="duplicated"):
        ledger.claim(source_row(claim("claim:1")))


@pytest.mark.parametrize(
    "field,value",
    (
        ("physical_sample_id", 9),
        ("analysis_entity_id", True),
        ("dataset_id", 1.0),
        ("site_uuid", "foreign"),
    ),
)
def test_chronology_cannot_transfer_between_owners(field: str, value: Any) -> None:
    row = claim("claim:1")
    row[field] = value
    record = ChronologyAccounting(accounting()).claim(source_row(row))
    assert "source_chronology_owner_mismatch" in record["reason_codes"]


def test_missing_claim_does_not_silently_disappear() -> None:
    owner = accounting()
    with pytest.raises(ValueError, match="does not cover"):
        ChronologyAccounting(owner).entity(owner.entities["entity:1"])
