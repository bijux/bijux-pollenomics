"""Retain refused native parents and account for their known child rows.

Only the provider's declared hierarchy is traversed. A malformed container has
no extractable row population; its literal value is retained, never guessed.
One failed parent retains its subtree once, rather than copying every child.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

from ..diagnostics import add_orphan
from ..identifiers import optional_source_id
from ..state import RelationalBuildState


def _list_rows(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def chronology_source_counts(value: object) -> Counter[str]:
    wrappers = _list_rows(value)
    counts = Counter({"chronology_rows": len(wrappers)})
    for wrapper in wrappers:
        if isinstance(wrapper, Mapping):
            chronology = wrapper.get("chronology")
            if isinstance(chronology, Mapping):
                counts["chronology_control_rows"] += len(
                    _list_rows(chronology.get("chroncontrols"))
                )
    return +counts


def parent_source_counts(record: Mapping[str, object], level: str) -> Counter[str]:
    """Count declared rows, including malformed list entries, below a parent."""
    if level == "sample":
        return +Counter(
            sample_rows=1,
            age_claim_rows=len(_list_rows(record.get("ages"))),
            observation_rows=len(_list_rows(record.get("datum"))),
        )
    if level == "dataset":
        samples = _list_rows(record.get("samples"))
        counts = Counter(dataset_rows=1, sample_rows=len(samples))
        for sample in samples:
            if isinstance(sample, Mapping):
                children = parent_source_counts(sample, "sample")
                children.pop("sample_rows")
                counts.update(children)
        return +counts
    if level == "collection_unit":
        counts = Counter(collection_unit_rows=1)
        counts.update(chronology_source_counts(record.get("chronologies")))
        dataset = record.get("dataset")
        if isinstance(dataset, Mapping):
            counts.update(parent_source_counts(dataset, "dataset"))
        return +counts
    if level == "site":
        counts = Counter(site_rows=1)
        unit = record.get("collectionunit")
        if isinstance(unit, Mapping):
            counts.update(parent_source_counts(unit, "collection_unit"))
        return +counts
    raise ValueError(f"Unsupported native parent level: {level}")


def required_parent_id(
    state: RelationalBuildState,
    record: Mapping[str, object],
    *,
    level: str,
    id_field: str,
    parent_id: str | None,
    own_counter: str,
) -> str | None:
    """An identity failure excludes this row and every known dependent row.

    The caller has already counted this parent. Descendant counters are added
    here only on refusal, because their normal projection will not be reached.
    """
    source_id = optional_source_id(record.get(id_field))
    if source_id is None:
        counts = parent_source_counts(record, level)
        add_orphan(
            state.orphans,
            level,
            parent_id,
            "missing_source_identifier",
            source_value=record,
            excluded_source_row_counts=counts,
        )
        counts[own_counter] -= 1
        state.source_counts.update(counts)
    return source_id


def native_rows(
    state: RelationalBuildState,
    record: Mapping[str, object],
    field: str,
    *,
    entity_type: str,
    parent_id: str,
) -> list[object]:
    value = record.get(field)
    if isinstance(value, list):
        return value
    if field in record:
        add_orphan(
            state.orphans,
            entity_type,
            parent_id,
            f"invalid_{field}_container",
            source_value=value,
            source_field_present=True,
            excluded_source_row_counts={},
        )
    return []


def refuse_chronology_sibling(
    state: RelationalBuildState, unit: Mapping[str, object], unit_id: str
) -> None:
    """Dataset admission also gates its unit-owned chronology projection."""
    value = {
        field: unit[field]
        for field in ("chronologies", "defaultchronology")
        if field in unit
    }
    if not value:
        return
    counts = chronology_source_counts(value.get("chronologies"))
    state.source_counts.update(counts)
    add_orphan(
        state.orphans,
        "collection_unit",
        unit_id,
        "dataset_identity_unavailable_for_chronology_projection",
        source_value=value,
        source_field_present=True,
        excluded_source_row_counts=counts,
    )


def refuse_dataset_context(
    state: RelationalBuildState, site: Mapping[str, object], site_id: str
) -> None:
    """Preserve site-level dataset metadata when its native dataset is blocked."""
    if "dataset" in site:
        add_orphan(
            state.orphans,
            "site",
            site_id,
            "dataset_context_unavailable_for_projection",
            source_value=site["dataset"],
            source_field_present=True,
            excluded_source_row_counts={},
        )
