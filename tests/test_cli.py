from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from bijux_pollenomics.cli import main


class CliTests(unittest.TestCase):
    def test_report_country_requires_both_shared_map_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "data" / "aadr" / "v62.0" / "ho"
            root.mkdir(parents=True, exist_ok=True)
            (root / "v62.0_HO_public.anno").write_text(
                "Genetic ID\tMaster ID\tGroup ID\tLocality\tPolitical Entity\tLat.\tLong.\tPublication abbreviation\tYear first published\tFull Date\tDate mean in BP\tData type\tMolecular Sex\n",
                encoding="utf-8",
            )

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
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

    def test_publish_reports_command_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "data" / "aadr" / "v62.0" / "ho"
            root.mkdir(parents=True, exist_ok=True)
            (root / "v62.0_HO_public.anno").write_text(
                "\n".join(
                    [
                        "Genetic ID\tMaster ID\tGroup ID\tLocality\tPolitical Entity\tLat.\tLong.\tPublication abbreviation\tYear first published\tFull Date\tDate mean in BP\tData type\tMolecular Sex",
                        "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "publish-reports",
                        "--countries",
                        "Sweden",
                        "--aadr-root",
                        str(Path(tmp) / "data" / "aadr"),
                        "--output-root",
                        str(Path(tmp) / "docs" / "report"),
                        "--context-root",
                        str(Path(tmp) / "data"),
                    ]
                )

        self.assertEqual(exit_code, 0)
