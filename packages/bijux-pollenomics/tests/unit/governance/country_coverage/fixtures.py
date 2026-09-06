"""Governed country-coverage test fixtures and mutation helpers."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import cast

import pytest
from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
)
from bijux_pollenomics.governance.country_coverage import (
    COUNTRIES,
    build_country_dimension_coverage_ledger,
)

from tests.support.repository import REPOSITORY_ROOT

_READ_BYTES = Path.read_bytes


_REPOSITORY_ROOT = REPOSITORY_ROOT


_CELL_SCHEMA_PATH = (
    _REPOSITORY_ROOT.parent
    / "bijux-pollenomics-execution-control/contracts/country-coverage.schema.json"
)


_LEDGER_PATH = _REPOSITORY_ROOT / "data/country_dimension_coverage.json"


_SEAD_ACQUISITION_ROOT = f"data/sead/raw/acquisitions/{SEAD_GOVERNED_EVIDENCE_RUN_ID}"


_SEAD_ADMISSION_PATH = f"{_SEAD_ACQUISITION_ROOT}/admission.json"


_SEAD_DECISIONS_PATH = f"{_SEAD_ACQUISITION_ROOT}/country-decisions.json"


_SEAD_SITES_PATH = f"{_SEAD_ACQUISITION_ROOT}/payloads/tbl_sites.json"


_COUNTRY_COVERAGE_ARTIFACT_ROOT = (
    _REPOSITORY_ROOT / "artifacts/execution-control/country-coverage"
)


def _build() -> dict[str, object]:
    return build_country_dimension_coverage_ledger(
        _REPOSITORY_ROOT, cell_schema_path=_CELL_SCHEMA_PATH
    )


def _replace_input_document(
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
    mutate: Callable[[dict[str, object]], None],
) -> bytes:
    target = (_REPOSITORY_ROOT / relative_path).resolve()
    original = _READ_BYTES(target)
    document = cast(dict[str, object], json.loads(original))
    mutate(document)
    replacement = (
        json.dumps(document, ensure_ascii=False, allow_nan=False, sort_keys=True) + "\n"
    ).encode("utf-8")

    def read_bytes(path: Path) -> bytes:
        if path.resolve() == target:
            return replacement
        return _READ_BYTES(path)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    return original


def _replace_input_documents(
    monkeypatch: pytest.MonkeyPatch, replacements: Mapping[str, bytes]
) -> None:
    targets = {
        (_REPOSITORY_ROOT / relative_path).resolve(): payload
        for relative_path, payload in replacements.items()
    }

    def read_bytes(path: Path) -> bytes:
        target = path.resolve()
        return targets[target] if target in targets else _READ_BYTES(path)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)


def _document_bytes(document: Mapping[str, object]) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, allow_nan=False, sort_keys=True) + "\n"
    ).encode("utf-8")


def _set_nested(
    document: dict[str, object], path: tuple[str, ...], value: object
) -> None:
    current = document
    for key in path[:-1]:
        current = cast(dict[str, object], current[key])
    current[path[-1]] = value


def _cells(ledger: Mapping[str, object]) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], ledger["cells"])


def _cell(
    ledger: Mapping[str, object], source: str, dimension: str, country: str
) -> dict[str, object]:
    matches = [
        cell
        for cell in _cells(ledger)
        if (
            cell["source_family"],
            cell["country_dimension"],
            cell["country_code"],
        )
        == (source, dimension, country)
    ]
    assert len(matches) == 1
    return matches[0]


def _counts(cell: Mapping[str, object]) -> Mapping[str, int | None]:
    return cast(Mapping[str, int | None], cell["counts"])


def _measure_total(
    ledger: Mapping[str, object],
    source: str,
    dimension: str,
    measure: str,
    *,
    countries: tuple[str, ...] = COUNTRIES,
) -> int:
    values = [
        _counts(_cell(ledger, source, dimension, country))[measure]
        for country in countries
    ]
    assert all(value is not None for value in values)
    return sum(cast(list[int], values))
