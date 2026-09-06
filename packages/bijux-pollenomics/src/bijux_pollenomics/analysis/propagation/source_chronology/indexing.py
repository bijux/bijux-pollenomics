"""Relational chronology indexing and fail-closed claim selection."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .admission import canonical_claim_interval, chronology_reason
from .identity import canonical, optional_text


@dataclass(frozen=True)
class SourceChronologySelection:
    """One selected chronology claim or an explicit selection refusal."""

    claim: Mapping[str, object] | None
    selection_posture: str
    refusal_reason: str | None = None
    chronology_reason_code: str | None = None


def source_chronologies(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, tuple[Mapping[str, object], ...]]:
    """Index distinct claims by sample while retaining conflicting duplicates."""
    indexed: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    seen: dict[tuple[str, str], str] = {}
    for row in rows:
        source_record_id = optional_text(row.get("source_record_id"))
        claim_id = optional_text(row.get("chronology_claim_id"))
        if source_record_id is None or claim_id is None:
            continue
        key = source_record_id, claim_id
        encoded = canonical(row)
        existing = seen.get(key)
        if existing is None:
            seen[key] = encoded
            indexed[source_record_id].append(row)
        elif existing != encoded:
            indexed[source_record_id].append(row)
    return {
        key: tuple(sorted(values, key=lambda row: str(row["chronology_claim_id"])))
        for key, values in indexed.items()
    }


def select_source_chronology(
    claims: Sequence[Mapping[str, object]],
) -> SourceChronologySelection:
    """Prefer one usable source default, otherwise one usable alternative.

    Multiple usable defaults or alternatives are not resolved by list order. A
    source default that cannot supply a comparable canonical BP interval does not
    suppress a unique usable non-default claim.
    """
    representations: dict[tuple[str, str], set[str]] = defaultdict(set)
    for claim in claims:
        identity = (
            optional_text(claim.get("source_record_id")) or "",
            optional_text(claim.get("chronology_claim_id")) or "",
        )
        representations[identity].add(canonical(claim))
    if any(len(values) > 1 for values in representations.values()):
        return SourceChronologySelection(
            claim=None,
            selection_posture="refused_conflicting_claim_representation",
            refusal_reason="conflicting_source_chronology_claim",
        )
    usable_defaults = tuple(
        claim
        for claim in claims
        if claim.get("is_default_chronology") is True
        and canonical_claim_interval(claim) is not None
    )
    if len(usable_defaults) == 1:
        return SourceChronologySelection(
            claim=next(iter(usable_defaults)),
            selection_posture="selected_source_default",
        )
    if len(usable_defaults) > 1:
        return SourceChronologySelection(
            claim=None,
            selection_posture="refused_ambiguous_source_defaults",
            refusal_reason="ambiguous_source_default_chronology",
        )

    usable_alternatives = tuple(
        claim
        for claim in claims
        if claim.get("is_default_chronology") is not True
        and canonical_claim_interval(claim) is not None
    )
    if len(usable_alternatives) == 1:
        return SourceChronologySelection(
            claim=next(iter(usable_alternatives)),
            selection_posture="selected_unique_nondefault",
        )
    if len(usable_alternatives) > 1:
        return SourceChronologySelection(
            claim=None,
            selection_posture="refused_ambiguous_nondefault_alternatives",
            refusal_reason="ambiguous_comparable_alternative_chronology",
        )

    defaults = tuple(
        claim for claim in claims if claim.get("is_default_chronology") is True
    )
    if len(defaults) == 1:
        default = next(iter(defaults))
        reason = (
            "non_comparable_source_default_chronology"
            if default.get("comparability_status") != "comparable"
            else "invalid_source_default_chronology_interval"
        )
        return SourceChronologySelection(
            claim=None,
            selection_posture="refused_no_comparable_chronology",
            refusal_reason=reason,
            chronology_reason_code=chronology_reason(default),
        )
    return SourceChronologySelection(
        claim=None,
        selection_posture="refused_no_comparable_chronology",
        refusal_reason="missing_comparable_source_chronology",
    )


__all__ = [
    "SourceChronologySelection",
    "select_source_chronology",
    "source_chronologies",
]
