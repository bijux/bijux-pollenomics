"""Protect the primary Berel identity and conflicting horse cohort scopes."""

from __future__ import annotations

import csv
from io import StringIO
import json

import pytest

from bijux_pollenomics.adna.projects.evidence.chronology import (
    build_project_sample_chronology_rows,
)
from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master,
)
from bijux_pollenomics.adna.projects.sample_master.tables.horse_domestication import (
    HORSE_DOMESTICATION_ARCHIVE,
    _berel_archive_locator,
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
    assert source["chronology_text"] == "2,300 yBP"
    assert (
        source["political_entity"]
        == source["latitude_text"]
        == source["longitude_text"]
        == ""
    )
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
