"""Compact summaries preserve the retained population and scientific refusals."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.source_completion.neotoma_screen_summary import (
    summary_bytes,
)

REPOSITORY = Path(__file__).resolve().parents[4]
REPORT = REPOSITORY / "docs/report/source-relations/neotoma/pollen-screen"


@pytest.fixture(scope="module")
def screen() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((REPORT / "report.json").read_bytes()))


def test_retained_compact_summary_reproduces_exact_bytes(
    screen: dict[str, Any],
) -> None:
    assert summary_bytes(screen) == (REPORT / "summary.json").read_bytes()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("lra_accepted_samples", 1),
        ("lra_accepted_samples", False),
        ("executable_request", {"sample_id": "invented"}),
        ("claims_not_made", []),
        ("screen_status", "accepted"),
    ],
)
def test_summary_refuses_admission_or_missing_scope(
    screen: dict[str, Any], field: str, value: Any
) -> None:
    changed = {**screen, field: value}
    with pytest.raises(ValueError, match="refusal-only"):
        summary_bytes(changed)


def test_summary_refuses_changed_candidate_digest(screen: dict[str, Any]) -> None:
    changed = {**screen, "candidate_sample_ids_sha256": "0" * 64}
    with pytest.raises(ValueError, match="population identity"):
        summary_bytes(changed)


def test_summary_refuses_lost_sample_decision(screen: dict[str, Any]) -> None:
    changed = {**screen, "sample_decisions": screen["sample_decisions"][1:]}
    with pytest.raises(ValueError, match="denominators|candidate IDs"):
        summary_bytes(changed)


def test_summary_refuses_changed_country_population(screen: dict[str, Any]) -> None:
    changed = {
        **screen,
        "country_denominators": copy.deepcopy(screen["country_denominators"]),
    }
    changed["country_denominators"]["SE"]["samples"] += 1
    with pytest.raises(ValueError, match="denominators"):
        summary_bytes(changed)
