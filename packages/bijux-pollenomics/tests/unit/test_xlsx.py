from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.data_downloader.shared import (
    list_xlsx_sheet_names,
    read_xlsx_sheet_rows,
)

from tests.support.workbooks import write_xlsx


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


if __name__ == "__main__":
    unittest.main()
