from __future__ import annotations

import argparse
import unittest
from unittest.mock import patch

from bijux_pollenomics.command_line.arguments import build_parser
from bijux_pollenomics.command_line.dispatch import run_command


class CommandLineUnitTests(unittest.TestCase):
    def test_run_command_routes_non_country_commands_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["collect-data", "aadr"])

        with patch("bijux_pollenomics.command_line.dispatch.run_collect_data", return_value=7) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 7)
        handler.assert_called_once_with(args)

    def test_run_command_routes_country_command_with_parser(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["report-country", "Sweden"])

        with patch("bijux_pollenomics.command_line.dispatch.run_report_country", return_value=5) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 5)
        handler.assert_called_once_with(args, parser=parser)

    def test_build_parser_requires_command(self) -> None:
        parser = build_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args([])

    def test_run_command_rejects_unsupported_command(self) -> None:
        parser = build_parser()
        args = argparse.Namespace(command="unsupported")

        with self.assertRaises(SystemExit) as error:
            run_command(args, parser=parser)

        self.assertEqual(error.exception.code, 2)
