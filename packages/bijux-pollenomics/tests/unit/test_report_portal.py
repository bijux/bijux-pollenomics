from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.reporting.presentation import publish_report_portal


class ReportPortalUnitTests(unittest.TestCase):
    def test_publish_report_portal_classifies_report_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_root = Path(tmp) / "report"
            (report_root / "world").mkdir(parents=True, exist_ok=True)
            (report_root / "countries" / "sweden").mkdir(parents=True, exist_ok=True)

            (report_root / "world" / "README.md").write_text(
                "# World Evidence Surface\n\nThis page explains the world parent surface in prose before listing artifacts.\n\n## Output Files\n\n- one link\n",
                encoding="utf-8",
            )
            (report_root / "world" / "world_map.html").write_text(
                "<html></html>",
                encoding="utf-8",
            )
            (report_root / "world" / "world_point_traceability.md").write_text(
                "# World point traceability\n\nThis page explains why visible points can be inspected and checked.\n",
                encoding="utf-8",
            )
            (report_root / "countries" / "sweden" / "README.md").write_text(
                "# Sweden Bundle\n\nThis page explains the country surface before the file list.\n",
                encoding="utf-8",
            )
            (report_root / "animal_point_evidence_review.md").write_text(
                "# Animal point evidence review\n\nThis page explains how animal point support is reviewed.\n",
                encoding="utf-8",
            )
            (report_root / "animal_output_honesty.md").write_text(
                "# Animal output honesty\n\nThis page explains blocked and thin publication rows.\n",
                encoding="utf-8",
            )
            (report_root / "repository_truth_posture.md").write_text(
                "# Repository truth posture\n\nThis page explains the current repository claim boundary.\n",
                encoding="utf-8",
            )
            (report_root / "published_reports_summary.json").write_text(
                json.dumps({"schema_version": "published-reports-summary.v1"}, indent=2),
                encoding="utf-8",
            )

            artifacts = publish_report_portal(report_root)

            self.assertEqual(artifacts["report_portal_index"], "index.md")
            self.assertTrue((report_root / "index.md").is_file())
            self.assertTrue((report_root / "maps" / "index.md").is_file())
            self.assertTrue((report_root / "scopes" / "index.md").is_file())
            self.assertTrue((report_root / "reviews" / "index.md").is_file())
            self.assertTrue((report_root / "caveats" / "index.md").is_file())
            self.assertTrue((report_root / "maintenance" / "index.md").is_file())

            registry = json.loads(
                (report_root / "report_surface_registry.json").read_text(
                    encoding="utf-8"
                )
            )
            quality = json.loads(
                (report_root / "report_narrative_quality_review.json").read_text(
                    encoding="utf-8"
                )
            )

            rows_by_path = {
                row["repository_path"]: row for row in registry["rows"]
            }
            self.assertEqual(
                rows_by_path["docs/report/world/README.md"]["family"], "scopes"
            )
            self.assertEqual(
                rows_by_path["docs/report/world/world_map.html"]["audience"],
                "public_reading_surface",
            )
            self.assertEqual(
                rows_by_path["docs/report/animal_output_honesty.md"]["family"],
                "caveats",
            )
            self.assertEqual(
                rows_by_path["docs/report/repository_truth_posture.md"]["audience"],
                "maintainer_diagnostic",
            )
            self.assertIn("reader_ready", quality["quality_posture_counts"])


if __name__ == "__main__":
    unittest.main()
