from __future__ import annotations

from pathlib import Path
import tempfile

import pytest

from bijux_pollenomics.reporting.adna.foundation_outputs.release import (
    _chronology_row_blocks_publication,
    build_animal_publication_release_gate,
)

from ..support import AnimalFoundationOutputsTestCase, sample_row, write_json

pytestmark = pytest.mark.generated_artifacts


class AnimalChronologyReleaseGateTests(AnimalFoundationOutputsTestCase):
    def test_conflicting_sample_chronology_blocks_publication(self) -> None:
        self.assertTrue(
            _chronology_row_blocks_publication(
                {
                    "chronology_normalization_status": "normalized_interval",
                    "chronology_precision_posture": "sample_precise_interval",
                    "chronology_conflict_note": "sample and site intervals disagree",
                }
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
        intake_recovery_payload = {
            "release_guard": {
                "passing": False,
                "implausibly_low_recovery_project_count": 1,
            }
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
            write_json(
                normalized_root / "sample_records.json",
                {
                    "samples": [
                        sample_row(
                            stable_token="ovis_aries:sample:blocked",
                            locality_token="ovis_aries:sample-site:blocked",
                            locality_text="Blocked Site",
                            project_accession="PRJTEST",
                            master_id="sample:blocked",
                        ),
                    ]
                },
            )
            write_json(normalized_root / "locality_summaries.json", {"localities": []})
            write_json(
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
            write_json(
                country_root / "sweden_animal_adna_test_summary.json",
                {"sample_rows": [{"sample_record_id": "ovis_aries:sample:blocked"}]},
            )
            point_payload = {
                "rows": [
                    {
                        "feature_id": "animal-atlas-feature:blocked",
                        "paper_url": "https://doi.org/10.1/test",
                        "sample_rows": [
                            sample_row(
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
            (docs_root / "public" / "nordic-atlas").mkdir(parents=True, exist_ok=True)
            (docs_root / "public" / "pollenomics-data" / "outputs").mkdir(
                parents=True, exist_ok=True
            )
            (docs_root / "index.md").write_text("", encoding="utf-8")
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
                data_root=data_root,
                report_root=report_root,
                docs_root=docs_root,
                point_payload=point_payload,
                review_payload=review_payload,
                sample_database_review_payload=sample_database_review_payload,
                intake_recovery_payload=intake_recovery_payload,
                temporal_comparison_payload={"published_feature_guard_findings": []},
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
