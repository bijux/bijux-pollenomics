"""Tests for complete pig workbook-to-archive source reconciliation."""

from __future__ import annotations

from collections import Counter

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.pig_panel import (
    build_pig_panel_join_audit,
)

from .support import (
    ARCHIVE_SOURCE_PATH,
    MODERN_WORKBOOK_SOURCE_PATH,
    WORKBOOK_SOURCE_PATH,
    governed_inputs,
)

pytestmark = pytest.mark.generated_artifacts


def _audit():  # type: ignore[no-untyped-def]
    ancient_rows, modern_rows, archive_text = governed_inputs()
    return build_pig_panel_join_audit(
        source_path=WORKBOOK_SOURCE_PATH,
        rows=ancient_rows,
        modern_source_path=MODERN_WORKBOOK_SOURCE_PATH,
        modern_rows=modern_rows,
        archive_source_path=ARCHIVE_SOURCE_PATH,
        archive_text=archive_text,
    )


def test_audit_reconciles_the_complete_archive_denominator() -> None:
    audit = _audit()

    assert len(audit) == 343
    assert len({row.archive_native_sample_id for row in audit}) == 343
    assert len({row.sample_label for row in audit}) == 343
    assert Counter(row.source_sample_kind for row in audit) == {
        "ancient_or_archaeological": 320,
        "modern": 23,
    }
    ancient = [
        row for row in audit if row.source_sample_kind == "ancient_or_archaeological"
    ]
    modern = [row for row in audit if row.source_sample_kind == "modern"]
    assert all(row.locality_text and row.political_entity for row in ancient)
    assert all(not row.locality_text and not row.political_entity for row in modern)
    assert sum(row.source_mean_age_is_numeric for row in ancient) == 306
    assert sum(not row.source_mean_age_is_numeric for row in ancient) == 14


def test_archive_accession_cannot_alias_distinct_labels_across_runs() -> None:
    ancient_rows, modern_rows, archive_text = governed_inputs()
    lines = archive_text.splitlines()
    header = lines[0].split("\t")
    indexes = {name: header.index(name) for name in ("run_accession", "submitted_ftp")}
    aa014 = next(line.split("\t") for line in lines[1:] if "AA014_" in line)
    aa014[indexes["run_accession"]] = "ERR_ALIAS_REVIEW"
    aa014[indexes["submitted_ftp"]] = aa014[indexes["submitted_ftp"]].replace(
        "AA014_", "AA013_"
    )
    aliased_archive = "\n".join((*lines, "\t".join(aa014)))

    with pytest.raises(ValueError, match="map to multiple ancient labels"):
        build_pig_panel_join_audit(
            source_path=WORKBOOK_SOURCE_PATH,
            rows=ancient_rows,
            modern_source_path=MODERN_WORKBOOK_SOURCE_PATH,
            modern_rows=modern_rows,
            archive_source_path=ARCHIVE_SOURCE_PATH,
            archive_text=aliased_archive,
        )


def test_modern_id_cannot_alias_distinct_archive_accessions() -> None:
    ancient_rows, modern_rows, archive_text = governed_inputs()
    mutable_modern_rows = [list(row) for row in modern_rows]
    alias_index = next(
        index
        for index, row in enumerate(mutable_modern_rows)
        if len(row) > 4 and row[4] == "SAMEA5772909"
    )
    mutable_modern_rows[alias_index][0] = "HA20U06"

    with pytest.raises(
        ValueError, match="modern IDs map to multiple archive accessions"
    ):
        build_pig_panel_join_audit(
            source_path=WORKBOOK_SOURCE_PATH,
            rows=ancient_rows,
            modern_source_path=MODERN_WORKBOOK_SOURCE_PATH,
            modern_rows=tuple(tuple(row) for row in mutable_modern_rows),
            archive_source_path=ARCHIVE_SOURCE_PATH,
            archive_text=archive_text,
        )


def test_archive_run_cannot_belong_to_distinct_sample_accessions() -> None:
    ancient_rows, modern_rows, archive_text = governed_inputs()
    lines = archive_text.splitlines()
    header = lines[0].split("\t")
    run_index = header.index("run_accession")
    mutated_lines = []
    for line in lines:
        columns = line.split("\t")
        if columns[run_index] == "ERR2985951":
            columns[run_index] = "ERR2985949"
        mutated_lines.append("\t".join(columns))

    with pytest.raises(ValueError, match="ERR2985949 maps to multiple sample"):
        build_pig_panel_join_audit(
            source_path=WORKBOOK_SOURCE_PATH,
            rows=ancient_rows,
            modern_source_path=MODERN_WORKBOOK_SOURCE_PATH,
            modern_rows=modern_rows,
            archive_source_path=ARCHIVE_SOURCE_PATH,
            archive_text="\n".join(mutated_lines),
        )


