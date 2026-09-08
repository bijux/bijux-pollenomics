from __future__ import annotations

from pathlib import Path
import tempfile

from bijux_pollenomics.governance import (
    build_repository_claim_audit,
    build_repository_governance_artifact_review,
    render_repository_claim_audit_markdown,
    render_repository_governance_artifact_review_markdown,
)

from .support import RepositoryTruthTestCase


class RepositoryGovernanceTests(RepositoryTruthTestCase):
    def test_governance_artifact_review_marks_accounting_surfaces_for_retirement(
        self,
    ) -> None:
        payload = build_repository_governance_artifact_review(
            data_root=self.data_root,
            report_root=self.report_root,
        )
        markdown = render_repository_governance_artifact_review_markdown(payload)

        self.assertEqual(
            payload["schema_version"], "repository-governance-artifact-review.v1"
        )
        self.assertEqual(payload["summary"]["retire"], 1)
        retired_row = next(row for row in payload["rows"] if row["action"] == "retire")
        self.assertEqual(
            retired_row["artifact_path"],
            "docs/report/animal_output_audit.json",
        )
        self.assertIn("publication_accounting", markdown)

    def test_governance_artifact_review_reads_isolated_report_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root = root / "repository" / "data"
            report_root = root / "evidence" / "reference-build"
            data_root.mkdir(parents=True)
            report_root.mkdir(parents=True)
            (report_root / "animal_output_audit.json").write_text(
                "{}", encoding="utf-8"
            )

            payload = build_repository_governance_artifact_review(
                data_root=data_root,
                report_root=report_root,
            )

        self.assertEqual(payload["summary"], {"keep": 0, "reframe": 0, "retire": 1})
        self.assertEqual(
            [row["artifact_path"] for row in payload["rows"]],
            ["docs/report/animal_output_audit.json"],
        )

    def test_claim_audit_passes_once_animal_review_freezes_broad_readiness(
        self,
    ) -> None:
        payload = build_repository_claim_audit(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        markdown = render_repository_claim_audit_markdown(payload)

        self.assertEqual(payload["schema_version"], "repository-claim-audit.v2")
        self.assertTrue(payload["overall_ok"])
        self.assertTrue(all(row["passed"] for row in payload["checks"]))
        docs_breadth_row = next(
            row
            for row in payload["checks"]
            if row["check_id"]
            == "docs_scope_validation_keeps_repository_story_wide_enough"
        )
        self.assertTrue(docs_breadth_row["passed"])
        self.assertIn("# Repository claim audit", markdown)
