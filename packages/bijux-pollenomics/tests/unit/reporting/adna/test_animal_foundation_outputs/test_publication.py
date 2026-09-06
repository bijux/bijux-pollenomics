from __future__ import annotations

import json
from pathlib import Path
import tempfile

import pytest

from bijux_pollenomics.reporting.adna.foundation_outputs.publication import (
    publish_animal_foundation_outputs,
)
from .support import AnimalFoundationOutputsTestCase

pytestmark = pytest.mark.generated_artifacts


class AnimalFoundationPublicationTests(AnimalFoundationOutputsTestCase):
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
                "animal_sample_chronology_review_json",
                artifacts,
            )
            self.assertIn(
                "animal_temporal_comparison_review_json",
                artifacts,
            )
            self.assertIn(
                "animal_sample_database_review_json",
                artifacts,
            )
            self.assertIn(
                "animal_intake_recovery_review_json",
                artifacts,
            )
            review_path = output_root / artifacts["animal_foundation_review_json"]
            chronology_path = (
                output_root / artifacts["animal_sample_chronology_review_json"]
            )
            temporal_comparison_path = (
                output_root / artifacts["animal_temporal_comparison_review_json"]
            )
            intake_recovery_path = (
                output_root / artifacts["animal_intake_recovery_review_json"]
            )
            sample_database_review_path = (
                output_root / artifacts["animal_sample_database_review_json"]
            )
            gate_path = output_root / artifacts["animal_publication_release_gate_json"]
            self.assertTrue(review_path.is_file())
            self.assertTrue(chronology_path.is_file())
            self.assertTrue(temporal_comparison_path.is_file())
            self.assertTrue(intake_recovery_path.is_file())
            self.assertTrue(sample_database_review_path.is_file())
            self.assertTrue(gate_path.is_file())
            review_payload = json.loads(review_path.read_text(encoding="utf-8"))
            chronology_payload = json.loads(chronology_path.read_text(encoding="utf-8"))
            intake_recovery_payload = json.loads(
                intake_recovery_path.read_text(encoding="utf-8")
            )
            sample_database_review_payload = json.loads(
                sample_database_review_path.read_text(encoding="utf-8")
            )
            gate_payload = json.loads(gate_path.read_text(encoding="utf-8"))
            self.assertEqual(
                review_payload["public_posture"],
                "governed_metadata_foundation_not_reference_grade",
            )
            self.assertEqual(chronology_payload["row_count"], 1454)
            self.assertGreater(
                intake_recovery_payload["stage_review"]["blocked_projects"],
                0,
            )
            self.assertTrue(
                sample_database_review_payload["sample_database_claim_supported"]
            )
            self.assertFalse(
                sample_database_review_payload["nordic_view_supported_now"]
            )
            self.assertFalse(
                sample_database_review_payload["region_agnostic_contract_ready"]
            )
            self.assertTrue(gate_payload["overall_ok"])
            traceability_check = next(
                row
                for row in gate_payload["checks"]
                if row["check_id"] == "published_points_keep_required_traceability"
            )
            self.assertEqual(
                traceability_check["description"],
                "Every published animal point keeps declared identity, site, coordinate, and citation traceability; provisional project context remains explicitly non-final sample evidence.",
            )
