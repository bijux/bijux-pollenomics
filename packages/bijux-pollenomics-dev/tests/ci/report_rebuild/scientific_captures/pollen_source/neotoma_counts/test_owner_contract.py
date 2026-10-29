"""Keep current count evidence separate from unresolved original mass custody."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source.neotoma_counts import (
    selected_counts as subject,
)


def owners() -> list[dict[str, Any]]:
    return [
        {
            "owner_id": owner,
            "role": "unresolved",
            "paths": [path],
            "producer_paths": [],
            "producer_inputs": [],
            "verification": subject.ORIGINAL_COUNT_CRITERION,
        }
        for owner, path in subject.OWNERS.items()
    ]


def test_two_source_count_owners_preserve_original_unresolved_criterion() -> None:
    subject.ownership(owners())


@pytest.mark.parametrize(
    "change",
    [
        "role",
        "criterion",
        "paths",
        "producer",
        "input",
        "owner_id",
        "missing",
        "duplicate",
    ],
)
def test_count_custody_or_ownership_inflation_refuses(change: str) -> None:
    selected = owners()
    if change == "role":
        selected[0]["role"] = "retained_source"
    elif change == "criterion":
        selected[0]["verification"] += " Invented acceptance."
    elif change == "paths":
        selected[0]["paths"] = ["docs/report/constructed/other.json"]
    elif change == "producer":
        selected[0]["producer_paths"] = ["constructed.py"]
    elif change == "input":
        selected[0]["producer_inputs"] = ["constructed.json"]
    elif change == "owner_id":
        selected[0]["owner_id"] = "constructed/other"
    elif change == "missing":
        selected.pop()
    else:
        selected.append(deepcopy(selected[0]))
    with pytest.raises(ReportRebuildError):
        subject.ownership(selected)


def test_overlapping_sibling_cannot_claim_partial_count_path() -> None:
    selected = owners()
    selected.append({"owner_id": "constructed/sibling", "paths": selected[0]["paths"]})
    with pytest.raises(ReportRebuildError):
        subject.ownership(selected)


def test_unrelated_owner_does_not_discharge_or_invalidate_count_criterion() -> None:
    selected = owners()
    selected.append(
        {
            "owner_id": "constructed/unrelated",
            "paths": ["docs/report/constructed/other.json"],
        }
    )
    subject.ownership(selected)
