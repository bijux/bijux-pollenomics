from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import pytest

from bijux_pollenomics.reporting import (
    generate_published_reports,
)


from ..fixtures.aadr import write_anno
from ..fixtures.animal_adna import write_tracked_animal_species
from ..fixtures.context_sources import write_neotoma_context


pytestmark = pytest.mark.generated_artifacts


class CountryReportTests(unittest.TestCase):
    def test_generate_published_reports_writes_shared_and_country_bundles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report"
            context_root = Path(tmp) / "data"
            write_anno(
                root / "1240k" / "v62.0_1240k_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF",
                    "NO1\tNO1\tNorway_Group\tOslo\tNorway\t59.9139\t10.7522\tPaperB\t2021\t600 BCE\t2550\tAG\tM",
                ],
            )
            write_neotoma_context(context_root)
            write_tracked_animal_species(
                context_root / "adna" / "species" / "ovis_aries",
                latin_name="Ovis aries",
                common_name="sheep",
                locality="Sweden sheep lead",
                political_entity="Sweden",
                project_accession="PRJEB59481",
                support_class="accepted",
                product_role="domesticated_core",
                nordic_inclusion=True,
                chronology_bucket="1001-3000 BP",
                paper_title="Baltic short-tailed sheep aDNA",
                paper_doi="10.1000/sheep",
            )
            write_tracked_animal_species(
                context_root / "adna" / "species" / "rangifer_tarandus",
                latin_name="Rangifer tarandus",
                common_name="reindeer",
                locality="Svalbard reindeer lead",
                political_entity="Norway",
                project_accession="PRJEB60484",
                support_class="comparator_only",
                product_role="comparator",
                nordic_inclusion=True,
                chronology_bucket="0-1000 BP",
                paper_title="Ancient reindeer context",
                paper_doi="10.1000/reindeer",
            )

            report = generate_published_reports(
                version_dir=root,
                countries=["Sweden", "Norway"],
                output_root=output,
                title="Nordic Evidence Atlas",
                slug="nordic-atlas",
                context_root=context_root,
            )

            self.assertEqual(report.countries, ("Sweden", "Norway"))
            self.assertTrue((output / "published_reports_summary.json").exists())
            self.assertTrue((output / "animal_output_audit.json").exists())
            self.assertTrue((output / "animal_output_audit.md").exists())
            self.assertTrue((output / "animal_country_species_coverage.json").exists())
            self.assertTrue((output / "animal_country_species_coverage.md").exists())
            self.assertTrue((output / "animal_atlas_readiness.json").exists())
            self.assertTrue((output / "animal_atlas_readiness.md").exists())
            self.assertTrue((output / "animal_output_honesty.json").exists())
            self.assertTrue((output / "animal_output_honesty.md").exists())
            self.assertTrue((output / "animal_atlas_exclusion_report.json").exists())
            self.assertTrue((output / "animal_atlas_exclusion_report.md").exists())
            self.assertTrue((output / "animal_foundation_validation.json").exists())
            self.assertTrue((output / "animal_foundation_validation.md").exists())
            self.assertTrue((output / "animal_cross_surface_drift.json").exists())
            self.assertTrue((output / "animal_cross_surface_drift.md").exists())
            self.assertTrue((output / "animal_scientific_caveat_ledger.json").exists())
            self.assertTrue((output / "animal_scientific_caveat_ledger.md").exists())
            self.assertTrue((output / "animal_point_evidence_review.json").exists())
            self.assertTrue((output / "animal_point_evidence_review.md").exists())
            self.assertTrue(
                (output / "animal_project_publication_gap_review.json").exists()
            )
            self.assertTrue(
                (output / "animal_project_publication_gap_review.md").exists()
            )
            self.assertTrue((output / "animal_foundation_review.json").exists())
            self.assertTrue((output / "animal_foundation_review.md").exists())
            self.assertTrue((output / "animal_publication_release_gate.json").exists())
            self.assertTrue((output / "animal_publication_release_gate.md").exists())
            self.assertTrue((output / "repository_truth_posture.json").exists())
            self.assertTrue((output / "repository_truth_posture.md").exists())
            self.assertTrue((output / "repository_claim_audit.json").exists())
            self.assertTrue((output / "repository_claim_audit.md").exists())
            self.assertTrue((output / "animal_human_chronology_overlap.json").exists())
            self.assertTrue((output / "animal_pollen_chronology_overlap.json").exists())
            self.assertTrue(
                (output / "animal_first_appearance_by_country.json").exists()
            )
            self.assertTrue((output / "nordic_farming_history_scenario.json").exists())
            self.assertTrue(
                (output / "world" / "nordic-atlas_map.html").exists()
            )
            self.assertTrue(
                (output / "regions" / "nordic" / "nordic_map.html").exists()
            )
            self.assertTrue((output / "countries" / "sweden" / "README.md").exists())
            self.assertTrue((output / "countries" / "norway" / "README.md").exists())
            self.assertTrue(
                (
                    output
                    / "countries"
                    / "sweden"
                    / "sweden_animal_adna_v62.0_summary.json"
                ).exists()
            )
            self.assertTrue(
                (
                    output
                    / "countries"
                    / "norway"
                    / "norway_animal_adna_v62.0_summary.json"
                ).exists()
            )
            sweden_readme = (output / "countries" / "sweden" / "README.md").read_text(
                encoding="utf-8"
            )
            published_summary = json.loads(
                (output / "published_reports_summary.json").read_text(encoding="utf-8")
            )
            animal_output_audit = json.loads(
                (output / "animal_output_audit.json").read_text(encoding="utf-8")
            )
            animal_output_honesty = json.loads(
                (output / "animal_output_honesty.json").read_text(encoding="utf-8")
            )
            country_species_coverage = json.loads(
                (output / "animal_country_species_coverage.json").read_text(
                    encoding="utf-8"
                )
            )
            atlas_exclusion_report = json.loads(
                (output / "animal_atlas_exclusion_report.json").read_text(
                    encoding="utf-8"
                )
            )
            foundation_review = json.loads(
                (output / "animal_foundation_review.json").read_text(encoding="utf-8")
            )
            repository_claim_audit = json.loads(
                (output / "repository_claim_audit.json").read_text(encoding="utf-8")
            )
            release_gate = json.loads(
                (output / "animal_publication_release_gate.json").read_text(
                    encoding="utf-8"
                )
            )
            atlas_readiness = json.loads(
                (output / "animal_atlas_readiness.json").read_text(encoding="utf-8")
            )
            atlas_summary = json.loads(
                (output / "regions" / "nordic" / "nordic_summary.json").read_text(
                    encoding="utf-8"
                )
            )
            atlas_traceability = json.loads(
                (
                    output
                    / "regions"
                    / "nordic"
                    / "nordic_animal_point_traceability.json"
                ).read_text(encoding="utf-8")
            )
            sweden_animal_geojson = json.loads(
                (
                    output
                    / "countries"
                    / "sweden"
                    / "sweden_animal_adna_v62.0_localities.geojson"
                ).read_text(encoding="utf-8")
            )
            sweden_summary = json.loads(
                (
                    output / "countries" / "sweden" / "sweden_aadr_v62.0_summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertIn("../../regions/nordic/nordic_map.html", sweden_readme)
            self.assertIn(">Nordic Evidence Surface</a>", sweden_readme)
            self.assertEqual(report.shared_map_dir, output / "world")
            self.assertIn(output / "countries" / "sweden", report.country_output_dirs)
            self.assertEqual(
                published_summary["artifacts"]["world_bundle"]["slug"],
                "nordic-atlas",
            )
            self.assertEqual(
                published_summary["artifacts"]["world_bundle"]["bundle_manifest"],
                "nordic-atlas_bundle.json",
            )
            self.assertEqual(
                published_summary["artifacts"]["animal_output_audit_json"],
                "animal_output_audit.json",
            )
            self.assertEqual(
                published_summary["artifacts"]["animal_output_audit_markdown"],
                "animal_output_audit.md",
            )
            self.assertEqual(
                published_summary["artifacts"]["public_animal_reporting"][
                    "animal_country_species_coverage_json"
                ],
                "animal_country_species_coverage.json",
            )
            self.assertEqual(
                published_summary["artifacts"]["public_animal_reporting"][
                    "animal_atlas_readiness_json"
                ],
                "animal_atlas_readiness.json",
            )
            self.assertEqual(
                published_summary["artifacts"]["public_animal_reporting"][
                    "animal_foundation_validation_json"
                ],
                "animal_foundation_validation.json",
            )
            self.assertEqual(
                published_summary["artifacts"]["public_animal_reporting"][
                    "animal_foundation_review_json"
                ],
                "animal_foundation_review.json",
            )
            self.assertEqual(
                published_summary["artifacts"]["public_animal_reporting"][
                    "animal_publication_release_gate_json"
                ],
                "animal_publication_release_gate.json",
            )
            self.assertEqual(
                published_summary["artifacts"]["repository_truth"][
                    "repository_truth_posture_json"
                ],
                "repository_truth_posture.json",
            )
            self.assertEqual(animal_output_audit["report_root"], "docs/report")
            self.assertEqual(
                foundation_review["public_posture"],
                "governed_metadata_foundation_not_reference_grade",
            )
            self.assertTrue(repository_claim_audit["overall_ok"])
            self.assertTrue(release_gate["overall_ok"])
            self.assertFalse(release_gate["reference_grade_support_ready"])
            sheep_audit_row = next(
                row
                for row in animal_output_audit["species_rows"]
                if row["species_latin_name"] == "Ovis aries"
            )
            self.assertEqual(sheep_audit_row["country_output_count"], 1)
            sheep_country_row = next(
                row
                for row in country_species_coverage["rows"]
                if row["country"] == "Sweden"
                and row["species_latin_name"] == "Ovis aries"
            )
            self.assertEqual(sheep_country_row["sample_row_count"], 1)
            self.assertEqual(sheep_country_row["sample_lineage_backed_sample_count"], 1)
            self.assertEqual(sheep_country_row["site_evidence_backed_sample_count"], 1)
            self.assertEqual(
                sheep_country_row["chronology_provenance_backed_sample_count"], 1
            )
            self.assertEqual(
                sheep_country_row["coordinate_provenance_backed_sample_count"], 1
            )
            self.assertEqual(sheep_country_row["geocoded_site_count"], 1)
            self.assertEqual(sheep_country_row["direct_coordinate_site_count"], 0)
            sheep_readiness = next(
                row
                for row in atlas_readiness["rows"]
                if row["species_latin_name"] == "Ovis aries"
            )
            self.assertGreaterEqual(
                sheep_readiness["publication_candidate_count"],
                1,
            )
            self.assertGreaterEqual(
                sheep_readiness["country_mapped_locality_counts"]["Sweden"],
                1,
            )
            self.assertIn(
                sheep_readiness["readiness_status"],
                {"thin", "publishable"},
            )
            self.assertIn("tracked_sample_count", animal_output_honesty["totals"])
            self.assertIn("row_count", atlas_exclusion_report)
            self.assertIn("sweden", published_summary["artifacts"]["country_bundles"])
            self.assertIn("nordic", published_summary["artifacts"]["regional_bundles"])
            self.assertEqual(
                published_summary["artifacts"]["country_bundles"]["sweden"][
                    "bundle_manifest"
                ],
                "sweden_aadr_v62.0_bundle.json",
            )
            self.assertEqual(sweden_summary["animal_adna"]["total_species"], 1)
            self.assertEqual(
                atlas_summary["output_dir"],
                "docs/report/regions/nordic",
            )
            self.assertEqual(
                sweden_summary["output_dir"],
                "docs/report/countries/sweden",
            )
            self.assertNotIn(".report.staging", atlas_summary["output_dir"])
            self.assertNotIn(".report.staging", sweden_summary["output_dir"])
            self.assertEqual(
                atlas_summary["artifacts"]["animal_point_traceability_json"],
                "nordic_animal_point_traceability.json",
            )
            sweden_evidence_row_ids = {
                feature["properties"]["evidence_row_id"]
                for feature in sweden_animal_geojson["features"]
            }
            atlas_evidence_row_ids = {
                row["evidence_row_id"]
                for row in atlas_traceability["rows"]
                if row["species_latin_name"] == "Ovis aries"
            }
            self.assertEqual(sweden_evidence_row_ids, atlas_evidence_row_ids)
            sweden_animal_summary = json.loads(
                (
                    output
                    / "countries"
                    / "sweden"
                    / "sweden_animal_adna_v62.0_summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertIn(
                "evidence_quality_summary",
                sweden_animal_summary,
            )
            self.assertIn(
                "traceability_summary",
                sweden_animal_summary,
            )
            self.assertTrue(
                sweden_animal_summary["sample_rows"][0]["sample_lineage_path"]
            )
            self.assertTrue(
                sweden_animal_summary["sample_rows"][0]["chronology_provenance_path"]
            )
            self.assertTrue(
                sweden_animal_summary["sample_rows"][0]["coordinate_provenance_path"]
            )
