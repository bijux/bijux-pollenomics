"""Orchestrate complete policy-owned count reconciliation derivation."""

from __future__ import annotations

from itertools import product
from pathlib import Path

from ...release_evidence.models import (
    _COUNTRIES,
    CountReconciliation,
    _ReleaseEvidencePolicy,
)
from .country import governed_country_values
from .propagation import propagation_scope_counts, scope_suffix
from .records import aggregate_source_count, derived_count, unavailable_count


def derive_reconciliations(
    root: Path, policy: _ReleaseEvidencePolicy
) -> tuple[CountReconciliation, ...]:
    """Derive every source and partition count required by policy."""
    rows: list[CountReconciliation] = []
    propagation_manifest_path = next(
        (
            artifact.path
            for artifact in policy.required_artifacts
            if artifact.identity == "propagation"
        ),
        None,
    )
    propagation_reconciliation_path = (
        str(
            Path(propagation_manifest_path).with_name(
                "primary_scenario_reconciliation.json"
            )
        )
        if propagation_manifest_path is not None
        else None
    )
    for requirement in policy.required_reconciliations:
        stem = f"{requirement.source}.{requirement.entity}"
        if requirement.dimension == "country":
            values = governed_country_values(root, requirement)
            partitions: list[CountReconciliation] = []
            for country_code in sorted(_COUNTRIES):
                if values is None:
                    partition = unavailable_count(
                        f"{stem}.country.{country_code.lower()}",
                        requirement,
                        "country",
                        country_code=country_code,
                    )
                else:
                    partition = derived_count(
                        f"{stem}.country.{country_code.lower()}",
                        requirement,
                        "country",
                        values[country_code],
                        country_code=country_code,
                    )
                partitions.append(partition)
            rows.append(
                aggregate_source_count(f"{stem}.source", requirement, partitions)
            )
            rows.extend(partitions)
            continue
        scope_partitions = propagation_scope_counts(
            root,
            requirement,
            reconciliation_path=propagation_reconciliation_path,
        )
        if scope_partitions is None:
            scope_partitions = []
            scope_keys = tuple(key for key, _values in requirement.scope_values)
            for scope_values in product(
                *(values for _key, values in requirement.scope_values)
            ):
                scope = tuple(zip(scope_keys, scope_values, strict=True))
                scope_partitions.append(
                    unavailable_count(
                        f"{stem}.scope.{scope_suffix(scope)}",
                        requirement,
                        "scope",
                        scope=scope,
                    )
                )
        rows.append(
            aggregate_source_count(f"{stem}.source", requirement, scope_partitions)
        )
        rows.extend(scope_partitions)
    return tuple(rows)
