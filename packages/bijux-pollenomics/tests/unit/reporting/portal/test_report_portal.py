from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.reporting.presentation import (
    publish_report_portal,
    report_portal,
)


class ReportPortalUnitTests(unittest.TestCase):
    def test_report_portal_facade_exposes_only_the_publication_entry_point(
        self,
    ) -> None:
        self.assertEqual(report_portal.__all__, ["publish_report_portal"])
        self.assertIs(report_portal.publish_report_portal, publish_report_portal)

    def test_publish_report_portal_classifies_report_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_root = Path(tmp) / "report"
            (report_root / "world").mkdir(parents=True, exist_ok=True)
            (report_root / "countries" / "sweden").mkdir(parents=True, exist_ok=True)

            (report_root / "world" / "scope_example.md").write_text(
                "# World Evidence Surface\n\nThis page explains the world parent surface in prose before listing artifacts.\n\n## Output Files\n\n- one link\n",
                encoding="utf-8",
            )
            (report_root / "world" / "world_map.html").write_text(
                "<html></html>",
                encoding="utf-8",
            )
            (report_root / "world" / "scope_point_traceability.md").write_text(
                "# World point traceability\n\nThis page explains why visible points can be inspected and checked.\n",
                encoding="utf-8",
            )
            (report_root / "countries" / "sweden" / "scope_example.md").write_text(
                "# Sweden Bundle\n\nThis page explains the country surface before the file list.\n",
                encoding="utf-8",
            )
            (report_root / "animal_scope_example_review.md").write_text(
                "# Animal point evidence review\n\nThis page explains how animal point support is reviewed.\n",
                encoding="utf-8",
            )
            (report_root / "scope_example_honesty.md").write_text(
                "# Animal output honesty\n\nThis page explains blocked and thin publication rows.\n",
                encoding="utf-8",
            )
            (report_root / "repository_scope_example.md").write_text(
                "# Repository truth posture\n\nThis page explains the current repository claim boundary.\n",
                encoding="utf-8",
            )
            (report_root / "published_reports_summary.json").write_text(
                json.dumps(
                    {"schema_version": "published-reports-summary.v1"}, indent=2
                ),
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

            rows_by_path = {row["repository_path"]: row for row in registry["rows"]}
            registry_page = (report_root / "report_surface_registry.md").read_text(
                encoding="utf-8"
            )
            self.assertIn(
                "[machine-readable registry](report_surface_registry.json)",
                registry_page,
            )
            self.assertIn("[Map surfaces](maps/index.md)", registry_page)
            self.assertNotIn("docs/report/world/world_map.html", registry_page)
            quality_page = (
                report_root / "report_narrative_quality_review.md"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "[machine-readable review](report_narrative_quality_review.json)",
                quality_page,
            )
            self.assertNotIn("docs/report/world/scope_example.md", quality_page)
            self.assertEqual(
                rows_by_path["docs/report/world/scope_example.md"]["family"], "scopes"
            )
            self.assertEqual(
                rows_by_path["docs/report/world/world_map.html"]["audience"],
                "public_reading_surface",
            )
            self.assertEqual(
                rows_by_path["docs/report/scope_example_honesty.md"]["family"],
                "caveats",
            )
            self.assertEqual(
                rows_by_path["docs/report/repository_scope_example.md"]["audience"],
                "maintainer_diagnostic",
            )
            self.assertIn("reader_ready", quality["quality_posture_counts"])

    def test_inventory_tracks_paths_and_excludes_its_own_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "study" / "README.md"
            source.parent.mkdir()
            source.write_text(
                "# Study\n\nThis source explains a scoped result and its evidence boundary.\n"
            )
            (root / "machine.json").write_text('{"source": "domain manifest"}')
            publish_report_portal(root)
            registry = json.loads((root / "report_surface_registry.json").read_text())
            excluded = set(registry["excluded_metadata_paths"])
            indexed = {r["repository_path"] for r in registry["rows"]}
            all_paths = {
                f"docs/report/{p.relative_to(root).as_posix()}"
                for p in root.rglob("*")
                if p.is_file()
            }
            self.assertEqual(indexed | excluded, all_paths)
            self.assertFalse(indexed & excluded)
            self.assertEqual(len(excluded), 4)
            for row in registry["rows"]:
                self.assertNotIn("content_sha256", row)
            before = {
                p.relative_to(root): p.read_bytes()
                for p in root.rglob("*")
                if p.is_file()
            }
            publish_report_portal(root)
            self.assertEqual(
                before,
                {
                    p.relative_to(root): p.read_bytes()
                    for p in root.rglob("*")
                    if p.is_file()
                },
            )
            source.write_text(
                "# Revised study\r\n\r\nThe interpretation now has a changed source boundary.\r\n"
            )
            publish_report_portal(root)
            after = json.loads((root / "report_surface_registry.json").read_text())
            row = next(
                r
                for r in after["rows"]
                if r["repository_path"] == "docs/report/study/README.md"
            )
            self.assertEqual(after, registry)
            self.assertNotIn("content_sha256", row)
            quality = json.loads(
                (root / "report_narrative_quality_review.json").read_text()
            )
            review = next(
                r
                for r in quality["rows"]
                if r["repository_path"] == row["repository_path"]
            )
            self.assertNotIn("content_sha256", review)
            self.assertEqual(review["heading_count"], 1)
            self.assertEqual(
                quality["review_scope"],
                "automated layout signals; no human or scientific review",
            )


if __name__ == "__main__":
    unittest.main()
