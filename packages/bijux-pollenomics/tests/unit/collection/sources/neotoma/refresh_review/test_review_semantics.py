from __future__ import annotations

import copy
import hashlib
from typing import Any, cast

import pytest

import bijux_pollenomics.collection.sources.neotoma.refresh_review as refresh_review


def _baseline() -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": "neotoma-refresh-baseline.v1",
        "source_family": "neotoma",
        "identity": {"build_id": "build", "source_snapshot_id": "source"},
        "schemas": {"sites": "sites.v1"},
        "counts": {"sites": 4, "observations": 10},
        "input_artifacts": {"raw": {"sha256": "a" * 64}},
    }
    value["baseline_id"] = (
        "sha256:" + hashlib.sha256(refresh_review._canonical_json(value)).hexdigest()
    )
    return value


def _rehash(value: dict[str, object]) -> None:
    value.pop("baseline_id", None)
    value["baseline_id"] = (
        "sha256:" + hashlib.sha256(refresh_review._canonical_json(value)).hexdigest()
    )


def test_fixed_point_reconciles_every_denominator_without_approval_claim() -> None:
    baseline = _baseline()
    review = refresh_review.build_neotoma_refresh_review(baseline, baseline)

    assert review["status"] == "fixed_point"
    assert review["change_count"] == 0
    assert review["unexplained_change_count"] == 0
    assert review["fixed_point"] is True
    assert review["baseline_update_permitted"] is True
    assert review["review_posture"] == "no_refresh_drift"
    assert review["zero_diff_proof"] == {
        "identity_equal": True,
        "schemas_equal": True,
        "counts_equal": True,
        "input_artifacts_equal": True,
    }


def test_changes_are_deterministic_typed_and_denominator_complete() -> None:
    prior = _baseline()
    candidate = copy.deepcopy(prior)
    counts = candidate["counts"]
    assert isinstance(counts, dict)
    counts["sites"] = 6
    counts["samples"] = 12
    _rehash(candidate)

    review = refresh_review.build_neotoma_refresh_review(
        prior,
        candidate,
        explanations={"counts:sites": "Expected scope growth."},
    )

    assert review["status"] == "review_required"
    assert review["change_count"] == 2
    assert review["unexplained_change_count"] == 1
    assert review["baseline_update_permitted"] is False
    changes = cast(list[dict[str, object]], review["changes"])
    assert [change["change_id"] for change in changes] == [
        "counts:samples",
        "counts:sites",
    ]
    assert changes == [
        {
            "change_id": "counts:samples",
            "section": "counts",
            "field": "samples",
            "change_kind": "added",
            "prior": None,
            "candidate": 12,
            "explanation": None,
        },
        {
            "change_id": "counts:sites",
            "section": "counts",
            "field": "sites",
            "change_kind": "increased",
            "prior": 4,
            "candidate": 6,
            "explanation": "Expected scope growth.",
            "delta": 2,
        },
    ]


def test_missing_baselines_remain_explicit_null_refusals() -> None:
    review = refresh_review.build_neotoma_refresh_review(
        None,
        None,
        missing_reasons=["source_unavailable", "missing_prior_baseline"],
    )

    assert review == {
        "schema_version": "neotoma-refresh-review.v1",
        "source_family": "neotoma",
        "status": "refused",
        "refusal_reasons": [
            "missing_candidate_baseline",
            "missing_prior_baseline",
            "source_unavailable",
        ],
        "prior_baseline_id": None,
        "candidate_baseline_id": None,
        "change_count": 0,
        "unexplained_change_count": 0,
        "fixed_point": False,
        "baseline_update_permitted": False,
        "changes": [],
    }


def test_review_resolves_collection_seam_from_facade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def collect(changes: list[dict[str, object]], **kwargs: Any) -> None:
        calls.append(str(kwargs["section"]))

    monkeypatch.setattr(refresh_review, "_collect_changes", collect)
    baseline = _baseline()
    review = refresh_review.build_neotoma_refresh_review(baseline, baseline)

    assert calls == ["identity", "schemas", "counts", "input_artifacts"]
    assert review["status"] == "fixed_point"


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        (lambda: refresh_review._mapping([], "payload"), "Expected object for payload"),
        (
            lambda: refresh_review._non_negative_integer(None, "count"),
            "Expected non-negative integer for count",
        ),
        (
            lambda: refresh_review._safe_public_path("../escape"),
            "Unsafe Neotoma public path: '../escape'",
        ),
    ],
)
def test_refusal_text_is_preserved(operation: Any, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        operation()
