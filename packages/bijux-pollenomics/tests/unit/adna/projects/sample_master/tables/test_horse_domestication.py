"""Protect the primary Berel identity and conflicting horse cohort scopes."""

from __future__ import annotations

import csv
from dataclasses import replace
from io import StringIO
import json

import pytest

from bijux_pollenomics.adna.projects.evidence import sites as site_evidence
from bijux_pollenomics.adna.projects.evidence.chronology import (
    build_project_sample_chronology_rows,
)
from bijux_pollenomics.adna.projects.registry.localities import (
    resolve_project_locality_leads,
)
from bijux_pollenomics.adna.projects.registry.samples import (
    build_species_curated_sample_rows,
)
from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master,
)
from bijux_pollenomics.adna.projects.sample_master.tables.horse_domestication import (
    HORSE_DOMESTICATION_ARCHIVE,
    _berel_archive_locator,
)
from bijux_pollenomics.adna.workflow.normalization import (
    build_species_normalization_bundle,
    localities,
)
from bijux_pollenomics.adna.workflow.normalization.samples import (
    _sample_record_is_admissible,
)
from bijux_pollenomics.adna.workflow.source_artifacts import read_source_artifact_text
from tests.support.repository import REPOSITORY_ROOT


def _archive_rows() -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(
        StringIO(
            read_source_artifact_text(REPOSITORY_ROOT / HORSE_DOMESTICATION_ARCHIVE)
        ),
        delimiter="\t",
    )
    assert reader.fieldnames is not None
    return reader.fieldnames, list(reader)


