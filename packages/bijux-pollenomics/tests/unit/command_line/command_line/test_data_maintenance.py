from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from bijux_pollenomics.command_line.parsing import build_parser
from bijux_pollenomics.command_line.runtime import run_command


class CommandLineUnitTests(unittest.TestCase):
    def test_build_parser_supports_validate_collection_summary_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["validate-collection-summary"])

        self.assertEqual(args.command, "validate-collection-summary")
        self.assertEqual(args.summary_path, Path("data/collection_summary.json"))

    def test_run_command_routes_validate_collection_summary_through_registry(
        self,
    ) -> None:
        parser = build_parser()
        args = parser.parse_args(["validate-collection-summary"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_validate_collection_summary",
            return_value=11,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 11)
        handler.assert_called_once_with(args)

    def test_build_parser_supports_refresh_data_contract_surfaces_command(
        self,
    ) -> None:
        parser = build_parser()
        args = parser.parse_args(["refresh-data-contract-surfaces"])

        self.assertEqual(args.command, "refresh-data-contract-surfaces")
        self.assertEqual(args.data_root, Path("data"))
        self.assertEqual(args.version, "v66")

    def test_run_command_routes_refresh_data_contract_surfaces_through_registry(
        self,
    ) -> None:
        parser = build_parser()
        args = parser.parse_args(["refresh-data-contract-surfaces"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_refresh_data_contract_surfaces",
            return_value=12,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 12)
        handler.assert_called_once_with(args)

    def test_build_parser_supports_refresh_animal_adna_foundation_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["refresh-animal-adna-foundation"])

        self.assertEqual(args.command, "refresh-animal-adna-foundation")
        self.assertEqual(args.version, "v66")
        self.assertEqual(args.species, [])

    def test_run_command_routes_refresh_animal_adna_foundation_through_registry(
        self,
    ) -> None:
        parser = build_parser()
        args = parser.parse_args(["refresh-animal-adna-foundation"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_refresh_animal_adna_foundation",
            return_value=13,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 13)
        handler.assert_called_once_with(args)
