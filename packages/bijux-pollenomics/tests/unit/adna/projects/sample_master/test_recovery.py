from __future__ import annotations

from collections import Counter
from dataclasses import replace
import gzip
import hashlib
import json
from pathlib import Path

from tests.support.repository import REPOSITORY_ROOT
import tempfile
import unittest

import pytest

from bijux_pollenomics.adna.projects.sample_master.archive import (
    _build_archive_sample_accession_lookup,
    _project_scope_archive_sample_accessions,
)
from bijux_pollenomics.adna.projects.sample_master.identity import (
    _cell_value,
    _format_horse_age_text,
    _merge_sample_row_group,
)
from bijux_pollenomics.adna.projects.sample_master.tables import _read_xlsx_rows
from bijux_pollenomics.adna.projects.registry.archive_samples import (
    read_archive_project_samples,
)
from bijux_pollenomics.adna.projects.sample_master import (
    build_cross_project_sample_master_completeness,
    build_project_sample_master,
    build_project_sample_master_rows,
    build_sample_identity_ambiguity_ledger,
)
from bijux_pollenomics.adna.workflow.source_artifacts import (
    read_source_artifact_bytes,
    resolve_source_artifact_path,
)
from bijux_pollenomics.adna.sources.archive import build_archive_project_catalog
from bijux_pollenomics.adna.workflow.normalization import (
    build_species_normalization_bundle,
)

pytestmark = pytest.mark.generated_artifacts


class AdnaSampleMasterUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = REPOSITORY_ROOT / "data"

    def test_archive_native_sample_master_expands_accession_ranges(self) -> None:
        rows = build_project_sample_master_rows(self.data_root, "KU605068-KU605080")

        self.assertEqual(len(rows), 13)
        self.assertEqual(rows[0].archive_native_sample_id, "KU605068")
        self.assertEqual(rows[-1].archive_native_sample_id, "KU605080")
        self.assertTrue(
            all(row.sample_evidence_status == "article_text_extracted" for row in rows)
        )
        self.assertTrue(all(row.sample_identity_resolution == "final" for row in rows))

        palm = next(row for row in rows if row.archive_native_sample_id == "KU605068")
        self.assertEqual(palm.preferred_sample_label, "Palm152")
        self.assertEqual(palm.locality_text, "Palmyra")
        self.assertEqual(palm.political_entity, "Syria")
        self.assertEqual(palm.chronology_text, "1650-2050 BP")

        modern = next(row for row in rows if row.archive_native_sample_id == "KU605080")
        self.assertEqual(modern.preferred_sample_label, "Drom820")
        self.assertEqual(modern.locality_text, "Pakistan")
        self.assertEqual(modern.chronology_text, "0 BP (modern comparator)")

    def test_dog_accessions_recover_article_owned_sites_and_dates(self) -> None:
        hx = build_project_sample_master_rows(self.data_root, "SRS1407453")
        mitogenomes = build_project_sample_master_rows(
            self.data_root, "KX379528-KX379529"
        )

        self.assertEqual(len(hx), 1)
        self.assertEqual(hx[0].preferred_sample_label, "HXH")
        self.assertEqual(hx[0].locality_text, "Herxheim")
        self.assertEqual(hx[0].chronology_text, "5223-5040 BCE")

        self.assertEqual(len(mitogenomes), 2)
        ctc = next(
            row for row in mitogenomes if row.archive_native_sample_id == "KX379528"
        )
        self.assertEqual(ctc.preferred_sample_label, "CTC")
        self.assertEqual(ctc.locality_text, "Cherry Tree Cave")
        self.assertEqual(ctc.chronology_text, "2900-2632 BCE")

    def test_sheep_project_sample_master_extracts_rows_from_supplementary_tables(
        self,
    ) -> None:
        rows = build_project_sample_master_rows(self.data_root, "PRJEB36540")

        self.assertGreater(len(rows), 10)
        first = rows[0]
        self.assertEqual(first.sample_evidence_status, "direct_table_extracted")
        self.assertEqual(first.sample_basis, "supplementary_table_sample_label_anchor")
        self.assertIn("42003_2021_2794_MOESM4_ESM.zip", first.sample_lineage_path)
        self.assertIn("Sheet1!row", first.sample_lineage_locator)
        self.assertEqual(first.sample_identity_resolution, "final")

    def test_horse_project_sample_master_merges_lab_and_panel_tables(self) -> None:
        rows = build_project_sample_master_rows(self.data_root, "PRJEB22390")

        self.assertEqual(len(rows), 42)
        botai = next(
            row for row in rows if row.archive_native_sample_id == "CGG_1_018173"
        )
        self.assertEqual(botai.preferred_sample_label, "Botai 1 5500")
        self.assertEqual(botai.locality_text, "Botai")
        self.assertEqual(botai.chronology_text, "5500 BP")
        self.assertIn("aao3297_tables11.xlsx", botai.sample_lineage_path)
        self.assertIn("aao3297_tables15.xlsx", botai.sample_lineage_path)
        self.assertEqual(botai.sample_identity_resolution, "final")

    def test_horse_time_series_and_dom2_projects_publish_recovered_sample_rows(
        self,
    ) -> None:
        time_series_rows = build_project_sample_master_rows(
            self.data_root, "PRJEB31613"
        )
        dom2_rows = build_project_sample_master_rows(self.data_root, "PRJEB44430")
        domestication_rows = build_project_sample_master_rows(
            self.data_root, "PRJEB19970"
        )

        self.assertEqual(len(time_series_rows), 244)
        self.assertEqual(len(dom2_rows), 248)
        self.assertEqual(len(domestication_rows), 14)

        uppsala = next(
            row
            for row in time_series_rows
            if row.preferred_sample_label == "Uppsala_Upps02_1317"
        )
        self.assertEqual(uppsala.locality_text, "Uppsala")
        self.assertEqual(uppsala.political_entity, "Sweden")
        self.assertEqual(uppsala.latitude_text, "59.860999999999997")
        self.assertEqual(uppsala.longitude_text, "17.638999999999999")
        self.assertEqual(uppsala.chronology_text, "1217-1417 BP")

        ginnerup = next(
            row
            for row in dom2_rows
            if row.preferred_sample_label == "DJM130x6_Dan_m3011"
        )
        self.assertEqual(ginnerup.locality_text, "Ginnerup")
        self.assertEqual(ginnerup.political_entity, "Denmark")
        self.assertEqual(ginnerup.latitude_text, "56.41134")
        self.assertEqual(ginnerup.longitude_text, "10.74481")
        self.assertEqual(ginnerup.chronology_text, "4961 BP")
        self.assertEqual(ginnerup.archive_native_sample_id, "SAMEA9533224")

        berel = next(
            row
            for row in domestication_rows
            if row.preferred_sample_label == "Berel_BER01_A_2300"
        )
        self.assertEqual(berel.locality_text, "Berel'")
        self.assertEqual(berel.political_entity, "Kazakhstan")
        self.assertEqual(berel.chronology_text, "2300 BP")

    def test_goat_cattle_and_reindeer_projects_publish_source_backed_sample_rows(
        self,
    ) -> None:
        goat_rows = build_project_sample_master_rows(self.data_root, "PRJNA1328209")
        cattle_rows = build_project_sample_master_rows(self.data_root, "PRJNA705960")
        reindeer_rows = build_project_sample_master_rows(self.data_root, "PRJEB60484")

        self.assertEqual(len(goat_rows), 5)
        self.assertEqual(len(cattle_rows), 11)
        self.assertEqual(len(reindeer_rows), 20)

        qinghai = next(row for row in goat_rows if row.preferred_sample_label == "DC23")
        self.assertEqual(qinghai.locality_text, "Lake Qinghai basin")
        self.assertEqual(qinghai.chronology_text, "3480-3580 BP")
        self.assertIn("Supplementary_tables.xlsx", qinghai.sample_lineage_path)

        cattle_anchor = cattle_rows[0]
        self.assertEqual(
            cattle_anchor.sample_basis, "archive_project_sample_accession_anchor"
        )
        self.assertEqual(cattle_anchor.sample_evidence_status, "archive_native")
        self.assertTrue(cattle_anchor.archive_native_sample_id.startswith("SAMN"))

        reindeer_anchor = reindeer_rows[0]
        self.assertEqual(
            reindeer_anchor.sample_basis, "archive_project_sample_accession_anchor"
        )
        self.assertEqual(reindeer_anchor.sample_evidence_status, "archive_native")
        self.assertTrue(reindeer_anchor.archive_native_sample_id.startswith("SAMEA"))

    def test_locally_captured_archive_projects_publish_native_sample_rows(
        self,
    ) -> None:
        expected_counts = {
            "PRJEB30282": 343,
            "PRJEB31621": 77,
            "PRJEB41594": 5,
            "PRJEB59481": 5,
            "PRJEB75467": 44,
            "PRJEB81815": 87,
        }

        for project_accession, expected_count in expected_counts.items():
            with self.subTest(project_accession=project_accession):
                rows = build_project_sample_master_rows(
                    self.data_root, project_accession
                )
                self.assertEqual(len(rows), expected_count)
                self.assertTrue(
                    all(row.sample_identity_resolution == "final" for row in rows)
                )
                self.assertTrue(all(row.sample_lineage_path for row in rows))
                self.assertTrue(all(row.sample_lineage_locator for row in rows))

    def test_recovery_target_raw_identity_taxonomy_and_receipts_close_exactly(
        self,
    ) -> None:
        archive_projects = (
            "PRJEB30282",
            "PRJEB31621",
            "PRJEB41594",
            "PRJEB59481",
            "PRJEB60484",
            "PRJEB75467",
            "PRJEB81815",
            "PRJNA705960",
            "SRP073444",
        )
        catalog = build_archive_project_catalog()
        catalog_species = {
            row.project_accession: row.species_latin_name for row in catalog
        }
        raw_expected: dict[tuple[str, str], tuple[str, str, str, str, str, str]] = {}
        for project_accession in archive_projects:
            logical_path = (
                self.data_root
                / "adna/governance/source_library/projects"
                / project_accession
                / "archive_metadata.html"
            )
            self._assert_source_receipt_closes(logical_path, project_accession)
            configured_species = catalog_species[project_accession]
            for raw_row in read_archive_project_samples(logical_path):
                names = " | ".join(raw_row.source_native_scientific_names)
                source_identity = (
                    raw_row.archive_native_sample_id
                    or raw_row.archive_native_experiment_id
                )
                raw_expected[(project_accession, source_identity)] = (
                    raw_row.archive_native_sample_id,
                    raw_row.archive_native_experiment_id,
                    raw_row.source_native_identity_kind,
                    " | ".join(raw_row.source_native_tax_ids),
                    names,
                    _expected_taxon_alignment(configured_species, names),
                )

        cat_workbook = (
            self.data_root
            / "adna/governance/source_library/papers/10.1016-j.xgen.2025.101099/"
            "supplementary/1-s2.0-S2666979X25003556-mmc3.xlsx"
        )
        self._assert_source_receipt_closes(cat_workbook, "PRJNA1178732")
        cat_rows = _read_xlsx_rows(cat_workbook, sheet_name="A")
        cat_headers = {value.strip(): index for index, value in enumerate(cat_rows[2])}
        for row in cat_rows[3:]:
            label = _cell_value(row, cat_headers["Sample ID"])
            name = _cell_value(row, cat_headers["Species"])
            if label and name:
                raw_expected[("PRJNA1178732", label)] = (
                    "",
                    "",
                    "biological_sample",
                    "",
                    name,
                    _expected_taxon_alignment("Felis catus", name),
                )

        target_projects = (*archive_projects, "PRJNA1178732")
        master_rows = [
            row
            for project_accession in target_projects
            for row in build_project_sample_master_rows(
                self.data_root, project_accession
            )
        ]
        master_by_source_identity = {
            (
                row.project_accession,
                row.archive_native_sample_id
                or row.archive_native_experiment_id
                or row.supplementary_table_sample_label,
            ): row
            for row in master_rows
        }
        self.assertEqual(len(raw_expected), 634)
        self.assertEqual(set(master_by_source_identity), set(raw_expected))
        for source_identity, expected_taxonomy in raw_expected.items():
            row = master_by_source_identity[source_identity]
            self.assertEqual(
                (
                    row.archive_native_sample_id,
                    row.archive_native_experiment_id,
                    row.source_native_identity_kind,
                    row.source_native_tax_id,
                    row.source_native_scientific_name,
                    row.taxon_alignment_status,
                ),
                expected_taxonomy,
                source_identity,
            )

        bundles = tuple(
            build_species_normalization_bundle(species)
            for species in (
                "horse",
                "pig",
                "sheep",
                "cattle",
                "goat",
                "dog",
                "cat",
                "camel",
                "reindeer",
                "donkey",
            )
        )
        normalized_rows = [row for bundle in bundles for row in bundle.sample_records]
        stable_tokens = [row.identity.stable_token for row in normalized_rows]
        normalized_by_master = {
            (row.project_accession, row.master_id): row for row in normalized_rows
        }
        self.assertEqual(len(stable_tokens), 1451)
        self.assertEqual(len(set(stable_tokens)), 1451)
        self.assertEqual(len(normalized_by_master), 1451)
        all_master_rows = [
            row
            for project in catalog
            for row in build_project_sample_master_rows(
                self.data_root, project.project_accession
            )
        ]
        admitted_master_by_identity = {
            (row.project_accession, row.repo_stable_sample_id): row
            for row in all_master_rows
            if row.sample_identity_resolution == "final"
            and row.sample_evidence_status != "experiment_level_only"
        }
        self.assertEqual(len(all_master_rows), 1471)
        self.assertEqual(len(admitted_master_by_identity), 1451)
        self.assertEqual(set(normalized_by_master), set(admitted_master_by_identity))
        for key, master_row in admitted_master_by_identity.items():
            normalized = normalized_by_master[key]
            self.assertEqual(
                (
                    normalized.source_native_tax_id,
                    normalized.source_native_scientific_name,
                    normalized.taxon_alignment_status,
                ),
                (
                    master_row.source_native_tax_id,
                    master_row.source_native_scientific_name,
                    master_row.taxon_alignment_status,
                ),
                key,
            )

    def _assert_source_receipt_closes(
        self,
        logical_path: Path,
        project_accession: str,
    ) -> None:
        receipt_path = logical_path.with_suffix(logical_path.suffix + ".metadata.json")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        logical_payload = read_source_artifact_bytes(logical_path)
        stored_path = resolve_source_artifact_path(logical_path)
        stored_payload = stored_path.read_bytes()
        receipt_projects = (
            receipt["project_accession"]
            if "project_accession" in receipt
            else receipt["project_accessions"]
        )
        expected_projects: str | list[str] = (
            project_accession if "project_accession" in receipt else [project_accession]
        )
        self.assertEqual(receipt_projects, expected_projects)
        self.assertEqual(receipt["byte_size"], len(logical_payload))
        self.assertEqual(
            receipt["content_sha256"], hashlib.sha256(logical_payload).hexdigest()
        )
        self.assertEqual(receipt["storage_byte_size"], len(stored_payload))
        self.assertEqual(
            receipt["storage_sha256"], hashlib.sha256(stored_payload).hexdigest()
        )
        bundle_path = (
            self.data_root
            / "adna/governance/source_library/projects"
            / project_accession
            / "bundle_manifest.json"
        )
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        self.assertIn(
            str(logical_path.relative_to(self.data_root)),
            bundle["local_artifact_paths"],
        )

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

    def test_horse_age_text_keeps_range_labels_stable(self) -> None:
        self.assertEqual(
            _format_horse_age_text("5500 - 5700"),
            "5500-5700 BP",
        )
        self.assertEqual(
            _format_horse_age_text("2300"),
            "2300 BP",
        )

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
        self.assertEqual(horse_counts, Counter({14: 1, 42: 1, 244: 1, 248: 1}))
        self.assertEqual(ambiguity_rows, ())

    def test_archive_accession_readers_accept_compressed_archive_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            archive_dir = (
                output_root
                / "adna"
                / "governance"
                / "source_library"
                / "projects"
                / "PRJTEST"
            )
            archive_dir.mkdir(parents=True, exist_ok=True)
            with gzip.open(
                archive_dir / "archive_metadata.html.gz", "wt", encoding="utf-8"
            ) as handle:
                handle.write(
                    "sample_accession\tsubmitted_ftp\n"
                    "SAMEA1\tftp://example.org/Alpha_E1.fastq.gz\n"
                    "SAMEA2\tftp://example.org/Beta_i1.fastq.gz\n"
                )

            accessions = _project_scope_archive_sample_accessions(
                output_root,
                "PRJTEST",
            )
            lookup = _build_archive_sample_accession_lookup(
                output_root,
                "PRJTEST",
            )

        self.assertEqual(accessions, ("SAMEA1", "SAMEA2"))
        self.assertEqual(lookup["alpha"], "SAMEA1")
        self.assertEqual(lookup["beta"], "SAMEA2")


def _expected_taxon_alignment(configured_species: str, source_names: str) -> str:
    names = tuple(name.strip() for name in source_names.split(" | ") if name.strip())
    if not names:
        return "not_reported"
    if len(names) > 1:
        return "archive_taxon_conflict"
    if names[0].casefold() == configured_species.casefold():
        return "project_species_match"
    return "project_species_mismatch"


if __name__ == "__main__":
    unittest.main()