def test_source_status_partitions_do_not_widen_domesticated_admission() -> None:
    audit = _audit()

    assert Counter(row.domestication_status for row in audit) == {
        "Domestic": 121,
        "Wild": 85,
        "Unknown": 109,
        "domestic || domestic || domestic": 3,
        "NA || NA || NA": 1,
        "Unknown || Domestic || Domestic": 1,
        "not_reported_in_domestication_status_fields": 23,
    }
    assert Counter(row.disposition for row in audit) == {
        "admitted_domesticated_core": 2,
        "excluded_unreviewed_domesticated_scope": 142,
        "excluded_wild": 85,
        "excluded_domestication_unknown": 109,
        "excluded_noncanonical_domestication_status": 5,
    }
    admitted = [row for row in audit if row.disposition == "admitted_domesticated_core"]
    assert {row.sample_label for row in admitted} == {"AA015", "AA016"}


def test_raw_chronology_fields_remain_source_owned_and_noncomparable() -> None:
    audit = _audit()
    by_label = {row.sample_label: row for row in audit}

    radiocarbon = by_label["BLT025"]
    assert (
        radiocarbon.radiocarbon_lab_number,
        radiocarbon.uncalibrated_date_text,
        radiocarbon.uncalibrated_error_text,
        radiocarbon.calibrated_from_bp_text,
        radiocarbon.calibrated_to_bp_text,
        radiocarbon.source_age_text,
        radiocarbon.source_mean_age_text,
    ) == ("OxA-24689", "8000", "40", "9009", "8717", "Late Mesolithic", "8898")
    assert radiocarbon.chronology_text == ""
    assert (
        radiocarbon.chronology_disposition
        == "refused_context_only_unresolved_age_semantics"
    )

    indirect = by_label["AA129"]
    assert "Four C14 dates for this layer" in indirect.source_age_text
    assert indirect.source_mean_age_text == "-"
    assert indirect.chronology_disposition == "unresolved_missing_source_mean"
    assert indirect.chronology_text == ""

    admitted = {
        row.sample_label: row.chronology_text for row in audit if row.chronology_text
    }
    assert admitted == {"AA015": "4700 BP", "AA016": "1000 BP"}


def test_source_mean_precision_is_preserved_without_canonical_admission() -> None:
    ancient_rows, modern_rows, archive_text = governed_inputs()
    mutable_rows = [list(row) for row in ancient_rows]
    aa014_index = next(
        index for index, row in enumerate(mutable_rows) if row and row[0] == "AA014"
    )
    mutable_rows[aa014_index][28] = "6950.5"

    audit = build_pig_panel_join_audit(
        source_path=WORKBOOK_SOURCE_PATH,
        rows=tuple(tuple(row) for row in mutable_rows),
        modern_source_path=MODERN_WORKBOOK_SOURCE_PATH,
        modern_rows=modern_rows,
        archive_source_path=ARCHIVE_SOURCE_PATH,
        archive_text=archive_text,
    )
    aa014 = next(row for row in audit if row.sample_label == "AA014")

    assert aa014.source_mean_age_text == "6950.5"
    assert aa014.source_mean_age_is_numeric
    assert aa014.chronology_text == ""


def test_modern_rows_preserve_exact_accession_identity_without_locality_or_date() -> (
    None
):
    audit = _audit()
    by_accession = {row.archive_native_sample_id: row for row in audit}

    assert (
        by_accession["SAMEA5772927"].sample_label,
        by_accession["SAMEA5772927"].modern_population,
        by_accession["SAMEA5772927"].modern_breed_or_country,
        by_accession["SAMEA5772927"].workbook_source_locator,
    ) == ("HA20U06", "EUD", "Hampshire", "Sheet1!row4")
    assert (
        by_accession["SAMEA5772909"].sample_label,
        by_accession["SAMEA5772909"].modern_breed_or_country,
        by_accession["SAMEA5772909"].workbook_source_locator,
    ) == ("LR24M21", "Landrace2", "Sheet1!row9")
    modern = [row for row in audit if row.source_sample_kind == "modern"]
    assert all(
        row.chronology_disposition == "unresolved_not_reported" for row in modern
    )
    assert all(not row.chronology_text for row in modern)


def test_audit_serialization_keeps_both_source_surfaces_and_raw_fields() -> None:
    audit_row = next(row for row in _audit() if row.sample_label == "AA015")
    payload = audit_row.as_dict()

    assert payload["workbook_source_path"] == WORKBOOK_SOURCE_PATH
    assert payload["workbook_source_locator"] == "Sheet1!row1212"
    assert payload["archive_source_path"] == ARCHIVE_SOURCE_PATH
    assert payload["source_age_text"] == "2800-2600 BC"
    assert payload["source_mean_age_text"] == "4700"
    assert payload["chronology_text"] == "4700 BP"
    assert payload["domestication_status"] == "Domestic"
