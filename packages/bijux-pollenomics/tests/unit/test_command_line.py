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

    def test_build_parser_supports_adna_normalization_bundle_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-normalization-bundle", "--species", "horse"])

        self.assertEqual(args.command, "adna-normalization-bundle")
        self.assertEqual(args.species, "horse")
        self.assertFalse(args.json)

    def test_run_command_routes_adna_normalization_bundle_through_registry(self) -> None:
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

    def test_build_parser_supports_adna_layout_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["adna-layout", "--species", "horse"])

        self.assertEqual(args.command, "adna-layout")
        self.assertEqual(args.species, "horse")
        self.assertFalse(args.json)

    def test_build_parser_supports_adna_runtime_manifest_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["adna-runtime-manifest", "--species", "Homo sapiens"]
        )

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
