"""Compare public horse provenance with the original workbook's XML records."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from typing import cast
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import pytest

from bijux_pollenomics.adna.projects.evidence.chronology.audits import (
    build_sample_chronology_provenance_rows,
)
from tests.support.repository import REPOSITORY_ROOT

pytestmark = pytest.mark.generated_artifacts

_SOURCE = (
    "data/adna/governance/source_library/papers/10.1016-j.cell.2019.03.049/"
    "supplementary/1-s2.0-S0092867419303848-mmc1.xlsx"
)
_HASH = "e37e1720c160cc0d7eaa4037ece22c1d9f8812f0cb31635647f26ca93137dd29"
_XML = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_COLUMNS = ("D", "R", "S", "T", "U", "V", "W", "X")


def _xml_record(
    reference: str, cells: dict[str, ET.Element], strings: list[str]
) -> dict[str, object]:
    cell = cells.get(reference)
    value = None if cell is None else cell.find(f"{_XML}v")
    formula = None if cell is None else cell.find(f"{_XML}f")
    inline = None if cell is None else cell.find(f"{_XML}is")
    kind = None if cell is None else cell.get("t")
    raw = None if value is None else value.text
    resolved = strings[int(raw)] if kind == "s" and raw is not None else raw
    return {
        "cell_reference": reference,
        "cell_state": "missing_cell"
        if cell is None
        else "present_blank"
        if value is None and formula is None and inline is None
        else "present_value",
        "native_type_attribute": kind,
        "native_style_attribute": None if cell is None else cell.get("s"),
        "value_element_present": value is not None,
        "native_value_literal": raw,
        "resolved_literal": resolved,
        "formula_present": formula is not None,
        "formula_literal": None if formula is None else formula.text,
        "formula_attributes": {} if formula is None else dict(formula.attrib),
        "inline_string_present": inline is not None,
    }


def test_public_horse_fields_match_all_original_xml_cells_and_selected_rows() -> None:
    source = REPOSITORY_ROOT / _SOURCE
    payload = source.read_bytes()
    assert sha256(payload).hexdigest() == _HASH
    assert len(payload) == 81_103
    with ZipFile(source) as workbook:
        strings = [
            "".join(node.itertext())
            for node in ET.fromstring(workbook.read("xl/sharedStrings.xml"))
        ]
        sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
    physical = sheet.findall(f"{_XML}sheetData/{_XML}row")
    cells = {cell.attrib["r"]: cell for row in physical for cell in row}
    assert len(cells) == sum(len(row) for row in physical)
    assert not sheet.findall(f".//{_XML}is")

    def literal(reference: str) -> str:
        return str(_xml_record(reference, cells, strings)["resolved_literal"] or "")

    owners: dict[str, int] = {}
    excluded: Counter[str] = Counter()
    for row in physical:
        number = int(row.attrib["r"])
        if number <= 4:
            continue
        label, species = literal(f"A{number}"), literal(f"I{number}")
        if species != "horse":
            excluded[species or "missing_sample_label"] += 1
            continue
        registration = literal(f"B{number}")
        anchor = label if registration in {"", "N/A"} else registration
        key = f"prjeb31613:{anchor}".casefold()
        assert key not in owners
        owners[key] = number
    assert len(owners) == 245
    assert excluded == {"mule": 27, "ass": 3, "hemione": 3, "missing_sample_label": 2}
    assert len(physical) == 284
    headers = [
        _xml_record(f"{column}{number}", cells, strings)
        for column in _COLUMNS
        for number in range(1, 5)
    ]
    assert [
        node.attrib["ref"]
        for node in sheet.findall(f"{_XML}mergeCells/{_XML}mergeCell")
    ] == ["M3:N3", "O3:P3"]
    assert literal("T1") == "IntCal13"
    assert literal("T2") == "Unmodelled (BC/AD) "
    assert literal("R4") == "(from 2017)"

    actual = build_sample_chronology_provenance_rows(REPOSITORY_ROOT / "data")
    assert len(actual) == 1_475
    baseline = [
        row
        for path in (
            REPOSITORY_ROOT / "data/adna/governance/source_library/projects"
        ).glob("*/sample_chronology_provenance.json")
        for row in json.loads(path.read_text())["rows"]
    ]

    def selected(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
        return {
            str(row["repo_stable_sample_id"]): {
                key: value
                for key, value in row.items()
                if key != "source_chronology_fields"
            }
            for row in rows
        }

    assert len(baseline) == 1_475
    assert len(selected(baseline)) == len(selected(list(actual))) == 1_475
    assert selected(list(actual)) == selected(baseline)
    horse = {
        str(row["repo_stable_sample_id"]): row
        for row in actual
        if row["project_accession"] == "PRJEB31613"
    }
    assert horse.keys() == owners.keys()
    assert all(
        "source_chronology_fields" not in row
        for row in actual
        if row["project_accession"] != "PRJEB31613"
    )
    patterns: Counter[tuple[bool, ...]] = Counter()
    types: Counter[str | None] = Counter()
    column_states = {}
    for column in _COLUMNS:
        records = [
            _xml_record(f"{column}{number}", cells, strings)
            for number in owners.values()
        ]
        counts = Counter(record["cell_state"] for record in records)
        column_states[column] = {
            state: counts[state]
            for state in ("present_value", "present_blank", "missing_cell")
        }
        column_states[column]["formula_present"] = sum(
            record["formula_present"] is True for record in records
        )
    for key, number in owners.items():
        packet = cast(dict[str, object], horse[key]["source_chronology_fields"])
        assert packet["status"] == "retained_literal_source_fields"
        assert packet["worksheet"] == "Sheet1"
        assert packet["worksheet_part"] == "xl/worksheets/sheet1.xml"
        assert packet["worksheet_merged_ranges"] == ["M3:N3", "O3:P3"]
        assert packet["physical_row_number"] == number
        assert packet["repo_stable_sample_id"] == key
        assert packet["sample_label_literal"] == literal(f"A{number}")
        assert packet["registration_literal"] == literal(f"B{number}")
        assert packet["header_cells"] == headers
        assert packet["identity_cells"] == [
            _xml_record(f"{column}{number}", cells, strings)
            for column in ("A", "B", "I")
        ]
        expected = [
            _xml_record(f"{column}{number}", cells, strings) for column in _COLUMNS
        ]
        assert packet["fields"] == expected
        workbook_identity = cast(dict[str, object], packet["source_workbook"])
        assert workbook_identity["sha256"] == _HASH
        assert workbook_identity["byte_count"] == len(payload)
        assert workbook_identity["path"] == _SOURCE
        assert workbook_identity["historical_acquisition_authenticated"] is False
        assert all(
            packet[name] is False
            for name in (
                "date_conversion_performed",
                "formula_evaluation_performed",
                "selected_chronology_changed",
                "scientific_admission",
            )
        )
        population = cast(dict[str, object], packet["source_population"])
        assert (
            population["horse_rows"] == population["matched_chronology_owners"] == 245
        )
        assert population["physical_data_rows"] == 280
        assert population["excluded_rows_by_source_species"] == dict(excluded)
        assert population["field_cell_states_by_column"] == column_states
        patterns[
            tuple(record["value_element_present"] is True for record in expected[1:])
        ] += 1
        types[cast(str | None, expected[0]["native_type_attribute"])] += 1
    assert patterns == {(True,) * 7: 54, (False,) * 7: 191}
    assert types == {None: 147, "s": 98}
    assert sum(literal(f"D{number}") == "-" for number in owners.values()) == 8
    for key, number in owners.items():
        if literal(f"D{number}") == "-":
            assert horse[key]["published_wording"] == ""
            assert horse[key]["provenance_surface"] == ""
            assert horse[key]["provenance_locator"] == ""
            assert horse[key]["normalization_status"] == "unresolved"
            assert all(
                horse[key][name] is None
                for name in ("time_start_bp", "time_end_bp", "time_mean_bp")
            )
    assert _xml_record("D72", cells, strings)["formula_literal"] == "4625+67"
    assert literal("D72") == "4692"
    assert literal("D282") == "1143" and literal("X282") == "-2895.5"
    assert sum(column_states[column]["formula_present"] for column in _COLUMNS) == 1
    assert (
        sum(
            sum(
                column_states[column][state]
                for state in ("present_value", "present_blank", "missing_cell")
            )
            for column in _COLUMNS
        )
        == 1_960
    )
    assert sha256(source.read_bytes()).hexdigest() == _HASH
