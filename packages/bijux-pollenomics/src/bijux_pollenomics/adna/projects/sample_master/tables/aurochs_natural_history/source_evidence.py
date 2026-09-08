"""Fail-closed extraction of the pinned PRJEB75467 source records."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from typing import Final

from .evidence import (
    ARCHIVE_IDENTITIES,
    AUROCHS_NATURAL_HISTORY_SHEET,
    AUROCHS_PROGENITOR_POPULATION_LABELS,
    CHRONOLOGY_UNAVAILABLE_SAMPLE_LABELS,
    PAPER_ONLY_SAMPLE_LABEL,
    SPECIMEN_ID_UNAVAILABLE_SAMPLE_LABELS,
)
from .field_validation import _cell, _required, _source_coordinate_pair
from .source_values import (
    _basename_has_label,
    _parse_calibrated_bp_interval,
    _parse_mitochondrial_date,
    _submitted_basenames,
)

_EXPECTED_WORKBOOK_HEADER: Final = (
    "Analysis ID",
    "Original specimen ID",
    "Specimen steward institution(s)",
    "Sampled element",
    "Country",
    "Locality",
    "Latitude (proximal to site)",
    "Longitude (proximal to site)",
    "Date uncal BP",
    "Radiocarbon date ID",
    "Date BC/AD (OxCal 4.4, IntCal 20)",
    "Date cal BP (OxCal 4.4, IntCal 20)",
    "Associated culture",
    "Library type",
    "UDG treatment",
    "Endogenous DNA content (%)",
    "Coverage (X)",
    "Mitochondrial coverage (X)",
    "C>T at 1st CpG pos",
    "Species",
    "Sex",
    "Mitochondrial haplogroup",
    "mtDNA date BP (BEAST)",
    "Analysis date given",
    "Analysis population label",
    "AdmixtureGraph/TreeMix/D Statistic group",
    "MSMC Cross Population Analysis group",
    "Fst Sliding Windows group",
)
_EXPECTED_ARCHIVE_HEADER: Final = (
    "run_accession",
    "study_accession",
    "sample_accession",
    "experiment_accession",
    "tax_id",
    "scientific_name",
    "library_layout",
    "library_source",
    "library_strategy",
    "instrument_model",
    "base_count",
    "read_count",
    "fastq_bytes",
    "fastq_ftp",
    "submitted_ftp",
    "sra_ftp",
)


@dataclass(frozen=True)
class AurochsWorkbookEvidence:
    """One exact row from the governed natural-history workbook."""

    sample_label: str
    row_number: int
    original_specimen_id: str
    steward_institution: str
    sampled_element: str
    political_entity: str
    locality_text: str
    latitude_text: str
    longitude_text: str
    uncalibrated_date_text: str
    radiocarbon_date_id: str
    calibrated_date_text: str
    source_bp_text: str
    associated_culture: str
    library_type: str
    udg_treatment: str
    coverage_text: str
    source_native_scientific_name: str
    mitochondrial_date_text: str
    analysis_mean_text: str
    mean_bp: float | None
    younger_bp: int | None
    older_bp: int | None
    population_label: str
    chronology_kind: str

    @property
    def source_locator(self) -> str:
        """Return an executable spreadsheet cell-range locator."""
        return f"{AUROCHS_NATURAL_HISTORY_SHEET}!A{self.row_number}:Y{self.row_number}"


@dataclass(frozen=True)
class AurochsArchiveEvidence:
    """Archive-native sequencing evidence for one explicit BioSample join."""

    sample_label: str
    sample_accession: str
    line_numbers: tuple[int, ...]
    run_accessions: tuple[str, ...]
    experiment_accessions: tuple[str, ...]
    submitted_basenames: tuple[str, ...]
    source_native_tax_id: str
    source_native_scientific_name: str

    @property
    def source_locator(self) -> str:
        """Return stable line and identity selectors into the pinned TSV payload."""
        lines = ",".join(str(value) for value in self.line_numbers)
        return (
            f"sample_accession:{self.sample_accession};"
            f"submitted_filename_prefix:{self.sample_label};tsv_lines:{lines}"
        )


def _chronology_fields(
    row: tuple[str, ...], label: str
) -> tuple[int | None, int | None, float | None, str]:
    """Parse source chronology without inventing values for an undated specimen."""
    chronology_cells = tuple(_cell(row, index) for index in (8, 9, 10, 11, 22, 23))
    if label in CHRONOLOGY_UNAVAILABLE_SAMPLE_LABELS:
        if any(chronology_cells):
            raise ValueError(
                f"PRJEB75467 {label} chronology-unavailable contract drift"
            )
        return None, None, None, "source_chronology_unavailable"
    if _cell(row, 11):
        younger, older = _parse_calibrated_bp_interval(_cell(row, 11), label)
        chronology_kind = "calibrated_radiocarbon_interval"
        if not _cell(row, 8) or not _cell(row, 9) or not _cell(row, 10):
            raise ValueError(f"PRJEB75467 {label} radiocarbon evidence incomplete")
        modeled_mean = None
    else:
        younger, older, modeled_mean = _parse_mitochondrial_date(_cell(row, 22), label)
        chronology_kind = "mitochondrial_beast_interval"
    try:
        mean_bp = float(_cell(row, 23))
    except ValueError as error:
        raise ValueError(f"PRJEB75467 {label} analysis mean is invalid") from error
    if chronology_kind == "calibrated_radiocarbon_interval":
        if mean_bp != (younger + older) / 2:
            raise ValueError(f"PRJEB75467 {label} calibrated mean drift")
    elif mean_bp != modeled_mean:
        raise ValueError(f"PRJEB75467 {label} mitochondrial mean drift")
    return younger, older, mean_bp, chronology_kind


def _parse_workbook_evidence(
    rows: tuple[tuple[str, ...], ...],
) -> dict[str, AurochsWorkbookEvidence]:
    """Extract the explicit governed subset and reject identity/source drift."""
    if not rows or tuple(rows[0][: len(_EXPECTED_WORKBOOK_HEADER)]) != (
        _EXPECTED_WORKBOOK_HEADER
    ):
        raise ValueError("PRJEB75467 Supplementary Data 1 header drift")
    expected_labels = {
        *(identity.sample_label for identity in ARCHIVE_IDENTITIES),
        PAPER_ONLY_SAMPLE_LABEL,
    }
    indexed: dict[str, list[tuple[int, tuple[str, ...]]]] = {
        label: [] for label in expected_labels
    }
    for row_number, row in enumerate(rows[1:], start=2):
        label = _cell(row, 0)
        if label in indexed:
            indexed[label].append((row_number, row))
    malformed = {
        label: len(matches) for label, matches in indexed.items() if len(matches) != 1
    }
    if malformed:
        raise ValueError(
            f"PRJEB75467 workbook identities must occur exactly once: {malformed}"
        )

    evidence: dict[str, AurochsWorkbookEvidence] = {}
    for label, matches in indexed.items():
        row_number, row = matches[0]
        species_name = _cell(row, 19)
        population_label = _required(_cell(row, 24), label, "population label")
        if species_name != "Bos primigenius":
            raise ValueError(f"PRJEB75467 {label} source taxonomy drift")
        if population_label not in AUROCHS_PROGENITOR_POPULATION_LABELS:
            raise ValueError(f"PRJEB75467 {label} progenitor-population evidence drift")
        latitude, longitude = _source_coordinate_pair(
            _cell(row, 6), _cell(row, 7), label=label
        )
        younger, older, mean_bp, chronology_kind = _chronology_fields(row, label)
        original_specimen_id = _cell(row, 1)
        if label in SPECIMEN_ID_UNAVAILABLE_SAMPLE_LABELS:
            if original_specimen_id:
                raise ValueError(
                    f"PRJEB75467 {label} specimen-ID-unavailable contract drift"
                )
        else:
            original_specimen_id = _required(original_specimen_id, label, "specimen ID")
        evidence[label] = AurochsWorkbookEvidence(
            sample_label=label,
            row_number=row_number,
            original_specimen_id=original_specimen_id,
            steward_institution=_required(_cell(row, 2), label, "steward institution"),
            sampled_element=_required(_cell(row, 3), label, "sampled element"),
            political_entity=_required(_cell(row, 4), label, "country"),
            locality_text=_required(_cell(row, 5), label, "locality"),
            latitude_text=latitude,
            longitude_text=longitude,
            uncalibrated_date_text=_cell(row, 8),
            radiocarbon_date_id=_cell(row, 9),
            calibrated_date_text=_cell(row, 10),
            source_bp_text=_cell(row, 11) or _cell(row, 22),
            associated_culture=_cell(row, 12),
            library_type=_required(_cell(row, 13), label, "library type"),
            udg_treatment=_required(_cell(row, 14), label, "UDG treatment"),
            coverage_text=_required(_cell(row, 16), label, "genomic coverage"),
            source_native_scientific_name=species_name,
            mitochondrial_date_text=_cell(row, 22),
            analysis_mean_text=_cell(row, 23),
            mean_bp=mean_bp,
            younger_bp=younger,
            older_bp=older,
            population_label=population_label,
            chronology_kind=chronology_kind,
        )
    fre1 = evidence[PAPER_ONLY_SAMPLE_LABEL]
    if fre1.udg_treatment != "No" or float(fre1.coverage_text) != 0.0:
        raise ValueError("PRJEB75467 Fre1 paper-only sequencing evidence drift")
    return evidence


def _parse_archive_evidence(archive_text: str) -> dict[str, AurochsArchiveEvidence]:
    """Resolve only explicit, globally unique BioSample-to-filename joins."""
    reader = csv.DictReader(StringIO(archive_text), delimiter="\t")
    if tuple(reader.fieldnames or ()) != _EXPECTED_ARCHIVE_HEADER:
        raise ValueError("PRJEB75467 archive header drift")
    expected = {
        identity.sample_label: identity.sample_accession
        for identity in ARCHIVE_IDENTITIES
    }
    archive_rows = tuple(
        (line_number, row, _submitted_basenames(row["submitted_ftp"]))
        for line_number, row in enumerate(reader, start=2)
    )
    _validate_archive_accession_provenance(archive_rows)
    labels = (*expected, PAPER_ONLY_SAMPLE_LABEL)
    claimed_labels_by_line: dict[int, tuple[str, ...]] = {}
    fre1_matches: list[int] = []
    for line_number, _, basenames in archive_rows:
        matched = tuple(
            label
            for label in labels
            if any(_basename_has_label(name, label) for name in basenames)
        )
        claimed_labels_by_line[line_number] = matched
        if len(matched) > 1:
            raise ValueError(
                f"PRJEB75467 archive line {line_number} has cross-contaminated labels"
            )
        if matched == (PAPER_ONLY_SAMPLE_LABEL,):
            fre1_matches.append(line_number)
    if fre1_matches:
        raise ValueError(
            "PRJEB75467 archive unexpectedly assigns Fre1 sequencing identity"
        )

    evidence: dict[str, AurochsArchiveEvidence] = {}
    for label, expected_accession in expected.items():
        matches = tuple(
            item
            for item in archive_rows
            if item[1]["sample_accession"] == expected_accession
        )
        if not matches:
            raise ValueError(f"PRJEB75467 archive join missing for {label}")
        mislabeled_lines = tuple(
            line_number
            for line_number, _, basenames in matches
            if not basenames
            or any(not _basename_has_label(name, label) for name in basenames)
        )
        if mislabeled_lines:
            raise ValueError(
                f"PRJEB75467 archive filename identity drift for {label}: "
                f"lines {mislabeled_lines}"
            )
        foreign_claims = tuple(
            line_number
            for line_number, row, _ in archive_rows
            if row["sample_accession"] != expected_accession
            and label in claimed_labels_by_line[line_number]
        )
        if foreign_claims:
            raise ValueError(
                f"PRJEB75467 archive accession join drift for {label}: "
                f"foreign lines {foreign_claims}"
            )
        if any(row["study_accession"] != "PRJEB75467" for _, row, _ in matches):
            raise ValueError(f"PRJEB75467 archive study join drift for {label}")
        taxa = {(row["tax_id"], row["scientific_name"]) for _, row, _ in matches}
        if taxa != {("9909", "Bos primigenius")}:
            raise ValueError(f"PRJEB75467 archive taxonomy drift for {label}: {taxa}")
        evidence[label] = AurochsArchiveEvidence(
            sample_label=label,
            sample_accession=expected_accession,
            line_numbers=tuple(line for line, _, _ in matches),
            run_accessions=tuple(
                sorted({row["run_accession"] for _, row, _ in matches})
            ),
            experiment_accessions=tuple(
                sorted({row["experiment_accession"] for _, row, _ in matches})
            ),
            submitted_basenames=tuple(
                sorted({name for _, _, names in matches for name in names})
            ),
            source_native_tax_id="9909",
            source_native_scientific_name="Bos primigenius",
        )
    accession_claims = [row.sample_accession for row in evidence.values()]
    if len(accession_claims) != len(set(accession_claims)):
        raise ValueError("PRJEB75467 archive joins reuse a BioSample accession")
    return evidence


def _validate_archive_accession_provenance(
    archive_rows: tuple[tuple[int, dict[str, str], tuple[str, ...]], ...],
) -> None:
    """Require globally unambiguous run and experiment ownership."""
    sample_by_identity: dict[tuple[str, str], str] = {}
    for line_number, row, _ in archive_rows:
        sample_accession = row["sample_accession"].strip()
        if not sample_accession:
            raise ValueError(
                f"PRJEB75467 archive sample_accession is blank at line {line_number}"
            )
        for field in ("run_accession", "experiment_accession"):
            identity = row[field].strip()
            if not identity:
                raise ValueError(
                    f"PRJEB75467 archive {field} is blank at line {line_number}"
                )
            key = (field, identity)
            prior_sample = sample_by_identity.setdefault(key, sample_accession)
            if prior_sample != sample_accession:
                raise ValueError(
                    f"PRJEB75467 archive {field} maps to multiple BioSamples: "
                    f"{identity} -> {prior_sample}, {sample_accession}"
                )


__all__ = [
    "AurochsArchiveEvidence",
    "AurochsWorkbookEvidence",
    "_parse_archive_evidence",
    "_parse_workbook_evidence",
]
