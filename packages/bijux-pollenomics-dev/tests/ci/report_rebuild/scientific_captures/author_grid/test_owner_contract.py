"""Retain strict three-owner and typed-value boundaries without a native packet."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.author_grid import (
    admission,
    historical_reader,
    transport,
)


def owners() -> list[dict[str, Any]]:
    """Construct only the three declared output roles, with no source inputs."""
    return [
        {
            "owner_id": owner,
            "role": "retained_source",
            "paths": paths.copy(),
            "producer_paths": [],
            "producer_inputs": [],
        }
        for owner, paths in admission.OWNERS.items()
    ]


def test_exact_three_retained_owners_are_distinct() -> None:
    assert admission.owner_rows(owners()) == owners()


@pytest.mark.parametrize(
    "change",
    ["role", "producer", "input", "missing", "duplicate", "paths", "sibling-overlap"],
)
def test_original_unqualified_or_overlapping_owner_refusals(change: str) -> None:
    selected = owners()
    if change == "role":
        selected[0]["role"] = "generated_owner"
    elif change == "producer":
        selected[0]["producer_paths"] = ["writer.py"]
    elif change == "input":
        selected[0]["producer_inputs"] = ["other.json"]
    elif change == "missing":
        selected.pop()
    elif change == "duplicate":
        selected.append(deepcopy(selected[0]))
    elif change == "paths":
        selected[0]["paths"].append(historical_reader.FAMILY + "README.md")
    else:
        selected.append(
            {
                "owner_id": "unrelated",
                "role": "unresolved",
                "paths": [next(iter(admission.PRODUCTS))],
            }
        )
    with pytest.raises((ValueError, ReportRebuildError)):
        admission.owner_rows(selected)


def test_disjoint_reader_is_not_a_numerical_report_role() -> None:
    reader: JsonObject = {
        "owner_id": "reader",
        "role": "maintained_editorial",
        "paths": [historical_reader.FAMILY + "README.md"],
    }
    assert len(admission.owner_rows([*owners(), reader])) == 3
    assert admission.validated_author_grid_capture(Path("/unused"), {}, [reader]) == (
        (),
        {},
    )


@pytest.mark.parametrize(
    ("value", "wanted"), [(False, 0), (None, 0), (0.0, 0), (True, 1)]
)
def test_original_typed_zero_and_unknown_refusals(value: object, wanted: int) -> None:
    with pytest.raises(ValueError):
        transport.typed(value, wanted)
