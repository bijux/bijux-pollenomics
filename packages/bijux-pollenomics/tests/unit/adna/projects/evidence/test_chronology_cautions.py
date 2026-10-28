"""Source-owned cautions remain visible without rewriting reported dates."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from bijux_pollenomics.adna.domain.models import AdnaSiteEvidenceRecord
from bijux_pollenomics.adna.projects.evidence.chronology import audits, rows
from bijux_pollenomics.adna.projects.evidence.chronology.models import (
    AdnaProjectSampleChronologyRow,
)
from bijux_pollenomics.adna.projects.evidence.chronology.semantics import (
    _temporal_semantics_for_chronology_row,
    _uncertainty_note_for,
)
from bijux_pollenomics.adna.projects.sample_master import AdnaProjectSampleMasterRow
from bijux_pollenomics.adna.projects.sample_master.tables.obishir_sheep import (
    obishir_chronology_caution,
)
from bijux_pollenomics.adna.sources.archive import build_archive_project_catalog
from bijux_pollenomics.reporting.adna.foundation_outputs.release import (
    _chronology_row_blocks_publication,
)


def _masters() -> tuple[AdnaProjectSampleMasterRow, ...]:
    result = []
    for accession, alias, date in (
        ("SAMEA8022720", "OB20-01", ""),
        ("SAMEA8022721", "OB20-06", "5991-5771 cal BCE"),
        ("SAMEA8022722", "OB21-04", "1045-835 cal BCE"),
        ("SAMEA8022723", "OB21-06", ""),
        ("SAMEA8022724", "OB20-04", "3003-2701 cal BCE"),
    ):
        result.append(
            AdnaProjectSampleMasterRow(
                species_latin_name="Ovis aries",
                species_common_name="sheep",
                project_accession="PRJEB41594",
                repo_stable_sample_id=f"prjeb41594:{accession.lower()}",
                archive_native_sample_id=accession,
                paper_native_sample_label=alias,
                supplementary_table_sample_label="",
                preferred_sample_label=alias,
                sample_basis="archive_project_sample_accession_anchor",
                sample_evidence_status="archive_native",
                sample_lineage_path="source.xml",
                sample_lineage_locator=accession,
                sample_lineage_excerpt=alias,
                sample_identity_resolution="final",
                sample_ambiguity_note="",
                locality_text="Obishir V",
                political_entity="Kyrgyzstan",
                latitude_text="",
                longitude_text="",
                chronology_text=date,
                chronology_dating_basis="radiocarbon",
                chronology_evidence_class="direct_radiocarbon_date" if date else "",
                chronology_precision_posture="sample_precise_interval" if date else "",
            )
        )
    return tuple(result)


@pytest.fixture
def specimen_rows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[AdnaProjectSampleChronologyRow, ...]:
    monkeypatch.setattr(rows, "build_project_sample_master_rows", lambda *_: _masters())
    monkeypatch.setattr(rows, "resolve_project_site_evidence", lambda *_: ())
    return rows.build_project_sample_chronology_rows(tmp_path, "PRJEB41594")


@pytest.mark.parametrize(
    "accession",
    [
        "SAMEA8022720",
        "SAMEA8022721",
        "SAMEA8022722",
        "SAMEA8022723",
        "OB20-04",
        "unknown",
    ],
)
def test_caution_requires_the_exact_source_accession(accession: str) -> None:
    assert obishir_chronology_caution(accession) == ""


def test_one_source_caution_preserves_all_dating_fields(
    specimen_rows: tuple[AdnaProjectSampleChronologyRow, ...],
) -> None:
    assert len(specimen_rows) == 5
    cautioned = [row for row in specimen_rows if row.chronology_conflict_note]
    assert len(cautioned) == 1
    row = cautioned[0]
    assert row.repo_stable_sample_id == "prjeb41594:samea8022724"
    assert row.chronology_text == "3003-2701 cal BCE"
    assert (row.time_start_bp, row.time_end_bp, row.time_mean_bp) == (4650, 4952, 4801)
    assert row.chronology_strength == "sample_owned_interval"
    assert row.chronology_normalization_status == "normalized_interval"
    assert row.chronology_evidence_class == "direct_radiocarbon_date"
    assert row.chronology_precision_posture == "sample_precise_interval"
    assert row.dating_basis == "radiocarbon"
    assert "AA-114607" in row.chronology_conflict_note
    assert "stratigraphically inconsistent" in row.review_note
    assert sum(row.chronology_strength == "unresolved" for row in specimen_rows) == 2


def test_caution_reaches_existing_attention_conflict_and_temporal_consumers(
    specimen_rows: tuple[AdnaProjectSampleChronologyRow, ...],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = next(
        p
        for p in build_archive_project_catalog()
        if p.project_accession == "PRJEB41594"
    )
    monkeypatch.setattr(audits, "build_archive_project_catalog", lambda: (project,))
    monkeypatch.setattr(
        audits, "build_project_sample_chronology_rows", lambda *_: specimen_rows
    )
    conflicts = audits.build_sample_chronology_conflict_ledger(tmp_path)
    assert [row["repo_stable_sample_id"] for row in conflicts] == [
        "prjeb41594:samea8022724"
    ]
    row = specimen_rows[-1]
    assert audits._row_requires_attention(row)
    assert not audits._row_requires_attention(specimen_rows[1])
    assert _uncertainty_note_for(row) == row.chronology_conflict_note
    semantics = _temporal_semantics_for_chronology_row(row)
    assert semantics["comparison_note"] == row.chronology_conflict_note
    assert semantics["comparability_posture"] == "numeric_interval"
    provenance = audits.build_sample_chronology_provenance_rows(tmp_path)
    packet = next(
        p for p in provenance if p["repo_stable_sample_id"] == row.repo_stable_sample_id
    )
    assert packet["uncertainty_note"] == row.chronology_conflict_note
    assert packet["temporal_semantics"] == semantics


def test_existing_publication_gate_keeps_its_conflict_consequence(
    specimen_rows: tuple[AdnaProjectSampleChronologyRow, ...],
) -> None:
    row = specimen_rows[-1]
    assert not _chronology_row_blocks_publication(
        replace(row, chronology_conflict_note="").as_dict()
    )
    assert _chronology_row_blocks_publication(row.as_dict())


def test_source_caution_does_not_overwrite_existing_context_conflict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(rows, "build_project_sample_master_rows", lambda *_: _masters())
    site = AdnaSiteEvidenceRecord(
        project_accession="PRJEB41594",
        species_latin_name="Ovis aries",
        species_common_name="sheep",
        site_label="Obishir V",
        political_entity="Kyrgyzstan",
        source_artifact_path="site.json",
        source_artifact_kind="context",
        source_locator="site",
        exact_source_text="different project age",
        source_support_status="source_context",
        chronology_text="1000-900 cal BCE",
    )
    monkeypatch.setattr(rows, "resolve_project_site_evidence", lambda *_: (site,))
    row = rows.build_project_sample_chronology_rows(tmp_path, "PRJEB41594")[-1]
    assert "project" in row.chronology_conflict_note
    assert "stratigraphically inconsistent" in row.chronology_conflict_note
    assert "conflicts with the project-level context row" in row.review_note
    assert (row.time_start_bp, row.time_end_bp) == (4650, 4952)


def test_warning_is_not_inferred_from_a_reused_accession_in_another_project(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(rows, "build_project_sample_master_rows", lambda *_: _masters())
    monkeypatch.setattr(rows, "resolve_project_site_evidence", lambda *_: ())
    other = rows.build_project_sample_chronology_rows(tmp_path, "PRJEB19970")
    assert all(not row.chronology_conflict_note for row in other)
