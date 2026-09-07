"""Lossless reconciliation of source-reported AADR Political Entity evidence."""

from __future__ import annotations

from collections import defaultdict

from bijux_pollenomics.adna.species.homo_sapiens.materialization.models import (
    AadrSourceRow,
)
from bijux_pollenomics.adna.species.homo_sapiens.materialization.reconciliation import (
    AadrPanelReconciliation,
    AadrReconciledRecord,
    AadrSourceRowLink,
)

from .models import (
    AadrPoliticalEntityEvidence,
    AadrPoliticalEntityEvidenceGroup,
    AadrPoliticalEntityReconciliation,
    PoliticalEntityDisposition,
    PoliticalEntityReconciliationStatus,
)

FOUR_COUNTRY_EXACT_SOURCE_VALUES: dict[str, PoliticalEntityDisposition] = {
    "Denmark": "DK",
    "Finland": "FI",
    "Norway": "NO",
    "Sweden": "SE",
}

_POLITICAL_ENTITY_COLUMN_PREFIX = "political entity"


def source_reported_political_entity_evidence(
    row: AadrSourceRow,
) -> AadrPoliticalEntityEvidence:
    """Read one Political Entity token without guessing a country from other fields."""
    matching_indexes = tuple(
        index
        for index, column_name in enumerate(row.column_names)
        if column_name.casefold() == _POLITICAL_ENTITY_COLUMN_PREFIX
        or column_name.casefold().startswith(_POLITICAL_ENTITY_COLUMN_PREFIX)
    )
    if len(matching_indexes) > 1:
        raise ValueError("AADR Political Entity source columns are ambiguous")
    if not matching_indexes:
        return AadrPoliticalEntityEvidence(
            raw_value=None,
            trimmed_value=None,
            status="column_unavailable",
        )
    index = matching_indexes[0]
    if index >= len(row.raw_tokens):
        return AadrPoliticalEntityEvidence(
            raw_value=None,
            trimmed_value=None,
            status="token_missing",
        )
    raw_value = row.raw_tokens[index]
    trimmed_value = raw_value.strip()
    if not trimmed_value:
        return AadrPoliticalEntityEvidence(
            raw_value=raw_value,
            trimmed_value=None,
            status="value_missing",
        )
    return AadrPoliticalEntityEvidence(
        raw_value=raw_value,
        trimmed_value=trimmed_value,
        status="reported",
    )


def reconcile_source_reported_political_entities(
    reconciliation: AadrPanelReconciliation,
) -> tuple[AadrPoliticalEntityReconciliation, ...]:
    """Reconcile exact source tokens without selecting a winning panel row."""
    return tuple(_reconcile_record(record) for record in reconciliation.records)


def _reconcile_record(
    record: AadrReconciledRecord,
) -> AadrPoliticalEntityReconciliation:
    grouped: dict[AadrPoliticalEntityEvidence, list[AadrSourceRowLink]] = defaultdict(
        list
    )
    for row, link in zip(
        record.source_evidence_rows,
        record.source_rows,
        strict=True,
    ):
        grouped[source_reported_political_entity_evidence(row)].append(link)
    groups = tuple(
        AadrPoliticalEntityEvidenceGroup(
            evidence=evidence,
            source_rows=tuple(sorted(links, key=lambda link: link.key)),
        )
        for evidence, links in sorted(
            grouped.items(), key=lambda item: _evidence_sort_key(item[0])
        )
    )
    reported_values = {
        group.evidence.trimmed_value
        for group in groups
        if group.evidence.status == "reported"
        and group.evidence.trimmed_value is not None
    }
    if len(reported_values) > 1:
        status: PoliticalEntityReconciliationStatus = "conflict"
        disposition: PoliticalEntityDisposition = "conflict"
    elif reported_values:
        reported_value = next(iter(reported_values))
        status = (
            "complementary"
            if any(group.evidence.status != "reported" for group in groups)
            else "exact"
        )
        disposition = FOUR_COUNTRY_EXACT_SOURCE_VALUES.get(reported_value, "other")
    else:
        status = "exact"
        disposition = "missing"
    return AadrPoliticalEntityReconciliation(
        genetic_id=record.genetic_id,
        evidence_groups=groups,
        reconciliation_status=status,
        disposition=disposition,
    )


def _evidence_sort_key(
    evidence: AadrPoliticalEntityEvidence,
) -> tuple[str, str, str]:
    return (
        evidence.status,
        evidence.trimmed_value or "",
        evidence.raw_value or "",
    )


__all__ = [
    "FOUR_COUNTRY_EXACT_SOURCE_VALUES",
    "reconcile_source_reported_political_entities",
    "source_reported_political_entity_evidence",
]
