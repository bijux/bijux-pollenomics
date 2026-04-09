from __future__ import annotations

import csv
import io
from pathlib import Path
from zipfile import ZipFile


def write_landclim_ii_zip(
    path: Path,
    rows: list[dict[str, str]],
    *,
    include_standard_errors: bool = True,
    time_window_count: int = 25,
) -> None:
    """Write a LandClim II CSV archive for tests with the documented folder layout."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["LCGRID_ID", "lonDD", "latDD", "PICEA"]
    populated_buffer = io.StringIO()
    populated_writer = csv.DictWriter(populated_buffer, fieldnames=fieldnames)
    populated_writer.writeheader()
    populated_writer.writerows(rows)
    empty_buffer = io.StringIO()
    empty_writer = csv.DictWriter(empty_buffer, fieldnames=fieldnames)
    empty_writer.writeheader()
    with ZipFile(path, "w") as archive:
        for time_window_index in range(1, time_window_count + 1):
            means_name = f"LANDCLIMII.RV.means.JUN2021/TW{time_window_index}.RV.estimates.jun21.csv"
            archive.writestr(
                means_name,
                populated_buffer.getvalue()
                if time_window_index == 1
                else empty_buffer.getvalue(),
            )
            if include_standard_errors:
                standard_errors_name = (
                    f"LANDCLIMII.RV.standarderrors.JUN2021/"
                    f"TW{time_window_index}.standarderrors.jun21.csv"
                )
                archive.writestr(standard_errors_name, empty_buffer.getvalue())


def write_xlsx(path: Path, sheets: dict[str, list[list[object]]]) -> None:
    """Write a small XLSX workbook without requiring third-party packages."""
    path.parent.mkdir(parents=True, exist_ok=True)

    shared_strings: list[str] = []
    shared_string_index: dict[str, int] = {}
    worksheet_documents: dict[str, str] = {}
    relationships: list[str] = []
    workbook_sheets: list[str] = []

    for sheet_number, (sheet_name, rows) in enumerate(sheets.items(), start=1):
        cells_by_row: list[str] = []
        for row_number, row in enumerate(rows, start=1):
            cells: list[str] = []
            for column_number, value in enumerate(row, start=1):
                if value in ("", None):
                    continue
                reference = f"{column_letters(column_number)}{row_number}"
                if isinstance(value, bool):
                    cells.append(
                        f'<c r="{reference}" t="b"><v>{"1" if value else "0"}</v></c>'
                    )
                elif isinstance(value, (int, float)):
                    cells.append(f'<c r="{reference}"><v>{value}</v></c>')
                else:
                    text = str(value)
                    if text not in shared_string_index:
                        shared_string_index[text] = len(shared_strings)
                        shared_strings.append(text)
                    cells.append(
                        f'<c r="{reference}" t="s"><v>{shared_string_index[text]}</v></c>'
                    )
            cells_by_row.append(f'<row r="{row_number}">{"".join(cells)}</row>')

        worksheet_documents[f"xl/worksheets/sheet{sheet_number}.xml"] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f"<sheetData>{''.join(cells_by_row)}</sheetData>"
            "</worksheet>"
        )
        relationships.append(
            "<Relationship "
            f'Id="rId{sheet_number}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{sheet_number}.xml"/>'
        )
        workbook_sheets.append(
            f'<sheet name="{sheet_name}" sheetId="{sheet_number}" r:id="rId{sheet_number}"/>'
        )

    shared_strings_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'count="{len(shared_strings)}" uniqueCount="{len(shared_strings)}">'
        + "".join(f"<si><t>{escape_xml(value)}</t></si>" for value in shared_strings)
        + "</sst>"
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{''.join(workbook_sheets)}</sheets>"
        "</workbook>"
    )
    relationships_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(relationships)
        + "</Relationships>"
    )

    with ZipFile(path, "w") as workbook:
        workbook.writestr("xl/workbook.xml", workbook_xml)
        workbook.writestr("xl/_rels/workbook.xml.rels", relationships_xml)
        workbook.writestr("xl/sharedStrings.xml", shared_strings_xml)
        for filename, document in worksheet_documents.items():
            workbook.writestr(filename, document)


def column_letters(index: int) -> str:
    """Convert a 1-based column index to spreadsheet letters."""
    letters = ""
    current = index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def escape_xml(value: str) -> str:
    """Escape a text value for XML content."""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
