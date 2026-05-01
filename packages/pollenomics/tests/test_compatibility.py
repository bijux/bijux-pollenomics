from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2] / "bijux-pollenomics" / "src"),
)

from bijux_pollenomics.cli import build_parser as build_runtime_parser
from pollenomics import __version__, collect_data
from pollenomics.cli import build_parser


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

        alias_commands = set(alias_parser._subparsers._group_actions[0].choices)
        runtime_commands = set(runtime_parser._subparsers._group_actions[0].choices)

        self.assertEqual(alias_commands, runtime_commands)


if __name__ == "__main__":
    unittest.main()
