from __future__ import annotations

import unittest

from bijux_pollenomics.foundation import build_release_readiness_report


class ReleaseReadinessUnitTests(unittest.TestCase):
    def test_release_readiness_report_surfaces_curation_failures_for_cattle(self) -> None:
        report = build_release_readiness_report("Bos taurus")

        self.assertEqual(report.schema_version, "release-readiness-report.v1")
        self.assertFalse(report.curation_integrity_ok)
        self.assertFalse(report.overall_ok)
        self.assertIn("curation_integrity_contract_failed", report.findings)

    def test_release_readiness_report_passes_for_dog_publication_contracts(self) -> None:
        report = build_release_readiness_report("dog")

        self.assertTrue(report.source_identity_ok)
        self.assertTrue(report.normalized_record_contract_ok)
        self.assertTrue(report.atlas_bundle_contract_ok)
        self.assertTrue(report.ranking_provenance_ok)


if __name__ == "__main__":
    unittest.main()
