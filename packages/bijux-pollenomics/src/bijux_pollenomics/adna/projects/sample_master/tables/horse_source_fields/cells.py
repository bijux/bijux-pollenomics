"""Original horse worksheet cells, headers and formula caches without evaluation."""

from __future__ import annotations

from collections.abc import Mapping
from io import BytesIO
import re
import xml.etree.ElementTree as ET
import zipfile

_SHEET_PART = "xl/worksheets/sheet1.xml"

_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

_CELL_REFERENCE = re.compile(r"([A-Z]+)([1-9][0-9]*)")


def _horse_literal_cells(
    payload: bytes,
) -> tuple[dict[str, dict[str, object]], tuple[int, ...], tuple[str, ...]]:
    """Read original cell representations without evaluating a formula or date."""
    if len(payload) > 4_000_000:
        raise ValueError("Horse source workbook exceeds the bounded reader limit")
    with zipfile.ZipFile(BytesIO(payload)) as workbook:
        entries = workbook.infolist()
        if len({entry.filename for entry in entries}) != len(entries):
            raise ValueError("Horse source workbook has duplicate ZIP members")
        if sum(entry.file_size for entry in entries) > 16_000_000:
            raise ValueError("Horse source workbook expands beyond the reader limit")
        sheets = ET.fromstring(workbook.read("xl/workbook.xml"))
        relationships = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
        sheet = sheets.find("x:sheets/x:sheet[@name='Sheet1']", _NS)
        if sheet is None:
            raise ValueError("Horse source workbook has no Sheet1")
        relation_id = sheet.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        targets = [
            node.get("Target")
            for node in relationships
            if node.get("Id") == relation_id and node.get("TargetMode") != "External"
        ]
        if targets not in (["worksheets/sheet1.xml"], ["/xl/worksheets/sheet1.xml"]):
            raise ValueError("Horse source Sheet1 relationship differs")
        shared: list[str] = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            for item in ET.fromstring(workbook.read("xl/sharedStrings.xml")).findall(
                "x:si", _NS
            ):
                if item.find("x:rPh", _NS) is not None:
                    raise ValueError("Horse source phonetic strings are unsupported")
                shared.append(
                    "".join(node.text or "" for node in item.findall(".//x:t", _NS))
                )
        worksheet = ET.fromstring(workbook.read(_SHEET_PART))
    cells: dict[str, dict[str, object]] = {}
    row_numbers: list[int] = []
    for row in worksheet.findall("x:sheetData/x:row", _NS):
        number_text = row.get("r", "")
        if re.fullmatch(r"[1-9][0-9]*", number_text) is None:
            raise ValueError("Horse source row number is invalid")
        number = int(number_text)
        if number in row_numbers:
            raise ValueError("Horse source row number is duplicated")
        row_numbers.append(number)
        for cell in row.findall("x:c", _NS):
            reference = cell.get("r", "")
            match = _CELL_REFERENCE.fullmatch(reference)
            if match is None or match[2] != number_text or reference in cells:
                raise ValueError("Horse source cell ownership is invalid")
            value = cell.find("x:v", _NS)
            formula = cell.find("x:f", _NS)
            inline = cell.find("x:is", _NS)
            raw = value.text if value is not None else None
            kind = cell.get("t")
            literal = raw
            if kind == "s" and raw is not None:
                if re.fullmatch(r"[0-9]+", raw) is None or int(raw) >= len(shared):
                    raise ValueError("Horse source shared-string index is invalid")
                literal = shared[int(raw)]
            elif kind == "inlineStr" and inline is not None:
                literal = "".join(
                    node.text or "" for node in inline.findall(".//x:t", _NS)
                )
            elif kind not in {None, "n", "s", "str", "inlineStr", "b", "e", "d"}:
                raise ValueError("Horse source cell type is unsupported")
            cells[reference] = {
                "cell_reference": reference,
                "cell_state": "present_blank"
                if value is None and formula is None and inline is None
                else "present_value",
                "native_type_attribute": kind,
                "native_style_attribute": cell.get("s"),
                "value_element_present": value is not None,
                "native_value_literal": raw,
                "resolved_literal": literal,
                "formula_present": formula is not None,
                "formula_literal": formula.text if formula is not None else None,
                "formula_attributes": dict(formula.attrib)
                if formula is not None
                else {},
                "inline_string_present": inline is not None,
            }
    merges = tuple(
        node.get("ref", "")
        for node in worksheet.findall("x:mergeCells/x:mergeCell", _NS)
    )
    return cells, tuple(row_numbers), merges


def _horse_cell(
    cells: Mapping[str, dict[str, object]], reference: str
) -> dict[str, object]:
    if reference in cells:
        return dict(cells[reference])
    return {
        "cell_reference": reference,
        "cell_state": "missing_cell",
        "native_type_attribute": None,
        "native_style_attribute": None,
        "value_element_present": False,
        "native_value_literal": None,
        "resolved_literal": None,
        "formula_present": False,
        "formula_literal": None,
        "formula_attributes": {},
        "inline_string_present": False,
    }
