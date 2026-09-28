from __future__ import annotations

import json
from unittest.mock import patch

from bijux_pollenomics.governance import (
    build_repository_atlas_input_audit,
    build_repository_cross_domain_evidence_matrix,
    build_repository_scientific_progress_audit,
    build_repository_source_acquisition_queue,
    build_repository_source_ecosystem_review,
    build_repository_source_explainer_audit,
    build_repository_source_family_matrix,
    build_repository_truth_posture,
    render_repository_atlas_input_audit_markdown,
    render_repository_cross_domain_evidence_matrix_markdown,
    render_repository_scientific_progress_audit_markdown,
    render_repository_source_acquisition_queue_markdown,
    render_repository_source_ecosystem_review_markdown,
    render_repository_source_explainer_audit_markdown,
    render_repository_source_family_matrix_markdown,
)
from bijux_pollenomics.governance.repository_truth.metrics.filesystem import (
    _count_geojson_features,
)

from .support import RepositoryTruthTestCase


class RepositorySourceEvidenceTests(RepositoryTruthTestCase):
    def test_published_sead_population_agrees_across_truth_surfaces(self) -> None:
        def report(stem):  # type: ignore[no-untyped-def]
            return json.loads((self.report_root / f"{stem}.json").read_text())

        matrix = report("repository_source_family_matrix")
        atlas = report("repository_atlas_input_audit")
        cross_domain = report("repository_cross_domain_evidence_matrix")
        posture = report("repository_truth_posture")
        claim = report("repository_claim_audit")
        source_row = next(row for row in matrix["rows"] if row["source_key"] == "sead")
        atlas_row = next(row for row in atlas["rows"] if row["input_key"] == "sead")
        archaeology = next(
            row
            for row in cross_domain["rows"]
            if row["domain_key"] == "archaeology_context"
        )
        published = _count_geojson_features(
            self.report_root
            / "regions"
            / "nordic"
            / "nordic_environmental_sites.geojson"
        )
        assert published == 2069
        assert source_row["visible_count"] == published
        assert atlas_row["metrics"]["site_count"] == published
        assert archaeology["tracked_metrics"]["sead_site_count"] == published
        for truth in (posture, claim):
            assert truth["counts"]["tracked_sead_site_count"] == published
            assert truth["counts"]["sead_source_bbox_site_count"] == 2195

    def test_published_sead_site_denominator_must_match_normalized_layer(self) -> None:
        published = (
            self.report_root
            / "regions"
            / "nordic"
            / "nordic_environmental_sites.geojson"
        )

        def changed_count(path):  # type: ignore[no-untyped-def]
            count = _count_geojson_features(path)
            return count + 1 if path == published else count

        with patch(
            "bijux_pollenomics.governance.repository_truth.metrics.counts._count_geojson_features",
            side_effect=changed_count,
        ):
            with self.assertRaisesRegex(ValueError, "Published SEAD site count"):
                build_repository_source_family_matrix(
                    data_root=self.data_root,
                    docs_root=self.docs_root,
                    report_root=self.report_root,
                )

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
        sead_row = next(
            row for row in matrix_payload["rows"] if row["source_key"] == "sead"
        )
        self.assertEqual(sead_row["visible_count"], 2069)
        self.assertEqual(
            raa_row["acquisition_posture"], "refused_not_publication_ready"
        )
        self.assertIn("missing_raw_inventory", raa_row["main_gap"])
        self.assertIn("Animal aDNA papers and supplements", matrix_markdown)
        self.assertIn("animal_adna", queue_markdown)
        self.assertNotIn("sead_temporal_reference_capture", queue_markdown)

    def test_archived_supplements_do_not_remain_an_acquisition_gap(self) -> None:
        matrix = build_repository_source_family_matrix(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        queue = build_repository_source_acquisition_queue(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        posture = build_repository_truth_posture(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        counts = posture["counts"]
        self.assertEqual(counts["tracked_paper_count"], 18)
        self.assertEqual(counts["papers_with_archived_supplements"], 18)
        animal_row = next(
            row for row in matrix["rows"] if row["source_key"] == "animal_adna"
        )
        self.assertEqual(
            animal_row["acquisition_posture"], "all_tracked_supplements_archived"
        )
        self.assertNotIn("supplement ingestion", animal_row["main_gap"])
        self.assertNotIn("supplement_capture_recovery", posture["incomplete_programs"])
        self.assertEqual(queue["rows"][0]["queue_key"], "animal_adna_sample_extraction")
        self.assertTrue(
            all("archive missing" not in row for row in posture["recovery_priorities"])
        )

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
        sead_input = next(
            row for row in atlas_payload["rows"] if row["input_key"] == "sead"
        )
        self.assertEqual(sead_input["metrics"]["site_count"], 2069)
        self.assertEqual(sead_input["metrics"]["source_bounding_box_site_count"], 2195)
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
