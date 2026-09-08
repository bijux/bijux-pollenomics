"""Tests for sample-master completeness and ambiguity ledgers."""

from __future__ import annotations

from collections import Counter

import pytest

from bijux_pollenomics.adna.projects.sample_master import (
    build_cross_project_sample_master_completeness,
    build_project_sample_master,
    build_sample_identity_ambiguity_ledger,
)

from .support import SampleMasterRecoveryTestCase

pytestmark = pytest.mark.generated_artifacts


class CompletenessTests(SampleMasterRecoveryTestCase):
    def test_project_sample_master_completeness_tracks_expected_and_recovered_counts(
        self,
    ) -> None:
        camel = build_project_sample_master(self.data_root, "KU605068-KU605080")

        self.assertEqual(camel.expected_sample_count, 13)
        self.assertEqual(camel.recovered_sample_count, 13)
        self.assertEqual(camel.final_sample_count, 13)
        self.assertEqual(camel.unresolved_sample_count, 0)
        self.assertTrue(camel.expected_sample_count_provenance)
        self.assertTrue(camel.expected_sample_count_artifact_path)

    def test_cross_project_completeness_and_ambiguity_ledgers_are_reader_visible(
        self,
    ) -> None:
        completeness_rows = build_cross_project_sample_master_completeness(
            self.data_root
        )
        ambiguity_rows = build_sample_identity_ambiguity_ledger(self.data_root)

        self.assertEqual(len(completeness_rows), 40)
        self.assertTrue(
            any(
                row["project_accession"] == "KU605068-KU605080"
                and row["expected_sample_count"] == 13
                and row["recovered_sample_count"] == 13
                for row in completeness_rows
            )
        )
        horse_counts = Counter(
            row["recovered_sample_count"]
            for row in completeness_rows
            if row["project_accession"]
            in {"PRJEB19970", "PRJEB22390", "PRJEB31613", "PRJEB44430"}
        )
        self.assertEqual(horse_counts, Counter({15: 1, 42: 1, 245: 1, 248: 1}))
        self.assertEqual(
            {
                (row["project_accession"], row["repo_stable_sample_id"])
                for row in ambiguity_rows
            },
            {
                ("PRJEB81815", "prjeb81815:samea120246597"),
                ("PRJEB81815", "prjeb81815:samea120246598"),
                ("PRJEB81815", "prjeb81815:samea120246599"),
            },
        )
        self.assertTrue(
            all(
                row["sample_ambiguity_note"]
                and row["sample_lineage_path"]
                and row["sample_lineage_locator"]
                for row in ambiguity_rows
            )
        )
