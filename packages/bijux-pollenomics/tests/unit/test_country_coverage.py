from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import pytest
from bijux_pollenomics.foundation.country_coverage import (
    COUNT_FIELDS,
    COUNTRIES,
    COUNTRY_DIMENSIONS,
    SOURCE_FAMILIES,
    build_country_dimension_coverage_ledger,
    write_country_dimension_coverage_ledger,
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
_CELL_SCHEMA_PATH = (
    _REPOSITORY_ROOT.parent
    / "bijux-pollenomics-execution-control/contracts/country-coverage.schema.json"
)
_LEDGER_PATH = _REPOSITORY_ROOT / "data/country_dimension_coverage.json"


def _build() -> dict[str, object]:
    return build_country_dimension_coverage_ledger(
        _REPOSITORY_ROOT, cell_schema_path=_CELL_SCHEMA_PATH
    )


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


def test_ledger_has_one_schema_valid_cell_per_complete_partition() -> None:
    ledger = _build()
    cells = _cells(ledger)

    assert ledger["cell_count"] == 144
    assert len(cells) == len(SOURCE_FAMILIES) * len(COUNTRY_DIMENSIONS) * len(COUNTRIES)
    assert {
        (
            cell["source_family"],
            cell["country_dimension"],
            cell["country_code"],
        )
        for cell in cells
    } == {
        (source, dimension, country)
        for source in SOURCE_FAMILIES
        for dimension in COUNTRY_DIMENSIONS
        for country in COUNTRIES
    }
    assert all(set(_counts(cell)) == set(COUNT_FIELDS) for cell in cells)
    assert all(cell["availability_status"] != "unknown" for cell in cells)
    assert all(
        cell["country_assignment_method"] is None
        if cell["country_dimension"] == "source_reported"
        else isinstance(cell["country_assignment_method"], str)
        for cell in cells
    )
    schema_bytes = _CELL_SCHEMA_PATH.read_bytes()
    assert ledger["cell_schema_sha256"] == hashlib.sha256(schema_bytes).hexdigest()
    assert json.loads(schema_bytes)["$id"] == ledger["cell_schema_id"]


def test_landclim_keeps_reported_country_separate_from_publication() -> None:
    ledger = _build()
    reported = {
        country: _counts(_cell(ledger, "landclim", "source_reported", country))["sites"]
        for country in COUNTRIES
    }
    published = {
        country: _counts(_cell(ledger, "landclim", "publication", country))["sites"]
        for country in COUNTRIES
    }

    assert reported == {
        "SE": 163,
        "DK": 127,
        "NO": 84,
        "FI": 62,
        "UNASSIGNED": 54,
        "OUTSIDE": 0,
    }
    assert published == {
        "SE": 198,
        "DK": 127,
        "NO": 93,
        "FI": 72,
        "UNASSIGNED": 0,
        "OUTSIDE": 0,
    }
    unassigned = _cell(ledger, "landclim", "source_reported", "UNASSIGNED")
    assert unassigned["availability_status"] == "available_partial"
    assert "source_country_not_reported" in cast(list[str], unassigned["reason_codes"])
    governed = _cell(ledger, "landclim", "governed_assignment", "SE")
    assert governed["availability_status"] == "blocked"
    assert all(value is None for value in _counts(governed).values())


def test_neotoma_dimensions_reconcile_without_collapsing_country_identity() -> None:
    ledger = _build()
    observed_partitions = ("SE", "DK", "NO", "FI", "UNASSIGNED")

    assert _measure_total(ledger, "neotoma", "source_reported", "sites") == 200
    assert _measure_total(ledger, "neotoma", "governed_assignment", "sites") == 200
    assert (
        _measure_total(ledger, "neotoma", "governed_assignment", "accepted_records")
        == 193
    )
    assert (
        _measure_total(ledger, "neotoma", "governed_assignment", "unresolved_records")
        == 7
    )
    assert (
        _measure_total(ledger, "neotoma", "governed_assignment", "excluded_records")
        == 0
    )
    assert (
        _measure_total(
            ledger,
            "neotoma",
            "governed_assignment",
            "datasets",
            countries=observed_partitions,
        )
        == 209
    )
    assert (
        _measure_total(
            ledger,
            "neotoma",
            "governed_assignment",
            "collection_units",
            countries=observed_partitions,
        )
        == 206
    )
    assert (
        _measure_total(
            ledger,
            "neotoma",
            "governed_assignment",
            "samples",
            countries=observed_partitions,
        )
        == 12_388
    )
    assert (
        _measure_total(
            ledger,
            "neotoma",
            "governed_assignment",
            "age_claims",
            countries=observed_partitions,
        )
        == 23_281
    )
    assert (
        _measure_total(
            ledger,
            "neotoma",
            "governed_assignment",
            "observations",
            countries=observed_partitions,
        )
        == 370_936
    )
    assert _measure_total(ledger, "neotoma", "publication", "sites") == 200
    assert _counts(_cell(ledger, "neotoma", "source_reported", "SE"))["sites"] == 101
    assert _counts(_cell(ledger, "neotoma", "governed_assignment", "SE"))["sites"] == 98
    assert _counts(_cell(ledger, "neotoma", "publication", "SE"))["sites"] == 99
    unassigned = _cell(ledger, "neotoma", "governed_assignment", "UNASSIGNED")
    assert _counts(unassigned)["unresolved_records"] == 7
    assert unassigned["availability_status"] == "unresolved"
    assert unassigned["lifecycle_status"] == "review_required"


def test_sead_preserves_assigned_review_and_refused_partitions() -> None:
    ledger = _build()
    source_unassigned = _cell(ledger, "sead", "source_reported", "UNASSIGNED")
    assert _counts(source_unassigned)["received_records"] == 2_195
    assert source_unassigned["availability_status"] == "available_partial"

    expected = {
        "SE": 1_925,
        "DK": 59,
        "NO": 45,
        "FI": 40,
        "UNASSIGNED": 103,
        "OUTSIDE": 23,
    }
    assert {
        country: _counts(_cell(ledger, "sead", "governed_assignment", country))["sites"]
        for country in COUNTRIES
    } == expected
    assert sum(expected.values()) == 2_195
    assert (
        _measure_total(ledger, "sead", "governed_assignment", "accepted_records")
        == 2_069
    )
    assert (
        _measure_total(ledger, "sead", "governed_assignment", "unresolved_records")
        == 103
    )
    assert (
        _measure_total(ledger, "sead", "governed_assignment", "excluded_records") == 23
    )
    review = _cell(ledger, "sead", "governed_assignment", "UNASSIGNED")
    refused = _cell(ledger, "sead", "governed_assignment", "OUTSIDE")
    assert _counts(review)["unresolved_records"] == 103
    assert review["lifecycle_status"] == "review_required"
    assert _counts(refused)["excluded_records"] == 23
    assert refused["lifecycle_status"] == "refused"
    for country in COUNTRIES:
        publication = _cell(ledger, "sead", "publication", country)
        assert publication["availability_status"] == "blocked"
        assert publication["lifecycle_status"] == "unavailable"
        assert all(value is None for value in _counts(publication).values())


def test_source_specific_absence_and_review_are_not_encoded_as_zero() -> None:
    ledger = _build()

    for source in ("raa", "svar"):
        sweden = _cell(ledger, source, "publication", "SE")
        denmark = _cell(ledger, source, "publication", "DK")
        assert sweden["availability_status"] == "blocked"
        assert sweden["lifecycle_status"] == "refused"
        assert denmark["availability_status"] == "not_available_from_source"
        assert denmark["lifecycle_status"] == "unavailable"
        assert all(
            value is None
            for dimension in COUNTRY_DIMENSIONS
            for country in COUNTRIES
            for value in _counts(_cell(ledger, source, dimension, country)).values()
        )

    for dimension in COUNTRY_DIMENSIONS:
        for country in ("SE", "DK", "NO", "FI"):
            boundary = _cell(ledger, "boundaries", dimension, country)
            assert boundary["lifecycle_status"] == "review_required"
    assert _measure_total(ledger, "boundaries", "publication", "published_records") == 4

    nordic_countries = ("SE", "DK", "NO", "FI")
    assert (
        _measure_total(
            ledger,
            "aadr",
            "publication",
            "samples",
            countries=nordic_countries,
        )
        == 1_231
    )
    assert (
        _measure_total(
            ledger,
            "aadr",
            "publication",
            "sites",
            countries=nordic_countries,
        )
        == 447
    )
    assert all(
        _cell(ledger, "aadr", "publication", country)["lifecycle_status"]
        == "review_required"
        for country in COUNTRIES
    )
    assert all(
        value is None
        for dimension in ("source_reported", "governed_assignment")
        for country in COUNTRIES
        for value in _counts(_cell(ledger, "aadr", dimension, country)).values()
    )

    assert (
        _measure_total(
            ledger,
            "animal_adna",
            "publication",
            "samples",
            countries=nordic_countries,
        )
        == 3
    )
    assert _counts(_cell(ledger, "animal_adna", "publication", "NO"))["samples"] == 0
    assert _counts(_cell(ledger, "animal_adna", "publication", "FI"))["samples"] == 0


def test_checked_ledger_and_atomic_writer_are_fixed_point() -> None:
    first = _build()
    second = _build()
    assert first == second

    artifacts = _REPOSITORY_ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=artifacts) as temporary_directory:
        output = Path(temporary_directory) / "country_dimension_coverage.json"
        first_bytes = write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=output,
        )
        second_bytes = write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=output,
        )
        assert first_bytes == second_bytes == output.read_bytes()
        assert output.stat().st_mode & 0o777 == 0o644

    assert _LEDGER_PATH.read_bytes() == first_bytes


def test_atomic_writer_refuses_output_outside_repository(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError, match="country coverage output must remain inside the repository"
    ):
        write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=tmp_path / "country_dimension_coverage.json",
        )
