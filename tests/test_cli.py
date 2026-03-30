from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from bijux_pollenomics.cli import build_parser, main
from bijux_pollenomics.settings import DEFAULT_AADR_VERSION, DEFAULT_ATLAS_SLUG, DEFAULT_ATLAS_TITLE, DEFAULT_PUBLISHED_COUNTRIES


class CliTests(unittest.TestCase):
    def test_parser_defaults_follow_project_settings(self) -> None:
        parser = build_parser()

        publish_args = parser.parse_args(["publish-reports"])
        map_args = parser.parse_args(["report-multi-country-map", "Sweden"])
        collect_args = parser.parse_args(["collect-data", "aadr"])

        self.assertEqual(publish_args.countries, DEFAULT_PUBLISHED_COUNTRIES)
        self.assertEqual(publish_args.name, DEFAULT_ATLAS_SLUG)
        self.assertEqual(publish_args.title, DEFAULT_ATLAS_TITLE)
        self.assertEqual(publish_args.version, DEFAULT_AADR_VERSION)
        self.assertEqual(map_args.name, DEFAULT_ATLAS_SLUG)
        self.assertEqual(map_args.title, DEFAULT_ATLAS_TITLE)
        self.assertEqual(map_args.version, DEFAULT_AADR_VERSION)
        self.assertEqual(collect_args.version, DEFAULT_AADR_VERSION)

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
