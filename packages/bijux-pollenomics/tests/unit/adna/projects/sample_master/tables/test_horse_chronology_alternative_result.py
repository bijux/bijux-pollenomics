"""Check saved horse alternative arithmetic with raw DOM and exact fractions."""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from xml.dom import minidom
from zipfile import ZipFile

import pytest

from tests.support.repository import REPOSITORY_ROOT

pytestmark = pytest.mark.generated_artifacts
_SOURCE = REPOSITORY_ROOT / (
    "data/adna/governance/source_library/papers/10.1016-j.cell.2019.03.049/"
    "supplementary/1-s2.0-S0092867419303848-mmc1.xlsx"
)
_RESULT = REPOSITORY_ROOT / (
    "artifacts/animal-source-chronology/source-alternatives/provenance.json"
)
_OLD = REPOSITORY_ROOT / (
    "artifacts/animal-source-chronology/native-source-fields/provenance.json"
)
_HASH = "e37e1720c160cc0d7eaa4037ece22c1d9f8812f0cb31635647f26ca93137dd29"


def _text(node: Any) -> str:
    return "".join(
        child.data if child.nodeType == child.TEXT_NODE else _text(child)
        for child in node.childNodes
    )


def _raw() -> tuple[dict[str, tuple[str | None, bool]], dict[str, int]]:
    assert sha256(_SOURCE.read_bytes()).hexdigest() == _HASH
    with ZipFile(_SOURCE) as archive:
        strings = [
            _text(node)
            for node in minidom.parseString(
                archive.read("xl/sharedStrings.xml")
            ).getElementsByTagName("si")
        ]
        document = minidom.parseString(archive.read("xl/worksheets/sheet1.xml"))
    cells = {}
    for cell in document.getElementsByTagName("c"):
        values = cell.getElementsByTagName("v")
        value = _text(values[0]) if values else None
        if cell.getAttribute("t") == "s" and value is not None:
            value = strings[int(value)]
        reference = cell.getAttribute("r")
        assert reference not in cells
        cells[reference] = (value, bool(cell.getElementsByTagName("f")))
    owners = {}
    for row in document.getElementsByTagName("row"):
        number = int(row.getAttribute("r"))
        if number <= 4 or cells.get(f"I{number}", (None, False))[0] != "horse":
            continue
        label = cells[f"A{number}"][0]
        registration = cells[f"B{number}"][0]
        anchor = label if registration in {None, "", "N/A"} else registration
        key = f"prjeb31613:{anchor}".casefold()
        assert key not in owners
        owners[key] = number
    assert len(owners) == 245
    return cells, owners


def _saved(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        pytest.skip(f"Requires retained actual provenance output: {path}")
    value = json.loads(path.read_text())
    if path == _OLD:
        assert isinstance(value, dict) and set(value) == {"rows"}
        value = value["rows"]
    assert isinstance(value, list) and len(value) == 1_475
    return value


def test_saved_alternatives_match_raw_source_fraction_arithmetic() -> None:
    actual = _saved(_RESULT)
    cells, owners = _raw()
    linked = {
        row["repo_stable_sample_id"]: row
        for row in actual
        if row["project_accession"] == "PRJEB31613"
    }
    assert linked.keys() == owners.keys()
    assert all(
        "source_chronology_alternatives" not in row
        for row in actual
        if row["project_accession"] != "PRJEB31613"
    )
    states: Counter[str] = Counter()
    for key, number in owners.items():
        result = linked[key]["source_chronology_alternatives"]
        assert result["repo_stable_sample_id"] == key
        for name in (
            "radiocarbon_R_S_normalized",
            "canonical_bp_conversion_performed",
            "formula_evaluation_performed",
            "selected_chronology_changed",
            "scientific_admission",
        ):
            assert result[name] is False
        assert result["reference_year"] == 2017
        assert result["calendar_year_zero_convention"] == (
            "not_explicitly_defined_by_source"
        )
        states[result["status"]] += 1
        raw = [cells.get(f"{column}{number}", (None, False)) for column in "TUVWX"]
        if all(value is None for value, _ in raw):
            assert (
                result["reason_code"] == "all_seven_source_alternatives_present_blank"
            )
            assert result["reference_arithmetic_performed"] is False
            continue
        assert all(value is not None and not formula for value, formula in raw)
        start, end, coverage, average, offset = (
            Fraction(str(value)) for value, _ in raw
        )
        midpoint_error = average - (start + end) / 2
        offset_error = offset - average + 2017
        assert (
            Fraction(result["source_average_minus_endpoint_midpoint"]) == midpoint_error
        )
        assert Fraction(result["source_X_minus_expected_signed_offset"]) == offset_error
        assert result["source_arithmetic_consistent"] == (
            midpoint_error == 0 and offset_error == 0
        )
        derived = result["derived_elapsed_2017_coordinate"]
        assert Fraction(derived["lower"]) == 2017 - end
        assert Fraction(derived["upper"]) == 2017 - start
        assert Fraction(derived["midpoint"]) == 2017 - average
        assert Fraction(result["source_coverage_percent"]) == coverage
        value, formula = cells[f"D{number}"]
        comparison = result["D_comparison"]
        try:
            d = None if value is None or formula else Fraction(value)
        except ValueError:
            d = None
        if d is None:
            assert comparison["status"] == "not_compared_non_numeric_missing_or_formula"
        else:
            residual = d - (2017 - average)
            assert (
                Fraction(comparison["D_minus_derived_elapsed_2017_midpoint"])
                == residual
            )
            assert comparison["status"] == (
                "equal_numeric_coordinate"
                if residual == 0
                else "different_numeric_coordinate"
            )
    assert states == {"source_alternative_arithmetic_accounted": 54, "refused": 191}
    assert sha256(_SOURCE.read_bytes()).hexdigest() == _HASH


def test_saved_alternative_is_only_addition_to_all_old_packets() -> None:
    current = _saved(_RESULT)
    previous = _saved(_OLD)
    stripped = [
        {
            key: value
            for key, value in row.items()
            if key != "source_chronology_alternatives"
        }
        for row in current
    ]
    assert stripped == previous
