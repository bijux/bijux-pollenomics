"""Versioned streaming projection of AADR accountability evidence."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Iterator
from decimal import Decimal
import json

from .chronology import AadrChronologyEvidence, AadrFullDateToken
from .models import (
    AadrCoordinateEvidence,
    AadrSourceFile,
    AadrSourceRow,
    AadrSourceTable,
)
from .projection_contract import (
    AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION,
    validate_aadr_accountability_summary,
)
from .reconciliation import (
    AadrChronologyEvidenceGroup,
    AadrCoordinateEvidenceGroup,
    AadrPanelReconciliation,
    AadrReconciledRecord,
    AadrSourceRowLink,
    AadrUnkeyedSourceRow,
)

_RECONCILIATION_STATUSES = ("exact", "complementary", "conflict")
_COORDINATE_EVIDENCE_STATUSES = (
    "admitted",
    "missing",
    "partial",
    "invalid_numeric",
    "non_finite",
    "out_of_range",
)
_CHRONOLOGY_EVALUATION_STATUSES = ("review_required", "refused")
_CHRONOLOGY_REFUSAL_REASONS = (
    "method_specific_policy_required",
    "source_chronology_missing",
    "invalid_numeric_evidence",
)


def build_aadr_accountability_summary(
    reconciliation: AadrPanelReconciliation,
) -> dict[str, object]:
    """Validate reconciliation denominators and return its versioned summary."""
    _validate_reconciliation(reconciliation)
    records = reconciliation.records
    keyed_source_row_count = sum(len(record.source_rows) for record in records)
    unkeyed_source_row_count = len(reconciliation.unkeyed_rows)
    coordinate_group_count = sum(len(record.coordinate_groups) for record in records)
    chronology_group_count = sum(len(record.chronology_groups) for record in records)
    source_files = _project_source_files(reconciliation)
    summary: dict[str, object] = {
        "schema_version": AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION,
        "record_kind": "accountability_summary",
        "dataset_names": list(reconciliation.dataset_names),
        "source_files": source_files,
        "denominators": {
            "source_file_count": len(source_files),
            "source_row_count": reconciliation.source_row_count,
            "keyed_source_row_count": keyed_source_row_count,
            "unkeyed_source_row_count": unkeyed_source_row_count,
            "genetic_id_count": len(records),
            "coordinate_evidence_group_count": (
                coordinate_group_count + unkeyed_source_row_count
            ),
            "chronology_evidence_group_count": (
                chronology_group_count + unkeyed_source_row_count
            ),
        },
        "status_counts": {
            "panel": _counter_dict(
                (record.panel_status for record in records),
                required=_RECONCILIATION_STATUSES,
            ),
            "coordinate": _counter_dict(
                (record.coordinate_status for record in records),
                required=_RECONCILIATION_STATUSES,
            ),
            "chronology": _counter_dict(
                (record.chronology_status for record in records),
                required=_RECONCILIATION_STATUSES,
            ),
            "reconciliation": _counter_dict(
                (record.reconciliation_status for record in records),
                required=_RECONCILIATION_STATUSES,
            ),
            "coordinate_evidence": _counter_dict(
                (
                    evidence.status
                    for evidence in _iter_projected_coordinate_evidence(reconciliation)
                ),
                required=_COORDINATE_EVIDENCE_STATUSES,
            ),
            "chronology_evaluation": _counter_dict(
                (
                    evidence.evaluation_status
                    for evidence in _iter_projected_chronology_evidence(reconciliation)
                ),
                required=_CHRONOLOGY_EVALUATION_STATUSES,
            ),
            "chronology_refusal_reason": _counter_dict(
                (
                    evidence.refusal_reason_code
                    for evidence in _iter_projected_chronology_evidence(reconciliation)
                ),
                required=_CHRONOLOGY_REFUSAL_REASONS,
            ),
            "taxon_scope_genetic_ids": _counter_dict(
                (record.taxon_scope_status for record in records),
                required=("not_asserted_by_source",),
            ),
            "taxon_scope_unkeyed_rows": _counter_dict(
                (row.taxon_scope_status for row in reconciliation.unkeyed_rows),
                required=("not_asserted_by_source",),
            ),
            "unkeyed_refusal_reason": _counter_dict(
                (row.refusal_reason_code for row in reconciliation.unkeyed_rows),
                required=("genetic_id_missing",),
            ),
        },
        "dataset_counts": {
            "source_rows": _counter_dict(
                _iter_source_row_dataset_names(reconciliation),
                required=reconciliation.dataset_names,
            ),
            "genetic_id_memberships": _counter_dict(
                (
                    dataset_name
                    for record in records
                    for dataset_name in record.dataset_names
                ),
                required=reconciliation.dataset_names,
            ),
        },
        "scientifically_admitted": False,
        "scientifically_admitted_chronology_group_count": 0,
        "taxon_scope_status": "not_asserted_by_source",
    }
    validate_aadr_accountability_summary(summary)
    return summary


def iter_aadr_accountability_records(
    reconciliation: AadrPanelReconciliation,
) -> Iterator[dict[str, object]]:
    """Yield one JSON-compatible record at a time after denominator validation."""
    _validate_reconciliation(reconciliation)
    for record in reconciliation.records:
        yield _project_reconciled_record(record)
    for unkeyed in reconciliation.unkeyed_rows:
        yield _project_unkeyed_row(unkeyed)


def iter_aadr_accountability_projection(
    reconciliation: AadrPanelReconciliation,
) -> Iterator[dict[str, object]]:
    """Yield the summary followed by deterministic accountability records."""
    yield build_aadr_accountability_summary(reconciliation)
    yield from iter_aadr_accountability_records(reconciliation)


def iter_aadr_accountability_json_lines(
    reconciliation: AadrPanelReconciliation,
) -> Iterator[str]:
    """Yield deterministic UTF-8 JSON Lines without accumulating v66 records."""
    for projected_record in iter_aadr_accountability_projection(reconciliation):
        yield (
            json.dumps(
                projected_record,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        )


def _project_reconciled_record(record: AadrReconciledRecord) -> dict[str, object]:
    source_rows_by_key = {
        _source_row_link(row).key: row for row in record.source_evidence_rows
    }
    return {
        "schema_version": AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION,
        "record_kind": "reconciled_genetic_id",
        "genetic_id": record.genetic_id,
        "genetic_id_raw_values": list(record.genetic_id_raw_values),
        "dataset_names": list(record.dataset_names),
        "taxon_scope_status": record.taxon_scope_status,
        "scientifically_admitted": False,
        "statuses": {
            "panel": record.panel_status,
            "coordinate": record.coordinate_status,
            "chronology": record.chronology_status,
            "reconciliation": record.reconciliation_status,
        },
        "source_rows": [
            _project_source_row(source_rows_by_key[link.key], link)
            for link in record.source_rows
        ],
        "coordinate_evidence_groups": [
            _project_coordinate_group(group) for group in record.coordinate_groups
        ],
        "chronology_evidence_groups": [
            _project_chronology_group(group) for group in record.chronology_groups
        ],
    }


def _project_unkeyed_row(unkeyed: AadrUnkeyedSourceRow) -> dict[str, object]:
    row = unkeyed.source_evidence_row
    return {
        "schema_version": AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION,
        "record_kind": "unkeyed_source_row",
        "genetic_id": None,
        "genetic_id_raw_values": [unkeyed.genetic_id_raw],
        "dataset_names": [row.source.dataset_name],
        "taxon_scope_status": unkeyed.taxon_scope_status,
        "scientifically_admitted": False,
        "statuses": {
            "panel": "refused",
            "coordinate": "not_reconciled",
            "chronology": "not_reconciled",
            "reconciliation": "refused",
        },
        "refusal_reason_code": unkeyed.refusal_reason_code,
        "source_rows": [_project_source_row(row, unkeyed.source_row)],
        "coordinate_evidence_groups": [
            _project_coordinate_evidence(row.coordinates, (unkeyed.source_row,))
        ],
        "chronology_evidence_groups": [
            _project_chronology_evidence(row.chronology, (unkeyed.source_row,))
        ],
    }


def _project_source_row(
    row: AadrSourceRow, link: AadrSourceRowLink
) -> dict[str, object]:
    return {
        "source_row": _project_source_link(link),
        "raw_tokens": list(row.raw_tokens),
        "unmatched_raw_tokens": list(row.unmatched_raw_tokens),
        "taxon_scope_status": row.taxon_scope_status,
    }


def _project_coordinate_group(
    group: AadrCoordinateEvidenceGroup,
) -> dict[str, object]:
    return _project_coordinate_evidence(group.evidence, group.source_rows)


def _project_coordinate_evidence(
    evidence: AadrCoordinateEvidence,
    source_rows: tuple[AadrSourceRowLink, ...],
) -> dict[str, object]:
    return {
        "source_row_keys": [link.key for link in source_rows],
        "latitude_raw": evidence.latitude_raw,
        "longitude_raw": evidence.longitude_raw,
        "latitude": evidence.latitude,
        "longitude": evidence.longitude,
        "status": evidence.status,
        "refusal_reason_code": (
            None if evidence.status == "admitted" else f"coordinate_{evidence.status}"
        ),
    }


def _project_chronology_group(
    group: AadrChronologyEvidenceGroup,
) -> dict[str, object]:
    return _project_chronology_evidence(group.evidence, group.source_rows)


def _project_chronology_evidence(
    evidence: AadrChronologyEvidence,
    source_rows: tuple[AadrSourceRowLink, ...],
) -> dict[str, object]:
    return {
        "source_row_keys": [link.key for link in source_rows],
        "date_method": {
            "raw_value": evidence.date_method.raw_value,
            "normalized_value": evidence.date_method.normalized_value,
            "family": evidence.date_method.family,
        },
        "date_mean_bp": _project_numeric_evidence(
            evidence.date_mean_bp.raw_value,
            evidence.date_mean_bp.parsed_value,
            evidence.date_mean_bp.status,
            evidence.date_mean_bp.sign,
        ),
        "date_stddev_bp": _project_numeric_evidence(
            evidence.date_stddev_bp.raw_value,
            evidence.date_stddev_bp.parsed_value,
            evidence.date_stddev_bp.status,
            evidence.date_stddev_bp.sign,
        ),
        "full_date": {
            "raw_value": evidence.full_date.raw_value,
            "normalized_value": evidence.full_date.normalized_value,
            "status": evidence.full_date.status,
            "tokens": [
                _project_full_date_token(token) for token in evidence.full_date.tokens
            ],
        },
        "evaluation_status": evidence.evaluation_status,
        "refusal_reason_code": evidence.refusal_reason_code,
        "scientifically_admitted": evidence.scientifically_admitted,
    }


def _project_numeric_evidence(
    raw_value: str,
    parsed_value: Decimal | None,
    status: str,
    sign: str | None,
) -> dict[str, object]:
    return {
        "raw_value": raw_value,
        "decimal_value": str(parsed_value) if parsed_value is not None else None,
        "status": status,
        "sign": sign,
    }


def _project_full_date_token(token: AadrFullDateToken) -> dict[str, object]:
    return {
        "kind": token.kind,
        "raw_value": token.raw_value,
        "first_decimal_value": str(token.first_value),
        "second_decimal_value": str(token.second_value),
        "era": token.era,
        "normalized_start": token.normalized_start,
        "normalized_end": token.normalized_end,
    }


def _project_source_link(link: AadrSourceRowLink) -> dict[str, object]:
    return {
        "key": link.key,
        "source_file_key": link.source_file_key,
        "source_path": link.source_path,
        "source_release": link.source_release,
        "dataset_name": link.dataset_name,
        "source_sha256": link.source_sha256,
        "source_record_number": link.source_record_number,
        "source_line_start": link.source_line_start,
        "source_line_end": link.source_line_end,
    }


def _project_source_files(
    reconciliation: AadrPanelReconciliation,
) -> list[dict[str, object]]:
    return [
        {
            "source_file_key": _source_file_key(source_file),
            "source_path": source_file.source_path,
            "source_release": source_file.source_release,
            "dataset_name": source_file.dataset_name,
            "source_sha256": source_file.source_sha256,
            "source_byte_count": source_file.source_byte_count,
            "source_row_count": row_count,
            "column_names": list(column_names),
        }
        for source_file, (row_count, column_names) in _source_file_rows(
            reconciliation
        ).items()
    ]


def _source_file_rows(
    reconciliation: AadrPanelReconciliation,
) -> dict[AadrSourceFile, tuple[int, tuple[str, ...]]]:
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


def _source_file_key(source_file: AadrSourceFile) -> str:
    return source_file.key


def _source_file_sort_key(source_file: AadrSourceFile) -> tuple[str, ...]:
    return (_source_file_key(source_file),)


def _source_row_link(row: AadrSourceRow) -> AadrSourceRowLink:
    return AadrSourceRowLink(
        source_path=row.source.source_path,
        source_release=row.source.source_release,
        dataset_name=row.source.dataset_name,
        source_sha256=row.source.source_sha256,
        source_record_number=row.source_record_number,
        source_line_start=row.source_line_start,
        source_line_end=row.source_line_end,
    )


def _validate_reconciliation(reconciliation: AadrPanelReconciliation) -> None:
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
        row_count
        for row_count, _column_names in _source_file_rows(reconciliation).values()
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
    expected_links = tuple(_source_row_link(row) for row in record.source_evidence_rows)
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
        raise ValueError(
            "AADR chronology cannot be admitted by accountability projection"
        )


def _validate_unkeyed_row(
    unkeyed: AadrUnkeyedSourceRow, dataset_names: tuple[str, ...]
) -> None:
    row = unkeyed.source_evidence_row
    if row.genetic_id_raw.strip():
        raise ValueError("AADR unkeyed row unexpectedly has a Genetic ID")
    if unkeyed.genetic_id_raw != row.genetic_id_raw:
        raise ValueError("AADR unkeyed raw Genetic ID diverges from source evidence")
    if unkeyed.source_row != _source_row_link(row):
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
                raise ValueError(
                    "AADR coordinate evidence group changes source evidence"
                )


def _validate_chronology_group_evidence(
    record: AadrReconciledRecord,
    source_rows_by_key: dict[str, AadrSourceRow],
) -> None:
    for group in record.chronology_groups:
        for link in group.source_rows:
            if source_rows_by_key[link.key].chronology != group.evidence:
                raise ValueError(
                    "AADR chronology evidence group changes source evidence"
                )


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


def _iter_source_row_dataset_names(
    reconciliation: AadrPanelReconciliation,
) -> Iterator[str]:
    for record in reconciliation.records:
        for row in record.source_evidence_rows:
            yield row.source.dataset_name
    for unkeyed in reconciliation.unkeyed_rows:
        yield unkeyed.source_evidence_row.source.dataset_name


def _iter_source_evidence_rows(
    reconciliation: AadrPanelReconciliation,
) -> Iterator[AadrSourceRow]:
    for record in reconciliation.records:
        yield from record.source_evidence_rows
    for unkeyed in reconciliation.unkeyed_rows:
        yield unkeyed.source_evidence_row


def _iter_projected_coordinate_evidence(
    reconciliation: AadrPanelReconciliation,
) -> Iterator[AadrCoordinateEvidence]:
    for record in reconciliation.records:
        for group in record.coordinate_groups:
            yield group.evidence
    for unkeyed in reconciliation.unkeyed_rows:
        yield unkeyed.source_evidence_row.coordinates


def _iter_projected_chronology_evidence(
    reconciliation: AadrPanelReconciliation,
) -> Iterator[AadrChronologyEvidence]:
    for record in reconciliation.records:
        for group in record.chronology_groups:
            yield group.evidence
    for unkeyed in reconciliation.unkeyed_rows:
        yield unkeyed.source_evidence_row.chronology


def _counter_dict(
    values: Iterable[str], *, required: Iterable[str] = ()
) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(set(counts) | set(required))}


__all__ = [
    "AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION",
    "build_aadr_accountability_summary",
    "iter_aadr_accountability_json_lines",
    "iter_aadr_accountability_projection",
    "iter_aadr_accountability_records",
    "validate_aadr_accountability_summary",
]
