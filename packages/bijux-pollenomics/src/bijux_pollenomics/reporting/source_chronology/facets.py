"""Deterministic facet metadata for source-chronology selectors."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SourceChronologyNode,
)

COUNTRY_NAMES = {
    "SE": "Sweden",
    "DK": "Denmark",
    "NO": "Norway",
    "FI": "Finland",
}


def build_facet_metadata(
    nodes: Sequence[SourceChronologyNode], *, node_level: str
) -> dict[str, object]:
    """Return exact feature and observation denominators for selectable facets."""
    selected = [node for node in nodes if node.node_level == node_level]
    return {
        "schema_version": "neotoma-source-chronology-facets.v1",
        "node_level": node_level,
        "node_count": len(selected),
        "observation_denominator": sum(len(node.observation_ids) for node in selected),
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
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for node in nodes:
        code = node.source_ecological_group
        if code is None:
            raise ValueError("source ecological-code node lost its literal code")
        counts[code][0] += 1
        counts[code][1] += len(node.observation_ids)
    return [
        {
            "value": code,
            "label": code,
            "feature_key": f"source:neotoma:ecological-code:{code}",
            "node_count": counts[code][0],
            "observation_denominator": counts[code][1],
        }
        for code in sorted(counts)
    ]


def _taxon_facets(nodes: Sequence[SourceChronologyNode]) -> list[dict[str, object]]:
    counts: dict[tuple[str, str, str], list[int]] = defaultdict(lambda: [0, 0])
    for node in nodes:
        if node.source_taxon_id is None or node.source_reported_name is None:
            raise ValueError("source taxon node lost exact source identity")
        key = (
            node.feature_key,
            str(node.source_taxon_id),
            node.source_reported_name,
        )
        counts[key][0] += 1
        counts[key][1] += len(node.observation_ids)
    return [
        {
            "value": feature_key,
            "source_taxon_id": taxon_id,
            "label": name,
            "node_count": counts[(feature_key, taxon_id, name)][0],
            "observation_denominator": counts[(feature_key, taxon_id, name)][1],
        }
        for feature_key, taxon_id, name in sorted(
            counts, key=lambda row: (row[2].casefold(), row[1], row[0])
        )
    ]


__all__ = ["COUNTRY_NAMES", "build_facet_metadata"]
