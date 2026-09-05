"""Derive scoped propagation reconciliation counts."""

from __future__ import annotations

from collections.abc import Mapping
from itertools import product
from pathlib import Path

from ...release_evidence.models import CountReconciliation
from ...release_evidence.models import _RequiredReconciliation
from .json_object import optional_json_object
from .records import reported_count


def propagation_scope_counts(
    root: Path,
    requirement: _RequiredReconciliation,
    *,
    reconciliation_path: str | None,
) -> list[CountReconciliation] | None:
    """Derive a complete scoped account from the primary propagation scenario."""
    if (
        requirement.derivation_adapter != "propagation_primary_reconciliation"
        or reconciliation_path is None
    ):
        return None
    document = optional_json_object(root, reconciliation_path)
    reconciliation = document.get("reconciliation") if document else None
    if not isinstance(reconciliation, Mapping):
        return None
    stem = f"{requirement.source}.{requirement.entity}"
    scopes = required_scopes(requirement)
    if requirement.derivation_metric == "candidate_statuses":
        status_counts = reconciliation.get("status_counts")
        if not isinstance(status_counts, Mapping):
            return None
        rows: list[CountReconciliation] = []
        for scope in scopes:
            status = dict(scope)["status"]
            value = status_counts.get(status)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                return None
            rows.append(
                propagation_status_count(stem, requirement, scope, status, value)
            )
        return rows
    total_field = {
        "evaluated_pairs": "evaluated_pair_count",
        "nodes": "input_event_count",
        "pair_refusals": "refused_pair_count",
    }.get(requirement.derivation_metric)
    total = reconciliation.get(total_field) if total_field else None
    if isinstance(total, bool) or not isinstance(total, int) or total != 0:
        return None
    return [
        reported_count(
            f"{stem}.scope.{scope_suffix(scope)}",
            requirement,
            "scope",
            0,
            scope=scope,
        )
        for scope in scopes
    ]


def required_scopes(
    requirement: _RequiredReconciliation,
) -> tuple[tuple[tuple[str, str], ...], ...]:
    """Expand the governed Cartesian scope in stable policy order."""
    keys = tuple(key for key, _values in requirement.scope_values)
    return tuple(
        tuple(zip(keys, values, strict=True))
        for values in product(*(values for _key, values in requirement.scope_values))
    )


def scope_suffix(scope: tuple[tuple[str, str], ...]) -> str:
    """Encode a governed scope as a stable reconciliation identity suffix."""
    return ".".join(f"{key}-{value.lower()}" for key, value in scope)


def propagation_status_count(
    stem: str,
    requirement: _RequiredReconciliation,
    scope: tuple[tuple[str, str], ...],
    status: str,
    value: int,
) -> CountReconciliation:
    """Assign propagation statuses to accepted, unresolved, or excluded counts."""
    fields = {
        "candidate_count": value,
        "eligible_count": 0,
        "accepted_count": 0,
        "unresolved_count": 0,
        "excluded_count": 0,
        "refused_count": 0,
    }
    if status in {"definite_candidate", "possible_candidate"}:
        fields["eligible_count"] = value
        fields["accepted_count"] = value
    elif status in {"indeterminate_order", "unresolved"}:
        fields["unresolved_count"] = value
    else:
        fields["excluded_count"] = value
    return CountReconciliation(
        identity=f"{stem}.scope.{scope_suffix(scope)}",
        dimension="scope",
        source=requirement.source,
        entity=requirement.entity,
        country_code=None,
        scope=scope,
        count_status="reported",
        reason_codes=(),
        **fields,
    )
