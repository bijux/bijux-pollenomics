"""Reconciliation tests."""

from __future__ import annotations
from pathlib import Path
from typing import cast
import pytest
from bijux_pollenomics.provenance import (
    CountReconciliation,
    ReleaseEvidenceError,
)
from .conftest import _artifacts, _build, _reconciliations, _rewrite_fixture_policy


def test_null_counts_are_rejected_while_zero_is_valid(tmp_path: Path) -> None:
    manifest = _build(tmp_path)
    rows = cast(list[dict[str, object]], manifest["reconciliations"])
    zero_row = next(row for row in rows if row["country_code"] == "FI")
    assert zero_row["candidate_count"] == 0

    reconciliations = _reconciliations()
    fi = next(item for item in reconciliations if item.country_code == "FI")
    reconciliations[reconciliations.index(fi)] = CountReconciliation(
        **{**fi.__dict__, "candidate_count": None}
    )
    with pytest.raises(ReleaseEvidenceError, match="non-null"):
        _build(tmp_path, reconciliations=reconciliations)


def test_country_totals_must_reconcile_to_source_without_omission(
    tmp_path: Path,
) -> None:
    missing_unassigned = [
        item for item in _reconciliations() if item.country_code != "UNASSIGNED"
    ]
    with pytest.raises(ReleaseEvidenceError, match="complete country reconciliation"):
        _build(tmp_path, reconciliations=missing_unassigned)

    reconciliations = _reconciliations()
    se = next(item for item in reconciliations if item.country_code == "SE")
    reconciliations[reconciliations.index(se)] = CountReconciliation(
        **{**se.__dict__, "candidate_count": 5, "excluded_count": 1}
    )
    with pytest.raises(ReleaseEvidenceError, match="country/source count mismatch"):
        _build(tmp_path, reconciliations=reconciliations)

    missing_outside = [
        item for item in _reconciliations() if item.country_code != "OUTSIDE"
    ]
    with pytest.raises(ReleaseEvidenceError, match="complete country reconciliation"):
        _build(tmp_path, reconciliations=missing_outside)


def test_caller_cannot_omit_a_policy_required_source_entity_group(
    tmp_path: Path,
) -> None:
    other_group = [
        CountReconciliation(
            **{
                **item.__dict__,
                "identity": item.identity.replace("neotoma", "sead"),
                "source": "sead",
            }
        )
        for item in _reconciliations()
    ]

    with pytest.raises(
        ReleaseEvidenceError, match="missing required reconciliation groups"
    ):
        _build(tmp_path, reconciliations=other_group)


def test_unavailable_counts_remain_null_and_reason_coded(tmp_path: Path) -> None:
    unavailable = [
        CountReconciliation(
            **{
                **item.__dict__,
                "candidate_count": None,
                "eligible_count": None,
                "accepted_count": None,
                "unresolved_count": None,
                "excluded_count": None,
                "refused_count": None,
                "count_status": "unavailable",
                "reason_codes": ("source_dimension_unavailable",),
            }
        )
        for item in _reconciliations()
    ]

    manifest = _build(tmp_path, reconciliations=unavailable)

    rows = cast(list[dict[str, object]], manifest["reconciliations"])
    assert all(row["candidate_count"] is None for row in rows)
    assert all(row["count_status"] == "unavailable" for row in rows)


def test_reconciliation_rejects_unexpected_groups_and_mixed_availability(
    tmp_path: Path,
) -> None:
    unexpected = [
        CountReconciliation(
            **{
                **item.__dict__,
                "identity": item.identity.replace("neotoma", "sead"),
                "source": "sead",
            }
        )
        for item in _reconciliations()
    ]
    with pytest.raises(ReleaseEvidenceError, match="unexpected reconciliation groups"):
        _build(tmp_path, reconciliations=[*_reconciliations(), *unexpected])

    unavailable = [
        CountReconciliation(
            **{
                **item.__dict__,
                "candidate_count": None,
                "eligible_count": None,
                "accepted_count": None,
                "unresolved_count": None,
                "excluded_count": None,
                "refused_count": None,
                "count_status": "unavailable",
                "reason_codes": ("source_dimension_unavailable",),
            }
        )
        for item in _reconciliations()
    ]
    country_row = unavailable[1]
    unavailable[1] = CountReconciliation(
        **{
            **country_row.__dict__,
            "count_status": "refused",
            "reason_codes": ("source_dimension_refused",),
        }
    )
    with pytest.raises(ReleaseEvidenceError, match="availability statuses differ"):
        _build(tmp_path, reconciliations=unavailable)


def test_policy_owned_scope_cross_product_cannot_be_omitted(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)

    def require_statuses(policy: dict[str, object]) -> None:
        requirements = cast(list[dict[str, object]], policy["required_reconciliations"])
        requirements[0]["dimension"] = "scope"
        requirements[0]["scope_values"] = {"status": ["accepted", "refused"]}

    _rewrite_fixture_policy(tmp_path, artifacts, require_statuses)
    rows = [
        CountReconciliation(
            identity="neotoma.samples.source",
            dimension="source",
            source="neotoma",
            entity="samples",
            country_code=None,
            candidate_count=0,
            eligible_count=0,
            accepted_count=0,
            unresolved_count=0,
            excluded_count=0,
            refused_count=0,
        ),
        CountReconciliation(
            identity="neotoma.samples.accepted",
            dimension="scope",
            source="neotoma",
            entity="samples",
            country_code=None,
            scope=(("status", "accepted"),),
            candidate_count=0,
            eligible_count=0,
            accepted_count=0,
            unresolved_count=0,
            excluded_count=0,
            refused_count=0,
        ),
    ]

    with pytest.raises(
        ReleaseEvidenceError, match="scope partition inventory mismatch"
    ):
        _build(tmp_path, artifacts=artifacts, reconciliations=rows)
