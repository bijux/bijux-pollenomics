"""Refuse declarations that cannot authorize a final held-out evaluation."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    validate_evaluation_policy,
)

from .support import ACCESS, policy_payload, scope_fixture


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "draft"),
        ("scope_manifest_sha256", "a" * 64),
        ("split_manifest_sha256", "a" * 64),
        ("locked_at", "2020-02-01T00:00:00Z"),
        ("minimum_buffer_m", None),
        ("minimum_buffer_m", True),
        ("spatial_support_policy", "nearest-training-only"),
        ("multiplicity_policy", "pick-best-cell"),
    ],
)
def test_invalid_policy(field: str, value: Any) -> None:
    scope = scope_fixture()
    payload = policy_payload(scope)
    payload[field] = value
    with pytest.raises(ValidationRefusal):
        validate_evaluation_policy(payload, scope=scope, first_test_access_at=ACCESS)


def test_nullable_and_boolean_cell_thresholds_refuse() -> None:
    scope = scope_fixture()
    for field, value in [
        ("maximum_mae_pp", None),
        ("minimum_sites", True),
        ("minimum_blocks", 1),
        ("nominal_predictive_coverage", 1),
    ]:
        payload = policy_payload(scope)
        payload["cells"][0][field] = value
        with pytest.raises(ValidationRefusal):
            validate_evaluation_policy(
                payload, scope=scope, first_test_access_at=ACCESS
            )


def test_local_pollen_fit_cannot_be_heldout_pollen_cell() -> None:
    scope = scope_fixture()
    payload = policy_payload(scope)
    payload["cells"][1]["experiment"] = "local_pollen_available"
    with pytest.raises(ValidationRefusal, match="not a held-out"):
        validate_evaluation_policy(payload, scope=scope, first_test_access_at=ACCESS)


def test_first_access_requires_timezone_and_actual_past() -> None:
    scope = scope_fixture()
    for access in [datetime(2020, 2, 1), datetime(9999, 1, 1, tzinfo=UTC)]:
        with pytest.raises(ValidationRefusal):
            validate_evaluation_policy(
                policy_payload(scope), scope=scope, first_test_access_at=access
            )


def test_duplicate_observed_units_and_group_block_splitting_refuse() -> None:
    scope = scope_fixture()
    duplicate = replace(
        scope.sites[3],
        vegetation_observation_id=scope.sites[2].vegetation_observation_id,
    )
    with pytest.raises(ValidationRefusal, match="Duplicate observed"):
        replace(scope, sites=(*scope.sites[:3], duplicate, *scope.sites[4:]))


def test_external_ids_cannot_shadow_training_or_outcome_records() -> None:
    from bijux_pollenomics.analysis.lra_validation.evaluation.api import ExternalInput

    scope = scope_fixture()
    for key in ("p0", "vegetation:2"):
        with pytest.raises(ValidationRefusal, match="shadow"):
            replace(
                scope,
                external_inputs=(
                    ExternalInput(key, "fixed_parameter", "f" * 64, None),
                ),
            )


def test_scope_order_is_not_scientific_identity_and_blocks_cannot_split_groups() -> (
    None
):
    scope = scope_fixture()
    assert (
        replace(scope, sites=tuple(reversed(scope.sites))).scope_sha256
        == scope.scope_sha256
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("coordinate_crs", "EPSG:3857"),
        ("age_type", "CE"),
        ("spatial_profile", "unreviewed-footprint"),
        ("temporal_profile", "untyped-coordinate"),
    ],
)
def test_support_types_and_profiles_are_not_inferred(field: str, value: str) -> None:
    support = scope_fixture().sites[0].support
    assert support is not None
    with pytest.raises(ValidationRefusal, match="Unsupported"):
        replace(support, **dict[str, Any]({field: value}))
