"""Six-bin batch completeness controls before any actual artifact observation."""

from copy import deepcopy
from typing import Any

import pytest

from .materialization import NAMES
from .scalar import METHODS
from .verification import closed_batch


def batch_fixture() -> dict[str, Any]:
    bins: list[dict[str, Any]] = [
        {
            "bin": name,
            "folds": [{"fold_id": fold} for fold in ("a", "b", "c")],
            "method_dispositions": [
                {"fold_id": fold, "method": method, "status": "predicted"}
                for fold in ("a", "b", "c")
                for method in METHODS
            ],
        }
        for name in NAMES
    ]
    dispositions = [
        {"bin": row["bin"], **item}
        for row in bins
        for item in row["method_dispositions"]
    ]
    return {
        "schema_version": "krageholm-regional-coupled-batch.v1",
        "operation": "prepare",
        "source_commit": "synthetic",
        "protocol": {"path": "prospective protocol"},
        "all_bins_accounted": True,
        "requested_folds": 18,
        "requested_method_dispositions": 54,
        "scientific_acceptance": "not_evaluated",
        "exposure": "prior_exposed_development",
        "bins": bins,
        "method_dispositions": dispositions,
        "status_counts": {"predicted": 54},
    }


def test_exact_six_bins18_folds54_dispositions_close() -> None:
    closed_batch(
        batch_fixture(), "prepare", "synthetic", {"path": "prospective protocol"}
    )


@pytest.mark.parametrize(
    "corruption",
    [
        "missing_bin",
        "duplicate_bin",
        "incomplete",
        "missing_fold",
        "duplicate_method",
        "status_count",
        "source_commit",
        "scientific_admission",
    ],
)
def test_incomplete_or_misrepresented_fixed_population_refuses(corruption: str) -> None:
    value = deepcopy(batch_fixture())
    if corruption == "missing_bin":
        value["bins"].pop()
    elif corruption == "duplicate_bin":
        value["bins"][1]["bin"] = value["bins"][0]["bin"]
    elif corruption == "incomplete":
        value["all_bins_accounted"] = False
    elif corruption == "missing_fold":
        value["bins"][0]["folds"].pop()
    elif corruption == "duplicate_method":
        value["bins"][0]["method_dispositions"][1] = value["bins"][0][
            "method_dispositions"
        ][0]
    elif corruption == "status_count":
        value["status_counts"]["predicted"] = 53
    elif corruption == "source_commit":
        value["source_commit"] = "another"
    else:
        value["scientific_acceptance"] = "accepted"
    with pytest.raises(ValueError):
        closed_batch(value, "prepare", "synthetic", {"path": "prospective protocol"})
