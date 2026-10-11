"""Admit structured predeclared rules; never select thresholds from test outcomes."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import json
from typing import cast

from ..contracts import (
    canonical_json,
    finite_number,
    manifest_sha256,
    required_identity,
)
from .contracts import (
    AcceptanceCell,
    EvaluationPolicy,
    EvaluationScope,
    Experiment,
    Target,
    digest,
    refuse,
)

POLICY_KEYS = frozenset(
    {
        "schema_version",
        "status",
        "scope_manifest_sha256",
        "split_manifest_sha256",
        "locked_at",
        "review_reference",
        "cells",
        "minimum_buffer_m",
        "spatial_support_policy",
        "temporal_support_policy",
        "zero_missing_policy",
        "multiplicity_policy",
        "independent_vegetation_reference_ids",
    }
)
CELL_KEYS = frozenset(AcceptanceCell.__dataclass_fields__)


def timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        refuse("Timestamp must be an explicit timezone-qualified ISO-8601 string")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        refuse("Malformed timestamp")
    if result.utcoffset() is None:
        refuse("Timestamp requires an explicit timezone")
    return result


def _number(value: object, *, lower: float, upper: float) -> float:
    result = finite_number(value)
    if not lower <= result <= upper:
        refuse("Policy threshold outside its declared unit bounds")
    return result


def _integer(value: object) -> int:
    if type(value) is not int or value < 2:
        refuse("Minimum independent-unit count must be an integer of at least two")
    return value


def _identity(value: object) -> str:
    if not isinstance(value, str):
        refuse("Expected a nonempty identity string")
    return required_identity(value)


def validate_evaluation_policy(
    payload: Mapping[str, object],
    *,
    scope: EvaluationScope,
    first_test_access_at: datetime,
) -> EvaluationPolicy:
    """Bind a complete v2 policy to actual scope/splits before declared first access.

    This checks chronology declarations and arithmetic eligibility. It cannot
    authenticate the review reference or prove when a person first saw outcomes.
    """
    if not isinstance(scope, EvaluationScope):
        refuse("Evaluation scope must be typed and validated")
    if frozenset(payload) != POLICY_KEYS:
        refuse("Policy fields must match the exact supported v2 schema")
    if (
        payload["schema_version"] != "pollenomics-final-evaluation.v2"
        or payload["status"] != "frozen"
    ):
        refuse(
            "Final evaluation requires a frozen v2 policy; draft/null policies refuse"
        )
    if (
        not isinstance(first_test_access_at, datetime)
        or first_test_access_at.utcoffset() is None
    ):
        refuse("First test access is required with an explicit timezone")
    locked = timestamp(payload["locked_at"])
    if (
        locked >= first_test_access_at
        or locked > datetime.now(UTC)
        or first_test_access_at > datetime.now(UTC)
    ):
        refuse(
            "Policy must be frozen strictly before first test access, not in the future"
        )
    _identity(payload["review_reference"])
    for field, actual in [
        ("scope_manifest_sha256", scope.scope_sha256),
        ("split_manifest_sha256", scope.split_sha256),
    ]:
        if digest(_identity(payload[field])) != actual:
            refuse("Policy scope/split identity differs from actual supplied manifests")
    fixed_profiles = {
        "spatial_support_policy": "same-footprint-wgs84-buffer-lower-bound-v1",
        "temporal_support_policy": "exact-typed-bp-interval-v1",
        "zero_missing_policy": "closed-fractions-missing-unscored-no-pseudocount-v1",
        "multiplicity_policy": "all-predeclared-cells-no-p-values-v1",
    }
    if any(payload[key] != expected for key, expected in fixed_profiles.items()):
        refuse("Unsupported support, missing-data or multiplicity profile")
    references = payload["independent_vegetation_reference_ids"]
    if not isinstance(references, (tuple, list)):
        refuse("Independent measured vegetation references must be explicit")
    reference_ids = tuple(_identity(x) for x in cast(list[object], references))
    if len(set(reference_ids)) != len(reference_ids):
        refuse("Duplicate vegetation reference identity")
    raw_cells = payload["cells"]
    if not isinstance(raw_cells, (tuple, list)) or not raw_cells:
        refuse("Policy must predeclare all acceptance cells")
    cells = []
    strata = {"all"} | {stratum for site in scope.sites for stratum in site.strata}
    for value in cast(list[object], raw_cells):
        if not isinstance(value, Mapping) or frozenset(value) != CELL_KEYS:
            refuse("Acceptance cell has unknown or missing fields")
        row = cast(Mapping[str, object], value)
        target, experiment = _identity(row["target"]), _identity(row["experiment"])
        if target not in {
            "vegetation_cover",
            "pollen_composition",
        } or experiment not in {"local_pollen_available", "all_target_pollen_withheld"}:
            refuse("Unsupported target or experiment")
        if experiment == "local_pollen_available" and target == "pollen_composition":
            refuse("Pollen fitted locally is not a held-out pollen target")
        if target == "vegetation_cover" and not reference_ids:
            refuse("Vegetation cells require independent measured reference identities")
        model, baseline, subgroup = (
            _identity(row[x]) for x in ("model_id", "baseline_id", "subgroup")
        )
        if model == baseline or subgroup not in strata:
            refuse(
                "Baseline must differ from model and subgroup must belong to frozen scope"
            )
        nominal = _number(row["nominal_predictive_coverage"], lower=0, upper=1)
        if nominal in {0, 1}:
            refuse("Nominal predictive coverage must lie strictly between zero and one")
        cells.append(
            AcceptanceCell(
                _identity(row["cell_id"]),
                cast(Experiment, experiment),
                cast(Target, target),
                model,
                baseline,
                subgroup,
                _number(row["maximum_mae_pp"], lower=0, upper=100),
                _number(row["minimum_baseline_improvement_pp"], lower=0, upper=100),
                _integer(row["minimum_sites"]),
                _integer(row["minimum_blocks"]),
                _number(row["maximum_prediction_failure_fraction"], lower=0, upper=1),
                _number(row["maximum_exclusion_fraction"], lower=0, upper=1),
                nominal,
                _number(row["coverage_tolerance"], lower=0, upper=1),
                _identity(row["interval_profile_id"]),
            )
        )
    if len({x.cell_id for x in cells}) != len(cells) or len(
        {(x.experiment, x.target, x.model_id, x.baseline_id, x.subgroup) for x in cells}
    ) != len(cells):
        refuse("Duplicate acceptance cell identity or comparison")
    serialized = canonical_json(dict(payload))
    return EvaluationPolicy(
        serialized,
        manifest_sha256(json.loads(serialized)),
        scope.scope_sha256,
        scope.split_sha256,
        first_test_access_at,
        tuple(cells),
        _number(payload["minimum_buffer_m"], lower=0, upper=40_100_000),
        reference_ids,
    )
