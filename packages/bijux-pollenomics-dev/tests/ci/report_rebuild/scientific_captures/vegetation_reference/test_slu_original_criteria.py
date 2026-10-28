"""Preserve original owner criteria independently of positive source evidence."""

from __future__ import annotations

import importlib
from copy import deepcopy
from types import ModuleType
from typing import Any

import pytest
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

EXPECTED: dict[str, dict[str, Any]] = {
    "vegetation_reference.slu_guide": {
        "owner_id": "validation/empd2-nfi-pairing/calibration-guide",
        "paths": [
            "docs/report/validation/empd2-nfi-pairing/inputs/slu-calibration-guide.pdf"
        ],
        "producer_inputs": [],
        "producer_paths": [],
        "role": "unresolved",
        "verification": "The tracked SLU calibration guide is pinned as SHA-256 793d90e287b2c686d0007f02497e12e8a72a47e5a45531918d9fc71d78499bc8 in the EMPD2–NFI report. Bind its original provider retrieval/copy receipt and publication/use statement to these exact bytes before retained-source ownership; the pairing producer consumes the guide but does not produce it.",
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
    assert module.ORIGINAL_OWNER == expected
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
