"""Independent exact-bound classification of geographic source admission."""

from __future__ import annotations

from fractions import Fraction
import math
from typing import Any

from bijux_pollenomics_dev.lra_validation.spatial_reference.geodesic import (
    distance_bounds,
)


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent geographic transfer: " + message)


def _number(value: Any) -> Fraction:
    _require(
        type(value) in (int, float) and math.isfinite(value), "finite native scalar"
    )
    return Fraction.from_float(float(value))


def audit_admission(
    packet: dict[str, Any], admission: dict[str, Any], policy: dict[str, Any]
) -> dict[str, Any]:
    """Independently classify source blocks and bounded footprint distances."""
    sites = {site["owner_id"]: site for site in packet["sites"]}
    minimum = Fraction.from_float(float(policy["minimum_buffer_m"]))
    tolerance = Fraction.from_float(1e-6)
    _require(
        admission["policy"] == policy
        and admission["schema_version"] == "krageholm-geographic-transfer-admission.v1",
        "geographic policy snapshot",
    )
    expected = []
    margins = []
    for role, actual in zip(
        sorted(packet["target_roles"], key=lambda row: row["target_id"]),
        admission["roles"],
        strict=True,
    ):
        target = sites[role["target_id"]]
        forbidden, excluded, comparisons = [], [], []
        _require(
            len(actual["comparisons"]) == len(role["required_source_owner_ids"]) == 3,
            "complete required source comparisons",
        )
        for owner, observed in zip(
            role["required_source_owner_ids"], actual["comparisons"], strict=True
        ):
            source = sites[owner]
            lower, upper = distance_bounds(source, target)
            distance = observed["distance"]
            _require(
                set(distance)
                == {
                    "centre_distance_m",
                    "target_radius_m",
                    "training_radius_m",
                    "target_coordinate_uncertainty_m",
                    "training_coordinate_uncertainty_m",
                    "lower_bound_m",
                },
                "all footprint distance components",
            )
            centre = _number(distance["centre_distance_m"])
            _require(
                lower - tolerance <= centre <= upper + tolerance,
                "centre outside independent geodesic bounds",
            )
            components = {
                "target_radius_m": target["target_radius_m"],
                "training_radius_m": source["source_radius_m"],
                "target_coordinate_uncertainty_m": target["coordinate_uncertainty_m"],
                "training_coordinate_uncertainty_m": source["coordinate_uncertainty_m"],
            }
            _require(
                all(distance[key] == value for key, value in components.items()),
                "source radius or coordinate allowance changed",
            )
            deduction = sum(
                (_number(value) for value in components.values()), Fraction()
            )
            clearance = _number(distance["lower_bound_m"])
            _require(
                abs(clearance - max(Fraction(), centre - deduction)) <= tolerance,
                "conservative clearance arithmetic",
            )
            if max(Fraction(), upper - deduction) < minimum:
                separated = False
            elif max(Fraction(), lower - deduction) >= minimum:
                separated = True
                margins.append(float(lower - deduction - minimum))
            else:
                raise ValueError(
                    "Independent geographic transfer: unresolved geodesic metric envelope"
                )
            blocked = source["block_id"] == role["heldout_block_id"]
            if blocked:
                forbidden.append(owner)
            if not separated:
                excluded.append(owner)
            comparisons.append(
                {
                    "source_owner_id": owner,
                    "target_owner_id": role["target_id"],
                    "source_block_id": source["block_id"],
                    "target_block_id": target["block_id"],
                    "forbidden_by_block": blocked,
                    "separation_eligible": separated,
                    "distance": distance,
                }
            )
        expected.append(
            {
                "case_id": role["case_id"],
                "target_id": role["target_id"],
                "heldout_block_id": role["heldout_block_id"],
                "required_source_owner_ids": role["required_source_owner_ids"],
                "forbidden_source_owner_ids": forbidden,
                "distance_excluded_source_owner_ids": excluded,
                "comparisons": comparisons,
                "status": "admitted" if not forbidden and not excluded else "refused",
                "reason": "complete_source_set_disjoint_and_separated"
                if not forbidden and not excluded
                else "source_in_held_geographic_block"
                if forbidden
                else "source_footprint_buffer_failed",
            }
        )
    _require(admission["roles"] == expected, "geographic role/source refusal inventory")
    summary = {
        "target_roles": 3,
        "admitted_roles": sum(row["status"] == "admitted" for row in expected),
        "refused_roles": sum(row["status"] == "refused" for row in expected),
        "source_target_comparisons": 9,
    }
    _require(admission["summary"] == summary, "geographic role summary")
    return {
        "status": "passed",
        **summary,
        "independent_oracle": "exact_rational_WGS84_metric_and_path_envelope",
        "minimum_certified_additional_joint_allowance_margin_m": min(margins)
        if margins
        else None,
        "scope": "Declared finite footprints and coordinate allowance only; no empirical source-area or field-independence calibration",
    }
