"""Fail-closed reconciliation of the PRJEB81815 European cat panel."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from io import StringIO
from pathlib import Path
from typing import Final

from bijux_pollenomics.adna.projects.sample_master.models import (
    AdnaProjectSampleMasterRow,
)
from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition

from .chronology import (
    _calendar_union_bp,
    _calendar_union_label,
)


EUROPEAN_CAT_PROJECT_ACCESSION: Final = "PRJEB81815"
EUROPEAN_CAT_WORKBOOK_MEMBER: Final = "science.adt2642_tables s1_to_s8.xlsx"

_EXPECTED_TAXA: Final = {
    ("9685", "Felis catus"): 42,
    ("463207", "Felis silvestris silvestris"): 38,
    ("61377", "Felis silvestris lybica"): 7,
}
_EXPECTED_ANCIENT_COUNTRIES: Final = {
    "Austria": 7,
    "Belgium": 3,
    "Bulgaria": 5,
    "France": 1,
    "Germany": 7,
    "Greece": 2,
    "Ireland": 1,
    "Italy": 22,
    "Portugal": 5,
    "Serbia": 3,
    "Spain": 3,
    "Turkey": 11,
}
_COORDINATE_ORDER_ANOMALY_IDS: Final = frozenset(
    {
        "DOScat01",
        "DOScat03",
        "ECLYcat01",
        "FLUMcat02",
        "GLCAcat01",
        "HAIScat01",
        "HAIScat04",
        "HAIScat10",
        "LHMcat02",
        "LHMcat03",
        "PRNcat02",
        "ROCcat01",
        "ROCcat02",
        "ROCcat04",
    }
)
_EXPECTED_UNRESOLVED: Final = {
    "SAMEA120246597": (
        "778_Fsl_chrINT.bam",
        "778_Fss",
        "archive and workbook taxonomic suffixes conflict",
    ),
    "SAMEA120246598": (
        "779_Fsl_chrINT.bam",
        "779_Fss",
        "archive and workbook taxonomic suffixes conflict",
    ),
    "SAMEA120246599": (
        "BG5_DpS_AF_chrINT_q1.bam",
        "BG05",
        "archive and workbook identifiers conflict by zero padding",
    ),
}


@dataclass(frozen=True)
class EuropeanCatReconciliationRow:
    """One archive identity and its exact or explicitly refused workbook join."""

    archive_native_sample_id: str
    archive_native_experiment_id: str
    archive_submitted_basename: str
    source_native_tax_id: str
    source_native_scientific_name: str
    reconciliation_status: str
    temporal_context: str
    panel_sample_id: str
    paper_native_sample_label: str
    locality_text: str
    political_entity: str
    source_latitude_text: str
    source_longitude_text: str
    latitude_text: str
    longitude_text: str
    coordinate_admission_status: str
    source_chronology_text: str
    normalized_chronology_text: str
    time_start_bp: int | None
    time_end_bp: int | None
    chronology_dating_basis: str
    chronology_evidence_class: str
    chronology_precision_posture: str
    workbook_locator: str
    conflict_note: str

    def to_sample_master_row(
        self,
        *,
        species: AdnaSpeciesDefinition,
        project: AdnaArchiveProject,
        archive_source_path: str,
        workbook_source_path: str,
    ) -> AdnaProjectSampleMasterRow:
        """Project defensible reconciliation fields into the existing sample schema."""

        exact = self.reconciliation_status.startswith("exact_")
        chronology_text = (
            self.normalized_chronology_text or self.source_chronology_text
            if exact
            else ""
        )
        source_locator = f"sample_accession:{self.archive_native_sample_id}"
        if exact:
            source_locator += f" || {self.workbook_locator}"
        excerpt = (
            f"ENA identifies {self.archive_native_sample_id} as "
            f"{self.source_native_scientific_name} (tax_id "
            f"{self.source_native_tax_id})."
        )
        if exact:
            excerpt += (
                f" Exact workbook join {self.panel_sample_id}; source chronology: "
                f"{self.source_chronology_text}."
            )
        elif self.conflict_note:
            excerpt += f" Supplementary-table join refused: {self.conflict_note}."
        return AdnaProjectSampleMasterRow(
            species_latin_name=species.latin_name,
            species_common_name=species.common_name,
            project_accession=project.project_accession,
            repo_stable_sample_id=(
                f"{project.project_accession}:{self.archive_native_sample_id}".casefold()
            ),
            archive_native_sample_id=self.archive_native_sample_id,
            paper_native_sample_label=self.paper_native_sample_label if exact else "",
            supplementary_table_sample_label=self.panel_sample_id if exact else "",
            preferred_sample_label=(
                self.paper_native_sample_label
                if exact
                else self.archive_native_sample_id
            ),
            sample_basis=(
                "archive_supplement_exact_join"
                if exact
                else "archive_identity_with_supplement_conflict"
            ),
            sample_evidence_status=(
                "direct_table_extracted" if exact else "manual_curation_required"
            ),
            sample_lineage_path=workbook_source_path if exact else archive_source_path,
            sample_lineage_locator=source_locator,
            sample_lineage_excerpt=excerpt,
            sample_identity_resolution="final" if exact else "ambiguous",
            sample_ambiguity_note="" if exact else self.conflict_note,
            locality_text=self.locality_text if exact else "",
            political_entity=self.political_entity if exact else "",
            latitude_text=self.latitude_text if exact else "",
            longitude_text=self.longitude_text if exact else "",
            chronology_text=chronology_text,
            chronology_dating_basis=(
                self.chronology_dating_basis if exact else "unknown"
            ),
            chronology_evidence_class=(
                self.chronology_evidence_class if exact else "unresolved"
            ),
            chronology_precision_posture=(
                self.chronology_precision_posture if exact else "unresolved"
            ),
            source_native_tax_id=self.source_native_tax_id,
            source_native_scientific_name=self.source_native_scientific_name,
            taxon_alignment_status=(
                "project_species_match"
                if self.source_native_scientific_name.casefold()
                == species.latin_name.casefold()
                else "project_species_mismatch"
            ),
            archive_native_experiment_id=self.archive_native_experiment_id,
            source_native_identity_kind="biological_sample_accession",
        )


@dataclass(frozen=True)
class _TableRow:
    row_number: int
    values: dict[str, str]


@dataclass(frozen=True)
class _ArchiveRow:
    sample_accession: str
    experiment_accession: str
    tax_id: str
    scientific_name: str
    submitted_basenames: tuple[str, ...]


def _reconcile_european_cat_panel(
    *,
    archive_text: str,
    table_s1_rows: tuple[tuple[str, ...], ...],
    table_s3_rows: tuple[tuple[str, ...], ...],
    table_s4_rows: tuple[tuple[str, ...], ...],
    table_s5_rows: tuple[tuple[str, ...], ...],
) -> tuple[EuropeanCatReconciliationRow, ...]:
    """Reconcile the archive and primary workbook without heuristic aliases."""

    archive_rows = _read_archive_rows(archive_text)
    _require(len(archive_rows) == 87, "PRJEB81815 must contain 87 archive samples")
    taxon_counts: dict[tuple[str, str], int] = {}
    for row in archive_rows:
        key = (row.tax_id, row.scientific_name)
        taxon_counts[key] = taxon_counts.get(key, 0) + 1
    _require(taxon_counts == _EXPECTED_TAXA, "archive taxonomy denominator drift")

    table_s1 = _table_rows(
        table_s1_rows,
        required_headers=(
            "ID",
            "Site",
            "Country",
            "Latitude",
            "Longitude",
            "Chronology / C14 date",
        ),
        primary_key="ID",
    )
    table_s3 = _collapse_deep_sequence_rows(table_s3_rows)
    table_s4 = _table_rows(
        table_s4_rows,
        required_headers=("ID ISPRA", "date", "Country", "Site"),
        primary_key="ID ISPRA",
    )
    table_s5 = _table_rows(
        table_s5_rows,
        required_headers=(
            "ID",
            "95.4% probability calibrated date",
            "notes",
        ),
        primary_key="ID",
    )
    _require(len(table_s3) == 70, "Table S3 must resolve to 70 ancient samples")
    _require(len(table_s4) == 17, "Table S4 must contain 17 modern samples")

    s1_by_id = _unique_index(table_s1, "ID", "Table S1 ID")
    s4_by_id = _unique_index(table_s4, "ID ISPRA", "Table S4 ID")
    s5_by_id = _unique_index(table_s5, "ID", "Table S5 ID")
    panel_ids = set(table_s3) | set(s4_by_id)
    rows: list[EuropeanCatReconciliationRow] = []
    for archive_row in archive_rows:
        matches = sorted(
            panel_id
            for panel_id in panel_ids
            if any(
                basename.startswith((f"{panel_id}_", f"{panel_id}-"))
                for basename in archive_row.submitted_basenames
            )
        )
        _require(len(matches) <= 1, "one archive sample matched multiple panel IDs")
        if not matches:
            rows.append(_unresolved_row(archive_row))
            continue
        panel_id = matches[0]
        submitted_basename = next(
            basename
            for basename in archive_row.submitted_basenames
            if basename.startswith((f"{panel_id}_", f"{panel_id}-"))
            and basename.endswith(".bam")
        )
        if panel_id in table_s3:
            rows.append(
                _ancient_row(
                    archive_row=archive_row,
                    submitted_basename=submitted_basename,
                    panel_id=panel_id,
                    table_s3_row=table_s3[panel_id],
                    s1_by_id=s1_by_id,
                    s5_by_id=s5_by_id,
                )
            )
        else:
            rows.append(
                _modern_row(
                    archive_row=archive_row,
                    submitted_basename=submitted_basename,
                    panel_id=panel_id,
                    table_s4_row=s4_by_id[panel_id],
                )
            )

    rows.sort(key=lambda row: row.archive_native_sample_id)
    _validate_reconciliation(tuple(rows))
    return tuple(rows)


def _build_european_cat_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    archive_source_path: str,
    archive_text: str,
    workbook_source_path: str,
    table_s1_rows: tuple[tuple[str, ...], ...],
    table_s3_rows: tuple[tuple[str, ...], ...],
    table_s4_rows: tuple[tuple[str, ...], ...],
    table_s5_rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    """Build all 87 archive-owned master rows from the reconciliation contract."""

    _require(
        project.project_accession == EUROPEAN_CAT_PROJECT_ACCESSION,
        "European cat adapter received the wrong project",
    )
    reconciled = _reconcile_european_cat_panel(
        archive_text=archive_text,
        table_s1_rows=table_s1_rows,
        table_s3_rows=table_s3_rows,
        table_s4_rows=table_s4_rows,
        table_s5_rows=table_s5_rows,
    )
    return tuple(
        row.to_sample_master_row(
            species=species,
            project=project,
            archive_source_path=archive_source_path,
            workbook_source_path=workbook_source_path,
        )
        for row in reconciled
    )


def _ancient_row(
    *,
    archive_row: _ArchiveRow,
    submitted_basename: str,
    panel_id: str,
    table_s3_row: _TableRow,
    s1_by_id: dict[str, _TableRow],
    s5_by_id: dict[str, _TableRow],
) -> EuropeanCatReconciliationRow:
    cat_id = table_s3_row.values["Cat ID"]
    _require(cat_id in s1_by_id, f"Table S3 cat ID missing from Table S1: {cat_id}")
    source = s1_by_id[cat_id]
    source_chronology = source.values["Chronology / C14 date"]
    _require(bool(source_chronology), f"ancient chronology missing for {cat_id}")
    calibration_text = ""
    if cat_id in s5_by_id:
        calibration_text = s5_by_id[cat_id].values["95.4% probability calibrated date"]
    elif cat_id == "DHcat06":
        donor = s5_by_id.get("DHcat05")
        if donor is None:
            raise ValueError("DHcat06 radiocarbon donor row is missing")
        note = donor.values["notes"]
        _require(
            all(token in note for token in ("DH05", "cat01", "DH06")),
            "DHcat05 same-individual note no longer supports DHcat06",
        )
        calibration_text = donor.values["95.4% probability calibrated date"]
    elif cat_id == "GLCAcat01":
        _require(
            "UBA-45133" in source_chronology and "cal BC" in source_chronology,
            "GLCAcat01 calibrated source claim drifted",
        )
        calibration_text = source_chronology

    interval_source = calibration_text or source_chronology
    interval = _calendar_union_bp(interval_source)
    evidence_class = (
        "direct_radiocarbon_date" if calibration_text else "archaeological_context_date"
    )
    normalized = _calendar_union_label(interval_source)
    _require(
        not calibration_text or interval is not None,
        f"calibrated interval could not be parsed for {cat_id}",
    )
    source_latitude = source.values["Latitude"]
    source_longitude = source.values["Longitude"]
    _require(
        bool(source_latitude) and bool(source_longitude),
        f"ancient coordinate pair missing for {cat_id}",
    )
    coordinate_admitted = cat_id not in _COORDINATE_ORDER_ANOMALY_IDS
    return EuropeanCatReconciliationRow(
        archive_native_sample_id=archive_row.sample_accession,
        archive_native_experiment_id=archive_row.experiment_accession,
        archive_submitted_basename=submitted_basename,
        source_native_tax_id=archive_row.tax_id,
        source_native_scientific_name=archive_row.scientific_name,
        reconciliation_status="exact_ancient",
        temporal_context="ancient",
        panel_sample_id=panel_id,
        paper_native_sample_label=cat_id,
        locality_text=source.values["Site"],
        political_entity=source.values["Country"],
        source_latitude_text=source_latitude,
        source_longitude_text=source_longitude,
        latitude_text=_display_coordinate(source_latitude)
        if coordinate_admitted
        else "",
        longitude_text=(
            _display_coordinate(source_longitude) if coordinate_admitted else ""
        ),
        coordinate_admission_status=(
            "source_reported_pair_admitted"
            if coordinate_admitted
            else "withheld_coordinate_order_anomaly"
        ),
        source_chronology_text=source_chronology,
        normalized_chronology_text=normalized,
        time_start_bp=None if interval is None else interval[0],
        time_end_bp=None if interval is None else interval[1],
        chronology_dating_basis=(
            "radiocarbon" if calibration_text else "archaeological_context"
        ),
        chronology_evidence_class=evidence_class,
        chronology_precision_posture=(
            "sample_approximate_or_modeled"
            if calibration_text
            else "contextual_interval"
            if interval is not None
            else "broad_period_only"
        ),
        workbook_locator=(
            f"{EUROPEAN_CAT_WORKBOOK_MEMBER}#"
            f"Table_S3!row{table_s3_row.row_number} -> "
            f"Table_S1!row{source.row_number}"
        ),
        conflict_note=(
            "literal latitude/longitude order conflicts with country and named-site geography"
            if not coordinate_admitted
            else ""
        ),
    )


def _modern_row(
    *,
    archive_row: _ArchiveRow,
    submitted_basename: str,
    panel_id: str,
    table_s4_row: _TableRow,
) -> EuropeanCatReconciliationRow:
    return EuropeanCatReconciliationRow(
        archive_native_sample_id=archive_row.sample_accession,
        archive_native_experiment_id=archive_row.experiment_accession,
        archive_submitted_basename=submitted_basename,
        source_native_tax_id=archive_row.tax_id,
        source_native_scientific_name=archive_row.scientific_name,
        reconciliation_status="exact_modern_context",
        temporal_context=table_s4_row.values["date"],
        panel_sample_id=panel_id,
        paper_native_sample_label=panel_id,
        locality_text=table_s4_row.values["Site"],
        political_entity=table_s4_row.values["Country"],
        source_latitude_text="",
        source_longitude_text="",
        latitude_text="",
        longitude_text="",
        coordinate_admission_status="unavailable_in_source_table",
        source_chronology_text=table_s4_row.values["date"],
        normalized_chronology_text="",
        time_start_bp=None,
        time_end_bp=None,
        chronology_dating_basis="modern_sampling",
        chronology_evidence_class="historical_or_recent_date",
        chronology_precision_posture="broad_period_only",
        workbook_locator=(
            f"{EUROPEAN_CAT_WORKBOOK_MEMBER}#Table_S4!row{table_s4_row.row_number}"
        ),
        conflict_note="",
    )


def _unresolved_row(archive_row: _ArchiveRow) -> EuropeanCatReconciliationRow:
    expected = _EXPECTED_UNRESOLVED.get(archive_row.sample_accession)
    if expected is None:
        raise ValueError("unexpected archive-to-workbook join refusal")
    basename, workbook_id, reason = expected
    _require(
        basename in archive_row.submitted_basenames,
        "expected unresolved archive basename drifted",
    )
    return EuropeanCatReconciliationRow(
        archive_native_sample_id=archive_row.sample_accession,
        archive_native_experiment_id=archive_row.experiment_accession,
        archive_submitted_basename=basename,
        source_native_tax_id=archive_row.tax_id,
        source_native_scientific_name=archive_row.scientific_name,
        reconciliation_status="unresolved_identifier_conflict",
        temporal_context="unresolved",
        panel_sample_id="",
        paper_native_sample_label="",
        locality_text="",
        political_entity="",
        source_latitude_text="",
        source_longitude_text="",
        latitude_text="",
        longitude_text="",
        coordinate_admission_status="withheld_unresolved_identity_join",
        source_chronology_text="",
        normalized_chronology_text="",
        time_start_bp=None,
        time_end_bp=None,
        chronology_dating_basis="unknown",
        chronology_evidence_class="unresolved",
        chronology_precision_posture="unresolved",
        workbook_locator="",
        conflict_note=f"{reason}: archive {basename}; workbook {workbook_id}",
    )


def _read_archive_rows(archive_text: str) -> tuple[_ArchiveRow, ...]:
    reader = csv.DictReader(StringIO(archive_text), delimiter="\t")
    required = {
        "sample_accession",
        "experiment_accession",
        "tax_id",
        "scientific_name",
        "submitted_ftp",
    }
    _require(
        reader.fieldnames is not None and required <= set(reader.fieldnames),
        "ENA archive columns required by the cat reconciliation are missing",
    )
    rows: list[_ArchiveRow] = []
    for source in reader:
        accession = source["sample_accession"].strip()
        if not accession:
            continue
        basenames = tuple(
            Path(item.strip()).name
            for item in source["submitted_ftp"].split(";")
            if item.strip()
        )
        rows.append(
            _ArchiveRow(
                sample_accession=accession,
                experiment_accession=source["experiment_accession"].strip(),
                tax_id=source["tax_id"].strip(),
                scientific_name=source["scientific_name"].strip(),
                submitted_basenames=basenames,
            )
        )
    _require(
        len({row.sample_accession for row in rows}) == len(rows),
        "duplicate ENA sample accession",
    )
    return tuple(rows)


def _table_rows(
    rows: tuple[tuple[str, ...], ...],
    *,
    required_headers: tuple[str, ...],
    primary_key: str,
) -> tuple[_TableRow, ...]:
    _require(len(rows) >= 2, "supplementary table has no header row")
    header = {
        value.strip(): index for index, value in enumerate(rows[1]) if value.strip()
    }
    _require(
        set(required_headers) <= set(header),
        f"supplementary table headers missing for {primary_key}",
    )
    built: list[_TableRow] = []
    for row_number, row in enumerate(rows[2:], start=3):
        values = {key: _cell_value(row, header[key]) for key in required_headers}
        if not values[primary_key]:
            continue
        built.append(_TableRow(row_number=row_number, values=values))
    return tuple(built)


def _collapse_deep_sequence_rows(
    rows: tuple[tuple[str, ...], ...],
) -> dict[str, _TableRow]:
    required = ("Sample ID", "Cat ID", "Individual", "Country", "Site", "element")
    parsed = _table_rows(rows, required_headers=required, primary_key="Sample ID")
    grouped: dict[str, list[_TableRow]] = {}
    for row in parsed:
        sample_id = row.values["Sample ID"].removesuffix("*")
        grouped.setdefault(sample_id, []).append(row)
    collapsed: dict[str, _TableRow] = {}
    for sample_id, group in grouped.items():
        signatures = {
            tuple(row.values[field] for field in required[1:]) for row in group
        }
        _require(
            len(signatures) == 1,
            f"repeated Table S3 rows disagree for {sample_id}",
        )
        first = group[0]
        collapsed[sample_id] = _TableRow(
            row_number=first.row_number,
            values={**first.values, "Sample ID": sample_id},
        )
    return collapsed


def _unique_index(
    rows: tuple[_TableRow, ...], key: str, label: str
) -> dict[str, _TableRow]:
    index: dict[str, _TableRow] = {}
    for row in rows:
        value = row.values[key]
        _require(value not in index, f"duplicate {label}: {value}")
        index[value] = row
    return index


def _display_coordinate(value: str) -> str:
    number = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{number:.2f}"


def _cell_value(row: tuple[str, ...], index: int) -> str:
    return "" if index >= len(row) else str(row[index]).strip()


def _validate_reconciliation(
    rows: tuple[EuropeanCatReconciliationRow, ...],
) -> None:
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row.reconciliation_status] = (
            status_counts.get(row.reconciliation_status, 0) + 1
        )
    _require(
        status_counts
        == {
            "exact_ancient": 70,
            "exact_modern_context": 14,
            "unresolved_identifier_conflict": 3,
        },
        "European cat reconciliation denominator drift",
    )
    ancient = tuple(row for row in rows if row.reconciliation_status == "exact_ancient")
    country_counts: dict[str, int] = {}
    for row in ancient:
        country_counts[row.political_entity] = (
            country_counts.get(row.political_entity, 0) + 1
        )
    _require(
        country_counts == _EXPECTED_ANCIENT_COUNTRIES,
        "ancient country denominator drift",
    )
    _require(
        sum(
            row.chronology_evidence_class == "direct_radiocarbon_date"
            for row in ancient
        )
        == 37,
        "radiocarbon chronology denominator drift",
    )
    _require(
        sum(
            row.chronology_evidence_class == "archaeological_context_date"
            for row in ancient
        )
        == 33,
        "archaeological chronology denominator drift",
    )
    _require(
        sum(
            row.coordinate_admission_status == "source_reported_pair_admitted"
            for row in ancient
        )
        == 56,
        "admitted coordinate denominator drift",
    )
    _require(
        sum(
            row.coordinate_admission_status == "withheld_coordinate_order_anomaly"
            for row in ancient
        )
        == 14,
        "coordinate-order refusal denominator drift",
    )
    _require(
        {
            row.archive_native_sample_id
            for row in rows
            if row.reconciliation_status.startswith("unresolved")
        }
        == set(_EXPECTED_UNRESOLVED),
        "identifier-conflict set drift",
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


__all__ = [
    "EUROPEAN_CAT_PROJECT_ACCESSION",
    "EUROPEAN_CAT_WORKBOOK_MEMBER",
    "EuropeanCatReconciliationRow",
    "_build_european_cat_rows",
    "_reconcile_european_cat_panel",
]
