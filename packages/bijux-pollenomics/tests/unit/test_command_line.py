from __future__ import annotations

import argparse
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from bijux_pollenomics.command_line.parsing import build_parser
from bijux_pollenomics.command_line.runtime import run_command


class CommandLineUnitTests(unittest.TestCase):
    def test_run_command_routes_non_country_commands_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["collect-data", "aadr"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_collect_data",
            return_value=7,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 7)
        handler.assert_called_once_with(args)

    def test_run_command_routes_country_command_with_parser(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["report-country", "Sweden"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_report_country",
            return_value=5,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 5)
        handler.assert_called_once_with(args, parser=parser)

    def test_build_parser_requires_command(self) -> None:
        parser = build_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args([])

    def test_build_parser_supports_top_level_version_flag(self) -> None:
        parser = build_parser()

        with self.assertRaises(SystemExit) as error:
            parser.parse_args(["--version"])

        self.assertEqual(error.exception.code, 0)

    def test_run_command_rejects_unsupported_command(self) -> None:
        parser = build_parser()
        args = argparse.Namespace(command="unsupported")

        with self.assertRaises(SystemExit) as error:
            run_command(args, parser=parser)

        self.assertEqual(error.exception.code, 2)

    def test_build_parser_supports_surface_map_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["surface-map"])

        self.assertEqual(args.command, "surface-map")
        self.assertFalse(args.json)

    def test_run_command_routes_surface_map_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["surface-map"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_surface_map",
            return_value=3,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 3)
        handler.assert_called_once_with(args)

    def test_build_parser_supports_product_scope_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["product-scope"])

        self.assertEqual(args.command, "product-scope")
        self.assertFalse(args.json)

    def test_run_command_routes_product_scope_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["product-scope"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_product_scope",
            return_value=4,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 4)
        handler.assert_called_once_with(args)

    def test_package_version_matches_pyproject(self) -> None:
        package_root = Path(__file__).resolve().parents[2]
        pyproject_text = package_root.joinpath("pyproject.toml").read_text(
            encoding="utf-8"
        )
        module_text = package_root.joinpath(
            "src/bijux_pollenomics/__init__.py"
        ).read_text(encoding="utf-8")
        pyproject_fallback = re.search(
            r'fallback-version\s*=\s*"(?P<version>[^"]+)"', pyproject_text
        )
        module_fallback = re.search(
            r'__version__\s*=\s*"(?P<version>[^"]+)"', module_text
        )

        self.assertIn('dynamic = ["version"]', pyproject_text)
        self.assertIn('requires-python = ">=3.11"', pyproject_text)
        self.assertIn("[tool.hatch.version]", pyproject_text)
        self.assertIn('source = "vcs"', pyproject_text)
        if pyproject_fallback is None:
            self.fail("Missing fallback-version in package pyproject.toml")
        if module_fallback is None:
            self.fail("Missing fallback __version__ in package module")
        self.assertEqual(
            pyproject_fallback.group("version"), module_fallback.group("version")
        )
