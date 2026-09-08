"""Adversarial tests for fail-closed aurochs evidence joins."""

from __future__ import annotations

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.aurochs_natural_history import (
    AUROCHS_NATURAL_HISTORY_WORKBOOK_SHA256,
    _parse_archive_evidence,
    _parse_workbook_evidence,
    _reconcile_aurochs_natural_history,
)

from .support import governed_inputs

pytestmark = pytest.mark.generated_artifacts


def _replace_archive_field(
    archive_text: str,
    *,
    target_sample: str,
    field: str,
    value: str,
) -> str:
    lines = archive_text.splitlines()
    header = lines[0].split("\t")
    sample_index = header.index("sample_accession")
    field_index = header.index(field)
    for index, line in enumerate(lines[1:], start=1):
        cells = line.split("\t")
        if cells[sample_index] != target_sample:
            continue
        cells[field_index] = value
        lines[index] = "\t".join(cells)
        return "\n".join(lines)
    raise AssertionError(f"archive fixture has no row for {target_sample}")


def test_hash_drift_is_refused_before_scientific_parsing() -> None:
    workbook_rows, _, archive_text = governed_inputs()

    with pytest.raises(ValueError, match="workbook sha256 drift"):
        _reconcile_aurochs_natural_history(
            workbook_rows=workbook_rows,
            workbook_sha256="0" * 64,
            archive_text=archive_text,
        )
    with pytest.raises(ValueError, match="archive sha256 drift"):
        _reconcile_aurochs_natural_history(
            workbook_rows=workbook_rows,
            workbook_sha256=AUROCHS_NATURAL_HISTORY_WORKBOOK_SHA256,
            archive_text=f"{archive_text}\n",
        )


def test_missing_and_duplicate_workbook_identities_are_refused() -> None:
    workbook_rows, _, _ = governed_inputs()
    hjo1 = next(row for row in workbook_rows if row and row[0] == "Hjo1")

    with pytest.raises(ValueError, match="must occur exactly once"):
        _parse_workbook_evidence(
            tuple(row for row in workbook_rows if not row or row[0] != "Hjo1")
        )
    with pytest.raises(ValueError, match="must occur exactly once"):
        _parse_workbook_evidence((*workbook_rows, hjo1))


def test_accession_cross_join_and_fre1_archive_identity_are_refused() -> None:
    _, _, archive_text = governed_inputs()
    wrong_accession = archive_text.replace("SAMEA115574419", "SAMEA115574441", 1)
    with pytest.raises(ValueError, match="accession join drift for Hjo1"):
        _parse_archive_evidence(wrong_accession)

    fabricated_fre1 = archive_text.replace("Hjo1-", "Fre1-")
    with pytest.raises(ValueError, match="unexpectedly assigns Fre1"):
        _parse_archive_evidence(fabricated_fre1)


def test_mixed_labels_on_one_archive_row_are_refused() -> None:
    _, _, archive_text = governed_inputs()
    cross_contaminated = archive_text.replace(
        "Hjo1-AGACTCC-CGACCTG_R1.fastq.gz;",
        "Hjo1-AGACTCC-CGACCTG_R1.fastq.gz;Ska1-forged.fastq.gz;",
        1,
    )

    with pytest.raises(ValueError, match="cross-contaminated labels"):
        _parse_archive_evidence(cross_contaminated)


def test_every_run_for_an_accession_must_retain_its_sample_filename() -> None:
    _, _, archive_text = governed_inputs()
    mislabeled = archive_text.replace("Hjo1-", "unbound-", 2)

    with pytest.raises(ValueError, match="filename identity drift for Hjo1"):
        _parse_archive_evidence(mislabeled)


def test_domestic_population_drift_is_refused() -> None:
    workbook_rows, _, _ = governed_inputs()
    bed4_index = next(
        index for index, row in enumerate(workbook_rows) if row and row[0] == "Bed4"
    )
    bed4 = list(workbook_rows[bed4_index])
    bed4[24] = "Holocene Domestic Germany"
    altered = (
        *workbook_rows[:bed4_index],
        tuple(bed4),
        *workbook_rows[bed4_index + 1 :],
    )

    with pytest.raises(ValueError, match="progenitor-population evidence drift"):
        _parse_workbook_evidence(altered)


@pytest.mark.parametrize(
    "field",
    ("sample_accession", "run_accession", "experiment_accession"),
)
def test_blank_archive_accession_fields_are_refused_globally(field: str) -> None:
    _, _, archive_text = governed_inputs()
    altered = _replace_archive_field(
        archive_text,
        target_sample="SAMEA115574409",
        field=field,
        value="",
    )

    with pytest.raises(ValueError, match=rf"archive {field} is blank at line"):
        _parse_archive_evidence(altered)


@pytest.mark.parametrize(
    ("field", "reused_identity"),
    (
        ("run_accession", "ERR13302321"),
        ("experiment_accession", "ERX12673181"),
    ),
)
def test_archive_sequence_identities_cannot_cross_biosamples(
    field: str, reused_identity: str
) -> None:
    _, _, archive_text = governed_inputs()
    altered = _replace_archive_field(
        archive_text,
        target_sample="SAMEA115574441",
        field=field,
        value=reused_identity,
    )

    with pytest.raises(
        ValueError, match=rf"archive {field} maps to multiple BioSamples"
    ):
        _parse_archive_evidence(altered)
