"""Tests for source-native taxonomy preservation and reconciliation."""

from __future__ import annotations

from dataclasses import replace

import pytest
from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)
from bijux_pollenomics.adna.projects.sample_master.identity import (
    _merge_sample_row_group,
)

from .support import SampleMasterRecoveryTestCase

pytestmark = pytest.mark.generated_artifacts


class TaxonomyTests(SampleMasterRecoveryTestCase):
    def test_archive_taxonomy_is_preserved_without_project_species_coercion(
        self,
    ) -> None:
        cattle_rows = build_project_sample_master_rows(self.data_root, "PRJEB31621")
        sheep_rows = build_project_sample_master_rows(self.data_root, "PRJEB41594")

        aurochs = next(
            row
            for row in cattle_rows
            if row.source_native_scientific_name == "Bos primigenius"
        )
        self.assertEqual(aurochs.species_latin_name, "Bos taurus")
        self.assertEqual(aurochs.source_native_tax_id, "9909")
        self.assertEqual(aurochs.taxon_alignment_status, "project_species_mismatch")
        self.assertIn("Bos primigenius", aurochs.sample_lineage_excerpt)

        goat = next(
            row
            for row in sheep_rows
            if row.source_native_scientific_name == "Capra hircus"
        )
        self.assertEqual(goat.source_native_tax_id, "9925")
        self.assertEqual(goat.taxon_alignment_status, "project_species_mismatch")

    def test_cat_supplement_preserves_sample_sites_dates_and_native_taxa(self) -> None:
        rows = build_project_sample_master_rows(self.data_root, "PRJNA1178732")

        self.assertEqual(len(rows), 22)
        domestic = next(row for row in rows if row.preferred_sample_label == "FS1")
        leopard = next(row for row in rows if row.preferred_sample_label == "FS8")
        self.assertEqual(domestic.locality_text, "Xitucheng City")
        self.assertEqual(domestic.political_entity, "China")
        self.assertEqual(domestic.chronology_text, "1115 - 1234 CE")
        self.assertEqual(domestic.source_native_scientific_name, "Felis catus")
        self.assertEqual(domestic.taxon_alignment_status, "project_species_match")
        self.assertEqual(
            leopard.source_native_scientific_name, "Prionailurus bengalensis"
        )
        self.assertEqual(leopard.taxon_alignment_status, "project_species_mismatch")

    def test_ncbi_sra_capture_preserves_experiment_accessions_and_labels(self) -> None:
        rows = build_project_sample_master_rows(self.data_root, "SRP073444")

        self.assertEqual(len(rows), 20)
        palm = next(
            row for row in rows if row.archive_native_experiment_id == "SRX1711558"
        )
        self.assertEqual(palm.archive_native_sample_id, "")
        self.assertEqual(palm.preferred_sample_label, "Palm143_II")
        self.assertEqual(palm.sample_lineage_locator, "experiment_accession:SRX1711558")
        self.assertEqual(
            palm.source_native_identity_kind, "sequencing_experiment_accession"
        )
        self.assertEqual(palm.sample_evidence_status, "experiment_level_only")
        self.assertEqual(palm.sample_identity_resolution, "provisional")
        self.assertIn("not a biological sample", palm.sample_ambiguity_note)
        self.assertEqual(palm.taxon_alignment_status, "not_reported")

    def test_merged_taxon_alignment_is_order_independent(self) -> None:
        base = build_project_sample_master_rows(self.data_root, "KU605068-KU605080")[0]
        unreported = replace(
            base,
            source_native_scientific_name="",
            taxon_alignment_status="not_reported",
        )
        mismatch = replace(
            base,
            source_native_scientific_name="Bos taurus",
            taxon_alignment_status="project_species_mismatch",
        )

        forward = _merge_sample_row_group([unreported, mismatch])
        reverse = _merge_sample_row_group([mismatch, unreported])

        self.assertEqual(forward.taxon_alignment_status, "project_species_mismatch")
        self.assertEqual(reverse.taxon_alignment_status, "project_species_mismatch")
        self.assertEqual(forward.source_native_scientific_name, "Bos taurus")
        self.assertEqual(reverse.source_native_scientific_name, "Bos taurus")
