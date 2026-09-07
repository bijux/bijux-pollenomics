"""Deterministic AADR panel reconciliation without evidence collapse."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal

from .chronology import AadrChronologyEvidence, AadrNumericEvidence
from .models import (
    AadrCoordinateEvidence,
    AadrSourceRow,
    AadrSourceTable,
    TaxonScopeStatus,
)

ReconciliationStatus = Literal["exact", "complementary", "conflict"]


@dataclass(frozen=True, slots=True)
class AadrSourceRowLink:
    """Stable lookup identity for one retained physical source row."""

    source_path: str
    source_release: str
    dataset_name: str
    source_sha256: str
    source_record_number: int
    source_line_start: int
    source_line_end: int

    @property
    def key(self) -> str:
        """Return a collision-resistant source-row key."""
        return (
            f"sha256:{self.source_sha256}:dataset:{self.dataset_name}:"
            f"record:{self.source_record_number}"
        )


@dataclass(frozen=True, slots=True)
class AadrCoordinateEvidenceGroup:
    """One atomic coordinate-pair claim and all rows that reported it."""

    evidence: AadrCoordinateEvidence
    source_rows: tuple[AadrSourceRowLink, ...]


@dataclass(frozen=True, slots=True)
class AadrChronologyEvidenceGroup:
    """One atomic chronology-evidence tuple and all rows that reported it."""

    evidence: AadrChronologyEvidence
    source_rows: tuple[AadrSourceRowLink, ...]


@dataclass(frozen=True, slots=True)
class AadrReconciledRecord:
    """All panel rows sharing one outer-trimmed source Genetic ID."""

    genetic_id: str
    genetic_id_raw_values: tuple[str, ...]
    dataset_names: tuple[str, ...]
    source_rows: tuple[AadrSourceRowLink, ...]
    coordinate_groups: tuple[AadrCoordinateEvidenceGroup, ...]
    chronology_groups: tuple[AadrChronologyEvidenceGroup, ...]
    coordinate_status: ReconciliationStatus
    chronology_status: ReconciliationStatus
    panel_status: ReconciliationStatus
    reconciliation_status: ReconciliationStatus
    taxon_scope_status: TaxonScopeStatus = field(
        default="not_asserted_by_source", init=False
    )


@dataclass(frozen=True, slots=True)
class AadrUnkeyedSourceRow:
    """An accountability row refused from Genetic-ID reconciliation."""

    source_row: AadrSourceRowLink
    genetic_id_raw: str
    refusal_reason_code: Literal["genetic_id_missing"] = "genetic_id_missing"
    taxon_scope_status: TaxonScopeStatus = field(
        default="not_asserted_by_source", init=False
    )


@dataclass(frozen=True, slots=True)
class AadrPanelReconciliation:
    """Deterministic reconciliation plus explicit unkeyed-row accountability."""

    dataset_names: tuple[str, ...]
    records: tuple[AadrReconciledRecord, ...]
    unkeyed_rows: tuple[AadrUnkeyedSourceRow, ...]
    source_row_count: int


def reconcile_aadr_panels(
    tables: Iterable[AadrSourceTable],
) -> AadrPanelReconciliation:
    """Group panel rows without selecting winners or synthesizing evidence."""
    source_tables = tuple(tables)
    panel_names = tuple(sorted({table.source.dataset_name for table in source_tables}))
    keyed_rows: dict[str, list[AadrSourceRow]] = defaultdict(list)
    unkeyed_rows: list[AadrUnkeyedSourceRow] = []
    source_row_count = 0
    for table in source_tables:
        for row in table.rows:
            source_row_count += 1
            genetic_id = row.genetic_id_raw.strip()
            if not genetic_id:
                unkeyed_rows.append(
                    AadrUnkeyedSourceRow(
                        source_row=_source_row_link(row),
                        genetic_id_raw=row.genetic_id_raw,
                    )
                )
                continue
            keyed_rows[genetic_id].append(row)
    records = tuple(
        _reconcile_record(genetic_id, keyed_rows[genetic_id], panel_names)
        for genetic_id in sorted(keyed_rows)
    )
    sorted_unkeyed = tuple(
        sorted(unkeyed_rows, key=lambda item: _source_link_sort_key(item.source_row))
    )
    linked_row_count = sum(len(record.source_rows) for record in records) + len(
        sorted_unkeyed
    )
    if linked_row_count != source_row_count:
        raise ValueError("AADR reconciliation did not account for every source row")
    return AadrPanelReconciliation(
        dataset_names=panel_names,
        records=records,
        unkeyed_rows=sorted_unkeyed,
        source_row_count=source_row_count,
    )


def _reconcile_record(
    genetic_id: str,
    source_rows: list[AadrSourceRow],
    panel_names: tuple[str, ...],
) -> AadrReconciledRecord:
    ordered_rows = tuple(sorted(source_rows, key=_source_row_sort_key))
    row_links = tuple(_source_row_link(row) for row in ordered_rows)
    coordinate_groups = _coordinate_groups(ordered_rows)
    chronology_groups = _chronology_groups(ordered_rows)
    coordinate_status = _coordinate_reconciliation_status(coordinate_groups)
    chronology_status = _chronology_reconciliation_status(chronology_groups)
    dataset_names = tuple(sorted({row.source.dataset_name for row in ordered_rows}))
    panel_status: ReconciliationStatus = (
        "exact" if dataset_names == panel_names else "complementary"
    )
    return AadrReconciledRecord(
        genetic_id=genetic_id,
        genetic_id_raw_values=tuple(
            sorted({row.genetic_id_raw for row in ordered_rows})
        ),
        dataset_names=dataset_names,
        source_rows=row_links,
        coordinate_groups=coordinate_groups,
        chronology_groups=chronology_groups,
        coordinate_status=coordinate_status,
        chronology_status=chronology_status,
        panel_status=panel_status,
        reconciliation_status=_overall_status(
            panel_status, coordinate_status, chronology_status
        ),
    )


def _coordinate_groups(
    source_rows: tuple[AadrSourceRow, ...],
) -> tuple[AadrCoordinateEvidenceGroup, ...]:
    grouped: dict[AadrCoordinateEvidence, list[AadrSourceRowLink]] = defaultdict(list)
    for row in source_rows:
        grouped[row.coordinates].append(_source_row_link(row))
    return tuple(
        AadrCoordinateEvidenceGroup(
            evidence=evidence,
            source_rows=tuple(sorted(links, key=_source_link_sort_key)),
        )
        for evidence, links in sorted(
            grouped.items(), key=lambda item: _coordinate_sort_key(item[0])
        )
    )


def _chronology_groups(
    source_rows: tuple[AadrSourceRow, ...],
) -> tuple[AadrChronologyEvidenceGroup, ...]:
    grouped: dict[AadrChronologyEvidence, list[AadrSourceRowLink]] = defaultdict(list)
    for row in source_rows:
        grouped[row.chronology].append(_source_row_link(row))
    return tuple(
        AadrChronologyEvidenceGroup(
            evidence=evidence,
            source_rows=tuple(sorted(links, key=_source_link_sort_key)),
        )
        for evidence, links in sorted(
            grouped.items(), key=lambda item: _chronology_sort_key(item[0])
        )
    )


def _coordinate_reconciliation_status(
    groups: tuple[AadrCoordinateEvidenceGroup, ...],
) -> ReconciliationStatus:
    claims = {_coordinate_claim(group.evidence) for group in groups}
    substantive_claims = claims - {None}
    if len(substantive_claims) > 1:
        return "conflict"
    if None in claims and substantive_claims:
        return "complementary"
    return "exact"


def _chronology_reconciliation_status(
    groups: tuple[AadrChronologyEvidenceGroup, ...],
) -> ReconciliationStatus:
    claims = tuple(_chronology_claim(group.evidence) for group in groups)
    if any(
        _chronology_claims_conflict(left, right)
        for index, left in enumerate(claims)
        for right in claims[index + 1 :]
    ):
        return "conflict"
    if len(set(claims)) > 1:
        return "complementary"
    return "exact"


def _overall_status(
    *statuses: ReconciliationStatus,
) -> ReconciliationStatus:
    if "conflict" in statuses:
        return "conflict"
    if "complementary" in statuses:
        return "complementary"
    return "exact"


def _coordinate_claim(
    evidence: AadrCoordinateEvidence,
) -> tuple[object, ...] | None:
    if evidence.status == "missing":
        return None
    if evidence.status == "admitted":
        return ("admitted", evidence.latitude, evidence.longitude)
    return (
        evidence.status,
        evidence.latitude_raw.strip(),
        evidence.longitude_raw.strip(),
    )


def _chronology_claim(
    evidence: AadrChronologyEvidence,
) -> tuple[object | None, ...]:
    return (
        evidence.date_method.normalized_value or None,
        _numeric_claim(evidence.date_mean_bp),
        _numeric_claim(evidence.date_stddev_bp),
        evidence.full_date.normalized_value or None,
    )


def _numeric_claim(evidence: AadrNumericEvidence) -> object | None:
    if evidence.status == "missing":
        return None
    if evidence.status == "parsed":
        return evidence.parsed_value
    return (evidence.status, evidence.raw_value.strip())


def _chronology_claims_conflict(
    left: tuple[object | None, ...], right: tuple[object | None, ...]
) -> bool:
    return any(
        left_value is not None and right_value is not None and left_value != right_value
        for left_value, right_value in zip(left, right, strict=True)
    )


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


def _source_row_sort_key(row: AadrSourceRow) -> tuple[object, ...]:
    return _source_link_sort_key(_source_row_link(row))


def _source_link_sort_key(link: AadrSourceRowLink) -> tuple[object, ...]:
    return (
        link.source_release,
        link.dataset_name,
        link.source_sha256,
        link.source_record_number,
        link.source_line_start,
    )


def _coordinate_sort_key(evidence: AadrCoordinateEvidence) -> tuple[object, ...]:
    return (
        evidence.status,
        evidence.latitude_raw,
        evidence.longitude_raw,
        evidence.latitude if evidence.latitude is not None else float("-inf"),
        evidence.longitude if evidence.longitude is not None else float("-inf"),
    )


def _chronology_sort_key(evidence: AadrChronologyEvidence) -> tuple[str, ...]:
    return (
        evidence.date_method.raw_value,
        evidence.date_mean_bp.raw_value,
        evidence.date_stddev_bp.raw_value,
        evidence.full_date.raw_value,
    )


__all__ = [
    "AadrChronologyEvidenceGroup",
    "AadrCoordinateEvidenceGroup",
    "AadrPanelReconciliation",
    "AadrReconciledRecord",
    "AadrSourceRowLink",
    "AadrUnkeyedSourceRow",
    "ReconciliationStatus",
    "reconcile_aadr_panels",
]
