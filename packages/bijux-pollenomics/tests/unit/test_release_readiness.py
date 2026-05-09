from __future__ import annotations

import unittest

from bijux_pollenomics.foundation import (
    build_release_bar,
    build_release_readiness_report,
)


class ReleaseReadinessUnitTests(unittest.TestCase):
    def test_release_readiness_report_surfaces_curation_failures_for_cattle(
        self,
    ) -> None:
        report = build_release_readiness_report("Bos taurus")

        self.assertEqual(report.schema_version, "release-readiness-report.v1")
        self.assertFalse(report.curation_integrity_ok)
        self.assertFalse(report.overall_ok)
        self.assertIn("curation_integrity_contract_failed", report.findings)

    def test_release_readiness_report_passes_for_dog_publication_contracts(
        self,
    ) -> None:
        report = build_release_readiness_report("dog")

        self.assertTrue(report.source_identity_ok)
        self.assertTrue(report.normalized_record_contract_ok)
        self.assertTrue(report.atlas_bundle_contract_ok)
        self.assertTrue(report.ranking_provenance_ok)

    def test_release_readiness_includes_atlas_evidence_surface_contract(self) -> None:
        report = build_release_readiness_report("Homo sapiens")

        self.assertTrue(report.atlas_bundle_contract_ok)
        self.assertNotIn("atlas_bundle_contract_failed", report.findings)

    def test_release_bar_keeps_current_posture_honest(self) -> None:
        release_bar = build_release_bar()

        self.assertEqual(release_bar.schema_version, "pollenomics-release-bar.v1")
        self.assertTrue(release_bar.species_aware_adna_support_defined)
        self.assertTrue(release_bar.bovine_split_rule_defined)
        self.assertTrue(release_bar.homo_sapiens_genotype_boundary_defined)
        self.assertTrue(release_bar.nonhuman_domestication_program_defined)
        self.assertTrue(release_bar.scientific_review_surface_defined)
        self.assertTrue(release_bar.ranking_boundary_defined)
        self.assertEqual(
            release_bar.current_posture,
            "governed_exploratory_not_release_bar_ready",
        )
        self.assertIn(
            "nonhuman_sample_and_locality_runtime_rows_not_implemented",
            release_bar.blockers,
        )


if __name__ == "__main__":
    unittest.main()
