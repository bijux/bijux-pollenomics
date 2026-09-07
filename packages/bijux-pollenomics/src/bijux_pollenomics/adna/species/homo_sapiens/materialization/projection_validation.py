"""Structural validation for the AADR accountability projection."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator

from .models import AadrSourceFile, AadrSourceRow, AadrSourceTable
from .reconciliation import (
    AadrPanelReconciliation,
    AadrReconciledRecord,
    AadrSourceRowLink,
    AadrUnkeyedSourceRow,
)


def source_file_rows(
    reconciliation: AadrPanelReconciliation,
) -> dict[AadrSourceFile, tuple[int, tuple[str, ...]]]:
    """Validate and index source tables by their physical source identity."""
    table_rows_by_key: dict[str, tuple[AadrSourceRow, ...]] = {}
    table_by_key: dict[str, AadrSourceTable] = {}
    for table in reconciliation.source_tables:
        source_file_key = table.source.key
        if source_file_key in table_by_key:
            raise ValueError("AADR physical source files must be unique")
        if any(row.source != table.source for row in table.rows):
            raise ValueError("AADR source table contains a row from another file")
        if any(row.column_names != table.column_names for row in table.rows):
            raise ValueError("AADR source table row schema diverges from its header")
        table_by_key[source_file_key] = table
        table_rows_by_key[source_file_key] = table.rows

    evidence_rows_by_key: dict[str, list[AadrSourceRow]] = {
        source_file_key: [] for source_file_key in table_by_key
    }
    for row in _iter_source_evidence_rows(reconciliation):
        source_file_key = row.source.key
        if source_file_key not in evidence_rows_by_key:
            raise ValueError("AADR source row names an unregistered physical file")
        evidence_rows_by_key[source_file_key].append(row)

    for source_file_key, table_rows in table_rows_by_key.items():
        evidence_rows = tuple(
            sorted(
                evidence_rows_by_key[source_file_key],
                key=lambda row: row.source_record_number,
            )
        )
        if evidence_rows != table_rows:
            raise ValueError("AADR source table rows diverge from reconciled evidence")

    return {
        table.source: (len(table.rows), table.column_names)
        for table in sorted(
            reconciliation.source_tables, key=lambda item: item.source.key
        )
    }


def source_file_key(source_file: AadrSourceFile) -> str:
    """Return the stable physical-source identity."""
    return source_file.key


def source_file_sort_key(source_file: AadrSourceFile) -> tuple[str, ...]:
    """Return the deterministic source-file ordering key."""
    return (source_file_key(source_file),)


def source_row_link(row: AadrSourceRow) -> AadrSourceRowLink:
    """Project a source row into its immutable evidence link."""
    return AadrSourceRowLink(
        source_path=row.source.source_path,
        source_release=row.source.source_release,
        dataset_name=row.source.dataset_name,
        source_sha256=row.source.source_sha256,
        source_record_number=row.source_record_number,
        source_line_start=row.source_line_start,
        source_line_end=row.source_line_end,
    )


def validate_reconciliation(reconciliation: AadrPanelReconciliation) -> None:
    """Validate ordering, linkage, evidence identity, and denominators."""
    if reconciliation.dataset_names != tuple(sorted(set(reconciliation.dataset_names))):
        raise ValueError("AADR reconciliation dataset names must be unique and sorted")
    record_ids = tuple(record.genetic_id for record in reconciliation.records)
    if record_ids != tuple(sorted(record_ids)) or len(record_ids) != len(
        set(record_ids)
    ):
        raise ValueError("AADR reconciled Genetic IDs must be unique and sorted")
    all_source_keys: list[str] = []
    for record in reconciliation.records:
        _validate_record(record, reconciliation.dataset_names)
        all_source_keys.extend(link.key for link in record.source_rows)
    for unkeyed in reconciliation.unkeyed_rows:
        _validate_unkeyed_row(unkeyed, reconciliation.dataset_names)
        all_source_keys.append(unkeyed.source_row.key)
    if len(all_source_keys) != reconciliation.source_row_count:
        raise ValueError("AADR source-row denominator diverges from linked rows")
    if len(all_source_keys) != len(set(all_source_keys)):
        raise ValueError("AADR source-row links must be globally unique")
    source_file_row_count = sum(
        row_count for row_count, _column_names in source_file_rows(reconciliation).values()
    )
    if source_file_row_count != reconciliation.source_row_count:
        raise ValueError("AADR source-file ledger denominator diverges")
    _validate_status_denominators(reconciliation)


def _validate_record(
    record: AadrReconciledRecord, dataset_names: tuple[str, ...]
) -> None:
    if not record.genetic_id or record.genetic_id != record.genetic_id.strip():
        raise ValueError("AADR reconciled Genetic ID is not canonically trimmed")
    if any(
        row.genetic_id_raw.strip() != record.genetic_id
        for row in record.source_evidence_rows
    ):
        raise ValueError("AADR source row is linked to the wrong Genetic ID")
    if record.taxon_scope_status != "not_asserted_by_source":
        raise ValueError("AADR reconciliation must not assert a taxon")
    observed_datasets = tuple(
        sorted({row.source.dataset_name for row in record.source_evidence_rows})
    )
    if record.dataset_names != observed_datasets or not set(observed_datasets) <= set(
        dataset_names
    ):
        raise ValueError("AADR record panel membership diverges from source rows")
    expected_links = tuple(source_row_link(row) for row in record.source_evidence_rows)
    if record.source_rows != expected_links:
        raise ValueError("AADR source evidence and row links diverge")
    source_rows_by_key = {
        link.key: row
        for link, row in zip(
            record.source_rows, record.source_evidence_rows, strict=True
        )
    }
    expected_keys = sorted(link.key for link in record.source_rows)
    _validate_group_links(
        expected_keys,
        (link.key for group in record.coordinate_groups for link in group.source_rows),
        dimension="coordinate",
    )
    _validate_group_links(
        expected_keys,
        (link.key for group in record.chronology_groups for link in group.source_rows),
        dimension="chronology",
    )
    _validate_coordinate_group_evidence(record, source_rows_by_key)
    _validate_chronology_group_evidence(record, source_rows_by_key)
    if any(
        group.evidence.scientifically_admitted for group in record.chronology_groups
    ):
        raise ValueError("AADR chronology cannot be admitted by accountability projection")


def _validate_unkeyed_row(
    unkeyed: AadrUnkeyedSourceRow, dataset_names: tuple[str, ...]
) -> None:
    row = unkeyed.source_evidence_row
    if row.genetic_id_raw.strip():
        raise ValueError("AADR unkeyed row unexpectedly has a Genetic ID")
    if unkeyed.genetic_id_raw != row.genetic_id_raw:
        raise ValueError("AADR unkeyed raw Genetic ID diverges from source evidence")
    if unkeyed.source_row != source_row_link(row):
        raise ValueError("AADR unkeyed source evidence and row link diverge")
    if row.source.dataset_name not in dataset_names:
        raise ValueError("AADR unkeyed row names an unknown dataset")
    if (
        row.taxon_scope_status != "not_asserted_by_source"
        or unkeyed.taxon_scope_status != "not_asserted_by_source"
    ):
        raise ValueError("AADR unkeyed row must not assert a taxon")
    if row.chronology.scientifically_admitted:
        raise ValueError("AADR unkeyed chronology cannot be scientifically admitted")


def _validate_coordinate_group_evidence(
    record: AadrReconciledRecord,
    source_rows_by_key: dict[str, AadrSourceRow],
) -> None:
    for group in record.coordinate_groups:
        for link in group.source_rows:
            if source_rows_by_key[link.key].coordinates != group.evidence:
                raise ValueError("AADR coordinate evidence group changes source evidence")


def _validate_chronology_group_evidence(
    record: AadrReconciledRecord,
    source_rows_by_key: dict[str, AadrSourceRow],
) -> None:
    for group in record.chronology_groups:
        for link in group.source_rows:
            if source_rows_by_key[link.key].chronology != group.evidence:
                raise ValueError("AADR chronology evidence group changes source evidence")


def _validate_group_links(
    expected_keys: list[str], observed_keys: Iterator[str], *, dimension: str
) -> None:
    if sorted(observed_keys) != expected_keys:
        raise ValueError(f"AADR {dimension} evidence-group links diverge")


def _validate_status_denominators(
    reconciliation: AadrPanelReconciliation,
) -> None:
    record_count = len(reconciliation.records)
    status_fields = (
        "panel_status",
        "coordinate_status",
        "chronology_status",
        "reconciliation_status",
        "taxon_scope_status",
    )
    for field_name in status_fields:
        counts = Counter(
            getattr(record, field_name) for record in reconciliation.records
        )
        if sum(counts.values()) != record_count:
            raise ValueError(f"AADR {field_name} denominator diverges")


def _iter_source_evidence_rows(
    reconciliation: AadrPanelReconciliation,
) -> Iterator[AadrSourceRow]:
    for record in reconciliation.records:
        yield from record.source_evidence_rows
    for unkeyed in reconciliation.unkeyed_rows:
        yield unkeyed.source_evidence_row
