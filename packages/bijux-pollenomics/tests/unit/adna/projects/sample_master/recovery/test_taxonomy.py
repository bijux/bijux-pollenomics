"""Tests for source-native taxonomy preservation and reconciliation."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil
import tempfile

import pytest

from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)
from bijux_pollenomics.adna.projects.sample_master.identity import (
    _merge_sample_row_group,
)
from bijux_pollenomics.adna.projects.registry.sites import (
    build_project_sample_site_rows,
)
from bijux_pollenomics.adna.projects.registry.samples import (
    build_species_curated_sample_rows,
)

from .support import SampleMasterRecoveryTestCase

pytestmark = pytest.mark.generated_artifacts


class TaxonomyTests(SampleMasterRecoveryTestCase):
    def test_obishir_samples_keep_alias_site_and_goat_identity(self) -> None:
        rows = build_project_sample_master_rows(self.data_root, "PRJEB41594")
        sites = build_project_sample_site_rows(self.data_root, "PRJEB41594")

        self.assertEqual(
            {
                row.archive_native_sample_id: row.paper_native_sample_label
                for row in rows
            },
            {
                "SAMEA8022720": "OB20-01",
                "SAMEA8022721": "OB20-06",
                "SAMEA8022722": "OB21-04",
                "SAMEA8022723": "OB21-06",
                "SAMEA8022724": "OB20-04",
            },
        )
        self.assertEqual(
            {
                row.species_latin_name
                for row in rows
                if row.archive_native_sample_id == "SAMEA8022722"
            },
            {"Capra hircus"},
        )
        self.assertEqual(
            {row.preferred_sample_label: row.chronology_text for row in rows},
            {
                "OB20-01": "",
                "OB20-06": "5991-5771 cal BCE",
                "OB21-04": "1045-835 cal BCE",
                "OB21-06": "",
                "OB20-04": "3003-2701 cal BCE",
            },
        )
        self.assertTrue(
            all(not row.latitude_text and not row.longitude_text for row in rows)
        )
        self.assertTrue(
            all("Reporting Summary p. 3" in row.sample_lineage_locator for row in rows)
        )
        self.assertTrue(
            all(
                row.locality_text == "Obishir V"
                and row.country_name == "Kyrgyzstan"
                and row.locality_resolution_status == "direct_sample_site"
                for row in sites
            )
        )
        goat = next(
            row
            for row in build_species_curated_sample_rows(
                "Ovis aries", output_root=self.data_root
            )
            if row.archive_native_sample_id == "SAMEA8022722"
        )
        self.assertEqual(goat.species_latin_name, "Capra hircus")
        self.assertEqual(goat.inclusion_status, "sample_context_blocked")
        for accession in ("SAMEA8022720", "SAMEA8022722"):
            self.assert_source_receipt_closes(
                self.data_root
                / "adna/governance/source_library/projects/PRJEB41594/ena_samples"
                / f"{accession}.xml",
                "PRJEB41594",
            )

    def test_obishir_alias_change_is_refused(self) -> None:
        from bijux_pollenomics.adna.projects.sample_master.tables.obishir_sheep import (
            build_obishir_sample_rows,
        )
        from bijux_pollenomics.adna.projects.sample_master.archive import (
            _project_scope_archive_sample_rows,
            _project_by_accession,
        )
        from bijux_pollenomics.adna.species.definitions import (
            resolve_species_definition,
        )
        from bijux_pollenomics.adna.sources.library.acquisition import (
            _xml_capture_refusal_reason,
        )

        tmp_path = Path(
            tempfile.mkdtemp(
                prefix="obishir-alias-", dir=self.data_root.parent / "artifacts"
            )
        )
        relative_files = [
            "adna/governance/source_library/papers/10.1038-s41562-021-01083-y/supplementary/41562_2021_1083_MOESM2_ESM.pdf",
            "adna/governance/source_library/papers/10.1038-s41562-021-01083-y/supplementary/41562_2021_1083_MOESM1_ESM.pdf",
            "adna/governance/source_library/projects/PRJEB41594/archive_metadata.html.gz",
        ]
        for accession in range(8022720, 8022725):
            prefix = f"adna/governance/source_library/projects/PRJEB41594/ena_samples/SAMEA{accession}.xml"
            relative_files.extend((prefix, prefix + ".metadata.json"))
        for relative in relative_files:
            destination = tmp_path / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.data_root / relative, destination)

        project = _project_by_accession("PRJEB41594")
        archive_rows = _project_scope_archive_sample_rows(
            tmp_path, resolve_species_definition("Ovis aries"), project
        )
        date_file = tmp_path / (
            "adna/governance/source_library/papers/10.1038-s41562-021-01083-y/"
            "supplementary/41562_2021_1083_MOESM1_ESM.pdf"
        )
        date_bytes = date_file.read_bytes()
        date_file.write_bytes(date_bytes + b"changed")
        with pytest.raises(ValueError, match="radiocarbon supplement changed"):
            build_obishir_sample_rows(tmp_path, archive_rows)
        date_file.write_bytes(date_bytes)
        alias_file = tmp_path / (
            "adna/governance/source_library/projects/PRJEB41594/ena_samples/"
            "SAMEA8022720.xml"
        )
        alias_file.write_bytes(
            alias_file.read_bytes().replace(b'alias="OB20-01"', b'alias="OB20-99"')
        )
        self.assertEqual(
            _xml_capture_refusal_reason(
                logical_path=alias_file,
                payload=alias_file.read_bytes(),
                content_type="application/xml",
            ),
            "ena_sample_source_semantic_mismatch",
        )
        with pytest.raises(ValueError, match="ENA receipt changed"):
            build_obishir_sample_rows(tmp_path, archive_rows)
        shutil.rmtree(tmp_path)

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
