"""Observation symmetry rules for paired final-evaluation rows."""

from __future__ import annotations

import json

from ..contracts import EvaluationPolicy, EvaluationRow, EvaluationScope, refuse
from ..policy import validate_evaluation_policy


def assert_final_inputs(
    policy: EvaluationPolicy,
    scope: EvaluationScope,
    rows: tuple[EvaluationRow, ...],
) -> None:
    """Replay the canonical policy and require one immutable typed row ledger."""
    checked = validate_evaluation_policy(
        json.loads(policy.canonical_policy_json),
        scope=scope,
        first_test_access_at=policy.first_test_access_at,
    )
    if checked != policy:
        refuse("Policy object differs from its canonical immutable declaration")
    if not isinstance(rows, tuple) or any(
        not isinstance(row, EvaluationRow) for row in rows
    ):
        refuse("Evaluation requires a complete typed immutable row ledger")


def assert_pair_observations(
    model: EvaluationRow,
    baseline: EvaluationRow,
    *,
    authenticated_failures: bool,
) -> None:
    """Keep predicted pairs symmetric while admitting value-free failed parents."""
    rows = (model, baseline)
    failed = tuple(row for row in rows if row.status == "prediction_failed")
    if authenticated_failures and any(
        any(
            value is not None
            for value in (
                row.observation,
                row.observation_reference_id,
                row.observation_kind,
                row.observation_support,
            )
        )
        for row in failed
    ):
        refuse("Authenticated failed predictions must remain observation-free")
    fields = tuple(
        (
            row.observation,
            row.observation_reference_id,
            row.observation_kind,
            row.observation_support,
        )
        for row in rows
    )
    if fields[0] == fields[1] or (authenticated_failures and failed):
        return
    refuse("Paired baseline and model must use identical observation values/support")
