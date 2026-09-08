"""Construct source-owned pig-panel evidence after exact identity reconciliation."""

from __future__ import annotations

from .admission import (
    chronology_admission,
    classify_domestication,
    source_mean_is_numeric,
)
from .identity import (
    archive_evidence,
    cell,
    coordinate_evidence_by_label,
    indexed_ancient_workbook_rows,
    indexed_modern_workbook_rows,
    required_cell,
    validate_ancient_workbook_header,
    validate_denominators,
    validate_modern_workbook_header,
    validate_site_coordinate_join,
)
from .models import PigPanelJoinAuditRow
from .site_coordinates import PigSiteCoordinateEvidence


def build_pig_panel_join_audit(
    *,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
    modern_source_path: str,
    modern_rows: tuple[tuple[str, ...], ...],
    archive_source_path: str,
    archive_text: str,
    coordinate_evidence: tuple[PigSiteCoordinateEvidence, ...] = (),
) -> tuple[PigPanelJoinAuditRow, ...]:
    """Reconcile the complete pinned pig archive denominator without inference."""
    validate_ancient_workbook_header(rows)
    validate_modern_workbook_header(modern_rows)
    archive = archive_evidence(archive_text)
    ancient_rows = indexed_ancient_workbook_rows(
        rows, required_labels=frozenset(archive.ancient_accession_by_label)
    )
    ancient_accessions = frozenset(archive.ancient_accession_by_label.values())
    modern_accessions = archive.sample_accessions - ancient_accessions
    modern_rows_by_accession = indexed_modern_workbook_rows(
        modern_rows, required_accessions=modern_accessions
    )
    validate_denominators(
        archive=archive,
        ancient_accessions=ancient_accessions,
        modern_accessions=modern_accessions,
    )
    coordinates_by_label = coordinate_evidence_by_label(coordinate_evidence)

    audit_rows = [
        _ancient_audit_row(
            sample_label=sample_label,
            archive_accession=archive.ancient_accession_by_label[sample_label],
            source_path=source_path,
            workbook_row=ancient_rows[sample_label],
            archive_source_path=archive_source_path,
            archive_locators=archive.locators_by_accession[
                archive.ancient_accession_by_label[sample_label]
            ],
            coordinate=coordinates_by_label.get(sample_label),
        )
        for sample_label in sorted(archive.ancient_accession_by_label)
    ]
    audit_rows.extend(
        _modern_audit_row(
            archive_accession=archive_accession,
            source_path=modern_source_path,
            workbook_row=modern_rows_by_accession[archive_accession],
            archive_source_path=archive_source_path,
            archive_locators=archive.locators_by_accession[archive_accession],
        )
        for archive_accession in sorted(modern_accessions)
    )
    observed_coordinate_labels = {
        row.sample_label
        for row in audit_rows
        if row.latitude_text or row.longitude_text
    }
    if observed_coordinate_labels != set(coordinates_by_label):
        raise ValueError("Pig coordinate evidence does not match a joined ancient row")
    audit_rows.sort(key=lambda row: row.archive_native_sample_id)
    return tuple(audit_rows)


