from __future__ import annotations

import unittest
from unittest.mock import patch

from bijux_pollenomics.command_line.parsing import build_parser
from bijux_pollenomics.command_line.runtime import run_command


class CommandLineUnitTests(unittest.TestCase):
    def test_build_parser_supports_adna_layout_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-layout", "--species", "horse"])

        self.assertEqual(args.command, "adna-layout")
        self.assertEqual(args.species, "horse")
        self.assertFalse(args.json)

    def test_build_parser_supports_adna_runtime_manifest_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-runtime-manifest", "--species", "Homo sapiens"])

        self.assertEqual(args.command, "adna-runtime-manifest")
        self.assertEqual(args.species, "Homo sapiens")
        self.assertEqual(args.version, "v66")
        self.assertFalse(args.json)

    def test_run_command_routes_adna_layout_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-layout", "--species", "horse"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_adna_layout",
            return_value=17,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 17)
        handler.assert_called_once_with(args)

    def test_run_command_routes_adna_runtime_manifest_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-runtime-manifest", "--species", "horse"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_adna_runtime_manifest",
            return_value=19,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 19)
        handler.assert_called_once_with(args)

    def test_build_parser_supports_adna_species_review_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-species-review", "--species", "horse"])

        self.assertEqual(args.command, "adna-species-review")
        self.assertEqual(args.species, "horse")
        self.assertFalse(args.json)

    def test_run_command_routes_adna_species_review_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-species-review", "--species", "horse"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_adna_species_review",
            return_value=19,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 19)
        handler.assert_called_once_with(args)
