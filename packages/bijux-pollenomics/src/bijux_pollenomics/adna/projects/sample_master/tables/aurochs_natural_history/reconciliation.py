"""Fail-closed workbook-to-archive reconciliation for Scandinavian aurochs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from hashlib import sha256
from io import StringIO
from pathlib import PurePosixPath
import re
from typing import Final

from bijux_pollenomics.adna.projects.sample_master.models import (
    AdnaProjectSampleMasterRow,
)
from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition

from .evidence import (
    ARCHIVE_IDENTITIES,
    AUROCHS_NATURAL_HISTORY_ARCHIVE_TEXT_SHA256,
    AUROCHS_NATURAL_HISTORY_PROJECT_ACCESSION,
    AUROCHS_NATURAL_HISTORY_SHEET,
    AUROCHS_NATURAL_HISTORY_WORKBOOK_SHA256,
    AUROCHS_WILD_POPULATION_LABEL,
    PAPER_ONLY_SAMPLE_LABEL,
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
_BP_INTERVAL_RE: Final = re.compile(r"(?P<older>\d+)-(?P<younger>\d+)")
_MITOCHONDRIAL_DATE_RE: Final = re.compile(
    r"(?P<mean>\d+(?:\.\d+)?) \((?P<younger>\d+)-(?P<older>\d+)\)"
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
    mean_bp: float
    younger_bp: int
    older_bp: int
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


@dataclass(frozen=True)
class AurochsNaturalHistoryReconciliationRow:
    """One joined sequence or explicitly refused paper-only aurochs identity."""

    workbook: AurochsWorkbookEvidence
    archive: AurochsArchiveEvidence | None
    reconciliation_status: str
    sequencing_status: str
    refusal_reason: str

    def to_sample_master_row(
        self,
        *,
        species: AdnaSpeciesDefinition,
        project: AdnaArchiveProject,
        workbook_source_path: str,
        archive_source_path: str,
    ) -> AdnaProjectSampleMasterRow:
        """Preserve source claims while refusing domestication or accession inference."""
        source = self.workbook
        archive = self.archive
        accession = "" if archive is None else archive.sample_accession
        chronology_basis = (
            "radiocarbon"
            if source.chronology_kind == "calibrated_radiocarbon_interval"
            else "mitochondrial_phylogenetic_model"
        )
        chronology_class = (
            "direct_radiocarbon_date"
            if source.chronology_kind == "calibrated_radiocarbon_interval"
            else "modeled_sample_date"
        )
        chronology_precision = (
            "sample_precise_interval"
            if source.chronology_kind == "calibrated_radiocarbon_interval"
            else "sample_approximate_or_modeled"
        )
        lineage_paths = [workbook_source_path]
        lineage_locators = [source.source_locator]
        if archive is not None:
            lineage_paths.append(archive_source_path)
            lineage_locators.append(archive.source_locator)
        excerpt_parts = (
            f"workbook sample {source.sample_label}",
            f"specimen {source.original_specimen_id}",
            f"locality {source.locality_text}, {source.political_entity}",
            f"source BP claim {source.source_bp_text}",
            f"canonical BP interval [{source.younger_bp}, {source.older_bp}]",
            f"published analysis mean {source.mean_bp:g} BP",
            f"source taxonomy {source.source_native_scientific_name}",
            f'population label "{source.population_label}"',
            "admitted only as explicit wild/progenitor context",
            self.refusal_reason,
        )
        return AdnaProjectSampleMasterRow(
            species_latin_name=species.latin_name,
            species_common_name=species.common_name,
            project_accession=project.project_accession,
            repo_stable_sample_id=(
                f"{project.project_accession}:{accession}".casefold()
                if accession
                else (
                    f"{project.project_accession}:supplement:{source.sample_label}"
                ).casefold()
            ),
            archive_native_sample_id=accession,
            paper_native_sample_label=source.sample_label,
            supplementary_table_sample_label=source.sample_label,
            preferred_sample_label=source.sample_label,
            sample_basis=(
                "supplementary_table_archive_primary_source_join"
                if archive is not None
                else "supplementary_table_paper_only_sequence_refusal"
            ),
            sample_evidence_status="direct_table_extracted",
            sample_lineage_path=" || ".join(lineage_paths),
            sample_lineage_locator=" || ".join(lineage_locators),
            sample_lineage_excerpt=" | ".join(
                value for value in excerpt_parts if value
            )[:1000],
            sample_identity_resolution="final"
            if archive is not None
            else "provisional",
            sample_ambiguity_note=self.refusal_reason,
            locality_text=source.locality_text,
            political_entity=source.political_entity,
            latitude_text=source.latitude_text,
            longitude_text=source.longitude_text,
            chronology_text=f"{source.younger_bp}-{source.older_bp} BP",
            chronology_dating_basis=chronology_basis,
            chronology_evidence_class=chronology_class,
            chronology_precision_posture=chronology_precision,
            source_native_tax_id=(
                "" if archive is None else archive.source_native_tax_id
            ),
            source_native_scientific_name=source.source_native_scientific_name,
            taxon_alignment_status="project_species_mismatch",
            source_native_identity_kind=(
                "biological_sample_accession"
                if archive is not None
                else "supplementary_sample_label"
            ),
            chronology_time_mean_bp=round(source.mean_bp),
        )


def _build_aurochs_natural_history_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    workbook_source_path: str,
    workbook_rows: tuple[tuple[str, ...], ...],
    workbook_sha256: str,
    archive_source_path: str,
    archive_text: str,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    """Build five archive joins and the explicit Fre1 paper-only refusal."""
    if species.latin_name != "Bos taurus":
        raise ValueError("aurochs natural-history adapter requires Bos taurus scope")
    if project.project_accession != AUROCHS_NATURAL_HISTORY_PROJECT_ACCESSION:
        raise ValueError("aurochs natural-history adapter requires PRJEB75467")
    if project.domestication_scope != "wild_or_progenitor_context":
        raise ValueError("PRJEB75467 wild/progenitor scope contract drift")
    reconciled = _reconcile_aurochs_natural_history(
        workbook_rows=workbook_rows,
        workbook_sha256=workbook_sha256,
        archive_text=archive_text,
    )
    return tuple(
        row.to_sample_master_row(
            species=species,
            project=project,
            workbook_source_path=workbook_source_path,
            archive_source_path=archive_source_path,
        )
        for row in reconciled
    )


def _reconcile_aurochs_natural_history(
    *,
    workbook_rows: tuple[tuple[str, ...], ...],
    workbook_sha256: str,
    archive_text: str,
) -> tuple[AurochsNaturalHistoryReconciliationRow, ...]:
    """Reconcile the hash-bound sources with no heuristic accession assignment."""
    if workbook_sha256 != AUROCHS_NATURAL_HISTORY_WORKBOOK_SHA256:
        raise ValueError("PRJEB75467 supplementary workbook sha256 drift")
    if (
        sha256(archive_text.encode("utf-8")).hexdigest()
        != AUROCHS_NATURAL_HISTORY_ARCHIVE_TEXT_SHA256
    ):
        raise ValueError("PRJEB75467 decompressed archive sha256 drift")
    workbook = _parse_workbook_evidence(workbook_rows)
    archive = _parse_archive_evidence(archive_text)
    reconciled = tuple(
        AurochsNaturalHistoryReconciliationRow(
            workbook=workbook[identity.sample_label],
            archive=archive[identity.sample_label],
            reconciliation_status="workbook_archive_literal_join",
            sequencing_status="archive_sequence_available",
            refusal_reason="",
        )
        for identity in ARCHIVE_IDENTITIES
    )
    fre1 = workbook[PAPER_ONLY_SAMPLE_LABEL]
    return (
        *reconciled,
        AurochsNaturalHistoryReconciliationRow(
            workbook=fre1,
            archive=None,
            reconciliation_status="paper_only_no_archive_accession",
            sequencing_status="archive_sequence_identity_not_evidenced",
            refusal_reason=(
                "Fre1 is paper-only: the workbook reports UDG treatment 'No' and "
                "0.0 genomic coverage, while the pinned PRJEB75467 archive has no "
                "Fre1 filename or BioSample identity; an accession is not inferred."
            ),
        ),
    )


def _parse_workbook_evidence(
    rows: tuple[tuple[str, ...], ...],
) -> dict[str, AurochsWorkbookEvidence]:
    """Extract the exact governed subset and reject missing or duplicate labels."""
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
        population_label = _cell(row, 24)
        if species_name != "Bos primigenius":
            raise ValueError(f"PRJEB75467 {label} source taxonomy drift")
        if population_label != AUROCHS_WILD_POPULATION_LABEL:
            raise ValueError(f"PRJEB75467 {label} wild-population evidence drift")
        latitude = _required_coordinate(_cell(row, 6), label=label, axis="latitude")
        longitude = _required_coordinate(_cell(row, 7), label=label, axis="longitude")
        if _cell(row, 11):
            younger, older = _parse_calibrated_bp_interval(_cell(row, 11), label)
            chronology_kind = "calibrated_radiocarbon_interval"
            if not _cell(row, 8) or not _cell(row, 9) or not _cell(row, 10):
                raise ValueError(f"PRJEB75467 {label} radiocarbon evidence incomplete")
        else:
            younger, older, modeled_mean = _parse_mitochondrial_date(
                _cell(row, 22), label
            )
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
        evidence[label] = AurochsWorkbookEvidence(
            sample_label=label,
            row_number=row_number,
            original_specimen_id=_required(_cell(row, 1), label, "specimen ID"),
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
    """Resolve only the five explicit BioSample joins from archive filename evidence."""
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
    fre1_matches: list[int] = []
    for line_number, _, basenames in archive_rows:
        matched = [
            label
            for label in (*expected, PAPER_ONLY_SAMPLE_LABEL)
            if any(_basename_has_label(name, label) for name in basenames)
        ]
        if len(matched) > 1:
            raise ValueError(
                f"PRJEB75467 archive line {line_number} has cross-contaminated labels"
            )
        if matched == [PAPER_ONLY_SAMPLE_LABEL]:
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
            for line_number, row, basenames in archive_rows
            if row["sample_accession"] != expected_accession
            and any(_basename_has_label(name, label) for name in basenames)
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


def _parse_calibrated_bp_interval(value: str, label: str) -> tuple[int, int]:
    match = _BP_INTERVAL_RE.fullmatch(value)
    if match is None:
        raise ValueError(f"PRJEB75467 {label} calibrated BP interval is invalid")
    younger = int(match.group("younger"))
    older = int(match.group("older"))
    if younger > older:
        raise ValueError(f"PRJEB75467 {label} calibrated BP interval direction drift")
    return younger, older


def _parse_mitochondrial_date(value: str, label: str) -> tuple[int, int, float]:
    match = _MITOCHONDRIAL_DATE_RE.fullmatch(value)
    if match is None:
        raise ValueError(f"PRJEB75467 {label} mitochondrial date is invalid")
    younger = int(match.group("younger"))
    older = int(match.group("older"))
    mean = float(match.group("mean"))
    if younger > mean or mean > older:
        raise ValueError(f"PRJEB75467 {label} mitochondrial date ordering drift")
    return younger, older, mean


def _submitted_basenames(value: str) -> tuple[str, ...]:
    return tuple(
        PurePosixPath(part.strip()).name for part in value.split(";") if part.strip()
    )


def _basename_has_label(basename: str, label: str) -> bool:
    return re.match(rf"^{re.escape(label)}(?:[_\-.]|$)", basename) is not None


def _required_coordinate(value: str, *, label: str, axis: str) -> str:
    try:
        number = float(value)
    except ValueError as error:
        raise ValueError(f"PRJEB75467 {label} {axis} is invalid") from error
    bound = 90 if axis == "latitude" else 180
    if not -bound <= number <= bound:
        raise ValueError(f"PRJEB75467 {label} {axis} is out of range")
    return value


def _required(value: str, label: str, field: str) -> str:
    if not value:
        raise ValueError(f"PRJEB75467 {label} {field} is missing")
    return value


def _cell(row: tuple[str, ...], index: int) -> str:
    return row[index].strip() if index < len(row) else ""


__all__ = [
    "AurochsArchiveEvidence",
    "AurochsNaturalHistoryReconciliationRow",
    "AurochsWorkbookEvidence",
    "_build_aurochs_natural_history_rows",
    "_parse_archive_evidence",
    "_parse_workbook_evidence",
    "_reconcile_aurochs_natural_history",
]
