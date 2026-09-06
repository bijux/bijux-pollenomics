from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import cast

from bijux_pollenomics.collection.sources.landclim.collection import (
    inspect_landclim_ii_archive,
)

from tests.support.workbooks import write_landclim_ii_zip


class LandClimArchiveContractTests(unittest.TestCase):
    def test_inspect_landclim_ii_archive_validates_documented_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "landclim_ii_reveals_results.zip"
            write_landclim_ii_zip(
                path,
                [
                    {
                        "LCGRID_ID": "GC001",
                        "lonDD": "17.5",
                        "latDD": "59.5",
                        "PICEA": "0.12",
                    }
                ],
            )

            summary = inspect_landclim_ii_archive(path)
        time_windows = cast(list[str], summary["time_windows"])

        self.assertEqual(summary["mean_file_count"], 25)
        self.assertEqual(summary["standard_error_file_count"], 25)
        self.assertEqual(time_windows[0], "0-100 BP")
        self.assertEqual(time_windows[-1], "11200-11700 BP")

    def test_inspect_landclim_ii_archive_rejects_missing_standard_error_folder(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "landclim_ii_reveals_results.zip"
            write_landclim_ii_zip(
                path,
                [
                    {
                        "LCGRID_ID": "GC001",
                        "lonDD": "17.5",
                        "latDD": "59.5",
                        "PICEA": "0.12",
                    }
                ],
                include_standard_errors=False,
            )

            with self.assertRaisesRegex(ValueError, "standard-error"):
                inspect_landclim_ii_archive(path)


if __name__ == "__main__":
    unittest.main()
