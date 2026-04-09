from __future__ import annotations

import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from bijux_pollenomics import __version__
from bijux_pollenomics.cli import build_parser, main
from bijux_pollenomics.config import (
    DEFAULT_AADR_VERSION,
    DEFAULT_ATLAS_SLUG,
    DEFAULT_ATLAS_TITLE,
    DEFAULT_PUBLISHED_COUNTRIES,
)

from tests.support.aadr import AADR_HEADER

REPO_ROOT = Path(__file__).resolve().parents[2]
EDITABLE_CONSOLE_SCRIPT = (
    REPO_ROOT / "artifacts" / ".venv" / "bin" / "bijux-pollenomics"
)


class CliTests(unittest.TestCase):
    def _require_console_script(self) -> Path:
        configured_console_script = os.environ.get("BIJUX_POLLENOMICS_CONSOLE_SCRIPT")
        if configured_console_script:
            return Path(configured_console_script)

        if EDITABLE_CONSOLE_SCRIPT.exists():
            return EDITABLE_CONSOLE_SCRIPT

        interpreter_sibling = Path(sys.executable).with_name("bijux-pollenomics")
        if interpreter_sibling.exists():
            return interpreter_sibling

        self.skipTest(
            "Installed console script not found. Run `make install` before installed-script checks."
        )
        raise AssertionError("unreachable")

    def test_module_entrypoint_displays_help(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = "src"

        result = subprocess.run(
            [sys.executable, "-m", "bijux_pollenomics", "--help"],
            cwd=REPO_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("usage: bijux-pollenomics", result.stdout)
        self.assertIn("publish-reports", result.stdout)

    def test_installed_console_script_displays_help(self) -> None:
        console_script = self._require_console_script()
        result = subprocess.run(
            [str(console_script), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("usage: bijux-pollenomics", result.stdout)
        self.assertIn("collect-data", result.stdout)

    def test_installed_console_script_displays_package_version(self) -> None:
        console_script = self._require_console_script()
        result = subprocess.run(
            [str(console_script), "--version"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), f"bijux-pollenomics {__version__}")

    def test_collect_data_help_lists_accepted_source_names(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = "src"

        result = subprocess.run(
            [sys.executable, "-m", "bijux_pollenomics", "collect-data", "--help"],
            cwd=REPO_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Accepted values:", result.stdout)
        self.assertIn(
            "all, aadr, boundaries, landclim, neotoma, raa, sead.", result.stdout
        )

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
                AADR_HEADER + "\n",
                encoding="utf-8",
            )

            stderr = io.StringIO()
            with (
                contextlib.redirect_stderr(stderr),
                self.assertRaises(SystemExit) as error,
            ):
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
                        AADR_HEADER,
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

    def test_report_country_command_writes_country_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "data" / "aadr" / "v62.0" / "ho"
            root.mkdir(parents=True, exist_ok=True)
            (root / "v62.0_HO_public.anno").write_text(
                "\n".join(
                    [
                        AADR_HEADER,
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
                        "report-country",
                        "Sweden",
                        "--aadr-root",
                        str(Path(tmp) / "data" / "aadr"),
                        "--output-root",
                        str(Path(tmp) / "docs" / "report"),
                    ]
                )

            bundle_root = Path(tmp) / "docs" / "report" / "sweden"
            self.assertEqual(exit_code, 0)
            self.assertIn("1 unique samples", stdout.getvalue())
            self.assertTrue((bundle_root / "README.md").exists())
            self.assertTrue((bundle_root / "sweden_aadr_v62.0_summary.json").exists())

    def test_report_multi_country_map_command_writes_atlas_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "data" / "aadr" / "v62.0" / "ho"
            root.mkdir(parents=True, exist_ok=True)
            (root / "v62.0_HO_public.anno").write_text(
                "\n".join(
                    [
                        AADR_HEADER,
                        "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                        "NO1\tNO1\tNorway_Group\tOslo\tNorway\t59.9139\t10.7522\tPaperB\t2021\t600 BCE\t2550\tHO\tM",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "report-multi-country-map",
                        "Sweden",
                        "Norway",
                        "--aadr-root",
                        str(Path(tmp) / "data" / "aadr"),
                        "--output-root",
                        str(Path(tmp) / "docs" / "report"),
                        "--context-root",
                        str(Path(tmp) / "data"),
                    ]
                )

            atlas_root = Path(tmp) / "docs" / "report" / "nordic-atlas"
            self.assertEqual(exit_code, 0)
            self.assertIn("2 unique samples", stdout.getvalue())
            self.assertTrue((atlas_root / "nordic-atlas_map.html").exists())
            self.assertTrue((atlas_root / "nordic-atlas_summary.json").exists())

    def test_collect_data_command_writes_summary_and_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            stdout = io.StringIO()
            with patch(
                "bijux_pollenomics.data_downloader.collector.download_aadr_anno_files"
            ) as download_aadr:
                download_aadr.return_value.downloaded_files = (Path("a"), Path("b"))
                with contextlib.redirect_stdout(stdout):
                    exit_code = main(
                        [
                            "collect-data",
                            "aadr",
                            "--output-root",
                            str(output_root),
                        ]
                    )

            self.assertEqual(exit_code, 0)
            self.assertIn("2 AADR .anno files", stdout.getvalue())
            self.assertTrue((output_root / "README.md").exists())
            self.assertTrue((output_root / "collection_summary.json").exists())

    def test_collect_data_command_accepts_case_insensitive_source_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            with patch(
                "bijux_pollenomics.data_downloader.collector.download_aadr_anno_files"
            ) as download_aadr:
                download_aadr.return_value.downloaded_files = ()

                exit_code = main(
                    [
                        "collect-data",
                        "AADR",
                        "--output-root",
                        str(output_root),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue((output_root / "collection_summary.json").exists())
