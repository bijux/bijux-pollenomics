"""Compact AADR source-accountability receipt and stream identity projection."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Iterator
from hashlib import sha256

from bijux_pollenomics.adna.species.homo_sapiens.materialization.models import (
    AadrSourceRow,
)
from bijux_pollenomics.adna.species.homo_sapiens.materialization.projection import (
    AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION,
    build_aadr_accountability_summary,
    iter_aadr_accountability_json_lines,
)
from bijux_pollenomics.adna.species.homo_sapiens.materialization.reconciliation import (
    AadrPanelReconciliation,
    AadrReconciledRecord,
)

from ..source_rows import validate_aadr_logical_source_path
from .contracts import (
    AADR_ACCOUNTABILITY_STREAM_MEDIA_TYPE,
    AADR_ACCOUNTABILITY_STREAM_STORAGE_CLASS,
    AADR_SOURCE_ACCOUNTABILITY_SCHEMA_VERSION,
    AADR_SOURCE_COUNTRY_POLICY_VERSION,
    POLITICAL_ENTITY_DISPOSITIONS,
)
from .models import (
    AadrPoliticalEntityEvidence,
    AadrPoliticalEntityReconciliation,
    AadrReleaseManifestIdentity,
)
from .political_entities import (
    FOUR_COUNTRY_EXACT_SOURCE_VALUES,
    reconcile_source_reported_political_entities,
    source_reported_political_entity_evidence,
)
from .validation import validate_aadr_source_accountability_receipt

_COORDINATE_EVIDENCE_STATUSES = (
    "admitted",
    "missing",
    "partial",
    "invalid_numeric",
    "non_finite",
    "out_of_range",
)
_RECONCILIATION_STATUSES = ("exact", "complementary", "conflict")
_COORDINATE_AVAILABILITY_STATUSES = ("present", "missing", "unusable")
_CHRONOLOGY_EVALUATION_STATUSES = ("review_required", "refused")
_CHRONOLOGY_REFUSAL_REASONS = (
    "method_specific_policy_required",
    "source_chronology_missing",
    "invalid_numeric_evidence",
)
_DATE_METHOD_FAMILIES = (
    "direct",
    "contextual",
    "modern",
    "known_historical",
    "modeled_relational",
    "unclassified",
)
_NUMERIC_STATUSES = ("parsed", "missing", "invalid", "non_finite")
_NUMERIC_SIGNS = ("negative", "zero", "positive", "null")
_FULL_DATE_STATUSES = ("parsed", "missing", "unparsed")
_POLITICAL_EVIDENCE_STATUSES = (
    "reported",
    "value_missing",
    "token_missing",
    "column_unavailable",
)


def build_aadr_accountability_stream_descriptor(
    reconciliation: AadrPanelReconciliation,
) -> dict[str, object]:
    """Hash the deterministic full projection without retaining its records."""
    digest = sha256()
    line_count = 0
    byte_count = 0
    for line in iter_aadr_accountability_json_lines(reconciliation):
        encoded = line.encode("utf-8")
        digest.update(encoded)
        line_count += 1
        byte_count += len(encoded)
    return {
        "schema_version": AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION,
        "media_type": AADR_ACCOUNTABILITY_STREAM_MEDIA_TYPE,
        "line_count": line_count,
        "byte_count": byte_count,
        "sha256": digest.hexdigest(),
        "materialized": False,
        "tracked": False,
        "storage_class": AADR_ACCOUNTABILITY_STREAM_STORAGE_CLASS,
    }


def build_aadr_source_accountability_receipt(
    reconciliation: AadrPanelReconciliation,
    *,
    release_manifest: AadrReleaseManifestIdentity,
) -> dict[str, object]:
    """Build one compact review receipt without admitting country or chronology."""
    _validate_input_identity(reconciliation, release_manifest)
    summary = build_aadr_accountability_summary(reconciliation)
    political_reconciliations = reconcile_source_reported_political_entities(
        reconciliation
    )
    record_pairs = tuple(
        zip(reconciliation.records, political_reconciliations, strict=True)
    )
    if any(
        record.genetic_id != political.genetic_id for record, political in record_pairs
    ):
        raise ValueError("AADR Political Entity reconciliation changed Genetic IDs")
    source_rows = tuple(_iter_source_rows(reconciliation))
    receipt: dict[str, object] = {
        "schema_version": AADR_SOURCE_ACCOUNTABILITY_SCHEMA_VERSION,
        "record_kind": "source_accountability_receipt",
        "source_family": "AADR",
        "source_release": release_manifest.source_release,
        "release_manifest": {
            "logical_path": release_manifest.logical_path,
            "sha256": release_manifest.sha256,
            "byte_count": release_manifest.byte_count,
        },
        "accountability_projection": {
            "summary": summary,
            "stream": build_aadr_accountability_stream_descriptor(reconciliation),
        },
        "source_reported_political_entity": {
            "policy_version": AADR_SOURCE_COUNTRY_POLICY_VERSION,
            "matching_rule": "outer_trimmed_case_sensitive_exact_source_value",
            "exact_source_values": [
                {"country_code": country_code, "source_value": source_value}
                for source_value, country_code in sorted(
                    FOUR_COUNTRY_EXACT_SOURCE_VALUES.items(),
                    key=lambda item: item[1],
                )
            ],
            "denominators": {
                "source_row_count": reconciliation.source_row_count,
                "keyed_source_row_count": sum(
                    len(record.source_rows) for record in reconciliation.records
                ),
                "unkeyed_source_row_count": len(reconciliation.unkeyed_rows),
                "genetic_id_count": len(reconciliation.records),
            },
            "physical_source_row_exact_value_counts": _physical_row_dispositions(
                source_rows
            ),
            "record_linked_source_row_disposition_counts": _linked_row_dispositions(
                record_pairs,
                unkeyed_source_row_count=len(reconciliation.unkeyed_rows),
            ),
            "genetic_id_disposition_counts": _counter_dict(
                (political.disposition for political in political_reconciliations),
                required=POLITICAL_ENTITY_DISPOSITIONS,
            ),
            "reconciliation_status_counts": _counter_dict(
                (
                    political.reconciliation_status
                    for political in political_reconciliations
                ),
                required=_RECONCILIATION_STATUSES,
            ),
            "evidence_status_counts": _counter_dict(
                (
                    source_reported_political_entity_evidence(row).status
                    for row in source_rows
                ),
                required=_POLITICAL_EVIDENCE_STATUSES,
            ),
            "source_value_counts": _source_value_counts(source_rows),
            "review_partitions": [
                _review_partition(disposition, record_pairs)
                for disposition in POLITICAL_ENTITY_DISPOSITIONS
            ],
        },
        "taxon_scope_status": "not_asserted_by_source",
        "scientifically_admitted": False,
        "country_assignment_admitted": False,
        "map_admitted": False,
    }
    validate_aadr_source_accountability_receipt(receipt)
    return receipt


def _validate_input_identity(
    reconciliation: AadrPanelReconciliation,
    release_manifest: AadrReleaseManifestIdentity,
) -> None:
    if not reconciliation.source_tables:
        raise ValueError("AADR accountability requires at least one source table")
    for table in reconciliation.source_tables:
        validate_aadr_logical_source_path(table.source.source_path)
        if table.source.source_release != release_manifest.source_release:
            raise ValueError("AADR source table release differs from release manifest")


def _iter_source_rows(
    reconciliation: AadrPanelReconciliation,
) -> Iterator[AadrSourceRow]:
    for record in reconciliation.records:
        yield from record.source_evidence_rows
    for unkeyed in reconciliation.unkeyed_rows:
        yield unkeyed.source_evidence_row


def _source_value_counts(
    source_rows: tuple[AadrSourceRow, ...],
) -> list[dict[str, object]]:
    counts = Counter(
        source_reported_political_entity_evidence(row) for row in source_rows
    )
    return [
        {
            "status": evidence.status,
            "raw_value": evidence.raw_value,
            "trimmed_value": evidence.trimmed_value,
            "source_row_count": counts[evidence],
        }
        for evidence in sorted(counts, key=_political_evidence_sort_key)
    ]


def _political_evidence_sort_key(
    evidence: AadrPoliticalEntityEvidence,
) -> tuple[str, str, str]:
    return (
        evidence.status,
        evidence.trimmed_value or "",
        evidence.raw_value or "",
    )


def _physical_row_dispositions(
    source_rows: tuple[AadrSourceRow, ...],
) -> dict[str, int]:
    return _counter_dict(
        (_physical_row_disposition(row) for row in source_rows),
        required=("DK", "FI", "NO", "SE", "other", "missing"),
    )


def _physical_row_disposition(row: AadrSourceRow) -> str:
    evidence = source_reported_political_entity_evidence(row)
    if evidence.status != "reported" or evidence.trimmed_value is None:
        return "missing"
    return FOUR_COUNTRY_EXACT_SOURCE_VALUES.get(evidence.trimmed_value, "other")


def _linked_row_dispositions(
    record_pairs: tuple[
        tuple[AadrReconciledRecord, AadrPoliticalEntityReconciliation], ...
    ],
    *,
    unkeyed_source_row_count: int,
) -> dict[str, int]:
    counts = Counter(
        {
            disposition: sum(
                len(record.source_rows)
                for record, political in record_pairs
                if political.disposition == disposition
            )
            for disposition in POLITICAL_ENTITY_DISPOSITIONS
        }
    )
    counts["unkeyed"] = unkeyed_source_row_count
    return {key: counts[key] for key in (*POLITICAL_ENTITY_DISPOSITIONS, "unkeyed")}


def _review_partition(
    disposition: str,
    record_pairs: tuple[
        tuple[AadrReconciledRecord, AadrPoliticalEntityReconciliation], ...
    ],
) -> dict[str, object]:
    selected = tuple(
        record
        for record, political in record_pairs
        if political.disposition == disposition
    )
    coordinate_groups = tuple(
        group for record in selected for group in record.coordinate_groups
    )
    chronology_groups = tuple(
        group for record in selected for group in record.chronology_groups
    )
    exact_source_value = next(
        (
            source_value
            for source_value, country_code in FOUR_COUNTRY_EXACT_SOURCE_VALUES.items()
            if country_code == disposition
        ),
        None,
    )
    return {
        "disposition": disposition,
        "country_code": disposition
        if disposition in {"DK", "FI", "NO", "SE"}
        else None,
        "exact_source_value": exact_source_value,
        "genetic_id_count": len(selected),
        "linked_source_row_count": sum(len(record.source_rows) for record in selected),
        "dataset_genetic_id_membership_counts": _counter_dict(
            (
                dataset_name
                for record in selected
                for dataset_name in record.dataset_names
            )
        ),
        "coordinate_review": {
            "evidence_group_count": len(coordinate_groups),
            "source_parse_status_counts": _counter_dict(
                (group.evidence.status for group in coordinate_groups),
                required=_COORDINATE_EVIDENCE_STATUSES,
            ),
            "genetic_id_availability_counts": _counter_dict(
                (_coordinate_availability(record) for record in selected),
                required=_COORDINATE_AVAILABILITY_STATUSES,
            ),
            "reconciliation_status_counts": _counter_dict(
                (record.coordinate_status for record in selected),
                required=_RECONCILIATION_STATUSES,
            ),
            "country_assignment_admitted": False,
            "map_admitted": False,
        },
        "chronology_review": {
            "evidence_group_count": len(chronology_groups),
            "evaluation_status_counts": _counter_dict(
                (group.evidence.evaluation_status for group in chronology_groups),
                required=_CHRONOLOGY_EVALUATION_STATUSES,
            ),
            "refusal_reason_counts": _counter_dict(
                (group.evidence.refusal_reason_code for group in chronology_groups),
                required=_CHRONOLOGY_REFUSAL_REASONS,
            ),
            "date_method_family_counts": _counter_dict(
                (group.evidence.date_method.family for group in chronology_groups),
                required=_DATE_METHOD_FAMILIES,
            ),
            "date_mean_status_counts": _counter_dict(
                (group.evidence.date_mean_bp.status for group in chronology_groups),
                required=_NUMERIC_STATUSES,
            ),
            "date_mean_sign_counts": _counter_dict(
                (
                    group.evidence.date_mean_bp.sign or "null"
                    for group in chronology_groups
                ),
                required=_NUMERIC_SIGNS,
            ),
            "date_stddev_status_counts": _counter_dict(
                (group.evidence.date_stddev_bp.status for group in chronology_groups),
                required=_NUMERIC_STATUSES,
            ),
            "date_stddev_sign_counts": _counter_dict(
                (
                    group.evidence.date_stddev_bp.sign or "null"
                    for group in chronology_groups
                ),
                required=_NUMERIC_SIGNS,
            ),
            "full_date_status_counts": _counter_dict(
                (group.evidence.full_date.status for group in chronology_groups),
                required=_FULL_DATE_STATUSES,
            ),
            "reconciliation_status_counts": _counter_dict(
                (record.chronology_status for record in selected),
                required=_RECONCILIATION_STATUSES,
            ),
            "scientifically_admitted_count": 0,
            "scientifically_admitted": False,
        },
        "taxon_scope_status": "not_asserted_by_source",
        "scientifically_admitted": False,
        "country_assignment_admitted": False,
        "map_admitted": False,
    }


def _coordinate_availability(record: AadrReconciledRecord) -> str:
    statuses = {group.evidence.status for group in record.coordinate_groups}
    if "admitted" in statuses:
        return "present"
    if statuses == {"missing"}:
        return "missing"
    return "unusable"


def _counter_dict(
    values: Iterable[str],
    *,
    required: Iterable[str] = (),
) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(set(counts) | set(required))}


__all__ = [
    "build_aadr_accountability_stream_descriptor",
    "build_aadr_source_accountability_receipt",
]
