from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import TypedDict
import unittest

import pytest

from bijux_pollenomics.adna.domain.models import AdnaSiteEvidenceRecord
from bijux_pollenomics.adna.projects.evidence.chronology import (
    build_cross_project_sample_chronology_audit,
    build_date_evidence_gap_queue,
    build_project_chronology_completeness_rows,
    build_project_sample_chronology_review_rows,
    build_project_sample_chronology_rows,
    build_sample_chronology_ambiguity_ledger,
    build_sample_chronology_conflict_ledger,
    build_sample_chronology_precision_audit,
    build_sample_chronology_provenance_rows,
    build_sample_chronology_review_rows,
    build_species_chronology_completeness_rows,
)
from bijux_pollenomics.adna.projects.evidence.chronology.resolution import (
    _resolve_chronology_source,
)
from bijux_pollenomics.adna.projects.sample_master import AdnaProjectSampleMasterRow
from tests.support.repository import REPOSITORY_ROOT


def test_source_fields_are_additive_to_the_actual_provenance_consumer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from bijux_pollenomics.adna.projects.evidence.chronology import audits
    from bijux_pollenomics.adna.projects.evidence.chronology.audits import provenance

    def row(project: str) -> SimpleNamespace:
        return SimpleNamespace(
            species_latin_name="Equus caballus",
            species_common_name="horse",
            project_accession=project,
            repo_stable_sample_id=f"{project}:alpha",
            preferred_sample_label="Horse A",
            sample_basis="source",
            sample_evidence_status="direct_table_extracted",
            sample_identity_resolution="final",
            sample_ambiguity_note="",
            chronology_text="" if project == "PRJEB31613" else "Age (years ago): 4692",
            chronology_provenance_text="raw source excerpt",
            chronology_provenance_path="",
            chronology_provenance_kind="tracked_source_artifact",
            chronology_provenance_locator="",
            dating_basis="unknown",
            chronology_evidence_class="unresolved",
            chronology_precision_posture="unresolved",
            chronology_normalization_status="unresolved",
            time_start_bp=None,
            time_end_bp=None,
            time_mean_bp=None,
        )

    monkeypatch.setattr(
        audits,
        "build_archive_project_catalog",
        lambda: (
            SimpleNamespace(project_accession="PRJEB31613"),
            SimpleNamespace(project_accession="other"),
        ),
    )
    monkeypatch.setattr(
        audits,
        "build_project_sample_chronology_rows",
        lambda root, project: (row(project),),
    )
    monkeypatch.setattr(
        provenance,
        "build_project_sample_master_rows",
        lambda root, project: (
            SimpleNamespace(
                repo_stable_sample_id="PRJEB31613:alpha",
                preferred_sample_label="Horse A",
                sample_lineage_locator="Sheet1!row5",
                sample_lineage_path="data/source.xlsx",
            ),
        ),
    )
    monkeypatch.setattr(
        audits,
        "_temporal_semantics_for_chronology_row",
        lambda source: {"comparability_posture": "contextual_label_only"},
    )
    monkeypatch.setattr(audits, "_normalization_rule_for", lambda source: "unresolved")
    monkeypatch.setattr(audits, "_uncertainty_note_for", lambda source: "unresolved")
    monkeypatch.setattr(
        provenance, "horse_source_chronology_fields", lambda root, *, owners: {}
    )
    baseline = provenance._build_sample_chronology_provenance_rows(tmp_path)
    context: dict[str, object] = {
        "repo_stable_sample_id": "PRJEB31613:alpha",
        "evidence_role": "source_context_only",
        "scientific_admission": False,
    }
    seen: list[dict[str, tuple[str, str, str]]] = []

    def native_fields(
        root: Path, *, owners: dict[str, tuple[str, str, str]]
    ) -> dict[str, dict[str, object]]:
        seen.append(owners)
        return dict.fromkeys(owners, context)

    monkeypatch.setattr(provenance, "horse_source_chronology_fields", native_fields)
    candidate = provenance._build_sample_chronology_provenance_rows(tmp_path)
    assert len(seen) == 1
    assert seen[0] == {
        "PRJEB31613:alpha": ("Horse A", "Sheet1!row5", "data/source.xlsx")
    }
    assert candidate[0]["source_chronology_fields"] == context
    assert "source_chronology_fields" not in candidate[1]
    assert (
        tuple(
            {
                key: value
                for key, value in packet.items()
                if key
                not in {"source_chronology_fields", "source_chronology_alternatives"}
            }
            for packet in candidate
        )
        == baseline
    )


