"""Literal horse date evidence retains source cells and enforces physical ownership."""

from __future__ import annotations

from pathlib import Path
from typing import cast
import xml.etree.ElementTree as ET
import zipfile

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.horse_source_fields import (
    horse_source_chronology_fields,
)

_SOURCE = (
    "adna/governance/source_library/papers/10.1016-j.cell.2019.03.049/"
    "supplementary/1-s2.0-S0092867419303848-mmc1.xlsx"
)
_OWNERS = {
    "prjeb31613:alpha": ("Horse A", "Sheet1!row5", f"data/{_SOURCE}"),
    "prjeb31613:horse b": ("Horse B", "Sheet1!row6", f"data/{_SOURCE}"),
}
_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _workbook(root: Path, *, alteration: str = "") -> Path:
    path = root / _SOURCE
    path.parent.mkdir(parents=True)
    worksheet = ET.Element(f"{{{_NS}}}worksheet")
    data = ET.SubElement(worksheet, f"{{{_NS}}}sheetData")
    rows = {
        number: ET.SubElement(data, f"{{{_NS}}}row", r=str(number))
        for number in range(1, 8)
    }

    def cell(
        reference: str, text: str | None, *, kind: str | None = "inlineStr"
    ) -> ET.Element:
        number = int(reference.lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        node = ET.SubElement(rows[number], f"{{{_NS}}}c", r=reference)
        if kind is not None:
            node.set("t", kind)
        if text is not None:
            if kind == "inlineStr":
                inline = ET.SubElement(node, f"{{{_NS}}}is")
                ET.SubElement(inline, f"{{{_NS}}}t").text = text
            else:
                ET.SubElement(node, f"{{{_NS}}}v").text = text
        return node

    for column, header in {
        "A": "Sample name",
        "B": "Registration number",
        "I": "Species",
        "D": "Age (years ago) ",
    }.items():
        cell(f"{column}4", header)
    cell("T1", "IntCal13")
    cell("T2", "Unmodelled (BC/AD) ")
    cell("R3", "14C age(BP)")
    cell("R4", "(from 2017)")
    for number, label, registration, species in (
        (5, " Horse A ", "Alpha", "horse"),
        (6, "Horse B", "N/A", "horse"),
        (7, "Other", "Gamma", "mule"),
    ):
        cell(f"A{number}", label)
        cell(f"B{number}", registration)
        cell(f"I{number}", species)
    cached = cell("D5", "4692", kind=None)
    cached.set("s", "3")
    ET.SubElement(cached, f"{{{_NS}}}f", t="shared", si="0").text = "4625+67"
    cell("R5", "2110.00", kind=None)
    cell("S5", "0", kind=None)
    cell("T5", "-39", kind=None)
    cell("U5", "59", kind=None)
    cell("V5", "95.4", kind=None)
    cell("D6", "0", kind="s")
    cell("R6", None, kind=None)
    cell("T6", "N/A")
    if alteration == "duplicate_cell":
        cell("R5", "99", kind=None)
    elif alteration == "duplicate_owner":
        rows[6].find(f"{{{_NS}}}c[@r='B6']/{{{_NS}}}is/{{{_NS}}}t").text = "Alpha"  # type: ignore[union-attr]
    elif alteration == "cross_row_cell":
        cached.set("r", "D6")
    elif alteration == "unknown_type":
        cached.set("t", "unhandled")
    elif alteration == "bad_shared_string":
        rows[6].find(f"{{{_NS}}}c[@r='D6']/{{{_NS}}}v").text = "99"  # type: ignore[union-attr]
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", ET.tostring(worksheet))
        archive.writestr(
            "xl/sharedStrings.xml", f'<sst xmlns="{_NS}"><si><t>-</t></si></sst>'
        )
        archive.writestr(
            "xl/workbook.xml",
            f'<workbook xmlns="{_NS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sheet1" r:id="rId1"/></sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>',
        )
    return path


def _records(value: object) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], value)


def test_missing_optional_source_is_unknown_and_preserves_existing_owners(
    tmp_path: Path,
) -> None:
    assert horse_source_chronology_fields(tmp_path, owners={}) == {}
    result = horse_source_chronology_fields(tmp_path, owners=_OWNERS)
    assert result.keys() == _OWNERS.keys()
    assert all(row["status"] == "refused" for row in result.values())
    assert all(
        row["reason_code"] == "horse_source_workbook_missing" for row in result.values()
    )
    assert all(row["source_population"] is None for row in result.values())
    assert all(row["selected_chronology_changed"] is False for row in result.values())


