from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from bijux_pollenomics.data_downloader.xlsx import list_xlsx_sheet_names, read_xlsx_sheet_rows


class XlsxReaderTests(unittest.TestCase):
    def test_sheet_names_and_rows_preserve_order_and_sparse_cells(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.xlsx"
            write_xlsx(
                path,
                {
                    "Metadata": [
                        ["Country", "", "Value"],
                        ["Sweden", "", "1"],
                    ],
                    "SiteData": [
                        ["Label", "Boolean", "Number"],
                        ["Shared", True, 2],
                    ],
                },
            )

            self.assertEqual(list_xlsx_sheet_names(path), ["Metadata", "SiteData"])
            self.assertEqual(
                read_xlsx_sheet_rows(path, "Metadata"),
                [["Country", "", "Value"], ["Sweden", "", "1"]],
            )
            self.assertEqual(
                read_xlsx_sheet_rows(path, "SiteData"),
                [["Label", "Boolean", "Number"], ["Shared", "TRUE", "2"]],
            )


def write_xlsx(path: Path, sheets: dict[str, list[list[object]]]) -> None:
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
                    cells.append(f'<c r="{reference}" t="b"><v>{"1" if value else "0"}</v></c>')
                elif isinstance(value, (int, float)):
                    cells.append(f'<c r="{reference}"><v>{value}</v></c>')
                else:
                    text = str(value)
                    if text not in shared_string_index:
                        shared_string_index[text] = len(shared_strings)
                        shared_strings.append(text)
                    cells.append(f'<c r="{reference}" t="s"><v>{shared_string_index[text]}</v></c>')
            cells_by_row.append(f'<row r="{row_number}">{"".join(cells)}</row>')

        worksheet_documents[f"xl/worksheets/sheet{sheet_number}.xml"] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{"".join(cells_by_row)}</sheetData>'
            "</worksheet>"
        )
        relationships.append(
            '<Relationship '
            f'Id="rId{sheet_number}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{sheet_number}.xml"/>'
        )
        workbook_sheets.append(f'<sheet name="{sheet_name}" sheetId="{sheet_number}" r:id="rId{sheet_number}"/>')

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
        f'<sheets>{"".join(workbook_sheets)}</sheets>'
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
    letters = ""
    current = index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


if __name__ == "__main__":
    unittest.main()