def _archive_text(headers: list[str], rows: list[dict[str, str]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=headers, delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def test_primary_identity_adds_one_owner_without_rewriting_comparators() -> None:
    data = REPOSITORY_ROOT / "data"
    master = build_project_sample_master(data, "PRJEB19970")
    previous = json.loads(
        (
            data
            / "adna/governance/source_library/projects/PRJEB19970/sample_master.json"
        ).read_text()
    )["rows"]
    current = {row.repo_stable_sample_id: row.as_dict() for row in master.rows}
    for row in previous:
        if row["preferred_sample_label"] != "BER11_L":
            assert current[row["repo_stable_sample_id"]] == row
    assert len(current) == 16
    assert master.expected_sample_count is None
    assert master.unresolved_sample_count is None
    assert master.expected_sample_count_status == "source_population_unresolved"
    source = current["prjeb19970:samea103910520"]
    assert source["preferred_sample_label"] == "BER11_L"
    assert source["archive_native_sample_id"] == "SAMEA103910520"
    assert source["archive_native_experiment_id"] == ""
    assert source["source_native_scientific_name"] == "Equus caballus"
    assert source["sample_evidence_status"] == "direct_table_extracted"
    assert source["chronology_text"] == "2,300 yBP"
    assert source["political_entity"] == "Kazakhstan"
    assert "PDF pp.16–17" in source["sample_lineage_locator"]
    assert source["latitude_text"] == source["longitude_text"] == ""
    modern = {"Connemara_0004A", "Somali_0226A"}
    assert modern <= {row.preferred_sample_label for row in master.rows}
    chronology = next(
        row
        for row in build_project_sample_chronology_rows(data, "PRJEB19970")
        if row.preferred_sample_label == "BER11_L"
    )
    assert chronology.time_start_bp is None
    assert chronology.time_end_bp is None
    assert chronology.time_mean_bp is None
    assert chronology.chronology_evidence_class == "unresolved"


def test_table_identity_retains_missing_coordinates_and_numeric_dating() -> None:
    assert any(
        lead.locality_text == "Berel'" and lead.political_entity == "Kazakhstan"
        for lead in resolve_project_locality_leads("PRJEB19970")
    )
    row = next(
        row
        for row in build_species_curated_sample_rows("horse")
        if row.stable_sample_id == "prjeb19970:samea103910520"
    )
    assert _sample_record_is_admissible(row)
    assert not _sample_record_is_admissible(
        replace(row, sample_evidence_status="pdf_text_extracted")
    )
    assert row.sample_evidence_status == "direct_table_extracted"
    assert row.site_label == "Berel'"
    assert row.political_entity == "Kazakhstan"
    assert row.latitude_text == row.longitude_text == ""
    assert row.time_start_bp is None and row.time_end_bp is None
    assert row.inclusion_status == "sample_context_blocked"


def test_primary_country_binding_joins_only_its_named_locality() -> None:
    bundle = build_species_normalization_bundle("horse")
    berel = [
        row
        for row in bundle.locality_records
        if row.identity.stable_token.startswith(
            "equus_caballus:locality:prjeb19970:berel"
        )
    ]
    assert len(berel) == 1
    known = berel[0]
    assert known.identity.political_entity == "Kazakhstan"
    assert known.sample_count == len(known.sample_chronologies) == 11
    assert known.sample_ids.count("prjeb19970:samea103910520") == 1
    primary = next(
        packet
        for packet in known.sample_chronologies
        if packet.sample_id == "prjeb19970:samea103910520"
    )
    assert primary.chronology.time_mean_bp is None
    assert "PDF pp.16–17" in primary.provenance_locator


def test_same_locality_name_does_not_merge_unknown_and_known_countries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = build_species_normalization_bundle("horse")
    curated = localities.build_species_curated_sample_rows("horse")
    rows = tuple(
        replace(row, political_entity=None)
        if row.stable_sample_id == "prjeb19970:samea103910520"
        else row
        for row in curated
    )
    leads = localities.build_species_project_locality_leads(
        tuple(summary.project_accession for summary in bundle.project_summaries)
    )
    known_lead = next(
        lead
        for lead in leads
        if lead.project_accession == "PRJEB19970"
        and lead.locality_text == "Berel'"
        and lead.political_entity == "Kazakhstan"
    )
    monkeypatch.setattr(localities, "build_species_curated_sample_rows", lambda _: rows)
    monkeypatch.setattr(
        localities,
        "build_species_project_locality_leads",
        lambda _: (*leads, replace(known_lead, political_entity="")),
    )
    records, _ = localities.build_species_project_locality_records(
        "horse",
        bundle.project_summaries,
        sample_records=bundle.sample_records,
    )
    berel = {
        row.identity.political_entity: row
        for row in records
        if row.identity.stable_token.startswith(
            "equus_caballus:locality:prjeb19970:berel"
        )
    }
    assert set(berel) == {"", "Kazakhstan"}
    assert berel[""].sample_ids == ("prjeb19970:samea103910520",)
    assert berel["Kazakhstan"].sample_count == 10
    assert set(berel[""].sample_ids).isdisjoint(berel["Kazakhstan"].sample_ids)


def test_primary_table_evidence_keeps_its_article_archive_kind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    primary = next(
        row
        for row in build_project_sample_master(
            REPOSITORY_ROOT / "data", "PRJEB19970"
        ).rows
        if row.preferred_sample_label == "BER11_L"
    )
    monkeypatch.setattr(
        site_evidence, "build_project_sample_master_rows", lambda *_: (primary,)
    )
    (evidence,) = site_evidence._direct_sample_site_rows("PRJEB19970")
    assert evidence.source_artifact_kind == "article_or_archive_text"
    assert "aam5298_librado.sm.pdf" in evidence.source_artifact_path
    assert "archive_metadata.html" in evidence.source_artifact_path


@pytest.mark.parametrize(
    "change",
    [
        "other_biosample",
        "other_project",
        "other_taxon",
        "label_neighbour",
        "mixed_filenames",
        "duplicate_run",
        "missing_bam",
    ],
)
def test_archive_join_refuses_conflicting_or_incomplete_evidence(change: str) -> None:
    headers, rows = _archive_rows()
    target = next(row for row in rows if row["run_accession"] == "ERR1885588")
    if change == "other_biosample":
        target["sample_accession"] = "SAMEA103910521"
    elif change == "other_project":
        target["study_accession"] = "PRJEB31613"
    elif change == "other_taxon":
        target["scientific_name"] = "Equus asinus"
    elif change == "label_neighbour":
        target["submitted_ftp"] = target["submitted_ftp"].replace(
            "BER11_L__", "BER11_L2__"
        )
    elif change == "mixed_filenames":
        target["submitted_ftp"] += ";ftp.example/BER12_M.fastq.gz"
    elif change == "duplicate_run":
        rows.append(dict(target))
    elif change == "missing_bam":
        rows = [row for row in rows if row["run_accession"] != "ERR1892229"]
    with pytest.raises(ValueError, match="PRJEB19970"):
        _berel_archive_locator(_archive_text(headers, rows))


def test_archive_join_includes_bam_and_fastq_without_counting_files_as_samples() -> (
    None
):
    headers, rows = _archive_rows()
    locator = _berel_archive_locator(_archive_text(headers, rows))
    assert locator.startswith("sample_accession:SAMEA103910520;")
    assert len(locator.split("tsv_lines:")[1].split(",")) == 13
    assert len({row["sample_accession"] for row in rows}) == 14
