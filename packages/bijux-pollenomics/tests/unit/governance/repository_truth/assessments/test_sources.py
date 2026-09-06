from __future__ import annotations

from bijux_pollenomics.governance import (
    build_repository_atlas_input_audit,
    build_repository_cross_domain_evidence_matrix,
    build_repository_scientific_progress_audit,
    build_repository_source_acquisition_queue,
    build_repository_source_ecosystem_review,
    build_repository_source_explainer_audit,
    build_repository_source_family_matrix,
    render_repository_atlas_input_audit_markdown,
    render_repository_cross_domain_evidence_matrix_markdown,
    render_repository_scientific_progress_audit_markdown,
    render_repository_source_acquisition_queue_markdown,
    render_repository_source_ecosystem_review_markdown,
    render_repository_source_explainer_audit_markdown,
    render_repository_source_family_matrix_markdown,
)
from .support import RepositoryTruthTestCase


class RepositorySourceEvidenceTests(RepositoryTruthTestCase):
    def test_source_family_matrix_and_acquisition_queue_keep_cross_domain_pressure_visible(
        self,
    ) -> None:
        matrix_payload = build_repository_source_family_matrix(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        queue_payload = build_repository_source_acquisition_queue(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        matrix_markdown = render_repository_source_family_matrix_markdown(
            matrix_payload
        )
        queue_markdown = render_repository_source_acquisition_queue_markdown(
            queue_payload
        )

        self.assertEqual(
            matrix_payload["schema_version"], "repository-source-family-matrix.v1"
        )
        self.assertEqual(
            queue_payload["schema_version"], "repository-source-acquisition-queue.v1"
        )
        self.assertEqual(matrix_payload["row_count"], 8)
        self.assertGreaterEqual(queue_payload["row_count"], 1)
        raa_row = next(
            row for row in matrix_payload["rows"] if row["source_key"] == "raa"
        )
        self.assertEqual(raa_row["visible_count"], 0)
        self.assertEqual(
            raa_row["acquisition_posture"], "refused_not_publication_ready"
        )
        self.assertIn("missing_raw_inventory", raa_row["main_gap"])
        self.assertIn("Animal aDNA papers and supplements", matrix_markdown)
        self.assertIn("animal_adna", queue_markdown)
        self.assertNotIn("sead_temporal_reference_capture", queue_markdown)

    def test_source_explainer_atlas_input_and_cross_domain_packets_keep_pollen_first(
        self,
    ) -> None:
        explainer_payload = build_repository_source_explainer_audit(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        atlas_payload = build_repository_atlas_input_audit(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        matrix_payload = build_repository_cross_domain_evidence_matrix(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        explainer_markdown = render_repository_source_explainer_audit_markdown(
            explainer_payload
        )
        atlas_markdown = render_repository_atlas_input_audit_markdown(atlas_payload)
        matrix_markdown = render_repository_cross_domain_evidence_matrix_markdown(
            matrix_payload
        )

        self.assertEqual(
            explainer_payload["schema_version"],
            "repository-source-explainer-audit.v1",
        )
        self.assertEqual(
            atlas_payload["schema_version"], "repository-atlas-input-audit.v2"
        )
        self.assertEqual(
            matrix_payload["schema_version"],
            "repository-cross-domain-evidence-matrix.v2",
        )
        self.assertEqual(explainer_payload["status_counts"]["present_useful_form"], 16)
        self.assertEqual(
            explainer_payload["status_counts"]["restoration_plan_required"], 0
        )
        self.assertEqual(atlas_payload["row_count"], 6)
        pollen_row = next(
            row
            for row in matrix_payload["rows"]
            if row["domain_key"] == "pollen_context"
        )
        self.assertEqual(pollen_row["tracked_metrics"]["landclim_site_count"], 490)
        self.assertEqual(pollen_row["tracked_metrics"]["neotoma_site_count"], 200)
        raa_input = next(
            row for row in atlas_payload["rows"] if row["input_key"] == "raa"
        )
        self.assertEqual(
            raa_input["metrics"]["publication_status"],
            "refused_not_publication_ready",
        )
        self.assertIsNone(raa_input["metrics"]["published_site_count"])
        self.assertNotIn(
            "docs/report/regions/nordic/sweden_archaeology_density.geojson",
            raa_input["published_paths"],
        )
        archaeology_row = next(
            row
            for row in matrix_payload["rows"]
            if row["domain_key"] == "archaeology_context"
        )
        self.assertEqual(archaeology_row["coverage_posture"], "raa_density_refused")
        self.assertIsNone(
            archaeology_row["tracked_metrics"]["raa_published_site_count"]
        )
        self.assertIn("Repository source explainer audit", explainer_markdown)
        self.assertIn("Repository atlas input audit", atlas_markdown)
        self.assertIn("Repository cross-domain evidence matrix", matrix_markdown)

    def test_source_ecosystem_review_keeps_sead_and_palaeopen_roles_distinct(
        self,
    ) -> None:
        payload = build_repository_source_ecosystem_review(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        markdown = render_repository_source_ecosystem_review_markdown(payload)

        self.assertEqual(
            payload["schema_version"], "repository-source-ecosystem-review.v1"
        )
        self.assertEqual(payload["row_count"], 2)
        sead_row = next(
            row for row in payload["rows"] if row["ecosystem_key"] == "sead"
        )
        palaeopen_row = next(
            row for row in payload["rows"] if row["ecosystem_key"] == "palaeopen"
        )
        self.assertEqual(sead_row["ecosystem_role"], "direct_source_infrastructure")
        self.assertEqual(palaeopen_row["ecosystem_role"], "open_data_network")
        self.assertIn(
            "temporal resolution and reference visibility remain uneven",
            " ".join(sead_row["limits"]),
        )
        self.assertIn("Repository source ecosystem review", markdown)
        self.assertIn("PalaeOpen", markdown)

    def test_scientific_progress_audit_prefers_evidence_depth_over_file_count(
        self,
    ) -> None:
        payload = build_repository_scientific_progress_audit(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        markdown = render_repository_scientific_progress_audit_markdown(payload)

        self.assertEqual(
            payload["schema_version"], "repository-scientific-progress-audit.v1"
        )
        self.assertEqual(payload["overall_progress_posture"], "data_recovery_required")
        self.assertIn("checked-in JSON file count", payload["anti_measures"])
        self.assertTrue(
            any(
                "all 18 tracked papers now ship archived supplementary material" in row
                for row in payload["findings"]
            )
        )
        self.assertIn("Do Not Use These As Progress", markdown)
