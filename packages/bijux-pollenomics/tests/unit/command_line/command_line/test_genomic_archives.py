from __future__ import annotations

import unittest
from unittest.mock import patch

from bijux_pollenomics.command_line.parsing import build_parser
from bijux_pollenomics.command_line.runtime import run_command


class CommandLineUnitTests(unittest.TestCase):
    def test_build_parser_supports_adna_species_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-species"])

        self.assertEqual(args.command, "adna-species")
        self.assertFalse(args.json)

    def test_run_command_routes_adna_species_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-species"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_adna_species",
            return_value=13,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 13)
        handler.assert_called_once_with(args)

    def test_build_parser_supports_adna_archive_projects_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-archive-projects", "--species", "horse"])

        self.assertEqual(args.command, "adna-archive-projects")
        self.assertEqual(args.species, "horse")
        self.assertFalse(args.json)

    def test_run_command_routes_adna_archive_projects_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-archive-projects"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_adna_archive_projects",
            return_value=15,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 15)
        handler.assert_called_once_with(args)

    def test_build_parser_supports_adna_artifact_plan_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-artifact-plan", "--species", "horse"])

        self.assertEqual(args.command, "adna-artifact-plan")
        self.assertEqual(args.species, "horse")
        self.assertFalse(args.json)

    def test_run_command_routes_adna_artifact_plan_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-artifact-plan", "--species", "horse"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_adna_artifact_plan",
            return_value=17,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 17)
        handler.assert_called_once_with(args)

    def test_build_parser_supports_adna_curation_manifest_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-curation-manifest", "--species", "horse"])

        self.assertEqual(args.command, "adna-curation-manifest")
        self.assertEqual(args.species, "horse")
        self.assertFalse(args.json)

    def test_run_command_routes_adna_curation_manifest_through_registry(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-curation-manifest", "--species", "horse"])

        with patch(
            "bijux_pollenomics.command_line.runtime.dispatch.run_adna_curation_manifest",
            return_value=16,
        ) as handler:
            exit_code = run_command(args, parser=parser)

        self.assertEqual(exit_code, 16)
        handler.assert_called_once_with(args)