def test_fields_preserve_formula_cache_tokens_hierarchy_and_all_missing_states(
    tmp_path: Path,
) -> None:
    _workbook(tmp_path)
    result = horse_source_chronology_fields(tmp_path, owners=_OWNERS)
    first = result["prjeb31613:alpha"]
    assert first["sample_label_literal"] == " Horse A "
    fields = {str(row["cell_reference"]): row for row in _records(first["fields"])}
    assert fields["D5"]["native_value_literal"] == "4692"
    assert fields["D5"]["formula_literal"] == "4625+67"
    assert fields["D5"]["formula_attributes"] == {"t": "shared", "si": "0"}
    assert fields["D5"]["native_style_attribute"] == "3"
    assert fields["R5"]["native_value_literal"] == "2110.00"
    assert fields["S5"]["resolved_literal"] == "0"
    assert fields["T5"]["resolved_literal"] == "-39"
    assert fields["U5"]["resolved_literal"] == "59"
    headers = {
        str(row["cell_reference"]): row for row in _records(first["header_cells"])
    }
    assert headers["R3"]["resolved_literal"] == "14C age(BP)"
    assert headers["R4"]["resolved_literal"] == "(from 2017)"
    assert headers["T2"]["resolved_literal"] == "Unmodelled (BC/AD) "
    second = result["prjeb31613:horse b"]
    missing = {str(row["cell_reference"]): row for row in _records(second["fields"])}
    assert missing["D6"]["native_value_literal"] == "0"
    assert missing["D6"]["resolved_literal"] == "-"
    assert missing["R6"]["cell_state"] == "present_blank"
    assert missing["S6"]["cell_state"] == "missing_cell"
    assert missing["T6"]["resolved_literal"] == "N/A"
    assert all(
        first[key] is False
        for key in (
            "date_conversion_performed",
            "formula_evaluation_performed",
            "selected_chronology_changed",
            "scientific_admission",
        )
    )
    population = cast(dict[str, object], first["source_population"])
    assert population["physical_data_rows"] == 3
    assert population["horse_rows"] == population["matched_chronology_owners"] == 2
    assert population["excluded_rows_by_source_species"] == {"mule": 1}
    counts = cast(dict[str, dict[str, int]], population["field_cell_states_by_column"])
    assert counts["R"] == {
        "present_value": 1,
        "present_blank": 1,
        "missing_cell": 0,
        "formula_present": 0,
    }
    assert counts["S"] == {
        "present_value": 1,
        "present_blank": 0,
        "missing_cell": 1,
        "formula_present": 0,
    }
    assert counts["D"]["formula_present"] == 1


@pytest.mark.parametrize(
    "alteration",
    [
        "duplicate_cell",
        "duplicate_owner",
        "cross_row_cell",
        "unknown_type",
        "bad_shared_string",
    ],
)
def test_invalid_native_ownership_and_representations_are_refused(
    tmp_path: Path, alteration: str
) -> None:
    _workbook(tmp_path, alteration=alteration)
    with pytest.raises(ValueError, match="Horse source"):
        horse_source_chronology_fields(tmp_path, owners=_OWNERS)


@pytest.mark.parametrize(
    "mismatch", ["missing_owner", "extra_owner", "label", "row", "path"]
)
def test_every_native_horse_must_match_one_existing_owner(
    tmp_path: Path, mismatch: str
) -> None:
    _workbook(tmp_path)
    owners = dict(_OWNERS)
    if mismatch == "missing_owner":
        owners.pop("prjeb31613:alpha")
    elif mismatch == "extra_owner":
        owners["prjeb31613:extra"] = ("Extra", "Sheet1!row9", f"data/{_SOURCE}")
    else:
        label, row, path = owners["prjeb31613:alpha"]
        owners["prjeb31613:alpha"] = (
            "Other" if mismatch == "label" else label,
            "Sheet1!row6" if mismatch == "row" else row,
            "data/other.xlsx" if mismatch == "path" else path,
        )
    with pytest.raises(ValueError, match="Horse (source rows|chronology owner)"):
        horse_source_chronology_fields(tmp_path, owners=owners)
