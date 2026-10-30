"""Admit a complete cached source set against a held geographic block."""

from __future__ import annotations

from dataclasses import asdict
import math
from typing import Any

from bijux_pollenomics.analysis.lra_validation.experiments.fitted.admission import (
    Footprint,
)
from bijux_pollenomics.analysis.lra_validation.spatial.support import support_separation


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Geographic transfer admission: " + message)


def admit_targets(packet: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """A forbidden or too-close source refuses the whole required-input case."""
    minimum = policy["minimum_buffer_m"]
    require(
        type(minimum) in (int, float) and math.isfinite(minimum) and minimum > 0,
        "Positive finite geographic buffer required",
    )
    sites = {site["owner_id"]: site for site in packet["sites"]}
    require(
        len(sites) == len(packet["sites"]) == 4
        and len({site["place_id"] for site in sites.values()}) == 4,
        "Four distinct original source places required",
    )
    require(
        set(policy["blocks"]) == {"sweden", "solsoe"},
        "Declared two-block partition required",
    )
    targets = {
        owner for owner, site in sites.items() if site["target_eligible"] is True
    }
    require(
        len(targets) == 3
        and {sites[owner]["place_id"] for owner in targets}
        == set(policy["target_places"]),
        "Three forecast targets required; regional source is not a target",
    )
    for site in sites.values():
        require(
            site["place_id"] in policy["blocks"][site["block_id"]],
            "Source place and geographic block disagree",
        )
        require(
            site["target_eligible"]
            == (site["place_id"] not in policy["source_only_places"]),
            "Source-only regional role changed",
        )
        for field, expected in (
            ("source_radius_m", policy["source_radius_m"]),
            ("coordinate_uncertainty_m", policy["coordinate_uncertainty_m"]),
        ):
            value = site[field]
            require(
                type(value) in (int, float)
                and math.isfinite(value)
                and value >= 0
                and value == expected,
                "Original declared source footprint or coordinate allowance changed",
            )
        if site["target_eligible"]:
            require(
                site["target_radius_m"] == policy["target_radius_m"],
                "Target footprint changed",
            )
    roles = packet["target_roles"]
    require(
        len(roles) == len({role["case_id"] for role in roles}) == 3
        and {role["target_id"] for role in roles} == targets,
        "Complete three-case role population required",
    )
    result = []
    for role in sorted(roles, key=lambda row: row["target_id"]):
        target = sites[role["target_id"]]
        require(role["heldout_block_id"] == target["block_id"], "Target block changed")
        sources = role["required_source_owner_ids"]
        require(
            len(sources) == len(set(sources)) == 3
            and set(sources) == set(sites) - {role["target_id"]},
            "The original complete three-source set is required without fallback",
        )
        comparisons = []
        forbidden, close = [], []
        for owner in sources:
            source = sites[owner]
            blocked = source["block_id"] == role["heldout_block_id"]
            if blocked:
                forbidden.append(owner)
            distance = support_separation(
                Footprint(
                    target["latitude"],
                    target["longitude"],
                    target["target_radius_m"],
                    target["coordinate_uncertainty_m"],
                ),
                Footprint(
                    source["latitude"],
                    source["longitude"],
                    source["source_radius_m"],
                    source["coordinate_uncertainty_m"],
                ),
            )
            separated = distance.lower_bound_m >= minimum
            if not separated:
                close.append(owner)
            comparisons.append(
                {
                    "source_owner_id": owner,
                    "target_owner_id": role["target_id"],
                    "source_block_id": source["block_id"],
                    "target_block_id": target["block_id"],
                    "forbidden_by_block": blocked,
                    "separation_eligible": separated,
                    "distance": asdict(distance),
                }
            )
        result.append(
            {
                "case_id": role["case_id"],
                "target_id": role["target_id"],
                "heldout_block_id": role["heldout_block_id"],
                "required_source_owner_ids": list(sources),
                "forbidden_source_owner_ids": forbidden,
                "distance_excluded_source_owner_ids": close,
                "comparisons": comparisons,
                "status": "admitted" if not forbidden and not close else "refused",
                "reason": "complete_source_set_disjoint_and_separated"
                if not forbidden and not close
                else "source_in_held_geographic_block"
                if forbidden
                else "source_footprint_buffer_failed",
            }
        )
    return {
        "schema_version": "krageholm-geographic-transfer-admission.v1",
        "policy": dict(policy),
        "roles": result,
        "summary": {
            "target_roles": 3,
            "admitted_roles": sum(row["status"] == "admitted" for row in result),
            "refused_roles": sum(row["status"] == "refused" for row in result),
            "source_target_comparisons": 9,
        },
    }
