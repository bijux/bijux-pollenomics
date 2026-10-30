"""Resolve complete locality chronology ownership against original sample rows."""

from __future__ import annotations

from ...domain.models.localities import AdnaSampleChronologySupport


def _resolve_sample_chronologies(
    locality: dict[str, object], sample_rows: tuple[dict[str, object], ...]
) -> tuple[AdnaSampleChronologySupport, ...]:
    """Keep exact children; missing ownership never falls back to the site hull."""
    sample_ids = locality.get("sample_ids")
    if not isinstance(sample_ids, list) or any(
        not isinstance(value, str) or not value or value != value.strip()
        for value in sample_ids
    ):
        raise TypeError("Animal locality sample IDs must be explicit nonblank text")
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("Animal locality sample identities must be unique")
    count = locality.get("sample_count")
    if type(count) is not int or count != len(sample_ids):
        raise ValueError(
            "Animal locality sample count must equal its declared ownership"
        )
    originals = tuple(
        AdnaSampleChronologySupport.from_sample_payload(row) for row in sample_rows
    )
    by_owner = {support.sample_id: support for support in originals}
    if any(not owner or owner != owner.strip() for owner in by_owner) or len(
        by_owner
    ) != len(originals):
        raise ValueError("Animal chronology sample source identities must be unique")
    if set(by_owner) != set(sample_ids):
        raise ValueError(
            "Animal locality membership requires exact matched source owners"
        )
    if "sample_chronologies" not in locality:
        return originals
    payloads = locality["sample_chronologies"]
    if not isinstance(payloads, list) or any(
        not isinstance(item, dict) for item in payloads
    ):
        raise TypeError("Animal locality sample chronology supports must be objects")
    supports = tuple(AdnaSampleChronologySupport.from_dict(item) for item in payloads)
    support_ids = [support.sample_id for support in supports]
    if len(support_ids) != len(set(support_ids)) or set(support_ids) != set(sample_ids):
        raise ValueError(
            "Animal chronology supports require complete unique membership"
        )
    if any(by_owner[support.sample_id] != support for support in supports):
        raise ValueError(
            "Animal chronology support requires exact matched original sample values"
        )
    return supports
