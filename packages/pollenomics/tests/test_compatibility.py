from __future__ import annotations

import argparse
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2] / "bijux-pollenomics" / "src"),
)

from bijux_pollenomics.cli import build_parser as build_runtime_parser
from bijux_pollenomics.command_line import build_parser as build_runtime_command_parser
from bijux_pollenomics.reporting.models import MultiCountryMapReport as RuntimeMapReport
from pollenomics import __version__, collect_data
from pollenomics.cli import build_parser
from pollenomics.command_line import build_parser as build_alias_command_parser
from pollenomics.reporting.models import MultiCountryMapReport as AliasMapReport


class PollenomicsCompatibilityTests(unittest.TestCase):
    def test_import_surface_re_exports_runtime_api(self) -> None:
        self.assertTrue(callable(collect_data))
        self.assertIsInstance(__version__, str)

    def test_cli_parser_supports_runtime_commands(self) -> None:
        parser = build_parser()

        self.assertEqual(parser.prog, "pollenomics")
        collect_args = parser.parse_args(["collect-data", "aadr"])

        self.assertEqual(collect_args.command, "collect-data")

    def test_cli_parser_command_set_matches_runtime_parser(self) -> None:
        alias_parser = build_parser()
        runtime_parser = build_runtime_parser()

        alias_commands = _extract_command_choices(alias_parser)
        runtime_commands = _extract_command_choices(runtime_parser)

        self.assertEqual(alias_commands, runtime_commands)

    def test_command_line_module_aliases_runtime_module_identity(self) -> None:
        self.assertIs(build_alias_command_parser, build_runtime_command_parser)

    def test_nested_runtime_types_keep_identity_under_alias_imports(self) -> None:
        self.assertIs(AliasMapReport, RuntimeMapReport)


def _extract_command_choices(parser: argparse.ArgumentParser) -> set[str]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):  # noqa: SLF001
            return {str(name) for name in action.choices}
    return set()


if __name__ == "__main__":
    unittest.main()
