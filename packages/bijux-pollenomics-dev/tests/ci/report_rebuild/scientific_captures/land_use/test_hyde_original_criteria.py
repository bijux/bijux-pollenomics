"""Preserve original owner criteria independently of positive source evidence."""

from __future__ import annotations

import importlib
from copy import deepcopy
from types import ModuleType
from typing import Any

import pytest
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

EXPECTED: dict[str, dict[str, Any]] = {
    "land_use.hyde_country": {
        "owner_id": "regions/nordic/hyde-country-cropland/report-products",
        "paths": [
            "docs/report/regions/nordic/hyde-country-cropland/country-years.csv",
            "docs/report/regions/nordic/hyde-country-cropland/report.json",
        ],
        "producer_inputs": [],
        "producer_paths": [
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/hyde_country_cropland.py"
        ],
        "role": "unresolved",
        "verification": "The retained country-year producer is `bijux_pollenomics_dev.source_completion.hyde_country_cropland --source-root <governed-HYDE-3.5-root> --output artifacts/jobs/vegetation-context-reproduction/hyde-country`. It reads the external general ZIP and three scenario country tables pinned in report.json. Bind exact HYDE release/source custody and permitted use before a fresh-output byte comparison of country-years.csv and report.json; no source grid, redistribution, calendar, CRS, or ecological reference acceptance is implied.",
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
