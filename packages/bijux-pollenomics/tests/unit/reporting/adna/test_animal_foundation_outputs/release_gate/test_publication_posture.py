from __future__ import annotations

from pathlib import Path
import tempfile

import pytest

from bijux_pollenomics.reporting.adna.foundation_outputs.drift import (
    build_animal_cross_surface_drift_report,
)
from bijux_pollenomics.reporting.adna.foundation_outputs.recovery import (
    build_animal_intake_recovery_review,
    build_animal_sample_database_review,
)
from bijux_pollenomics.reporting.adna.foundation_outputs.release import (
    _unsupported_numeric_chronology_exposed,
    build_animal_publication_release_gate,
)
from bijux_pollenomics.reporting.adna.foundation_outputs.review import (
    build_animal_foundation_review_packet,
    build_animal_point_evidence_review,
    build_animal_project_publication_gap_review,
    build_animal_scientific_caveat_ledger,
)
from bijux_pollenomics.reporting.adna.foundation_outputs.validation import (
    build_animal_foundation_validation_report,
)

from ..support import AnimalFoundationOutputsTestCase

pytestmark = pytest.mark.generated_artifacts


class AnimalPublicationPostureTests(AnimalFoundationOutputsTestCase):
    def test_release_gate_accepts_only_governed_numeric_precision_postures(
        self,
    ) -> None:
        assert not _unsupported_numeric_chronology_exposed(
            {
                "precision_posture": "contextual_interval",
                "time_start_bp": 100,
                "time_end_bp": 200,
            }
        )
        assert not _unsupported_numeric_chronology_exposed(
            {
                "precision_posture": "sample_approximate_or_modeled",
                "time_start_bp": 100,
                "time_end_bp": 200,
            }
        )
        assert _unsupported_numeric_chronology_exposed(
            {
                "precision_posture": "broad_period_only",
                "time_start_bp": 100,
                "time_end_bp": 200,
            }
        )
        assert _unsupported_numeric_chronology_exposed(
            {"time_start_bp": 100, "time_end_bp": 200}
        )
        assert not _unsupported_numeric_chronology_exposed(
            {"precision_posture": "broad_period_only"}
        )

    def test_foundation_review_and_release_gate_keep_public_posture_honest(
        self,
    ) -> None:
        validation_payload = build_animal_foundation_validation_report(
            data_root=self.data_root,
            report_root=self.report_root,
        )
        drift_payload = build_animal_cross_surface_drift_report(
            data_root=self.data_root,
            report_root=self.report_root,
        )
        caveat_payload = build_animal_scientific_caveat_ledger(self.data_root)
        point_payload = build_animal_point_evidence_review(
            data_root=self.data_root,
            report_root=self.report_root,
        )
        absence_payload = build_animal_project_publication_gap_review(
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
        intake_recovery_payload = build_animal_intake_recovery_review(
            data_root=self.data_root
        )
        sample_database_review_payload = build_animal_sample_database_review(
            data_root=self.data_root,
            report_root=self.report_root,
            point_payload=point_payload,
            review_payload=review_payload,
            intake_recovery_payload=intake_recovery_payload,
        )
        gate_payload = build_animal_publication_release_gate(
            data_root=self.data_root,
            report_root=self.report_root,
            docs_root=self.docs_root,
            point_payload=point_payload,
            review_payload=review_payload,
            sample_database_review_payload=sample_database_review_payload,
            intake_recovery_payload=intake_recovery_payload,
            temporal_comparison_payload={"published_feature_guard_findings": []},
        )

        self.assertEqual(
            review_payload["schema_version"], "animal-foundation-review.v1"
        )
        self.assertFalse(review_payload["reference_grade_claim_allowed"])
        self.assertEqual(
            review_payload["public_posture"],
            "governed_metadata_foundation_not_reference_grade",
        )
        self.assertEqual(
            sample_database_review_payload["schema_version"],
            "animal-sample-database-review.v1",
        )
        self.assertEqual(
            gate_payload["schema_version"], "animal-publication-release-gate.v1"
        )
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
        intake_recovery_payload = {
            "release_guard": {
                "passing": False,
                "implausibly_low_recovery_project_count": 1,
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            docs_root = Path(tmp) / "docs"
            (docs_root / "public" / "nordic-atlas").mkdir(parents=True, exist_ok=True)
            (docs_root / "public" / "pollenomics-data" / "outputs").mkdir(
                parents=True, exist_ok=True
            )
            (docs_root / "index.md").write_text(
                "all-species animal map readiness\nreference-grade nordic animal adna metadata-and-atlas foundation\n",
                encoding="utf-8",
            )
            (docs_root / "public" / "nordic-atlas" / "index.md").write_text(
                "",
                encoding="utf-8",
            )
            (
                docs_root
                / "public"
                / "pollenomics-data"
                / "outputs"
                / "nordic-atlas.md"
            ).write_text(
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
                intake_recovery_payload=intake_recovery_payload,
                temporal_comparison_payload={"published_feature_guard_findings": []},
            )

        self.assertFalse(gate_payload["overall_ok"])
        self.assertTrue(any(not row["passed"] for row in gate_payload["checks"]))
