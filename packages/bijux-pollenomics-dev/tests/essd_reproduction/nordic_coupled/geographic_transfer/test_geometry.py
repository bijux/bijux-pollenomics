"""Geographic withholding covers every local and the regional source."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.geographic_transfer.geometry import (
    admit_targets,
)


def metadata() -> tuple[dict[str, Any], dict[str, Any]]:
    policy = {
        "blocks": {"sweden": ["local-a", "local-b", "regional"], "solsoe": ["target"]},
        "source_only_places": ["regional"],
        "target_places": ["local-a", "local-b", "target"],
        "minimum_buffer_m": 20000.0,
        "target_radius_m": 1000.0,
        "source_radius_m": 100000.0,
        "coordinate_uncertainty_m": 0.0,
    }
    sites: list[dict[str, Any]] = [
        {
            "owner_id": owner,
            "place_id": owner,
            "block_id": "solsoe" if owner == "target" else "sweden",
            "target_eligible": owner != "regional",
            "latitude": 55.0,
            "longitude": longitude,
            "source_radius_m": 100000.0,
            "target_radius_m": 1000.0 if owner != "regional" else None,
            "coordinate_uncertainty_m": 0.0,
        }
        for owner, longitude in [
            ("local-a", 13.0),
            ("local-b", 13.1),
            ("regional", 13.2),
            ("target", 8.0),
        ]
    ]
    roles = [
        {
            "case_id": "case:" + site["owner_id"],
            "target_id": site["owner_id"],
            "heldout_block_id": site["block_id"],
            "required_source_owner_ids": [
                other["owner_id"] for other in sites if other != site
            ],
        }
        for site in sites
        if site["target_eligible"]
    ]
    return {"sites": sites, "target_roles": roles}, policy


def test_only_complete_source_set_in_opposite_block_can_be_admitted() -> None:
    packet, policy = metadata()
    original = deepcopy(packet)
    result = admit_targets(packet, policy)
    assert packet == original
    assert result["summary"] == {
        "target_roles": 3,
        "admitted_roles": 1,
        "refused_roles": 2,
        "source_target_comparisons": 9,
    }
    by_owner = {row["target_id"]: row for row in result["roles"]}
    assert by_owner["target"]["status"] == "admitted"
    for owner in ("local-a", "local-b"):
        assert by_owner[owner]["status"] == "refused"
        assert "regional" in by_owner[owner]["forbidden_source_owner_ids"]
        assert "regional" in by_owner[owner]["distance_excluded_source_owner_ids"]
        assert len(by_owner[owner]["comparisons"]) == 3


def test_one_nearby_required_source_cannot_be_dropped_or_replaced() -> None:
    packet, policy = metadata()
    packet["sites"][1]["longitude"] = 8.0
    target = next(
        row
        for row in admit_targets(packet, policy)["roles"]
        if row["target_id"] == "target"
    )
    assert target["status"] == "refused"
    assert target["forbidden_source_owner_ids"] == []
    assert target["distance_excluded_source_owner_ids"] == ["local-b"]
    assert len(target["required_source_owner_ids"]) == 3


def test_single_local_fallback_refuses_before_any_distance_model() -> None:
    packet, policy = metadata()
    packet["target_roles"][0]["required_source_owner_ids"].pop()
    with pytest.raises(ValueError, match="complete three-source set"):
        admit_targets(packet, policy)


def test_auxiliary_regional_owner_cannot_be_invented_as_a_forecast_target() -> None:
    packet, policy = metadata()
    packet["sites"][2]["target_eligible"] = True
    with pytest.raises(ValueError, match="Three forecast targets"):
        admit_targets(packet, policy)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_radius_m", 80.0),
        ("coordinate_uncertainty_m", -1.0),
        ("coordinate_uncertainty_m", False),
    ],
)
def test_source_support_cannot_be_shrunk_to_basin_or_invalid_allowance(
    field: str, value: Any
) -> None:
    packet, policy = metadata()
    packet["sites"][0][field] = value
    with pytest.raises(ValueError, match="Original declared source"):
        admit_targets(packet, policy)
