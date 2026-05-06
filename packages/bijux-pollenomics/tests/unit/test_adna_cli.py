from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch

from bijux_pollenomics.command_line.runtime.handlers import (
    run_adna_archive_projects,
    run_adna_artifact_plan,
    run_adna_curation_manifest,
    run_adna_domestication_coverage,
    run_adna_layout,
    run_adna_normalization_bundle,
    run_adna_release_readiness,
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

    def test_adna_curation_manifest_json_output_exposes_core_and_reject_projects(
        self,
    ) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            exit_code = run_adna_curation_manifest(
                type("Args", (), {"json": True, "species": "horse"})()
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["curation_class"], "paper_pinned_core")
        self.assertTrue(
            any(
                row["project_accession"] == "PRJEB22390"
                for row in payload["curated_projects"]
            )
        )
        self.assertTrue(
            any(
                row["project_accession"] == "PRJEB9799"
                for row in payload["rejected_projects"]
            )
        )

    def test_adna_domestication_coverage_json_output_marks_pretending_species(
        self,
    ) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            exit_code = run_adna_domestication_coverage(
                type("Args", (), {"json": True})()
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        cattle = next(
            row for row in payload["rows"] if row["species_latin_name"] == "Bos taurus"
        )
        self.assertEqual(cattle["coverage_posture"], "pretending")

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

    def test_adna_artifact_plan_json_output_exposes_governed_paths(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            exit_code = run_adna_artifact_plan(
                type("Args", (), {"json": True, "species": "horse"})()
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["schema_version"], "adna-species-artifact-plan.v1")
        target_paths = {item["target_path"] for item in payload["entries"]}
        self.assertIn(
            "data/adna/equus_caballus/manifests/normalization_bundle.json",
            target_paths,
        )
        self.assertIn(
            "data/adna/equus_caballus/review/species_review.json",
            target_paths,
        )

    def test_adna_normalization_bundle_json_output_exposes_lineage_and_refusals(
        self,
    ) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            exit_code = run_adna_normalization_bundle(
                type("Args", (), {"json": True, "species": "horse"})()
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(
            payload["schema_version"],
            "adna-nonhuman-normalization-bundle.v1",
        )
        self.assertTrue(payload["lineage_records"])
        self.assertTrue(payload["refusals"])
        self.assertEqual(
            payload["project_summaries"][0]["schema_version"],
            "adna-project-summary.v1",
        )

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

    def test_adna_release_readiness_json_output_exposes_cross_surface_gate(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            exit_code = run_adna_release_readiness(
                type("Args", (), {"json": True, "species": "dog"})()
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["schema_version"], "release-readiness-report.v1")
        self.assertEqual(payload["species_latin_name"], "Canis lupus familiaris")
        self.assertTrue(payload["source_identity_ok"])
        self.assertTrue(payload["atlas_bundle_contract_ok"])
        self.assertTrue(payload["ranking_provenance_ok"])

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
