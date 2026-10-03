"""aDNA cross-project source audit tests."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.adna.sources.library import (
    build_cross_project_source_audit,
    build_missing_source_blockers,
    build_source_intake_audit,
)

from .payloads import count, mapping, rows, strings


class SourceAuditTests(unittest.TestCase):
    def test_cross_project_source_audit_and_blockers_stay_reader_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            audit = build_cross_project_source_audit(output_root)
            blockers = build_missing_source_blockers(output_root)
            intake_audit = build_source_intake_audit(output_root)

        self.assertGreater(count(audit["paper_dependent_count"]), 0)
        self.assertGreater(count(audit["blocked_count"]), 0)
        blocker_counts = mapping(intake_audit["blocker_counts"])
        self.assertGreater(count(blocker_counts["missing_paper_capture_count"]), 0)
        self.assertGreater(count(blocker_counts["missing_sample_identifier_count"]), 0)
        self.assertTrue(
            any(
                row["project_accession"] == "PRJEB22390"
                and "missing_local_paper_evidence" in strings(row["blockers"])
                and "missing_paper_capture" in strings(row["blocker_categories"])
                for row in rows(blockers["rows"])
            )
        )
