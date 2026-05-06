from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch

from bijux_pollenomics.command_line.runtime.handlers import (
    run_adna_archive_projects,
    run_adna_layout,
    run_adna_runtime_manifest,
    run_adna_species,
    run_adna_species_review,
)


class AdnaCliUnitTests(unittest.TestCase):
    def test_adna_layout_json_output_exposes_species_root(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            exit_code = run_adna_layout(
                type("Args", (), {"json": True, "species": "horse"})()
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["root_dir"], "data/adna/equus_caballus")

    def test_adna_archive_projects_json_output_exposes_horse_project(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            exit_code = run_adna_archive_projects(
                type("Args", (), {"json": True, "species": "horse"})()
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        project = next(
            row for row in payload if row["project_accession"] == "PRJEB22390"
        )
        self.assertEqual(project["species_latin_name"], "Equus caballus")
        self.assertEqual(project["result_kind"], "read_run")
        self.assertEqual(project["evidence_strength"], "primary_paper_pinned")
        self.assertEqual(project["sequencing_target"], "shotgun_genome")

    def test_adna_species_review_json_output_exposes_review_packet(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            exit_code = run_adna_species_review(
                type("Args", (), {"json": True, "species": "horse"})()
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(
            payload["review"]["dataset_bucket"],
            "archive_verified_needs_paper_pinning",
        )
        self.assertIn("project_manifest", payload)
        self.assertIn("project_reviews", payload)
        self.assertIn("release_blockers", payload)
        self.assertTrue(
            any(
                item["project_accession"] == "PRJEB56293"
                and item["admissible_for_curated_support"] is False
                for item in payload["project_reviews"]
            )
        )
        self.assertIn("integrity", payload)

    def test_adna_runtime_manifest_json_output_exposes_human_boundary(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            exit_code = run_adna_runtime_manifest(
                type(
                    "Args",
                    (),
                    {"json": True, "species": "Homo sapiens", "version": "v66"},
                )()
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["runtime_ready"])
        self.assertEqual(
            payload["species_manifest"]["data_root"],
            "data/adna/homo_sapiens",
        )
        self.assertIn("metadata normalization only", payload["analysis_boundary"])

    def test_adna_species_json_output_exposes_human_support_row(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            exit_code = run_adna_species(type("Args", (), {"json": True})())

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        human_row = next(
            row for row in payload if row["latin_name"] == "Homo sapiens"
        )
        self.assertEqual(human_row["support_status"], "supported")
        self.assertEqual(human_row["source_families"], ["AADR"])


if __name__ == "__main__":
    unittest.main()
