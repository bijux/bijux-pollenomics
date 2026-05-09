from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
    ADNA_COVERAGE_POSTURES,
    ADNA_CURATION_CLASSES,
    build_domestication_coverage_report,
    build_species_curation_manifest,
)


class AdnaCurationUnitTests(unittest.TestCase):
    def test_species_curation_manifest_builds_paper_pinned_core_manifest_for_horse(
        self,
    ) -> None:
        manifest = build_species_curation_manifest("horse")

        self.assertEqual(manifest.curation_class, "paper_pinned_core")
        self.assertEqual(manifest.species.latin_name, "Equus caballus")
        self.assertGreaterEqual(len(manifest.curated_projects), 4)
        self.assertTrue(
            any(row.project_accession == "PRJEB22390" for row in manifest.curated_projects)
        )
        self.assertTrue(
            any(row.project_accession == "PRJEB56293" for row in manifest.pending_projects)
        )
        self.assertTrue(
            any(
                row.project_accession == "PRJEB9799"
                and row.rejection_reason == "modern_or_irrelevant"
                for row in manifest.rejected_projects
            )
        )

    def test_species_curation_manifest_builds_comparator_manifest_for_donkey(
        self,
    ) -> None:
        manifest = build_species_curation_manifest("donkey")

        self.assertEqual(manifest.curation_class, "comparator_only")
        self.assertEqual(manifest.curated_projects, ())
        self.assertGreaterEqual(len(manifest.pending_projects), 4)
        self.assertTrue(
            any(
                row.project_accession == "PRJEB55549"
                for row in manifest.rejected_projects
            )
        )

    def test_species_curation_manifest_builds_core_and_comparator_manifests_for_new_species(
        self,
    ) -> None:
        dog = build_species_curation_manifest("dog")
        camel = build_species_curation_manifest("camel")
        reindeer = build_species_curation_manifest("reindeer")

        self.assertEqual(dog.curation_class, "paper_pinned_core")
        self.assertTrue(any(row.project_accession == "SRS1407451" for row in dog.curated_projects))
        self.assertEqual(camel.curation_class, "paper_pinned_core")
        self.assertTrue(
            any(row.project_accession == "SRP073444" for row in camel.curated_projects)
        )
        self.assertEqual(reindeer.curation_class, "comparator_only")
        self.assertTrue(
            any(row.project_accession == "PRJEB60484" for row in reindeer.pending_projects)
        )

    def test_species_curation_manifest_classifies_genbank_and_precuration_species(
        self,
    ) -> None:
        chicken = build_species_curation_manifest("chicken")
        rabbit = build_species_curation_manifest("rabbit")

        self.assertEqual(chicken.curation_class, "genbank_only_or_non_project_archive")
        self.assertEqual(rabbit.curation_class, "weak_or_precuration")
        self.assertEqual(chicken.curated_projects, ())
        self.assertEqual(rabbit.pending_projects, ())

    def test_domestication_coverage_report_marks_strong_thin_and_current_core_rows(
        self,
    ) -> None:
        report = build_domestication_coverage_report()

        self.assertTrue(all(row.curation_class in ADNA_CURATION_CLASSES for row in report.rows))
        self.assertTrue(all(row.coverage_posture in ADNA_COVERAGE_POSTURES for row in report.rows))
        horse = next(row for row in report.rows if row.species_latin_name == "Equus caballus")
        chicken = next(
            row for row in report.rows if row.species_latin_name == "Gallus gallus domesticus"
        )
        cattle = next(row for row in report.rows if row.species_latin_name == "Bos taurus")

        self.assertEqual(horse.coverage_posture, "strong")
        self.assertEqual(chicken.coverage_posture, "thin")
        self.assertEqual(cattle.coverage_posture, "strong")


if __name__ == "__main__":
    unittest.main()
