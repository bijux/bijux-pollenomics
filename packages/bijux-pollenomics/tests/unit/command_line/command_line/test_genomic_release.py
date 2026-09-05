from __future__ import annotations

import unittest
from unittest.mock import patch

from bijux_pollenomics.command_line.parsing import build_parser
from bijux_pollenomics.command_line.runtime import run_command


class CommandLineUnitTests(unittest.TestCase):
    def test_build_parser_supports_adna_release_readiness_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-release-readiness", "--species", "dog"])

        self.assertEqual(args.command, "adna-release-readiness")
        self.assertEqual(args.species, "dog")
        self.assertFalse(args.json)

    def test_run_command_routes_adna_release_readiness_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-release-readiness", "--species", "dog"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_adna_release_readiness",
            return_value=19,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 19)
        handler.assert_called_once_with(args)

    def test_build_parser_supports_adna_release_bar_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-release-bar"])

        self.assertEqual(args.command, "adna-release-bar")
        self.assertFalse(args.json)

    def test_run_command_routes_adna_release_bar_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-release-bar"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_adna_release_bar",
            return_value=23,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 23)
        handler.assert_called_once_with(args)

    def test_build_parser_supports_adna_normalization_bundle_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-normalization-bundle", "--species", "horse"])

        self.assertEqual(args.command, "adna-normalization-bundle")
        self.assertEqual(args.species, "horse")
        self.assertFalse(args.json)

    def test_run_command_routes_adna_normalization_bundle_through_registry(
        self,
    ) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-normalization-bundle", "--species", "horse"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_adna_normalization_bundle",
            return_value=18,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 18)
        handler.assert_called_once_with(args)

    def test_build_parser_supports_adna_domestication_coverage_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-domestication-coverage"])

        self.assertEqual(args.command, "adna-domestication-coverage")
        self.assertFalse(args.json)

    def test_run_command_routes_adna_domestication_coverage_through_registry(
        self,
    ) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-domestication-coverage"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_adna_domestication_coverage",
            return_value=18,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 18)
        handler.assert_called_once_with(args)
