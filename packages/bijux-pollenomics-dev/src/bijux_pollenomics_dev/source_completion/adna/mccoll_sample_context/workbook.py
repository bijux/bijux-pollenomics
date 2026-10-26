"""Retain only the six requested original worksheet rows and descriptive cells."""

from __future__ import annotations

from io import BytesIO
import re
from typing import Any
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from bijux_pollenomics.collection.intake.workbooks import (
    cell_value,
    load_shared_strings,
    load_sheet_targets,
)

NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
SHEETS = {
    "S1.1": "S1.1. New Ancient Samples metad",
    "S5.1": "S5.1. Clustered Ancient Samples",
}
HEADERS = {
    "S1.1": dict(
        zip(
            [
                *"ABCDEFGHIJKLMNOPQR",
                "U",
                "V",
                "W",
                "X",
                "Y",
                "Z",
                "AA",
                "AB",
                "AC",
                "AD",
                "AG",
            ],
            [
                "GeoGenetics_ID",
                "Museum inv #",
                "Region",
                "Country",
                "Local",
                "Site",
                "Site Type",
                "Latitude",
                "Longitude",
                "Context",
                "Sample Material",
                "Description",
                "Sex",
                "Age",
                "context date",
                "C14 Lab #",
                "14C age (BP)",
                "±",
                "calBP from",
                "calBP to",
                "cal BP Mean",
                "BCE/CE from",
                "BCE/CE to",
                "BCE/CE mean",
                "Arch Period",
                "Arch Culture",
                "sampleId",
                "popId",
                "flag",
            ],
            strict=True,
        )
    ),
    "S5.1": dict(
        zip(
            [*"ABCDEFGHIJKLMNO", "R", "AG"],
            [
                "sampleId",
                "popId",
                "versionID",
                "site",
                "country",
                "region",
                "groupLabel",
                "latitude",
                "longitude",
                "dataSource",
                "age14C",
                "ageHigh",
                "ageLow",
                "ageAverage",
                "datingSource",
                "ageRaw",
                "archGroup",
            ],
            strict=True,
        )
    ),
}
OWNERS = {
    "S1.1": {
        575: "CGG_2_105915",
        588: "CGG_2_105916",
        589: "CGG_2_105918",
        590: "CGG_2_105917",
        745: "CGG_2_105916_CGG_2_105917_CGG_2_105918",
    },
    "S5.1": {2323: "CGG105916_CGG105917_CGG105918.mccoll_230821_ironage"},
}


def literal_rows(payload: bytes) -> list[dict[str, Any]]:
    """Decode original literal tokens; never evaluate formulas or convert dates."""
    if len(payload) > 4_000_000:
        raise ValueError("McColl workbook exceeds bounded input")
    result = []
    with ZipFile(BytesIO(payload)) as archive:
        entries = archive.infolist()
        if (
            len(entries) != len({e.filename for e in entries})
            or sum(e.file_size for e in entries) > 32_000_000
        ):
            raise ValueError("McColl workbook duplicate or oversized ZIP structure")
        targets, shared = load_sheet_targets(archive), load_shared_strings(archive)
        for ordinal, (table, sheet) in enumerate(SHEETS.items(), start=1):
            part = targets.get(sheet)
            if part != f"xl/worksheets/sheet{ordinal}.xml":
                raise ValueError("McColl worksheet relationship differs")
            tree = ET.fromstring(archive.read(part))
            rows: dict[int, dict[str, ET.Element]] = {}
            for row in tree.findall("x:sheetData/x:row", NS):
                text = row.get("r", "")
                if re.fullmatch(r"[1-9][0-9]*", text) is None or int(text) in rows:
                    raise ValueError("McColl physical row identity is invalid")
                cells = {}
                for native_cell in row.findall("x:c", NS):
                    ref = native_cell.get("r", "")
                    match = re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", ref)
                    if match is None or match[2] != text or match[1] in cells:
                        raise ValueError("McColl cell ownership is invalid")
                    cells[match[1]] = native_cell
                rows[int(text)] = cells
            for column, header in HEADERS[table].items():
                cell = rows.get(1, {}).get(column)
                if (
                    cell is None
                    or cell_value(cell, shared) != header
                    or cell.find("x:f", NS) is not None
                ):
                    raise ValueError("McColl descriptive header differs")
            for number, owner in OWNERS[table].items():
                cells = rows.get(number, {})
                identity = cells.get("A")
                if (
                    identity is None
                    or cell_value(identity, shared) != owner
                    or identity.find("x:f", NS) is not None
                ):
                    raise ValueError("McColl original row owner differs")
                fields = {}
                for column, header in HEADERS[table].items():
                    cell = cells.get(column)
                    value = None if cell is None else cell.find("x:v", NS)
                    formula = None if cell is None else cell.find("x:f", NS)
                    inline = None if cell is None else cell.find("x:is", NS)
                    raw = None if value is None else value.text
                    kind = None if cell is None else cell.get("t")
                    if kind == "s" and (
                        raw is None or not raw.isdecimal() or int(raw) >= len(shared)
                    ):
                        raise ValueError("McColl shared-string token is invalid")
                    fields[column] = {
                        "reference": f"{column}{number}",
                        "header_reference": f"{column}1",
                        "header_literal": header,
                        "native_type_attribute": kind,
                        "native_style_attribute": None
                        if cell is None
                        else cell.get("s"),
                        "native_value_literal": raw,
                        "resolved_literal": None
                        if cell is None
                        or (value is None and inline is None and formula is None)
                        else cell_value(cell, shared),
                        "formula_present": formula is not None,
                        "value_element_present": value is not None,
                        "inline_string_present": inline is not None,
                        "formula_literal": None if formula is None else formula.text,
                        "formula_attributes": {}
                        if formula is None
                        else dict(formula.attrib),
                        "cell_state": "missing_cell"
                        if cell is None
                        else "present_blank"
                        if value is None and inline is None and formula is None
                        else "present_value",
                    }
                result.append(
                    {
                        "table": table,
                        "sheet_name": sheet,
                        "worksheet_part": part,
                        "physical_row": number,
                        "owner_literal": owner,
                        "fields": fields,
                    }
                )
    return result
