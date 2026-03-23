from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bijux_pollen.cli import main


class CliTests(unittest.TestCase):
    def test_report_country_requires_both_shared_map_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "data" / "aadr" / "v62.0" / "ho"
            root.mkdir(parents=True, exist_ok=True)
            (root / "v62.0_HO_public.anno").write_text(
                "Genetic ID\tMaster ID\tGroup ID\tLocality\tPolitical Entity\tLat.\tLong.\tPublication abbreviation\tYear first published\tFull Date\tDate mean in BP\tData type\tMolecular Sex\n",
                encoding="utf-8",
            )

            with self.assertRaises(SystemExit) as error:
                main(
                    [
                        "report-country",
                        "Sweden",
                        "--aadr-root",
                        str(Path(tmp) / "data" / "aadr"),
                        "--shared-map-label",
                        "Nordic map",
                    ]
                )

        self.assertEqual(error.exception.code, 2)
