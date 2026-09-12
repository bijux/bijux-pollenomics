"""Final-test policy admission does not invent missing scientific decisions."""

from datetime import UTC, datetime
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import (
    FrozenPolicy,
    ValidationRefusal,
    validate_final_policy,
)


def example_policy() -> dict[str, object]:
    """Synthetic policy for parser tests only; not a project scientific approval."""
    return {
        "schema_version": "pollenomics-benchmark-policy.v1",
        "status": "frozen",
        "targets": ["vegetation_cover", "pollen_composition"],
        "experiments": ["local_pollen_available", "all_target_pollen_withheld"],
        "grouping": [
            "site_basin",
            "duplicate_source_identity",
            "core",
            "shared_derived_lineage",
        ],
        "scope_manifest_sha256": "a" * 64,
        "split_manifest_sha256": "b" * 64,
        "independent_vegetation_reference_ids": ["synthetic-test-only"],
        "vegetation_mae_max_percentage_points": 12,
        "pollen_composition_mae_max_percentage_points": 14,
        "minimum_paired_baseline_improvement": 0,
        "minimum_independent_sites": 3,
        "minimum_independent_blocks": 2,
        "subgroup_acceptance_policy": "synthetic test declaration",
        "nominal_predictive_interval_coverage": 0.95,
        "coverage_tolerance": 0.05,
        "maximum_prediction_failure_fraction": 0,
        "maximum_exclusion_fraction": 0,
        "zero_and_missing_taxon_policy": "explicit zeros; missing composition unscorable",
        "spatial_buffer_policy": "synthetic test declaration",
        "temporal_support_policy": "synthetic test declaration",
        "multiple_comparison_policy": "synthetic test declaration",
        "random_seed": 0,
        "locked_before_test_access_at": "2020-01-01T00:00:00Z",
        "reviewer": "synthetic-test-only-not-scientific-review",
    }


def validate(policy: dict[str, object], **kwargs: Any) -> FrozenPolicy:
    return validate_final_policy(
        policy, scope_manifest_sha256="a" * 64, split_manifest_sha256="b" * 64, **kwargs
    )


def test_valid_policy_receipt_is_immutable_and_deterministic() -> None:
    policy = example_policy()
    first = validate(policy)
    assert first == validate(dict(reversed(list(policy.items()))))
    policy["reviewer"] = "changed"
    assert first != validate(policy)


@pytest.mark.parametrize("field", list(example_policy()))
def test_every_required_policy_field_refuses_null(field: str) -> None:
    policy = example_policy()
    policy[field] = None
    with pytest.raises(ValidationRefusal):
        validate(policy)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "draft_not_executable"),
        ("vegetation_mae_max_percentage_points", float("nan")),
        ("minimum_independent_sites", True),
        ("minimum_independent_blocks", 1),
        ("nominal_predictive_interval_coverage", 1),
        ("coverage_tolerance", -0.1),
        ("maximum_exclusion_fraction", 2),
        ("reviewer", {}),
        ("zero_and_missing_taxon_policy", {"missing": None}),
        ("random_seed", True),
        ("locked_before_test_access_at", "2020-01-01"),
        ("locked_before_test_access_at", "9999-01-01T00:00:00Z"),
        ("targets", ["vegetation_cover", "pollen_composition", "pollen_composition"]),
    ],
)
def test_unfrozen_invalid_or_incomplete_policy_refuses(
    field: str, value: object
) -> None:
    policy = example_policy()
    policy[field] = value
    with pytest.raises(ValidationRefusal):
        validate(policy)


def test_policy_cannot_be_frozen_after_first_test_access_or_for_other_split() -> None:
    policy = example_policy()
    with pytest.raises(ValidationRefusal):
        validate(policy, test_access_at=datetime(2019, 1, 1, tzinfo=UTC))
    with pytest.raises(ValidationRefusal):
        validate(policy, test_access_at=datetime(2021, 1, 1))
    policy["split_manifest_sha256"] = "c" * 64
    with pytest.raises(ValidationRefusal):
        validate(policy)
