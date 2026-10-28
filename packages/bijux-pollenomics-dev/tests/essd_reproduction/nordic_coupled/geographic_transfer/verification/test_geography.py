"""Geographic roles are checked independently of host distance computation."""

from __future__ import annotations

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.geographic_transfer.geometry import (
    admit_targets,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.geographic_transfer.verification.geography import (
    audit_admission,
)

from ..test_geometry import metadata


def test_independent_bounds_certify_all_source_roles_and_positive_margin() -> None:
    packet, policy = metadata()
    admission = admit_targets(packet, policy)
    facts = audit_admission(packet, admission, policy)
    assert facts["admitted_roles"] == 1
    assert facts["refused_roles"] == 2
    assert facts["source_target_comparisons"] == 9
    assert facts["minimum_certified_additional_joint_allowance_margin_m"] > 0


def test_reported_clearance_cannot_hide_a_forbidden_source() -> None:
    packet, policy = metadata()
    admission = admit_targets(packet, policy)
    row = next(role for role in admission["roles"] if role["status"] == "refused")
    row["forbidden_source_owner_ids"] = []
    with pytest.raises(ValueError, match="source refusal inventory"):
        audit_admission(packet, admission, policy)


def test_zero_distance_tampering_fails_even_inside_an_exclusion() -> None:
    packet, policy = metadata()
    admission = admit_targets(packet, policy)
    admission["roles"][0]["comparisons"][0]["distance"]["centre_distance_m"] = 0.0
    with pytest.raises(ValueError, match="independent geodesic bounds"):
        audit_admission(packet, admission, policy)
