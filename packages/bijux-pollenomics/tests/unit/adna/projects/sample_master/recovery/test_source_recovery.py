"""Tests for project-specific sample recovery from governed sources."""

from __future__ import annotations

from collections import Counter
import csv
from dataclasses import replace
import io
import json

import pytest

from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)
from bijux_pollenomics.adna.projects.sample_master.archive import _project_by_accession
from bijux_pollenomics.adna.projects.sample_master.models import (
    AdnaProjectSampleMasterRow,
)
from bijux_pollenomics.adna.projects.sample_master.tables import _read_xlsx_rows
from bijux_pollenomics.adna.projects.sample_master.tables.goat_imputation import (
    _build_goat_imputation_rows,
    _qualify_goat_imputation_rows,
)
from bijux_pollenomics.adna.species.definitions import resolve_species_definition
from bijux_pollenomics.adna.workflow.source_artifacts import read_source_artifact_text

from .support import SampleMasterRecoveryTestCase

pytestmark = pytest.mark.generated_artifacts


class GoatImputationSourceTests(SampleMasterRecoveryTestCase):
    """Keep reused publication rows separate from project-owned specimens."""

    @staticmethod
    def _project_rows(
        table_rows: tuple[tuple[str, ...], ...],
    ) -> tuple[AdnaProjectSampleMasterRow, ...]:
        return _build_goat_imputation_rows(
            species=resolve_species_definition("Capra hircus"),
            project=_project_by_accession("PRJEB90141"),
            source_path="source.xlsx",
            rows=table_rows,
        )

    @staticmethod
    def _table(accession: str) -> tuple[tuple[str, ...], ...]:
        return (
            ("Sample", "Site", "C14 range, 2σ calibrated", "Accession"),
            ("source-label", "site", "6081-5891 BCE", accession),
        )

    def test_foreign_study_sample_matches_do_not_qualify_ownership(self) -> None:
        table = self._table("SAMEA1")
        rows = _qualify_goat_imputation_rows(
            rows=self._project_rows(table),
            table_rows=table,
            archive_text="study_accession\tsample_accession\nFOREIGN\tSAMEA1\nPRJEB90141\tSAMEA2\n",
            archive_source_path="archive.tsv",
        )
        self.assertEqual(rows[0].sample_identity_resolution, "ambiguous")
        self.assertIn("requested-study matches: ()", rows[0].sample_ambiguity_note)
        self.assertIn("('SAMEA1',)", rows[0].sample_ambiguity_note)
        self.assertIn("archive.tsv", rows[0].sample_lineage_path)

    def test_all_matching_pooled_accessions_remain_nonunique(self) -> None:
        literal = "  SAMEA1 ; SAMEA2  "
        table = self._table(literal)
        rows = _qualify_goat_imputation_rows(
            rows=self._project_rows(table),
            table_rows=table,
            archive_text="study_accession\tsample_accession\nPRJEB90141\tSAMEA1\nPRJEB90141\tSAMEA2\n",
            archive_source_path="archive.tsv",
        )
        row = rows[0]
        self.assertEqual(row.archive_native_sample_id, "SAMEA1")
        self.assertEqual(row.repo_stable_sample_id, "prjeb90141:samea1")
        self.assertEqual(row.sample_identity_resolution, "ambiguous")
        self.assertEqual(row.source_native_identity_kind, "supplementary_sample_label")
        self.assertIn(repr(literal), row.sample_ambiguity_note)
        self.assertIn(
            "requested-study matches: ('SAMEA1', 'SAMEA2')", row.sample_ambiguity_note
        )
        self.assertIn("trace only", row.sample_ambiguity_note)
        self.assertIn("unique biological specimen", row.sample_ambiguity_note)

    def test_complete_accession_cell_survives_clipped_source_excerpt(self) -> None:
        literal = "  SAMEA1; SAMEA2  "
        table = (
            ("Sample", "Site", "C14 range, 2σ calibrated", "Accession"),
            ("source-label", "long site " * 70, "6081-5891 BCE", literal),
        )
        projected = self._project_rows(table)
        self.assertEqual(len(projected[0].sample_lineage_excerpt), 300)
        self.assertNotIn("SAMEA2", projected[0].sample_lineage_excerpt)
        self.assertIn(repr(literal), projected[0].sample_ambiguity_note)
        qualified = _qualify_goat_imputation_rows(
            rows=projected,
            table_rows=table,
            archive_text=None,
            archive_source_path="archive.tsv",
        )[0]
        self.assertIn(repr(literal), qualified.sample_lineage_excerpt)
        self.assertIn("('SAMEA1', 'SAMEA2')", qualified.sample_lineage_excerpt)

    def test_missing_or_unusable_archive_is_unresolved_not_empty_population(
        self,
    ) -> None:
        for archive in (None, "", "sample_accession\nSAMEA1\n"):
            with self.subTest(archive=archive):
                table = self._table("SAMEA1")
                row = _qualify_goat_imputation_rows(
                    rows=self._project_rows(table),
                    table_rows=table,
                    archive_text=archive,
                    archive_source_path="archive.tsv",
                )[0]
                self.assertEqual(row.sample_identity_resolution, "ambiguous")
                self.assertIn("present in capture: None", row.sample_ambiguity_note)
                self.assertIn("unavailable", row.sample_ambiguity_note)

    def test_matching_single_accession_does_not_establish_specimen_binding(
        self,
    ) -> None:
        table = self._table("SAMEA1")
        row = _qualify_goat_imputation_rows(
            rows=self._project_rows(table),
            table_rows=table,
            archive_text="study_accession\tsample_accession\nPRJEB90141\tSAMEA1\n",
            archive_source_path="archive.tsv",
        )[0]
        self.assertIn("requested-study matches: ('SAMEA1',)", row.sample_ambiguity_note)
        self.assertEqual(row.sample_identity_resolution, "ambiguous")

    def test_native_four_rows_keep_keys_literals_and_all_accession_alternatives(
        self,
    ) -> None:
        relative = "adna/governance/source_library/"
        workbook = self.data_root / (
            relative + "papers/10.1093-gbe-evaf181/supplementary/"
            "GBE_Supplementary_Tables_S1-18_Goat_imputation.xlsx"
        )
        table = _read_xlsx_rows(workbook, sheet_name="Table S2 downsampled samples")
        archive_path = relative + "projects/PRJEB90141/archive_metadata.html"
        archive_text = read_source_artifact_text(self.data_root / archive_path)
        native = list(csv.DictReader(io.StringIO(archive_text), delimiter="\t"))
        self.assertEqual(len(native), 784)
        self.assertEqual(
            Counter(row["study_accession"] for row in native),
            {
                "PRJEB31857": 266,
                "PRJEB37208": 20,
                "PRJEB37276": 44,
                "PRJEB37122": 391,
                "PRJEB37841": 8,
                "PRJEB50463": 55,
            },
        )
        alternatives = {
            "Direkli1-2": "SAMEA4453841; SAMEA4453842",
            "Blagotin3": "SAMEA4588077",
            "Acem2": "SAMEA4591761",
            "Semnan3": "SAMEA4591758",
        }
        header = table[0]
        self.assertEqual(
            {
                row[header.index("Sample")]: row[header.index("Accession")]
                for row in table[1:]
                if row and row[header.index("Sample")]
            },
            alternatives,
        )
        baseline_path = self.data_root / (
            relative + "projects/PRJEB90141/sample_master.json"
        )
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        by_label = {row["preferred_sample_label"]: row for row in baseline["rows"]}
        projected = self._project_rows(table)
        # The stand-alone projection used by controls supplies a synthetic path;
        # restore the existing source path for the literal baseline comparison.
        projected = tuple(
            replace(
                row,
                sample_lineage_path=by_label[row.preferred_sample_label][
                    "sample_lineage_path"
                ],
            )
            for row in projected
        )
        qualified = _qualify_goat_imputation_rows(
            rows=projected,
            table_rows=table,
            archive_text=archive_text,
            archive_source_path="data/" + archive_path,
        )
        self.assertEqual(len(qualified), 4)
        changed = {
            "sample_identity_resolution",
            "sample_ambiguity_note",
            "source_native_identity_kind",
            "sample_lineage_path",
            "sample_lineage_locator",
            "sample_lineage_excerpt",
        }
        for row in qualified:
            prior = by_label[row.preferred_sample_label]
            self.assertEqual(
                {
                    key: value
                    for key, value in row.as_dict().items()
                    if key not in changed
                },
                {key: value for key, value in prior.items() if key not in changed},
            )
            self.assertEqual(row.sample_identity_resolution, "ambiguous")
            self.assertIn(
                repr(alternatives[row.preferred_sample_label]),
                row.sample_ambiguity_note,
            )
            self.assertIn("present in capture: False", row.sample_ambiguity_note)
            self.assertIn("requested-study matches: ()", row.sample_ambiguity_note)
        all_alternatives = {
            value.strip()
            for literal in alternatives.values()
            for value in literal.split(";")
        }
        self.assertEqual(len(all_alternatives), 5)
        self.assertFalse(all_alternatives & {row["sample_accession"] for row in native})


