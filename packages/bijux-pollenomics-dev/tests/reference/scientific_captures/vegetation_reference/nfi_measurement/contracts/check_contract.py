"""Controlled workbook decoder negatives; original private data and outcomes are not opened."""

from __future__ import annotations
import copy
from pathlib import Path
import tempfile
import unittest
from xml.sax.saxutils import escape
from zipfile import ZipFile
from contracts import BASAL, NS, exact, read, sha, source_projection

A = Path(__file__).resolve().parent
R = A.parents[2]


def controlled(
    path: Path,
    *,
    rows: int = 43892,
    area: str = "153.94",
    date: str = "40000",
    outcome: str = "SEALED",
    header_mutation: bool = False,
    dictionary_mutation: bool = False,
) -> None:
    retained = read(
        R / "docs/report/validation/empd2-nfi-pairing/nfi-measurement-schema.json"
    )
    headers = copy.deepcopy(retained["workbook_headers"])
    if header_mutation:
        headers[6] = "wrong_area"
    descriptions = {h: "controlled metadata definition" for h in headers}
    descriptions.update(retained["candidate_tree_basal_area_fields"])
    descriptions["PlotArea"] = retained["plot_area_description"]
    descriptions["LandUseClass"] = retained["land_use_description"]
    descriptions["Inventory_Date"] = "YYYY-MM-DD"
    if dictionary_mutation:
        descriptions[BASAL[0]] = "undocumented unit"
    strings = list(dict.fromkeys([*headers, *descriptions.values()]))
    indexes = {v: i for i, v in enumerate(strings)}
    shared = (
        '<sst xmlns="'
        + NS[1:-1]
        + '">'
        + "".join("<si><t>" + escape(v) + "</t></si>" for v in strings)
        + "</sst>"
    )
    dictionary = (
        '<worksheet xmlns="'
        + NS[1:-1]
        + '"><sheetData>'
        + "".join(
            f'<row r="{i}"><c r="A{i}" t="s"><v>{indexes[h]}</v></c><c r="B{i}" t="s"><v>{indexes[descriptions[h]]}</v></c></row>'
            for i, h in enumerate(headers, 1)
        )
        + "</sheetData></worksheet>"
    )

    def column(i: int) -> str:
        return chr(65 + i) if i < 26 else "A" + chr(65 + i - 26)

    head = (
        '<row r="1">'
        + "".join(
            f'<c r="{column(i)}1" t="s"><v>{indexes[h]}</v></c>'
            for i, h in enumerate(headers)
        )
        + "</row>"
    )
    body = "".join(
        f'<row r="{i}"><c r="D{i}"><v>{date}</v></c><c r="G{i}"><v>{area}</v></c><c r="H{i}"><v>1</v></c><c r="Z{i}"><v>{escape(outcome)}</v></c></row>'
        for i in range(2, rows + 2)
    )
    sheet = (
        '<worksheet xmlns="'
        + NS[1:-1]
        + '"><sheetData>'
        + head
        + body
        + "</sheetData></worksheet>"
    )
    with ZipFile(path, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", shared)
        archive.writestr("xl/worksheets/sheet1.xml", dictionary)
        archive.writestr("xl/worksheets/sheet2.xml", sheet)


class Controls(unittest.TestCase):
    def test_full_controlled_population_and_sealed_values(self) -> None:
        with tempfile.TemporaryDirectory(dir=A / "preflight") as folder:
            path = Path(folder) / "controlled.xlsx"
            controlled(path)
            result, audit = source_projection(path, expected_sha=sha(path))
            self.assertEqual(result["source_plot_support"]["plot_year_rows"], 43892)
            self.assertEqual(
                result["source_plot_support"]["metadata_cells_decoded"], 131676
            )
            self.assertEqual(audit["semantic_cells_decoded"]["support"], 131676)
            self.assertEqual(audit["measurement_outcome_cells_decoded"], 0)
            controlled(path, outcome="DIFFERENT_UNSELECTED_OUTCOME")
            changed, _ = source_projection(path, expected_sha=sha(path))
            changed["source_sha256"] = result["source_sha256"]
            exact(result, changed)

    def test_expected_source_identity_refuses_controlled_workbook(self) -> None:
        with tempfile.TemporaryDirectory(dir=A / "preflight") as folder:
            path = Path(folder) / "controlled.xlsx"
            controlled(path, rows=1)
            with self.assertRaisesRegex(ValueError, "Pinned original workbook differs"):
                source_projection(path)

    def test_schema_population_area_time_units_negatives(self) -> None:
        for selector in ("headers", "rows", "area", "time", "units"):
            with (
                self.subTest(selector=selector),
                tempfile.TemporaryDirectory(dir=A / "preflight") as folder,
            ):
                path = Path(folder) / "controlled.xlsx"
                controlled(
                    path,
                    rows=1 if selector == "rows" else 43892,
                    area="0" if selector == "area" else "153.94",
                    date="NaN" if selector == "time" else "40000",
                    header_mutation=selector == "headers",
                    dictionary_mutation=selector == "units",
                )
                with self.assertRaises(ValueError):
                    source_projection(path, expected_sha=sha(path))

    def test_typed_null_and_zero_not_interchangeable(self) -> None:
        for a, b in ((0, None), (0, 0.0), (["1"], [1]), ({"x": 1}, {"x": True})):
            with self.assertRaises(ValueError):
                exact(a, b)

    def test_calibration_closure_and_outcome_scope_not_inferred(self) -> None:
        text = (A / "prepare.py").read_text()
        self.assertIn('"retained_owner_admitted": False', text)
        self.assertIn("Original provider retrieval/copy receipt", text)
        self.assertIn("source_use_statements_verified", text)
        self.assertIn("Authenticated retained official-page body", text)
        self.assertNotIn("Publication/use statement bound to exact guide bytes", text)
        observer = (A / "observe.py").read_text()
        self.assertIn('"no_measured_pairs_admitted"', observer)
        self.assertNotIn("measurement_schema.build(", observer)


if __name__ == "__main__":
    unittest.main()
