"""Deterministic facet metadata for source-chronology selectors."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SourceChronologyNode,
)

from .facet_accountability import (
    COUNTRY_NAMES,
    FACET_SCHEMA_VERSION,
    PRESET_ACCOUNTABILITY_SCHEMA_VERSION,
    build_facet_accountability,
    build_source_label_preset_metadata,
    validate_facet_accountability,
)

SOURCE_ECOLOGICAL_CODE_LABELS = {
    "AQVP": "Aquatic Vascular Plants",
    "TRSH": "Trees and Shrubs",
    "UPHE": "Upland Herbs",
}


def source_ecological_code_label(code: str | None) -> str | None:
    """Return a source meaning label without claiming reviewed equivalence."""
    if code is None:
        return None
    return SOURCE_ECOLOGICAL_CODE_LABELS.get(code, code)


def build_facet_metadata(
    nodes: Sequence[SourceChronologyNode],
    *,
    node_level: str,
    source_snapshot_id: str,
    build_id: str,
) -> dict[str, object]:
    """Return exact feature and observation denominators for selectable facets."""
    if any(
        node.source_snapshot_id != source_snapshot_id or node.build_id != build_id
        for node in nodes
    ):
        raise ValueError("facet source identity differs from its result context")
    selected = [node for node in nodes if node.node_level == node_level]
    metadata: dict[str, object] = {
        "schema_version": FACET_SCHEMA_VERSION,
        "node_level": node_level,
        **build_facet_accountability(selected),
        "source_unit_counts": _value_counts(
            (node.source_unit, len(node.observation_ids)) for node in selected
        ),
        "source_ecological_codes": (
            _code_facets(selected) if node_level == "source_ecological_code" else []
        ),
        "source_taxa": _taxon_facets(selected) if node_level == "source_taxon" else [],
    }
    if node_level == "source_taxon":
        metadata.update(
            build_source_label_preset_metadata(
                selected,
                source_snapshot_id=source_snapshot_id,
                build_id=build_id,
            )
        )
    validate_facet_accountability(
        metadata,
        expected_node_level=node_level,
        source_snapshot_id=source_snapshot_id,
        build_id=build_id,
    )
    return metadata


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


def _code_facets(nodes: Sequence[SourceChronologyNode]) -> list[dict[str, object]]:
    members: dict[str, list[SourceChronologyNode]] = defaultdict(list)
    for node in nodes:
        code = node.source_ecological_group
        if code is None:
            raise ValueError("source ecological-code node lost its literal code")
        members[code].append(node)
    return [
        {
            "value": code,
            "label": source_ecological_code_label(code),
            "source_code": code,
            "feature_key": f"source:neotoma:ecological-code:{code}",
            **build_facet_accountability(members[code]),
        }
        for code in sorted(members)
    ]


def _taxon_facets(nodes: Sequence[SourceChronologyNode]) -> list[dict[str, object]]:
    members: dict[tuple[str, str, str], list[SourceChronologyNode]] = defaultdict(list)
    for node in nodes:
        if node.source_taxon_id is None or node.source_reported_name is None:
            raise ValueError("source taxon node lost exact source identity")
        key = (
            node.feature_key,
            str(node.source_taxon_id),
            node.source_reported_name,
        )
        members[key].append(node)
    return [
        {
            "value": feature_key,
            "source_taxon_id": taxon_id,
            "label": name,
            **build_facet_accountability(members[(feature_key, taxon_id, name)]),
        }
        for feature_key, taxon_id, name in sorted(
            members, key=lambda row: (row[2].casefold(), row[1], row[0])
        )
    ]


__all__ = [
    "COUNTRY_NAMES",
    "FACET_SCHEMA_VERSION",
    "PRESET_ACCOUNTABILITY_SCHEMA_VERSION",
    "SOURCE_ECOLOGICAL_CODE_LABELS",
    "build_facet_metadata",
    "source_ecological_code_label",
]
