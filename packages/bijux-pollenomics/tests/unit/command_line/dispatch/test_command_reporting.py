from __future__ import annotations

import unittest
from unittest.mock import patch

from bijux_pollenomics.command_line.parsing import build_parser
from bijux_pollenomics.command_line.runtime import run_command


class CommandLineUnitTests(unittest.TestCase):
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

    def test_build_parser_supports_ownership_map_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["ownership-map"])

        self.assertEqual(args.command, "ownership-map")
        self.assertFalse(args.json)

    def test_run_command_routes_ownership_map_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["ownership-map"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_ownership_map",
            return_value=8,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 8)
        handler.assert_called_once_with(args)

    def test_build_parser_supports_source_support_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["source-support"])

        self.assertEqual(args.command, "source-support")
        self.assertFalse(args.json)

    def test_run_command_routes_source_support_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["source-support"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_source_support",
            return_value=9,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 9)
        handler.assert_called_once_with(args)
