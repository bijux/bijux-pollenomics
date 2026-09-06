"""Construct canonical source, partition, and unavailable count records."""

from __future__ import annotations

from typing import cast

from ...release_evidence.models import (
    CountReconciliation,
    ReconciliationDimension,
    _RequiredReconciliation,
)
from .model import DerivedCount


def reported_count(
    identity: str,
    requirement: _RequiredReconciliation,
    dimension: ReconciliationDimension,
    value: int,
    *,
    country_code: str | None = None,
    scope: tuple[tuple[str, str], ...] = (),
) -> CountReconciliation:
    """Build a fully accepted reported count."""
    return CountReconciliation(
        identity=identity,
        dimension=dimension,
        source=requirement.source,
        entity=requirement.entity,
        country_code=country_code,
        candidate_count=value,
        eligible_count=value,
        accepted_count=value,
        unresolved_count=0,
        excluded_count=0,
        refused_count=0,
        scope=scope,
        count_status="reported",
        reason_codes=(),
    )


def derived_count(
    identity: str,
    requirement: _RequiredReconciliation,
    dimension: ReconciliationDimension,
    value: DerivedCount,
    *,
    country_code: str | None = None,
    scope: tuple[tuple[str, str], ...] = (),
) -> CountReconciliation:
    """Build a reported count carrying a derived terminal posture."""
    return CountReconciliation(
        identity=identity,
        dimension=dimension,
        source=requirement.source,
        entity=requirement.entity,
        country_code=country_code,
        candidate_count=value.candidate,
        eligible_count=value.eligible,
        accepted_count=value.accepted,
        unresolved_count=value.unresolved,
        excluded_count=value.excluded,
        refused_count=value.refused,
        scope=scope,
        count_status="reported",
        reason_codes=value.reason_codes,
    )


def aggregate_source_count(
    identity: str,
    requirement: _RequiredReconciliation,
    partitions: list[CountReconciliation],
) -> CountReconciliation:
    """Aggregate only fully reported partitions into a source count."""
    if any(item.count_status != "reported" for item in partitions):
        return unavailable_count(identity, requirement, "source")
    fields = {
        field: sum(cast(int, getattr(item, field)) for item in partitions)
        for field in (
            "candidate_count",
            "eligible_count",
            "accepted_count",
            "unresolved_count",
            "excluded_count",
            "refused_count",
        )
    }
    return CountReconciliation(
        identity=identity,
        dimension="source",
        source=requirement.source,
        entity=requirement.entity,
        country_code=None,
        scope=(),
        count_status="reported",
        reason_codes=(),
        **fields,
    )


def unavailable_count(
    identity: str,
    requirement: _RequiredReconciliation,
    dimension: ReconciliationDimension,
    *,
    country_code: str | None = None,
    scope: tuple[tuple[str, str], ...] = (),
) -> CountReconciliation:
    """Represent unavailable or refused evidence without inventing zeros."""
    return CountReconciliation(
        identity=identity,
        dimension=dimension,
        source=requirement.source,
        entity=requirement.entity,
        country_code=country_code,
        candidate_count=None,
        eligible_count=None,
        accepted_count=None,
        unresolved_count=None,
        excluded_count=None,
        refused_count=None,
        scope=scope,
        count_status=requirement.unavailable_status,
        reason_codes=(requirement.unavailable_reason_code,),
    )


def reconciliation_record(item: CountReconciliation) -> dict[str, object]:
    """Translate a count reconciliation into the canonical request record."""
    return {
        "identity": item.identity,
        "dimension": item.dimension,
        "source": item.source,
        "entity": item.entity,
        "country_code": item.country_code,
        "candidate_count": item.candidate_count,
        "eligible_count": item.eligible_count,
        "accepted_count": item.accepted_count,
        "unresolved_count": item.unresolved_count,
        "excluded_count": item.excluded_count,
        "refused_count": item.refused_count,
        "scope": dict(item.scope),
        "count_status": item.count_status,
        "reason_codes": list(item.reason_codes),
    }
