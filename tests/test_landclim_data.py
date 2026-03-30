from __future__ import annotations

import csv
import io
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from bijux_pollenomics.data_downloader.landclim import (
    build_landclim_grid_geojson,
    feature_key_from_center,
    feature_key_from_geometry,
    grid_geometry_from_nw_cell_label,
    landclim_i_site_records,
)


SWEDEN_BOUNDARIES = {
    "Sweden": {
        "features": [
            {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[16.0, 58.0], [19.0, 58.0], [19.0, 60.5], [16.0, 60.5], [16.0, 58.0]]],
                }
            }
        ]
    }
}
NORDIC_TEST_BBOX = (4.0, 54.0, 35.0, 72.0)


class LandClimDataTests(unittest.TestCase):
    def test_landclim_i_site_records_keep_basin_type_separate_from_time_windows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "landclim_i.xlsx"
            write_xlsx(
                path,
                {
                    "SiteData": [
                        [
                            "Country",
                            "Site name",
                            "Database name\\Author\\LandClimI member collating the data",
                            "Lat (DMS)",
                            "Long (DMS)",
                            "Elevation (masl)",
                            "Area of site (ha) (*Actual size)",
                            "Basin type (ie. Lake or Bog)",
                            "",
                            "",
                            "",
                            "",
                            "No. of dates for model (*incl. top)",
                        ],
                        ["", "", "", "", "", "", "", "0-100 cal BP", "100-350 cal BP", "350-700 cal BP", "2700-3200 cal BP", "5700-6200 cal BP"],
                        ["SWE", "Lake One", "EPD", "59.00.00N", "17.00.00E", "15", "20", "L", "", "L", "", "", "4*"],
                    ],
                },
            )

            records = landclim_i_site_records(path, NORDIC_TEST_BBOX, SWEDEN_BOUNDARIES)

            self.assertEqual(len(records), 1)
            popup = {label: value for label, value in records[0].popup_rows}
            self.assertEqual(popup["Site type"], "Lake")
            self.assertEqual(popup["Time windows"], "0-100 BP, 350-700 BP")

    def test_landclim_grid_merge_uses_one_feature_for_same_cell(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw_paths = {
                "landclim_i_land_cover_types.xlsx": tmp_path / "landclim_i_land_cover_types.xlsx",
                "landclim_i_plant_functional_types.xlsx": tmp_path / "landclim_i_plant_functional_types.xlsx",
                "landclim_ii_grid_cell_quality.xlsx": tmp_path / "landclim_ii_grid_cell_quality.xlsx",
                "landclim_ii_reveals_results.zip": tmp_path / "landclim_ii_reveals_results.zip",
            }
            write_xlsx(
                raw_paths["landclim_i_land_cover_types.xlsx"],
                {
                    "0-100BPmeanLC": [
                        ["Country", "", "Grid cell", "", "Open land"],
                        ["", "", "", "", ""],
                        ["SWE", "", "17°E 60°N", "", "0.25"],
                    ]
                },
            )
            write_xlsx(
                raw_paths["landclim_i_plant_functional_types.xlsx"],
                {
                    "0-100BPmeanLC": [
                        ["Country", "", "Grid cell", "", "PFT"],
                        ["", "", "", "", ""],
                        ["SWE", "", "17°E 60°N", "", "0.10"],
                    ]
                },
            )
            write_xlsx(
                raw_paths["landclim_ii_grid_cell_quality.xlsx"],
                {
                    "GC_quality_by_TW": [
                        ["LCGRID_ID", "", "", "0-100 BP"],
                        ["GC001", "", "", "1"],
                    ]
                },
            )
            write_landclim_ii_zip(
                raw_paths["landclim_ii_reveals_results.zip"],
                [
                    {
                        "LCGRID_ID": "GC001",
                        "lonDD": "17.5",
                        "latDD": "59.5",
                        "PICEA": "0.12",
                    }
                ],
            )

            geojson = build_landclim_grid_geojson(raw_paths, NORDIC_TEST_BBOX, SWEDEN_BOUNDARIES)

            self.assertEqual(len(geojson["features"]), 1)
            properties = geojson["features"][0]["properties"]
            popup = {row["label"]: row["value"] for row in properties["popup_rows"]}
            self.assertIn("LandClim I land-cover types", popup["Datasets"])
            self.assertIn("LandClim I plant functional types", popup["Datasets"])
            self.assertIn("LandClim II REVEALS grids", popup["Datasets"])
            self.assertEqual(popup["LandClim II quality"], "high")

    def test_landclim_grid_keys_match_between_workbook_and_csv_cells(self) -> None:
        geometry = grid_geometry_from_nw_cell_label("17°E 60°N")
        self.assertIsNotNone(geometry)
        self.assertEqual(feature_key_from_geometry(geometry), feature_key_from_center(17.5, 59.5))


def write_landclim_ii_zip(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["LCGRID_ID", "lonDD", "latDD", "PICEA"]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    with ZipFile(path, "w") as archive:
        archive.writestr("LANDCLIMII.RV.means.JUN2021/TW1.RV.estimates.jun21.csv", buffer.getvalue())


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