class _ConflictCase(TypedDict):
    sample_text: str
    site_text: str
    site_start_bp: int | None
    site_end_bp: int | None
    expected_fragment: str


CONFLICTING_CHRONOLOGY_CASES: tuple[_ConflictCase, ...] = (
    {
        "sample_text": "1200-1500 BP",
        "site_text": "900-1100 BP",
        "site_start_bp": 900,
        "site_end_bp": 1100,
        "expected_fragment": "interval",
    },
    {
        "sample_text": "Late Bronze Age",
        "site_text": "Early Iron Age",
        "site_start_bp": None,
        "site_end_bp": None,
        "expected_fragment": "wording",
    },
)

pytestmark = pytest.mark.generated_artifacts


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AssertionError("expected a chronology evidence mapping")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise AssertionError("chronology evidence keys must be strings")
        result[key] = item
    return result


def _count_mapping(value: object) -> dict[str, int]:
    result: dict[str, int] = {}
    for key, item in _mapping(value).items():
        if isinstance(item, bool) or not isinstance(item, int):
            raise AssertionError(f"chronology count {key} must be an integer")
        result[key] = item
    return result


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise AssertionError("expected chronology source text")
    return value


class AdnaProjectSampleChronologyUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = REPOSITORY_ROOT / "data"

    def test_obishir_dates_are_specimen_bound_and_keep_source_caution(self) -> None:
        rows = build_project_sample_chronology_rows(self.data_root, "PRJEB41594")
        by_label = {row.preferred_sample_label: row for row in rows}
        self.assertEqual(len(by_label), 5)
        for label, interval, lab in (
            ("OB20-06", (7720, 7940), "AA-114606"),
            ("OB20-04", (4650, 4952), "AA-114607"),
            ("OB21-04", (2784, 2994), "AA-114608"),
        ):
            row = by_label[label]
            self.assertEqual((row.time_start_bp, row.time_end_bp), interval)
            self.assertEqual(row.chronology_strength, "sample_owned_interval")
            self.assertEqual(row.chronology_evidence_class, "direct_radiocarbon_date")
            self.assertEqual(
                row.chronology_precision_posture, "sample_precise_interval"
            )
            self.assertIn(
                "41562_2021_1083_MOESM1_ESM.pdf", row.chronology_provenance_path
            )
            self.assertIn(lab, row.chronology_provenance_locator)
        self.assertIn(
            "stratigraphically inconsistent",
            by_label["OB20-04"].chronology_provenance_text,
        )
        for label in ("OB20-01", "OB21-06"):
            self.assertEqual(by_label[label].chronology_strength, "unresolved")
            self.assertIsNone(by_label[label].time_start_bp)

    def test_sheep_project_sample_chronology_rows_publish_strengths_and_provenance(
        self,
    ) -> None:
        rows = build_project_sample_chronology_rows(self.data_root, "PRJEB36540")

        self.assertEqual(len(rows), 190)
        first = next(row for row in rows if row.preferred_sample_label == "BH 28")
        self.assertEqual(first.chronology_strength, "sample_owned_interval")
        self.assertEqual(first.chronology_evidence_class, "direct_radiocarbon_date")
        self.assertEqual(first.chronology_precision_posture, "sample_precise_interval")
        self.assertEqual(first.chronology_normalization_status, "normalized_interval")
        self.assertIn(
            "42003_2021_2794_MOESM4_ESM.zip", first.chronology_provenance_path
        )
        self.assertEqual(
            first.chronology_provenance_kind, "supplementary_spreadsheet_row"
        )
        self.assertTrue(first.chronology_provenance_locator.startswith("Sheet1!row"))

    def test_horse_project_sample_chronology_rows_publish_sample_owned_bp_points(
        self,
    ) -> None:
        rows = build_project_sample_chronology_rows(self.data_root, "PRJEB22390")

        botai = next(
            row for row in rows if row.preferred_sample_label == "Botai 1 5500"
        )
        self.assertEqual(botai.chronology_strength, "sample_owned_interval")
        self.assertEqual(botai.chronology_evidence_class, "direct_radiocarbon_date")
        self.assertEqual(botai.chronology_precision_posture, "sample_precise_point")
        self.assertEqual(botai.chronology_normalization_status, "normalized_point")
        self.assertEqual(botai.chronology_text, "5500 BP")
        self.assertEqual((botai.time_start_bp, botai.time_end_bp), (5500, 5500))
        self.assertIn("aao3297_tables15.xlsx", botai.chronology_provenance_path)

    def test_horse_nordic_elapsed_age_retains_source_range_without_bp_promotion(
        self,
    ) -> None:
        rows = build_project_sample_chronology_rows(self.data_root, "PRJEB31613")

        uppsala = next(
            row for row in rows if row.preferred_sample_label == "Uppsala_Upps02_1317"
        )
        self.assertEqual(uppsala.chronology_strength, "sample_owned_text_only")
        self.assertEqual(uppsala.chronology_evidence_class, "unresolved")
        self.assertEqual(uppsala.chronology_precision_posture, "unresolved")
        self.assertEqual(uppsala.chronology_normalization_status, "text_only_unparsed")
        self.assertEqual(uppsala.chronology_text, "Age (years ago): 1217-1417")
        self.assertEqual((uppsala.time_start_bp, uppsala.time_end_bp), (None, None))
        self.assertIn(
            "1-s2.0-S0092867419303848-mmc1.xlsx", uppsala.chronology_provenance_path
        )

    def test_aurochs_chronology_preserves_published_means_inside_bp_intervals(
        self,
    ) -> None:
        rows = build_project_sample_chronology_rows(self.data_root, "PRJEB75467")
        by_label = {row.preferred_sample_label: row for row in rows}

        assert {
            label: (
                by_label[label].time_start_bp,
                by_label[label].time_end_bp,
                by_label[label].time_mean_bp,
            )
            for label in ("Hjo1", "Ska1", "Ska3", "Zea1", "Zea2")
        } == {
            "Hjo1": (7976, 8173, 8074),
            "Ska1": (9133, 9536, 9334),
            "Ska3": (9434, 9657, 9546),
            "Zea1": (6754, 7744, 7302),
            "Zea2": (6748, 7744, 7296),
        }

    def test_camel_paper_table_s1_assigns_contextual_sample_chronology(
        self,
    ) -> None:
        rows = build_project_sample_chronology_rows(self.data_root, "SRP073444")

        self.assertEqual(len(rows), 20)
        dated = [row for row in rows if row.time_start_bp is not None]
        self.assertEqual(len(dated), 16)
        self.assertEqual(
            sum(row.chronology_strength == "unresolved" for row in rows), 4
        )
        self.assertTrue(
            all(
                row.chronology_precision_posture == "contextual_interval"
                for row in dated
            )
        )
        palm = next(row for row in rows if row.preferred_sample_label == "Palm143_II")
        self.assertEqual((palm.time_start_bp, palm.time_end_bp), (1650, 2050))
        self.assertEqual(palm.chronology_evidence_class, "archaeological_context_date")

    def test_project_context_does_not_become_biological_sample_chronology(
        self,
    ) -> None:
        for accession in ("PRJNA705960", "SRS1407451"):
            rows = build_project_sample_chronology_rows(self.data_root, accession)
            self.assertTrue(rows)
            self.assertTrue(
                all(row.chronology_strength == "unresolved" for row in rows)
            )
            self.assertTrue(all(row.time_start_bp is None for row in rows))
            self.assertTrue(all(row.time_end_bp is None for row in rows))

    def test_cat_chronology_keeps_exact_intervals_and_refuses_identity_conflicts(
        self,
    ) -> None:
        rows = build_project_sample_chronology_rows(self.data_root, "PRJEB81815")
        unresolved = tuple(
            row for row in rows if row.sample_identity_resolution == "ambiguous"
        )

        self.assertEqual(len(rows), 87)
        self.assertEqual(
            sum(
                row.time_start_bp is not None and row.time_end_bp is not None
                for row in rows
            ),
            45,
        )
        self.assertEqual(len(unresolved), 3)
        self.assertTrue(
            all(
                row.chronology_normalization_status == "unresolved"
                for row in unresolved
            )
        )
        self.assertTrue(
            all(row.time_start_bp is row.time_end_bp is None for row in unresolved)
        )
        contextual = next(
            row for row in rows if row.preferred_sample_label == "HAIScat01"
        )
        self.assertEqual(
            (contextual.time_start_bp, contextual.time_end_bp), (900, 1150)
        )
        self.assertEqual(
            contextual.chronology_evidence_class, "archaeological_context_date"
        )
        self.assertEqual(contextual.chronology_precision_posture, "contextual_interval")

    def test_multi_site_projects_never_borrow_the_first_site_chronology(self) -> None:
        horse_rows = build_project_sample_chronology_rows(self.data_root, "PRJEB31613")
        sheep_rows = build_project_sample_chronology_rows(self.data_root, "PRJEB36540")

        horse = next(
            row
            for row in horse_rows
            if row.preferred_sample_label == "Derkul_NB2_Neolithic"
        )
        sheep = next(row for row in sheep_rows if row.preferred_sample_label == "TEP02")
        for row in (horse, sheep):
            with self.subTest(sample=row.preferred_sample_label):
                self.assertEqual(row.chronology_normalization_status, "unresolved")
                self.assertIsNone(row.time_start_bp)
                self.assertIsNone(row.time_end_bp)

    def test_chronology_review_audit_and_completeness_surfaces_stay_reader_visible(
        self,
    ) -> None:
        review_rows = build_project_sample_chronology_review_rows(self.data_root)
        audit = build_cross_project_sample_chronology_audit(self.data_root)
        ambiguity_rows = build_sample_chronology_ambiguity_ledger(self.data_root)
        conflict_rows = build_sample_chronology_conflict_ledger(self.data_root)
        precision_audit = build_sample_chronology_precision_audit(self.data_root)
        gap_queue = build_date_evidence_gap_queue(self.data_root)
        species_rows = build_species_chronology_completeness_rows(self.data_root)
        project_rows = build_project_chronology_completeness_rows(self.data_root)
        sample_review_rows = build_sample_chronology_review_rows(self.data_root)
        provenance_rows = build_sample_chronology_provenance_rows(self.data_root)

        self.assertEqual(len(review_rows), 40)
        sheep_review = next(
            row for row in review_rows if row["project_accession"] == "PRJEB36540"
        )
        self.assertEqual(sheep_review["sample_owned_interval_count"], 167)
        self.assertEqual(sheep_review["text_only_unparsed_count"], 13)
        self.assertEqual(audit["sample_row_count"], 1475)
        self.assertEqual(audit["normalized_interval_count"], 315)
        self.assertEqual(audit["normalized_point_count"], 368)
        self.assertEqual(audit["unresolved_count"], 406)
        audit_precision_counts = _count_mapping(audit["precision_counts"])
        self.assertEqual(audit_precision_counts["contextual_interval"], 32)
        self.assertEqual(audit_precision_counts["sample_approximate_or_modeled"], 200)
        self.assertEqual(audit_precision_counts["sample_precise_interval"], 239)
        self.assertFalse(
            any(
                row["project_accession"]
                in {
                    "KU605068-KU605080",
                    "KX379528-KX379529",
                    "SRS1407453",
                }
                and row["chronology_normalization_status"] == "unresolved"
                for row in ambiguity_rows
            )
        )
        self.assertEqual(conflict_rows, ())
        precision_counts = _count_mapping(precision_audit["precision_counts"])
        self.assertEqual(precision_counts["sample_approximate_or_modeled"], 200)
        sheep_species = next(
            row for row in species_rows if row["species_latin_name"] == "Ovis aries"
        )
        self.assertEqual(sheep_species["normalized_row_count"], 186)
        obishir_project = next(
            row for row in project_rows if row["project_accession"] == "PRJEB41594"
        )
        self.assertEqual(obishir_project["exact_sample_date_count"], 3)
        self.assertEqual(obishir_project["unresolved_count"], 2)
        baltic_sheep_project = next(
            row for row in project_rows if row["project_accession"] == "PRJEB59481"
        )
        self.assertEqual(baltic_sheep_project["normalized_row_count"], 4)
        self.assertEqual(baltic_sheep_project["exact_sample_date_count"], 3)
        self.assertEqual(baltic_sheep_project["contextual_date_count"], 1)
        self.assertEqual(baltic_sheep_project["broad_label_count"], 1)
        self.assertEqual(baltic_sheep_project["unresolved_count"], 0)
        camel_project = next(
            row
            for row in project_rows
            if row["project_accession"] == "KU605068-KU605080"
        )
        self.assertEqual(camel_project["unresolved_count"], 0)
        camel_sra_project = next(
            row for row in project_rows if row["project_accession"] == "SRP073444"
        )
        self.assertEqual(camel_sra_project["contextual_date_count"], 16)
        self.assertEqual(camel_sra_project["unresolved_count"], 4)
        goat_project = next(
            row for row in project_rows if row["project_accession"] == "PRJNA1328209"
        )
        self.assertEqual(goat_project["exact_sample_date_count"], 5)
        horse_species = next(
            row for row in species_rows if row["species_latin_name"] == "Equus caballus"
        )
        self.assertEqual(horse_species["normalized_row_count"], 290)
        horse_dom2 = next(
            row for row in project_rows if row["project_accession"] == "PRJEB44430"
        )
        self.assertEqual(horse_dom2["normalized_row_count"], 248)
        self.assertTrue(
            any(
                row["project_accession"] == "PRJNA705960"
                and row["gap_reasons"]
                == [
                    "no_sample_owned_chronology_recovered",
                    "missing_sample_level_date_evidence",
                ]
                for row in gap_queue
            )
        )
        self.assertTrue(
            any(
                row["project_accession"] == "PRJEB59481"
                and row["gap_reasons"]
                == ["broad_period_labels_still_need_stronger_date_support"]
                for row in gap_queue
            )
        )
        self.assertEqual(len(sample_review_rows), 1475)
        self.assertEqual(len(provenance_rows), 1475)
        horse_provenance = next(
            row
            for row in provenance_rows
            if row["project_accession"] == "PRJEB31613"
            and row["preferred_sample_label"] == "Uppsala_Upps02_1317"
        )
        horse_semantics = _mapping(horse_provenance["temporal_semantics"])
        published_wording = _text(horse_provenance["published_wording"])
        self.assertEqual(published_wording, "Age (years ago): 1217-1417")
        self.assertIsNone(horse_provenance["time_start_bp"])
        self.assertIsNone(horse_provenance["time_end_bp"])
        self.assertEqual(horse_provenance["evidence_class"], "unresolved")
        self.assertEqual(horse_provenance["precision_posture"], "unresolved")
        self.assertEqual(
            horse_semantics["comparability_posture"],
            "contextual_label_only",
        )
        self.assertEqual(
            horse_semantics["summary_label"],
            published_wording,
        )
        self.assertTrue(horse_provenance["provenance_surface"])
        self.assertTrue(horse_provenance["provenance_locator"])

    def test_conflicting_chronology_corpus_surfaces_disagreement_notes(self) -> None:
        for case in CONFLICTING_CHRONOLOGY_CASES:
            master_row = AdnaProjectSampleMasterRow(
                species_latin_name="Test species",
                species_common_name="test",
                project_accession="TEST",
                repo_stable_sample_id="test:sample:one",
                archive_native_sample_id="TEST-1",
                paper_native_sample_label="TEST-1",
                supplementary_table_sample_label="",
                preferred_sample_label="TEST-1",
                sample_basis="source_sample",
                sample_evidence_status="direct_table_extracted",
                chronology_text=case["sample_text"],
                sample_lineage_path="data/adna/governance/source_library/projects/TEST/sample_master.csv",
                sample_lineage_locator="row:1",
                sample_lineage_excerpt=case["sample_text"],
                sample_identity_resolution="final",
                sample_ambiguity_note="",
                locality_text="Test site",
                political_entity="",
                latitude_text="",
                longitude_text="",
            )
            site_row = AdnaSiteEvidenceRecord(
                project_accession="TEST",
                species_latin_name="Test species",
                species_common_name="test",
                site_label="Test site",
                political_entity=None,
                chronology_text=case["site_text"],
                time_start_bp=case["site_start_bp"],
                time_end_bp=case["site_end_bp"],
                source_artifact_path="data/adna/governance/source_library/papers/test/article.html",
                source_artifact_kind="article_or_archive_text",
                source_locator="body",
                exact_source_text=case["site_text"],
                source_support_status="source_anchored",
            )

            resolved = _resolve_chronology_source(
                master_row=master_row,
                site_row=site_row,
                dating_basis="mixed_radiocarbon_and_archaeological_context",
            )

            self.assertIn(case["expected_fragment"], resolved.chronology_conflict_note)
            self.assertEqual(resolved.chronology_strength[:12], "sample_owned")


if __name__ == "__main__":
    unittest.main()