def _ancient_audit_row(
    *,
    sample_label: str,
    archive_accession: str,
    source_path: str,
    workbook_row: tuple[int, tuple[str, ...]],
    archive_source_path: str,
    archive_locators: tuple[str, ...],
    coordinate: PigSiteCoordinateEvidence | None,
) -> PigPanelJoinAuditRow:
    row_number, row = workbook_row
    statuses = tuple(cell(row, index) for index in (33, 37, 38))
    domestication_status, disposition, disposition_reason = classify_domestication(
        sample_label, statuses
    )
    source_mean = cell(row, 28)
    source_mean_numeric = source_mean_is_numeric(source_mean)
    chronology_text, chronology_disposition, chronology_reason = chronology_admission(
        sample_label=sample_label,
        source_mean=source_mean,
        source_mean_is_numeric=source_mean_numeric,
    )
    locality = required_cell(row, 31, sample_label)
    political_entity = required_cell(row, 32, sample_label)
    if coordinate is not None:
        validate_site_coordinate_join(
            evidence=coordinate,
            archive_accession=archive_accession,
            locality_text=locality,
            political_entity=political_entity,
        )
    return PigPanelJoinAuditRow(
        sample_label=sample_label,
        archive_native_sample_id=archive_accession,
        source_sample_kind="ancient_or_archaeological",
        previous_extraction_code=cell(row, 1),
        mtdna_accession_text=cell(row, 2),
        source_text=cell(row, 3),
        locality_text=locality,
        political_entity=political_entity,
        museum_or_sample_code=cell(row, 20),
        additional_sample_information=cell(row, 21),
        radiocarbon_lab_number=cell(row, 22),
        uncalibrated_date_text=cell(row, 23),
        uncalibrated_error_text=cell(row, 24),
        calibrated_from_bp_text=cell(row, 25),
        calibrated_to_bp_text=cell(row, 26),
        source_age_text=cell(row, 27),
        source_mean_age_text=source_mean,
        source_mean_age_is_numeric=source_mean_numeric,
        period_text=cell(row, 29),
        source_group_text=cell(row, 30),
        zooarchaeology_status=statuses[0],
        combined_genetic_zooarchaeology_status=statuses[1],
        secondary_zooarchaeology_status=statuses[2],
        publication_status_text=cell(row, 39),
        modern_population="",
        modern_breed_or_country="",
        modern_coverage_text="",
        modern_doi_text="",
        chronology_text=chronology_text,
        chronology_disposition=chronology_disposition,
        chronology_disposition_reason=chronology_reason,
        domestication_status=domestication_status,
        disposition=disposition,
        disposition_reason=disposition_reason,
        workbook_source_path=source_path,
        workbook_source_locator=f"Sheet1!row{row_number}",
        archive_source_path=archive_source_path,
        archive_source_locators=archive_locators,
        latitude_text="" if coordinate is None else coordinate.latitude_text,
        longitude_text="" if coordinate is None else coordinate.longitude_text,
        map_admission=(
            "refused_missing_source_coordinates"
            if coordinate is None
            else "admitted_approximate_site_anchor"
        ),
        coordinate_basis="" if coordinate is None else coordinate.coordinate_basis,
        coordinate_confidence=(
            "" if coordinate is None else coordinate.coordinate_confidence
        ),
        coordinate_source_url=(
            "" if coordinate is None else coordinate.coordinate_source_url
        ),
        coordinate_source_locator=(
            "" if coordinate is None else coordinate.coordinate_source_locator
        ),
        coordinate_spatial_scope="" if coordinate is None else coordinate.spatial_scope,
    )


def _modern_audit_row(
    *,
    archive_accession: str,
    source_path: str,
    workbook_row: tuple[int, tuple[str, ...]],
    archive_source_path: str,
    archive_locators: tuple[str, ...],
) -> PigPanelJoinAuditRow:
    row_number, row = workbook_row
    sample_label = required_cell(row, 0, archive_accession)
    if required_cell(row, 4, sample_label) != archive_accession:
        raise ValueError(f"Pig modern workbook accession drift for {sample_label}")
    return PigPanelJoinAuditRow(
        sample_label=sample_label,
        archive_native_sample_id=archive_accession,
        source_sample_kind="modern",
        previous_extraction_code="",
        mtdna_accession_text="",
        source_text="",
        locality_text="",
        political_entity="",
        museum_or_sample_code="",
        additional_sample_information="",
        radiocarbon_lab_number="",
        uncalibrated_date_text="",
        uncalibrated_error_text="",
        calibrated_from_bp_text="",
        calibrated_to_bp_text="",
        source_age_text="",
        source_mean_age_text="",
        source_mean_age_is_numeric=False,
        period_text="",
        source_group_text="",
        zooarchaeology_status="",
        combined_genetic_zooarchaeology_status="",
        secondary_zooarchaeology_status="",
        publication_status_text="",
        modern_population=cell(row, 1),
        modern_breed_or_country=cell(row, 2),
        modern_coverage_text=cell(row, 3),
        modern_doi_text=cell(row, 5),
        chronology_text="",
        chronology_disposition="unresolved_not_reported",
        chronology_disposition_reason=(
            "The modern supplement row reports no sample-owned date field."
        ),
        domestication_status="not_reported_in_domestication_status_fields",
        disposition="excluded_unreviewed_domesticated_scope",
        disposition_reason=(
            "The modern population and breed fields are retained without extending "
            "the governed domesticated publication scope."
        ),
        workbook_source_path=source_path,
        workbook_source_locator=f"Sheet1!row{row_number}",
        archive_source_path=archive_source_path,
        archive_source_locators=archive_locators,
    )
