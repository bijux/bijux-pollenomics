"""Keep current Python, original R and release observations in distinct scopes."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.controlled_numerical.python_reference import (
    PREFIX,
    validate_products,
)

ROOT = Path(__file__).resolve().parents[7]


def products() -> tuple[dict[str, Any], dict[str, Any]]:
    directory = ROOT / PREFIX
    return (
        json.loads((directory / "current-python-comparison.json").read_bytes()),
        json.loads((directory / "current-python-trace-index.json").read_bytes()),
    )


def test_completed_comparison_preserves_original_R_and_author_epochs() -> None:
    evidence = validate_products(*products())
    assert evidence["current_core_cases"] == 43
    assert evidence["current_domain_cases"] == 23
    assert evidence["new_model_R_comparison_calls"] == 0


@pytest.mark.parametrize(
    "mutation",
    [
        "case",
        "tolerance",
        "mask",
        "failed",
        "R",
        "release",
        "future",
        "collector",
        "timeout",
        "vector",
        "author",
    ],
)
def test_observation_rejects_scientific_or_epoch_promotion(mutation: str) -> None:
    report, trace = copy.deepcopy(products())
    if mutation == "case":
        report["core"][1] = report["core"][0]
    elif mutation == "tolerance":
        report["core"][0]["atol"] *= 100
    elif mutation == "mask":
        report["source_domains"][0]["residual_diagnostics"]["NaN_masks_equal"] = False
    elif mutation == "failed":
        report["core"][0]["status"] = "failed"
    elif mutation == "R":
        report["fresh_R_executed"] = True
    elif mutation == "release":
        report["release_certificate"] = True
    elif mutation == "future":
        trace["scope"]["current_publication_HEAD_recomputation_claimed"] = True
    elif mutation == "collector":
        trace["execution"]["record"]["collector_exit"] = 1
    elif mutation == "timeout":
        trace["execution"]["record"]["timed_out"] = True
    elif mutation == "vector":
        report["source_domains"][0]["current_Python"]["sha256"] = "0" * 64
    elif mutation == "author":
        report["reused_author_comparison"]["original_whole_exit"] = 0
    with pytest.raises(ReportRebuildError):
        validate_products(report, trace)
