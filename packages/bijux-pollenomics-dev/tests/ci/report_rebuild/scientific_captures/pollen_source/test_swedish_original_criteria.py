"""Preserve original owner criteria independently of positive source evidence."""

from __future__ import annotations

from copy import deepcopy
import importlib
from types import ModuleType
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

EXPECTED: dict[str, dict[str, Any]] = {
    "pollen_source.swedish_cohort": {
        "owner_id": "source-relations/neotoma/swedish-cohort-availability/source-screen",
        "role": "unresolved",
        "paths": [
            "docs/report/source-relations/neotoma/swedish-cohort-availability/report.json"
        ],
        "producer_paths": [
            "docs/report/source-relations/neotoma/swedish-cohort-availability/replay.py"
        ],
        "producer_inputs": [
            "data/neotoma/relational/manifest.json",
            "data/neotoma/relational/surfaces/collection_units/part-00001.json",
            "data/neotoma/relational/surfaces/datasets/part-00001.json",
            "data/neotoma/relational/surfaces/sites/part-00001.json",
            "docs/report/source-relations/neotoma/swedish-cohort-availability/sources.json",
        ],
        "verification": "Replay requires --private-root: private source-manifest.json plus seven source records, EPD source-manifest.json and 17 metadata/age-table files. Those are not repository-confined; keep unresolved until exact private capture custody, permission and byte comparison are independently bound. Metadata-only refusal is not fresh-cohort acceptance.",
    }
}


def reader(name: str) -> ModuleType:
    return importlib.import_module(
        "bijux_pollenomics_dev.ci.report_rebuild.scientific_captures." + name
    )


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_exact_original_contract_remains_unresolved(name: str) -> None:
    module = reader(name)
    expected = deepcopy(EXPECTED[name])
    assert expected["role"] == "unresolved"
    assert expected == module.ORIGINAL_OWNER
    assert module._validate_original_owner([expected]) is None


@pytest.mark.parametrize("name", sorted(EXPECTED))
@pytest.mark.parametrize(
    "change",
    [
        "owner_id",
        "role",
        "paths",
        "producer_paths",
        "producer_inputs",
        "verification",
        "extra",
        "missing",
    ],
)
def test_original_contract_field_tampering_refuses(name: str, change: str) -> None:
    module = reader(name)
    owner = deepcopy(EXPECTED[name])
    if change == "owner_id":
        owner[change] = "constructed/other-owner"
    elif change == "role":
        owner[change] = "retained_source"
    elif change in {"paths", "producer_paths", "producer_inputs"}:
        owner[change] = [*owner[change], "constructed/other-member"]
    elif change == "verification":
        owner[change] += " Unsupported criterion change."
    elif change == "extra":
        owner["acceptance_discharged"] = True
    else:
        del owner["verification"]
    with pytest.raises(ReportRebuildError):
        module._validate_original_owner([owner])


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_duplicate_original_owner_refuses(name: str) -> None:
    module = reader(name)
    expected = deepcopy(EXPECTED[name])
    with pytest.raises(ReportRebuildError):
        module._validate_original_owner([expected, deepcopy(expected)])


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_other_owner_cannot_overlap_partial_evidence(name: str) -> None:
    module = reader(name)
    expected = deepcopy(EXPECTED[name])
    other = {"owner_id": "constructed/other-owner", "paths": [expected["paths"][0]]}
    with pytest.raises(ReportRebuildError):
        module._validate_original_owner([expected, other])


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_unrelated_owner_does_not_change_original_contract(name: str) -> None:
    module = reader(name)
    expected = deepcopy(EXPECTED[name])
    unrelated = {
        "owner_id": "constructed/unrelated-owner",
        "paths": ["docs/report/constructed/unrelated.json"],
    }
    assert module._validate_original_owner([expected, unrelated]) is None
