"""Deterministic facet metadata for source-chronology selectors."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import TypedDict

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SourceChronologyNode,
)

COUNTRY_NAMES = {
    "SE": "Sweden",
    "DK": "Denmark",
    "NO": "Norway",
    "FI": "Finland",
}

SOURCE_ECOLOGICAL_CODE_LABELS = {
    "AQVP": "Aquatic Vascular Plants",
    "TRSH": "Trees and Shrubs",
    "UPHE": "Upland Herbs",
}


class _FacetAggregate(TypedDict):
    node_count: int
    observation_denominator: int
    time_min_bp: float | int | None
    time_max_bp: float | int | None


def source_ecological_code_label(code: str | None) -> str | None:
    """Return a source meaning label without claiming reviewed equivalence."""
    if code is None:
        return None
    return SOURCE_ECOLOGICAL_CODE_LABELS.get(code, code)


def build_facet_metadata(
    nodes: Sequence[SourceChronologyNode], *, node_level: str
) -> dict[str, object]:
    """Return exact feature and observation denominators for selectable facets."""
    selected = [node for node in nodes if node.node_level == node_level]
    return {
        "schema_version": "neotoma-source-chronology-facets.v2",
        "node_level": node_level,
        **_facet_summary(selected),
        "country_counts": _country_counts(selected),
        "source_unit_counts": _value_counts(
            (node.source_unit, len(node.observation_ids)) for node in selected
        ),
        "source_ecological_codes": (
            _code_facets(selected) if node_level == "source_ecological_code" else []
        ),
        "source_taxa": _taxon_facets(selected) if node_level == "source_taxon" else [],
    }


def _value_counts(rows: Iterable[tuple[str, int]]) -> list[dict[str, object]]:
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for value, observations in rows:
        counts[value][0] += 1
        counts[value][1] += observations
    return [
        {
            "value": value,
            "node_count": counts[value][0],
            "observation_denominator": counts[value][1],
        }
        for value in sorted(counts)
    ]


def _country_counts(nodes: Sequence[SourceChronologyNode]) -> list[dict[str, object]]:
    counts = {country: [0, 0] for country in COUNTRY_NAMES.values()}
    for node in nodes:
        row = counts[COUNTRY_NAMES[node.country_code]]
        row[0] += 1
        row[1] += len(node.observation_ids)
    return [
        {
            "value": country,
            "node_count": counts[country][0],
            "observation_denominator": counts[country][1],
        }
        for country in COUNTRY_NAMES.values()
    ]


def _code_facets(nodes: Sequence[SourceChronologyNode]) -> list[dict[str, object]]:
    aggregates: dict[str, _FacetAggregate] = defaultdict(_empty_facet_aggregate)
    for node in nodes:
        code = node.source_ecological_group
        if code is None:
            raise ValueError("source ecological-code node lost its literal code")
        _add_to_facet_aggregate(aggregates[code], node)
    return [
        {
            "value": code,
            "label": source_ecological_code_label(code),
            "source_code": code,
            "feature_key": f"source:neotoma:ecological-code:{code}",
            **aggregates[code],
        }
        for code in sorted(aggregates)
    ]


def _taxon_facets(nodes: Sequence[SourceChronologyNode]) -> list[dict[str, object]]:
    aggregates: dict[tuple[str, str, str], _FacetAggregate] = defaultdict(
        _empty_facet_aggregate
    )
    for node in nodes:
        if node.source_taxon_id is None or node.source_reported_name is None:
            raise ValueError("source taxon node lost exact source identity")
        key = (
            node.feature_key,
            str(node.source_taxon_id),
            node.source_reported_name,
        )
        _add_to_facet_aggregate(aggregates[key], node)
    return [
        {
            "value": feature_key,
            "source_taxon_id": taxon_id,
            "label": name,
            **aggregates[(feature_key, taxon_id, name)],
        }
        for feature_key, taxon_id, name in sorted(
            aggregates, key=lambda row: (row[2].casefold(), row[1], row[0])
        )
    ]


def _facet_summary(nodes: Sequence[SourceChronologyNode]) -> _FacetAggregate:
    aggregate = _empty_facet_aggregate()
    for node in nodes:
        _add_to_facet_aggregate(aggregate, node)
    return aggregate


def _empty_facet_aggregate() -> _FacetAggregate:
    return {
        "node_count": 0,
        "observation_denominator": 0,
        "time_min_bp": None,
        "time_max_bp": None,
    }


def _add_to_facet_aggregate(
    aggregate: _FacetAggregate, node: SourceChronologyNode
) -> None:
    aggregate["node_count"] += 1
    aggregate["observation_denominator"] += len(node.observation_ids)
    if aggregate["time_min_bp"] is None or node.younger_bp < aggregate["time_min_bp"]:
        aggregate["time_min_bp"] = node.younger_bp
    if aggregate["time_max_bp"] is None or node.older_bp > aggregate["time_max_bp"]:
        aggregate["time_max_bp"] = node.older_bp


__all__ = [
    "COUNTRY_NAMES",
    "SOURCE_ECOLOGICAL_CODE_LABELS",
    "build_facet_metadata",
    "source_ecological_code_label",
]
