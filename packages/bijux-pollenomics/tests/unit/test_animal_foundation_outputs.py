from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.reporting.adna.foundation_outputs import (
    build_animal_cross_surface_drift_report,
    build_animal_foundation_review_packet,
    build_animal_sample_database_review,
    build_animal_sample_chronology_viewer,
    build_animal_foundation_validation_report,
    build_animal_point_support_packets,
    build_animal_project_absence_packets,
    build_animal_publication_release_gate,
    build_animal_scientific_caveat_ledger,
    publish_animal_foundation_outputs,
)


class AnimalFoundationOutputsUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[4]
        self.data_root = self.repo_root / "data"
        self.report_root = self.repo_root / "docs" / "report"
        self.docs_root = self.repo_root / "docs"

    def test_foundation_validation_exposes_structural_gaps_without_hiding_traceability(
        self,
    ) -> None:
        payload = build_animal_foundation_validation_report(
            data_root=self.data_root,
            report_root=self.report_root,
        )

        self.assertEqual(payload["schema_version"], "animal-foundation-validation.v1")
        paper_linkage_check = next(
            row
            for row in payload["checks"]
            if row["check_id"] == "sample_paper_linkage_present"
        )
        supplement_check = next(
            row
            for row in payload["checks"]
            if row["check_id"] == "supplement_required_projects_archived"
        )
        traceability_check = next(
            row for row in payload["checks"] if row["check_id"] == "atlas_rows_keep_traceability"
        )
        self.assertFalse(payload["overall_ok"])
        self.assertFalse(paper_linkage_check["passed"])
        self.assertTrue(supplement_check["passed"])
        self.assertTrue(traceability_check["passed"])

    def test_cross_surface_drift_report_stays_clean_for_current_shipped_rows(self) -> None:
        payload = build_animal_cross_surface_drift_report(
            data_root=self.data_root,
            report_root=self.report_root,
        )

        self.assertEqual(payload["schema_version"], "animal-cross-surface-drift.v1")
        self.assertEqual(len(payload["rows"]), 10)
        self.assertFalse(payload["drift_detected"])

    def test_scientific_caveat_ledger_groups_current_weak_points(self) -> None:
        payload = build_animal_scientific_caveat_ledger(self.data_root)

        self.assertEqual(payload["schema_version"], "animal-scientific-caveat-ledger.v1")
        self.assertGreater(payload["summary"]["unreadable_table_count"], 0)
        self.assertGreater(payload["summary"]["uncertain_site_assignment_count"], 0)
        self.assertGreater(payload["summary"]["region_only_geography_count"], 0)

    def test_point_support_packets_keep_sample_site_and_coordinate_support_together(
        self,
    ) -> None:
        payload = build_animal_point_support_packets(
            data_root=self.data_root,
            report_root=self.report_root,
        )

        self.assertEqual(payload["schema_version"], "animal-point-support-packets.v1")
        self.assertEqual(payload["row_count"], 2)
        first_row = payload["rows"][0]
        self.assertTrue(first_row["sample_rows"])
        self.assertTrue(first_row["site_evidence"])
        self.assertTrue(first_row["coordinate_provenance"])

    def test_project_absence_packets_explain_non_published_projects(self) -> None:
        payload = build_animal_project_absence_packets(
            data_root=self.data_root,
            report_root=self.report_root,
        )

        self.assertEqual(payload["schema_version"], "animal-project-absence-packets.v1")
        self.assertGreater(payload["row_count"], 0)
        self.assertTrue(
            any(
                row["absence_stage"] in {
                    "paper_or_metadata_capture",
                    "supplement_capture",
                    "site_extraction",
                    "coordinate_resolution",
                    "comparator_context_only",
                }
                for row in payload["rows"]
            )
        )

    def test_sample_chronology_viewer_keeps_current_governed_rows_reader_visible(self) -> None:
        payload = build_animal_sample_chronology_viewer(data_root=self.data_root)

        self.assertEqual(payload["schema_version"], "animal-sample-chronology-viewer.v1")
        self.assertEqual(payload["row_count"], 249)
        self.assertEqual(payload["normalization_counts"]["normalized_interval"], 156)
        self.assertEqual(payload["normalization_counts"]["normalized_point"], 54)
        self.assertEqual(payload["normalization_counts"]["unresolved"], 26)
        self.assertTrue(
            any(
                row["project_accession"] == "PRJEB36540"
                and row["chronology_strength"] == "sample_owned_interval"
                for row in payload["rows"]
            )
        )

    def test_sample_database_review_packet_proves_sample_owned_public_posture(self) -> None:
        point_payload = build_animal_point_support_packets(
            data_root=self.data_root,
            report_root=self.report_root,
        )
        payload = build_animal_sample_database_review(
            data_root=self.data_root,
            report_root=self.report_root,
            point_payload=point_payload,
            review_payload={"blockers": ["foundation_validation_not_yet_clean"]},
        )

        self.assertEqual(payload["schema_version"], "animal-sample-database-review.v1")
        self.assertEqual(
            payload["public_posture"],
            "partial_sample_owned_animal_evidence_surface",
        )
        self.assertTrue(payload["sample_database_claim_supported"])
        self.assertFalse(payload["nordic_view_supported_now"])
        self.assertFalse(payload["region_agnostic_contract_ready"])
        self.assertEqual(payload["counts"]["published_atlas_point_count"], 2)
        self.assertEqual(payload["counts"]["papers_with_archived_supplements"], 18)
        self.assertIn(
            "published_atlas_point_count_below_minimum_reading_depth",
            payload["posture_findings"],
        )
        self.assertNotIn(
            "supplement_backed_paper_coverage_still_too_low",
            payload["posture_findings"],
        )
        self.assertIn("sample_foundation_truth", payload["direct_links"])

    def test_foundation_review_and_release_gate_keep_public_posture_honest(self) -> None:
        validation_payload = build_animal_foundation_validation_report(
            data_root=self.data_root,
            report_root=self.report_root,
        )
        drift_payload = build_animal_cross_surface_drift_report(
            data_root=self.data_root,
            report_root=self.report_root,
        )
        caveat_payload = build_animal_scientific_caveat_ledger(self.data_root)
        point_payload = build_animal_point_support_packets(
            data_root=self.data_root,
            report_root=self.report_root,
        )
        absence_payload = build_animal_project_absence_packets(
            data_root=self.data_root,
            report_root=self.report_root,
        )
        review_payload = build_animal_foundation_review_packet(
            data_root=self.data_root,
            report_root=self.report_root,
            validation_payload=validation_payload,
            drift_payload=drift_payload,
            caveat_payload=caveat_payload,
            point_payload=point_payload,
            absence_payload=absence_payload,
        )
        sample_database_review_payload = build_animal_sample_database_review(
            data_root=self.data_root,
            report_root=self.report_root,
            point_payload=point_payload,
            review_payload=review_payload,
        )
        gate_payload = build_animal_publication_release_gate(
            data_root=self.data_root,
            report_root=self.report_root,
            docs_root=self.docs_root,
            point_payload=point_payload,
            review_payload=review_payload,
            sample_database_review_payload=sample_database_review_payload,
        )

        self.assertEqual(review_payload["schema_version"], "animal-foundation-review.v1")
        self.assertFalse(review_payload["reference_grade_claim_allowed"])
        self.assertEqual(
            review_payload["public_posture"],
            "governed_metadata_foundation_not_reference_grade",
        )
        self.assertEqual(
            sample_database_review_payload["schema_version"],
            "animal-sample-database-review.v1",
        )
        self.assertEqual(gate_payload["schema_version"], "animal-publication-release-gate.v1")
        self.assertTrue(gate_payload["overall_ok"])
        self.assertFalse(gate_payload["reference_grade_support_ready"])
        self.assertTrue(
            gate_payload["reference_grade_support_requirements"][
                "sample_database_artifacts_present"
            ]
        )

    def test_release_gate_fails_when_docs_overclaim_readiness(self) -> None:
        point_payload = {
            "rows": [
                {
                    "feature_id": "animal-atlas-feature:test",
                    "paper_url": "https://doi.org/10.1/test",
                    "sample_rows": [{"identity": {"stable_token": "x"}}],
                    "site_evidence": {"project_accession": "PRJTEST"},
                    "coordinate_provenance": {"project_accession": "PRJTEST"},
                }
            ]
        }
        review_payload = {
            "reference_grade_claim_allowed": False,
        }
        sample_database_review_payload = {
            "sample_database_claim_supported": True,
            "nordic_view_supported_now": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            docs_root = Path(tmp) / "docs"
            (docs_root / "05-nordic-evidence-atlas").mkdir(parents=True, exist_ok=True)
            (docs_root / "02-bijux-pollenomics-data" / "outputs").mkdir(
                parents=True, exist_ok=True
            )
            (docs_root / "index.md").write_text(
                "all-species animal map readiness\nreference-grade nordic animal adna metadata-and-atlas foundation\n",
                encoding="utf-8",
            )
            (docs_root / "05-nordic-evidence-atlas" / "index.md").write_text(
                "",
                encoding="utf-8",
            )
            (docs_root / "02-bijux-pollenomics-data" / "outputs" / "nordic-atlas.md").write_text(
                "",
                encoding="utf-8",
            )
            gate_payload = build_animal_publication_release_gate(
                data_root=self.data_root,
                report_root=self.report_root,
                docs_root=docs_root,
                point_payload=point_payload,
                review_payload=review_payload,
                sample_database_review_payload=sample_database_review_payload,
            )

        self.assertFalse(gate_payload["overall_ok"])
        self.assertTrue(
            any(not row["passed"] for row in gate_payload["checks"])
        )

    def test_release_gate_fails_when_project_locality_output_flattens_sample_sites(self) -> None:
        point_payload = {"rows": []}
        review_payload = {"reference_grade_claim_allowed": False}
        sample_database_review_payload = {
            "sample_database_claim_supported": True,
            "nordic_view_supported_now": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root = root / "data"
            docs_root = root / "docs"
            species_root = data_root / "adna" / "species" / "ovis_aries"
            normalized_root = species_root / "normalized"
            normalized_root.mkdir(parents=True, exist_ok=True)
            (species_root / "README.md").write_text(
                "# sheep\n\n- Curated sample rows: `2`\n",
                encoding="utf-8",
            )
            _write_json(
                normalized_root / "sample_records.json",
                {
                    "samples": [
                        _sample_row(
                            stable_token="ovis_aries:sample:one",
                            locality_token="ovis_aries:sample-site:one",
                            locality_text="Site One",
                            project_accession="PRJTEST",
                        ),
                        _sample_row(
                            stable_token="ovis_aries:sample:two",
                            locality_token="ovis_aries:sample-site:two",
                            locality_text="Site Two",
                            project_accession="PRJTEST",
                        ),
                    ]
                },
            )
            _write_json(
                normalized_root / "locality_summaries.json",
                {
                    "localities": [
                        {
                            "identity": {"stable_token": "ovis_aries:project-locality:prjtest"},
                            "project_accessions": ["PRJTEST"],
                            "sample_namespace": "ovis_aries:project_locality",
                        }
                    ]
                },
            )
            (docs_root / "05-nordic-evidence-atlas").mkdir(parents=True, exist_ok=True)
            (docs_root / "02-bijux-pollenomics-data" / "outputs").mkdir(
                parents=True, exist_ok=True
            )
            (docs_root / "index.md").write_text("", encoding="utf-8")
            (docs_root / "05-nordic-evidence-atlas" / "index.md").write_text(
                "",
                encoding="utf-8",
            )
            (docs_root / "02-bijux-pollenomics-data" / "outputs" / "nordic-atlas.md").write_text(
                "",
                encoding="utf-8",
            )

            gate_payload = build_animal_publication_release_gate(
                data_root=data_root,
                report_root=root / "report",
                docs_root=docs_root,
                point_payload=point_payload,
                review_payload=review_payload,
                sample_database_review_payload=sample_database_review_payload,
            )

        self.assertFalse(gate_payload["overall_ok"])
        self.assertTrue(
            any(
                row["check_id"]
                == "project_locality_outputs_do_not_flatten_sample_site_disagreement"
                and not row["passed"]
                for row in gate_payload["checks"]
            )
        )

    def test_release_gate_fails_when_blocked_sample_site_rows_publish_as_exact_rows(self) -> None:
        point_payload = {"rows": []}
        review_payload = {"reference_grade_claim_allowed": False}
        sample_database_review_payload = {
            "sample_database_claim_supported": True,
            "nordic_view_supported_now": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root = root / "data"
            docs_root = root / "docs"
            species_root = data_root / "adna" / "species" / "ovis_aries"
            normalized_root = species_root / "normalized"
            project_root = (
                data_root
                / "adna"
                / "governance"
                / "source_library"
                / "projects"
                / "PRJTEST"
            )
            normalized_root.mkdir(parents=True, exist_ok=True)
            project_root.mkdir(parents=True, exist_ok=True)
            (species_root / "README.md").write_text(
                "# sheep\n\n- Curated sample rows: `1`\n",
                encoding="utf-8",
            )
            _write_json(
                normalized_root / "sample_records.json",
                {
                    "samples": [
                        _sample_row(
                            stable_token="ovis_aries:sample:blocked",
                            locality_token="ovis_aries:sample-site:blocked",
                            locality_text="Blocked Site",
                            project_accession="PRJTEST",
                        ),
                    ]
                },
            )
            _write_json(normalized_root / "locality_summaries.json", {"localities": []})
            _write_json(
                project_root / "sample_sites.json",
                {
                    "rows": [
                        {
                            "repo_stable_sample_id": "ovis_aries:sample:blocked",
                            "locality_resolution_status": "project_level_site_only",
                        }
                    ]
                },
            )
            (docs_root / "05-nordic-evidence-atlas").mkdir(parents=True, exist_ok=True)
            (docs_root / "02-bijux-pollenomics-data" / "outputs").mkdir(
                parents=True, exist_ok=True
            )
            (docs_root / "index.md").write_text("", encoding="utf-8")
            (docs_root / "05-nordic-evidence-atlas" / "index.md").write_text(
                "",
                encoding="utf-8",
            )
            (docs_root / "02-bijux-pollenomics-data" / "outputs" / "nordic-atlas.md").write_text(
                "",
                encoding="utf-8",
            )

            gate_payload = build_animal_publication_release_gate(
                data_root=data_root,
                report_root=root / "report",
                docs_root=docs_root,
                point_payload=point_payload,
                review_payload=review_payload,
                sample_database_review_payload=sample_database_review_payload,
            )

        self.assertFalse(gate_payload["overall_ok"])
        self.assertTrue(
            any(
                row["check_id"]
                == "blocked_sample_site_rows_do_not_publish_as_exact_sites_or_atlas_points"
                and not row["passed"]
                for row in gate_payload["checks"]
            )
        )

    def test_release_gate_fails_when_unresolved_sample_chronology_reaches_country_and_atlas_outputs(
        self,
    ) -> None:
        review_payload = {"reference_grade_claim_allowed": False}
        sample_database_review_payload = {
            "sample_database_claim_supported": True,
            "nordic_view_supported_now": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root = root / "data"
            docs_root = root / "docs"
            report_root = root / "report"
            species_root = data_root / "adna" / "species" / "ovis_aries"
            normalized_root = species_root / "normalized"
            chronology_root = (
                data_root
                / "adna"
                / "governance"
                / "source_library"
                / "projects"
                / "PRJTEST"
            )
            country_root = report_root / "sweden"
            normalized_root.mkdir(parents=True, exist_ok=True)
            chronology_root.mkdir(parents=True, exist_ok=True)
            country_root.mkdir(parents=True, exist_ok=True)
            (species_root / "README.md").write_text(
                "# sheep\n\n- Curated sample rows: `1`\n",
                encoding="utf-8",
            )
            _write_json(
                normalized_root / "sample_records.json",
                {
                    "samples": [
                        _sample_row(
                            stable_token="ovis_aries:sample:blocked",
                            locality_token="ovis_aries:sample-site:blocked",
                            locality_text="Blocked Site",
                            project_accession="PRJTEST",
                            master_id="sample:blocked",
                        ),
                    ]
                },
            )
            _write_json(normalized_root / "locality_summaries.json", {"localities": []})
            _write_json(
                chronology_root / "sample_chronology.json",
                {
                    "rows": [
                        {
                            "repo_stable_sample_id": "sample:blocked",
                            "chronology_normalization_status": "unresolved",
                            "chronology_conflict_note": "",
                        }
                    ]
                },
            )
            _write_json(
                country_root / "sweden_animal_adna_test_summary.json",
                {"sample_rows": [{"sample_record_id": "ovis_aries:sample:blocked"}]},
            )
            point_payload = {
                "rows": [
                    {
                        "feature_id": "animal-atlas-feature:blocked",
                        "paper_url": "https://doi.org/10.1/test",
                        "sample_rows": [
                            _sample_row(
                                stable_token="ovis_aries:sample:blocked",
                                locality_token="ovis_aries:sample-site:blocked",
                                locality_text="Blocked Site",
                                project_accession="PRJTEST",
                                master_id="sample:blocked",
                            )
                        ],
                        "site_evidence": {"project_accession": "PRJTEST"},
                        "coordinate_provenance": {"project_accession": "PRJTEST"},
                    }
                ]
            }
            (docs_root / "05-nordic-evidence-atlas").mkdir(parents=True, exist_ok=True)
            (docs_root / "02-bijux-pollenomics-data" / "outputs").mkdir(
                parents=True, exist_ok=True
            )
            (docs_root / "index.md").write_text("", encoding="utf-8")
            (docs_root / "05-nordic-evidence-atlas" / "index.md").write_text(
                "",
                encoding="utf-8",
            )
            (docs_root / "02-bijux-pollenomics-data" / "outputs" / "nordic-atlas.md").write_text(
                "",
                encoding="utf-8",
            )

            gate_payload = build_animal_publication_release_gate(
                data_root=data_root,
                report_root=report_root,
                docs_root=docs_root,
                point_payload=point_payload,
                review_payload=review_payload,
                sample_database_review_payload=sample_database_review_payload,
            )

        self.assertFalse(gate_payload["overall_ok"])
        self.assertTrue(
            any(
                row["check_id"]
                == "unresolved_sample_chronology_does_not_publish_in_country_or_atlas_outputs"
                and not row["passed"]
                for row in gate_payload["checks"]
            )
        )

    def test_publish_animal_foundation_outputs_writes_expected_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            artifacts = publish_animal_foundation_outputs(
                output_root,
                data_root=self.data_root,
                docs_root=self.docs_root,
            )

            self.assertIn(
                "animal_foundation_review_json",
                artifacts,
            )
            self.assertIn(
                "animal_sample_chronology_viewer_json",
                artifacts,
            )
            self.assertIn(
                "animal_sample_database_review_json",
                artifacts,
            )
            review_path = output_root / artifacts["animal_foundation_review_json"]
            chronology_path = output_root / artifacts["animal_sample_chronology_viewer_json"]
            sample_database_review_path = (
                output_root / artifacts["animal_sample_database_review_json"]
            )
            gate_path = output_root / artifacts["animal_publication_release_gate_json"]
            self.assertTrue(review_path.is_file())
            self.assertTrue(chronology_path.is_file())
            self.assertTrue(sample_database_review_path.is_file())
            self.assertTrue(gate_path.is_file())
            review_payload = json.loads(review_path.read_text(encoding="utf-8"))
            chronology_payload = json.loads(chronology_path.read_text(encoding="utf-8"))
            sample_database_review_payload = json.loads(
                sample_database_review_path.read_text(encoding="utf-8")
            )
            gate_payload = json.loads(gate_path.read_text(encoding="utf-8"))
            self.assertEqual(
                review_payload["public_posture"],
                "governed_metadata_foundation_not_reference_grade",
            )
            self.assertEqual(chronology_payload["row_count"], 249)
            self.assertTrue(sample_database_review_payload["sample_database_claim_supported"])
            self.assertFalse(sample_database_review_payload["nordic_view_supported_now"])
            self.assertFalse(sample_database_review_payload["region_agnostic_contract_ready"])
            self.assertTrue(gate_payload["overall_ok"])

def _sample_row(
    *,
    stable_token: str,
    locality_token: str,
    locality_text: str,
    project_accession: str,
    master_id: str | None = None,
) -> dict[str, object]:
    return {
        "identity": {"stable_token": stable_token},
        "master_id": stable_token if master_id is None else master_id,
        "locality_identity": {
            "stable_token": locality_token,
            "locality_text": locality_text,
        },
        "project_accession": project_accession,
        "paper_doi": "10.1000/test",
        "paper_url": "https://doi.org/10.1000/test",
        "supplementary_source": "supplementary/test.csv",
        "sample_basis": "project_accession_anchor",
        "inclusion_status": "site_curated",
        "chronology": {
            "original_text": "1000-1200 BP",
            "time_start_bp": 1000,
            "time_end_bp": 1200,
        },
        "coordinates": {
            "latitude_text": "59.0",
            "longitude_text": "18.0",
            "confidence": "approximate",
        },
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
