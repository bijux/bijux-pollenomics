from __future__ import annotations

from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

SPREADSHEET_NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
PACKAGE_NS = {"pkg": "http://schemas.openxmlformats.org/package/2006/relationships"}
RELATIONSHIP_ATTRIBUTE = (
    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
)
CELL_REFERENCE_PATTERN = re.compile(r"([A-Z]+)(\d+)")


def list_xlsx_sheet_names(path: Path) -> list[str]:
    """Return workbook sheet names in display order."""
    path = Path(path)
    with ZipFile(path) as workbook:
        workbook_document = ET.fromstring(workbook.read("xl/workbook.xml"))
        sheets = workbook_document.find("main:sheets", SPREADSHEET_NS)
        if sheets is None:
            return []
        return [
            sheet.attrib.get("name", "")
            for sheet in sheets
            if sheet.attrib.get("name", "")
        ]


def read_xlsx_sheet_rows(path: Path, sheet_name: str) -> list[list[str]]:
    """Read one worksheet from an XLSX file into row-oriented string values."""
    path = Path(path)
    with ZipFile(path) as workbook:
        shared_strings = load_shared_strings(workbook)
        sheet_targets = load_sheet_targets(workbook)
        target = sheet_targets.get(sheet_name)
        if target is None:
            raise KeyError(f"Worksheet not found in {path.name}: {sheet_name}")

        worksheet = ET.fromstring(workbook.read(target))
        rows: list[list[str]] = []
        for row in worksheet.findall("main:sheetData/main:row", SPREADSHEET_NS):
            row_values: list[str] = []
            for cell in row.findall("main:c", SPREADSHEET_NS):
                reference = cell.get("r", "")
                column_index = column_index_from_reference(reference)
                while len(row_values) <= column_index:
                    row_values.append("")
                row_values[column_index] = cell_value(cell, shared_strings)
            rows.append(trim_trailing_empty_values(row_values))
        return rows


def load_shared_strings(workbook: ZipFile) -> list[str]:
    """Load the workbook shared-string table."""
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return []
    document = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in document.findall("main:si", SPREADSHEET_NS):
        values.append(
            "".join(
                node.text or "" for node in item.findall(".//main:t", SPREADSHEET_NS)
            )
        )
    return values


def load_sheet_targets(workbook: ZipFile) -> dict[str, str]:
    """Resolve workbook sheet names to internal worksheet XML targets."""
    workbook_document = ET.fromstring(workbook.read("xl/workbook.xml"))
    relationships = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    relationship_targets = {
        relationship.attrib["Id"]: relationship.attrib["Target"]
        for relationship in relationships.findall("pkg:Relationship", PACKAGE_NS)
    }

    targets: dict[str, str] = {}
    sheets = workbook_document.find("main:sheets", SPREADSHEET_NS)
    if sheets is None:
        return targets

    for sheet in sheets:
        name = sheet.attrib.get("name", "")
        relationship_id = sheet.attrib.get(RELATIONSHIP_ATTRIBUTE, "")
        target = relationship_targets.get(relationship_id, "")
        if name and target:
            targets[name] = f"xl/{target}"
    return targets


def column_index_from_reference(reference: str) -> int:
    """Convert an XLSX cell reference such as `H3` to a zero-based column index."""
    match = CELL_REFERENCE_PATTERN.fullmatch(reference.strip().upper())
    if match is None:
        return 0
    letters = match.group(1)
    index = 0
    for letter in letters:
        index = index * 26 + (ord(letter) - ord("A") + 1)
    return max(index - 1, 0)


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    """Decode one worksheet cell into a string value."""
    inline_text = "".join(
        node.text or "" for node in cell.findall("main:is//main:t", SPREADSHEET_NS)
    )
    if inline_text:
        return inline_text

    value_node = cell.find("main:v", SPREADSHEET_NS)
    if value_node is None or value_node.text is None:
        return ""

    value = value_node.text
    cell_type = cell.get("t", "")
    if cell_type == "s":
        try:
            return shared_strings[int(value)]
        except (IndexError, ValueError):
            return ""
    if cell_type == "b":
        return "TRUE" if value == "1" else "FALSE"
    return value


def trim_trailing_empty_values(values: list[str]) -> list[str]:
    """Trim empty cells at the end of one worksheet row."""
    last_nonempty_index = -1
    for index, value in enumerate(values):
        if value != "":
            last_nonempty_index = index
    return values[: last_nonempty_index + 1]


__all__ = ["list_xlsx_sheet_names", "read_xlsx_sheet_rows"]
