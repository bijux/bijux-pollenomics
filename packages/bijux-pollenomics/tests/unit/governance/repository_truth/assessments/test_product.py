from __future__ import annotations

from bijux_pollenomics.governance import (
    build_repository_brutal_honesty_review,
    build_repository_credibility_dashboard,
    build_repository_extension_review,
    build_repository_final_release_refusal,
    build_repository_output_sustainability_review,
    build_repository_product_model,
    render_repository_brutal_honesty_review_markdown,
    render_repository_credibility_dashboard_markdown,
    render_repository_extension_review_markdown,
    render_repository_final_release_refusal_markdown,
    render_repository_output_sustainability_review_markdown,
    render_repository_product_model_markdown,
)
from .support import RepositoryTruthTestCase


class RepositoryProductPostureTests(RepositoryTruthTestCase):
    def test_product_model_credibility_and_release_refusal_keep_scope_and_posture_explicit(
        self,
    ) -> None:
        product_payload = build_repository_product_model(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        credibility_payload = build_repository_credibility_dashboard(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        extension_payload = build_repository_extension_review(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        sustainability_payload = build_repository_output_sustainability_review(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        brutal_payload = build_repository_brutal_honesty_review(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        refusal_payload = build_repository_final_release_refusal(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )

        self.assertEqual(
            product_payload["schema_version"], "repository-product-model.v1"
        )
        self.assertEqual(
            product_payload["governing_model"],
            "world_parent_with_filtered_regional_and_country_derivatives",
        )
        self.assertEqual(
            credibility_payload["schema_version"],
            "repository-credibility-dashboard.v1",
        )
        self.assertEqual(
            credibility_payload["overall_posture"],
            "credible_but_still_recovery_bound",
        )
        extraction_row = next(
            row
            for row in credibility_payload["rows"]
            if row["dimension_key"] == "extraction_completeness"
        )
        self.assertEqual(extraction_row["score"], 2)
        self.assertEqual(
            extension_payload["schema_version"], "repository-extension-review.v1"
        )
        self.assertEqual(
            sustainability_payload["schema_version"],
            "repository-output-sustainability-review.v1",
        )
        self.assertEqual(
            brutal_payload["schema_version"], "repository-brutal-honesty-review.v1"
        )
        self.assertEqual(
            refusal_payload["schema_version"], "repository-final-release-refusal.v1"
        )
        self.assertFalse(refusal_payload["final_release_language_allowed"])
        self.assertIn("data_recovery", refusal_payload["blocking_dimensions"])
        self.assertIn("sead_treatment", refusal_payload["blocking_dimensions"])
        self.assertIn(
            "# Repository product model",
            render_repository_product_model_markdown(product_payload),
        )
        self.assertIn(
            "# Repository credibility dashboard",
            render_repository_credibility_dashboard_markdown(credibility_payload),
        )
        self.assertIn(
            "# Repository extension review",
            render_repository_extension_review_markdown(extension_payload),
        )
        self.assertIn(
            "# Repository output sustainability review",
            render_repository_output_sustainability_review_markdown(
                sustainability_payload
            ),
        )
        self.assertIn(
            "# Repository brutal honesty review",
            render_repository_brutal_honesty_review_markdown(brutal_payload),
        )
        self.assertIn(
            "# Repository final release refusal",
            render_repository_final_release_refusal_markdown(refusal_payload),
        )
