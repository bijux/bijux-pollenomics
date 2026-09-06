"""aDNA local reference-stash reconciliation tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bijux_pollenomics.adna.sources.inventory import (
    build_reference_stash_doi_integrity_audit,
    build_reference_stash_reconciliation,
    build_supplement_acquisition_checklist,
    build_supplement_file_family_audit,
    build_supplement_recovery_audit,
)
from bijux_pollenomics.adna.sources.library import (
    build_paper_registry,
    materialize_source_library,
)


class ReferenceStashTests(unittest.TestCase):
    def test_reference_stash_reconciliation_marks_local_staging_ahead_of_repo(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            stash_root = Path(tmp) / "stash"
            stash_root.mkdir(parents=True, exist_ok=True)
            (stash_root / "10.1016-j.cell.2019.03.049.pdf").write_bytes(b"%PDF-1.4\n")
            doi_dir = stash_root / "10.1016-j.cell.2019.03.049"
            doi_dir.mkdir(parents=True, exist_ok=True)
            (doi_dir / "table_s1.xlsx").write_bytes(b"sheet")

            with patch.dict(
                "os.environ",
                {"BIJUX_POLLENOMICS_REFERENCE_STASH_ROOT": str(stash_root)},
                clear=False,
            ):
                reconciliation = build_reference_stash_reconciliation(output_root)
                integrity = build_reference_stash_doi_integrity_audit(output_root)
                file_family_audit = build_supplement_file_family_audit(output_root)
                checklist = build_supplement_acquisition_checklist(output_root)
                recovery = build_supplement_recovery_audit(output_root)

        cell_row = next(
            row
            for row in reconciliation["rows"]
            if row["stash_slug"] == "10.1016-j.cell.2019.03.049"
        )
        checklist_row = next(
            row
            for row in checklist["rows"]
            if row["paper_doi"] == "10.1016/j.cell.2019.03.049"
        )
        family_row = next(
            row
            for row in file_family_audit["rows"]
            if row["paper_doi"] == "10.1016/j.cell.2019.03.049"
        )
        recovery_row = next(
            row
            for row in recovery["rows"]
            if row["paper_doi"] == "10.1016/j.cell.2019.03.049"
        )
        self.assertEqual(cell_row["alignment_status"], "local_reference_ahead_of_repo")
        self.assertTrue(integrity["all_stash_dois_tracked"])
        self.assertEqual(integrity["reference_stash_doi_count"], 1)
        self.assertEqual(
            checklist_row["acquisition_check_status"],
            "local_reference_ready_for_ingestion",
        )
        self.assertIn("xlsx_table", family_row["expected_supplementary_file_families"])
        self.assertEqual(
            recovery_row["recovery_status"],
            "local_reference_staged_needs_repo_ingestion",
        )

    def test_materialized_curated_stash_supplements_become_extractable_targets(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            stash_root = Path(tmp) / "stash"
            stash_root.mkdir(parents=True, exist_ok=True)
            (stash_root / "10.1111-1755-0998.12551.pdf").write_bytes(b"%PDF-1.4\n")
            doi_dir = stash_root / "10.1111-1755-0998.12551"
            doi_dir.mkdir(parents=True, exist_ok=True)
            (doi_dir / "men12551-sup-0001-supinfo.docx").write_bytes(b"docx")

            with patch.dict(
                "os.environ",
                {"BIJUX_POLLENOMICS_REFERENCE_STASH_ROOT": str(stash_root)},
                clear=False,
            ):
                materialize_source_library(output_root)
                paper_registry = build_paper_registry(output_root)
                recovery = build_supplement_recovery_audit(output_root)

        paper_row = next(
            row for row in paper_registry if row.paper_doi == "10.1111/1755-0998.12551"
        )
        recovery_row = next(
            row
            for row in recovery["rows"]
            if row["paper_doi"] == "10.1111/1755-0998.12551"
        )
        self.assertEqual(paper_row.supplementary_count, 1)
        self.assertEqual(paper_row.sample_extractability, "supplement_extractable")
        self.assertTrue(
            any(
                path.endswith("men12551-sup-0001-supinfo.docx")
                for path in paper_row.expected_supplementary_artifacts
            )
        )
        self.assertEqual(recovery_row["recovery_status"], "archived_and_parseable")
