"""aDNA cross-project source audit tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bijux_pollenomics.adna.sources.library import (
    build_cross_project_source_audit,
    build_missing_source_blockers,
    build_source_intake_audit,
)


class SourceAuditTests(unittest.TestCase):
    def test_cross_project_source_audit_and_blockers_stay_reader_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            audit = build_cross_project_source_audit(output_root)
            blockers = build_missing_source_blockers(output_root)
            intake_audit = build_source_intake_audit(output_root)

        self.assertGreater(audit["paper_dependent_count"], 0)
        self.assertGreater(audit["blocked_count"], 0)
        self.assertGreater(
            intake_audit["blocker_counts"]["missing_paper_capture_count"], 0
        )
        self.assertGreater(
            intake_audit["blocker_counts"]["missing_sample_identifier_count"], 0
        )
        self.assertTrue(
            any(
                row["project_accession"] == "PRJEB22390"
                and "missing_local_paper_evidence" in row["blockers"]
                and "missing_paper_capture" in row["blocker_categories"]
                for row in blockers["rows"]
            )
        )
