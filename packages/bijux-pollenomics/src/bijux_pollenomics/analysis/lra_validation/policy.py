"""Refuse final-test claims until the declared scientific policy is frozen."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
import re

from .contracts import ValidationRefusal, canonical_json, finite_number, manifest_sha256


@dataclass(frozen=True)
class FrozenPolicy:
    """A validated immutable policy receipt; review authenticity is external evidence."""

    canonical_policy_json: str
    policy_sha256: str


def _refuse(field: str, detail: str) -> None:
    raise ValidationRefusal("final_policy_not_frozen", f"{field}: {detail}")


def _nonempty(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value) and all(
            _nonempty(item)
            for item in (value.values() if isinstance(value, dict) else value)
        )
    return isinstance(value, (bool, int, float))


def validate_final_policy(
    policy: Mapping[str, object],
    *,
    scope_manifest_sha256: str,
    split_manifest_sha256: str,
    test_access_at: datetime | None = None,
) -> FrozenPolicy:
    """Validate the final-policy schema, thresholds, identities and lock chronology.

    Hashes bind policy to the caller's actual frozen scope and splits. The caller
    must supply first test access when outcomes have already been opened. Numeric
    thresholds are reviewed inputs, never defaults selected by this validator.
    This validates eligibility to evaluate, not scientific success or approvals.
    """
    if policy.get("schema_version") != "pollenomics-benchmark-policy.v1":
        _refuse("schema_version", "expected pollenomics-benchmark-policy.v1")
    if policy.get("status") != "frozen":
        _refuse("status", "draft policies cannot authorize final scoring")
    for name, actual in (
        ("scope_manifest_sha256", scope_manifest_sha256),
        ("split_manifest_sha256", split_manifest_sha256),
    ):
        value = policy.get(name)
        if (
            not isinstance(value, str)
            or not re.fullmatch(r"[0-9a-f]{64}", value)
            or value != actual
        ):
            _refuse(name, "must match the actual canonical manifest SHA-256")
    for name, expected in (
        ("targets", {"vegetation_cover", "pollen_composition"}),
        ("experiments", {"local_pollen_available", "all_target_pollen_withheld"}),
        (
            "grouping",
            {
                "site_basin",
                "duplicate_source_identity",
                "core",
                "shared_derived_lineage",
            },
        ),
    ):
        value = policy.get(name)
        if (
            not isinstance(value, (list, tuple))
            or any(not isinstance(item, str) for item in value)
            or set(value) != expected
            or len(value) != len(expected)
        ):
            _refuse(name, "must declare each governed value exactly once")
    references = policy.get("independent_vegetation_reference_ids")
    if (
        not isinstance(references, (list, tuple))
        or not references
        or any(not isinstance(value, str) or not value.strip() for value in references)
    ):
        _refuse(
            "independent_vegetation_reference_ids",
            "independent observation references are required",
        )
    for name, upper in (
        ("vegetation_mae_max_percentage_points", 100),
        ("pollen_composition_mae_max_percentage_points", 100),
        ("minimum_paired_baseline_improvement", 100),
        ("coverage_tolerance", 1),
        ("maximum_prediction_failure_fraction", 1),
        ("maximum_exclusion_fraction", 1),
    ):
        try:
            value = finite_number(policy.get(name))
        except ValidationRefusal:
            _refuse(name, "a reviewed non-null numeric threshold is required")
        if not 0 <= value <= upper:
            _refuse(name, f"must be between 0 and {upper}")
    try:
        nominal = finite_number(policy.get("nominal_predictive_interval_coverage"))
    except ValidationRefusal:
        _refuse(
            "nominal_predictive_interval_coverage",
            "a reviewed numeric coverage is required",
        )
    if not 0 < nominal < 1:
        _refuse(
            "nominal_predictive_interval_coverage", "must be strictly between 0 and 1"
        )
    for name in ("minimum_independent_sites", "minimum_independent_blocks"):
        value = policy.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 2:
            _refuse(name, "at least two independent units are required")
    seed = policy.get("random_seed")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        _refuse("random_seed", "a nonnegative integer is required")
    for name in (
        "subgroup_acceptance_policy",
        "zero_and_missing_taxon_policy",
        "spatial_buffer_policy",
        "temporal_support_policy",
        "multiple_comparison_policy",
        "reviewer",
    ):
        value = policy.get(name)
        if not isinstance(value, (str, Mapping)) or not _nonempty(value):
            _refuse(
                name,
                "a nonempty reviewed declaration with no missing values is required",
            )
    locked = policy.get("locked_before_test_access_at")
    try:
        if not isinstance(locked, str):
            raise ValueError("missing timestamp")
        timestamp = datetime.fromisoformat(locked.replace("Z", "+00:00"))
        if timestamp.utcoffset() is None:
            raise ValueError("missing timezone")
    except ValueError:
        _refuse(
            "locked_before_test_access_at",
            "an ISO-8601 timestamp with timezone is required",
        )
    if test_access_at is not None and test_access_at.utcoffset() is None:
        _refuse("test_access_at", "first access must have an explicit timezone")
    if timestamp > datetime.now(UTC) or (
        test_access_at is not None and timestamp >= test_access_at
    ):
        _refuse(
            "locked_before_test_access_at",
            "must precede first test access and cannot be in the future",
        )
    try:
        serialized = canonical_json(dict(policy))
    except (TypeError, ValueError) as exc:
        raise ValidationRefusal(
            "final_policy_not_frozen", "Policy must be finite JSON data"
        ) from exc
    return FrozenPolicy(serialized, manifest_sha256(dict(policy)))
