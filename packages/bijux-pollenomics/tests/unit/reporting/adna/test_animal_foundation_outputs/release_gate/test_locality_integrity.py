from __future__ import annotations

from pathlib import Path
import tempfile

import pytest

from bijux_pollenomics.reporting.adna.foundation_outputs.release import (
    build_animal_publication_release_gate,
)

from ..support import AnimalFoundationOutputsTestCase, sample_row, write_json

pytestmark = pytest.mark.generated_artifacts


class AnimalLocalityReleaseGateTests(AnimalFoundationOutputsTestCase):
    def test_release_gate_fails_when_project_locality_output_flattens_sample_sites(
        self,
    ) -> None:
        point_payload = {"rows": []}  # type: ignore[var-annotated]
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
            species_root = data_root / "adna" / "species" / "ovis_aries"
            normalized_root = species_root / "normalized"
            normalized_root.mkdir(parents=True, exist_ok=True)
            (species_root / "README.md").write_text(
                "# sheep\n\n- Curated sample rows: `2`\n",
                encoding="utf-8",
            )
            write_json(
                normalized_root / "sample_records.json",
                {
                    "samples": [
                        sample_row(
                            stable_token="ovis_aries:sample:one",
                            locality_token="ovis_aries:sample-site:one",
                            locality_text="Site One",
                            project_accession="PRJTEST",
                        ),
                        sample_row(
                            stable_token="ovis_aries:sample:two",
                            locality_token="ovis_aries:sample-site:two",
                            locality_text="Site Two",
                            project_accession="PRJTEST",
                        ),
                    ]
                },
            )
            write_json(
                normalized_root / "locality_summaries.json",
                {
                    "localities": [
                        {
                            "identity": {
                                "stable_token": "ovis_aries:project-locality:prjtest"
                            },
                            "project_accessions": ["PRJTEST"],
                            "sample_namespace": "ovis_aries:project_locality",
                        }
                    ]
                },
            )
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
                report_root=root / "report",
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
                == "project_locality_outputs_do_not_flatten_sample_site_disagreement"
                and not row["passed"]
                for row in gate_payload["checks"]
            )
        )

    def test_release_gate_fails_when_blocked_sample_site_rows_publish_as_exact_rows(
        self,
    ) -> None:
        point_payload = {"rows": []}  # type: ignore[var-annotated]
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
            write_json(
                normalized_root / "sample_records.json",
                {
                    "samples": [
                        sample_row(
                            stable_token="ovis_aries:sample:blocked",
                            locality_token="ovis_aries:sample-site:blocked",
                            locality_text="Blocked Site",
                            project_accession="PRJTEST",
                        ),
                    ]
                },
            )
            write_json(normalized_root / "locality_summaries.json", {"localities": []})
            write_json(
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
                report_root=root / "report",
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
                == "blocked_sample_site_rows_do_not_publish_as_exact_sites_or_atlas_points"
                and not row["passed"]
                for row in gate_payload["checks"]
            )
        )
