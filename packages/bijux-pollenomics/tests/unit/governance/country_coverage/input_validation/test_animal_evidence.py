"""Animal evidence uniqueness and disposition refusal tests."""

from __future__ import annotations

from copy import deepcopy
from typing import cast

import pytest

from ..fixtures import _build, _cell, _counts, _replace_input_document


def test_animal_publication_separates_locality_and_sample_denominators() -> None:
    ledger = _build()

    assert {
        country: _counts(_cell(ledger, "animal_adna", "publication", country))["sites"]
        for country in ("SE", "DK", "NO", "FI")
    } == {"SE": 3, "DK": 4, "NO": 0, "FI": 1}
    assert {
        country: _counts(_cell(ledger, "animal_adna", "publication", country))[
            "samples"
        ]
        for country in ("SE", "DK", "NO", "FI")
    } == {"SE": 5, "DK": 5, "NO": 0, "FI": 2}


def test_duplicate_animal_evidence_row_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def duplicate_row(document: dict[str, object]) -> None:
        rows = cast(list[dict[str, object]], document["rows"])
        rows.append(deepcopy(rows[0]))

    _replace_input_document(
        monkeypatch, "docs/report/animal_country_species_coverage.json", duplicate_row
    )

    with pytest.raises(ValueError, match="duplicate evidence row"):
        _build()


def test_legacy_animal_coverage_schema_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def use_legacy_schema(document: dict[str, object]) -> None:
        document["schema_version"] = "animal-country-species-coverage.v1"

    _replace_input_document(
        monkeypatch,
        "docs/report/animal_country_species_coverage.json",
        use_legacy_schema,
    )

    with pytest.raises(ValueError, match="schema version is unsupported"):
        _build()


def test_animal_evidence_totals_must_reconcile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def corrupt_total(document: dict[str, object]) -> None:
        rows = cast(list[dict[str, object]], document["rows"])
        rows[0]["mapped_sample_count"] = cast(int, rows[0]["mapped_sample_count"]) + 1

    _replace_input_document(
        monkeypatch, "docs/report/animal_country_species_coverage.json", corrupt_total
    )

    with pytest.raises(ValueError, match="animal sample disposition"):
        _build()


def test_animal_coordinate_basis_totals_must_reconcile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def corrupt_total(document: dict[str, object]) -> None:
        rows = cast(list[dict[str, object]], document["rows"])
        rows[0]["direct_coordinate_sample_count"] = (
            cast(int, rows[0]["direct_coordinate_sample_count"]) + 1
        )

    _replace_input_document(
        monkeypatch, "docs/report/animal_country_species_coverage.json", corrupt_total
    )

    with pytest.raises(ValueError, match="coordinate-basis evidence"):
        _build()