class SourceRecoveryTests(SampleMasterRecoveryTestCase):
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

        self.assertEqual(len(time_series_rows), 245)
        self.assertEqual(len(dom2_rows), 248)
        self.assertEqual(len(domestication_rows), 15)

        uppsala = next(
            row
            for row in time_series_rows
            if row.preferred_sample_label == "Uppsala_Upps02_1317"
        )
        self.assertEqual(uppsala.locality_text, "Uppsala")
        self.assertEqual(uppsala.political_entity, "Sweden")
        self.assertEqual(uppsala.latitude_text, "59.860999999999997")
        self.assertEqual(uppsala.longitude_text, "17.638999999999999")
        self.assertEqual(uppsala.chronology_text, "Age (years ago): 1217-1417")

        registration_missing = {
            row.preferred_sample_label: row
            for row in time_series_rows
            if row.preferred_sample_label in {"Batagai_5155", "Przewalski_Paratype_118"}
        }
        self.assertEqual(
            {row.repo_stable_sample_id for row in registration_missing.values()},
            {
                "prjeb31613:batagai_5155",
                "prjeb31613:przewalski_paratype_118",
            },
        )
        self.assertTrue(
            all(
                row.archive_native_sample_id == ""
                for row in registration_missing.values()
            )
        )

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
        self.assertEqual(berel.chronology_text, "Age (years ago): 2300")

        missing_registration_rows = {
            row.preferred_sample_label: row
            for row in domestication_rows
            if row.preferred_sample_label in {"Connemara_0004A", "Somali_0226A"}
        }
        self.assertEqual(
            set(missing_registration_rows), {"Connemara_0004A", "Somali_0226A"}
        )
        self.assertEqual(
            {row.repo_stable_sample_id for row in missing_registration_rows.values()},
            {"prjeb19970:connemara_0004a", "prjeb19970:somali_0226a"},
        )
        self.assertTrue(
            all(
                row.archive_native_sample_id == ""
                and row.locality_text == ""
                and row.political_entity == ""
                and row.chronology_text == ""
                for row in missing_registration_rows.values()
            )
        )

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
        self.assertEqual(
            reindeer_anchor.sample_evidence_status, "direct_table_extracted"
        )
        self.assertEqual(reindeer_anchor.preferred_sample_label, "MLM12")
        self.assertTrue(reindeer_anchor.archive_native_sample_id.startswith("SAMEA"))

    def test_locally_captured_archive_projects_publish_native_sample_rows(
        self,
    ) -> None:
        expected_counts = {
            "PRJEB30282": 343,
            "PRJEB31621": 78,
            "PRJEB41594": 5,
            "PRJEB59481": 5,
            "PRJEB75467": 45,
            "PRJEB81815": 87,
        }

        for project_accession, expected_count in expected_counts.items():
            with self.subTest(project_accession=project_accession):
                rows = build_project_sample_master_rows(
                    self.data_root, project_accession
                )
                self.assertEqual(len(rows), expected_count)
                if project_accession == "PRJEB81815":
                    self.assertEqual(
                        Counter(row.sample_identity_resolution for row in rows),
                        {"final": 84, "ambiguous": 3},
                    )
                elif project_accession == "PRJEB31621":
                    self.assertEqual(
                        Counter(row.sample_identity_resolution for row in rows),
                        {"final": 77, "provisional": 1},
                    )
                elif project_accession == "PRJEB75467":
                    self.assertEqual(
                        Counter(row.sample_identity_resolution for row in rows),
                        {"final": 44, "provisional": 1},
                    )
                elif project_accession == "SRP073444":
                    self.assertEqual(
                        Counter(row.sample_identity_resolution for row in rows),
                        {"final": 18, "ambiguous": 2},
                    )
                else:
                    self.assertTrue(
                        all(row.sample_identity_resolution == "final" for row in rows)
                    )
                self.assertTrue(all(row.sample_lineage_path for row in rows))
                self.assertTrue(all(row.sample_lineage_locator for row in rows))

    def test_cat_panel_preserves_source_taxa_and_refuses_spatial_inference(
        self,
    ) -> None:
        rows = build_project_sample_master_rows(self.data_root, "PRJEB81815")

        self.assertEqual(
            Counter(row.source_native_scientific_name for row in rows),
            {
                "Felis catus": 42,
                "Felis silvestris silvestris": 38,
                "Felis silvestris lybica": 7,
            },
        )
        self.assertEqual(
            Counter(row.chronology_precision_posture for row in rows),
            {
                "sample_approximate_or_modeled": 37,
                "broad_period_only": 39,
                "contextual_interval": 8,
                "unresolved": 3,
            },
        )
        self.assertEqual(
            sum(bool(row.latitude_text and row.longitude_text) for row in rows), 56
        )
        self.assertTrue(
            all(
                row.latitude_text == row.longitude_text == ""
                for row in rows
                if row.chronology_dating_basis == "modern_sampling"
            )
        )
        self.assertTrue(
            all("transect" not in row.locality_text.casefold() for row in rows)
        )
        exact = tuple(row for row in rows if row.sample_identity_resolution == "final")
        self.assertTrue(all(row.sample_lineage_path.endswith(".zip") for row in exact))
        self.assertTrue(
            all(
                "science.adt2642_tables s1_to_s8.xlsx" in row.sample_lineage_locator
                for row in exact
            )
        )
