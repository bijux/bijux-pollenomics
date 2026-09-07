"""Exact four-country accountability for Neotoma chronology facets."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypedDict

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SourceChronologyNode,
)

from .facet_validation import (
    COUNTRY_NAMES,
    FACET_SCHEMA_VERSION,
    PRESET_ACCOUNTABILITY_SCHEMA_VERSION,
    SITE_COUNT_SEMANTICS,
    validate_facet_accountability,
    validate_node_partition,
)
from .source_label_presets import (
    MEMBERSHIP_SEMANTICS,
    NEOTOMA_SOURCE_LABEL_PRESETS,
    NEOTOMA_SOURCE_LABEL_TAXA,
    build_neotoma_source_label_preset_catalog,
)
from .time_density import build_time_density


class _FacetAggregate(TypedDict):
    site_count: int
    node_count: int
    observation_denominator: int
    time_min_bp: float | int | None
    time_max_bp: float | int | None


def build_facet_accountability(
    nodes: Sequence[SourceChronologyNode],
) -> dict[str, object]:
    """Return one exact aggregate with exhaustive country accountability."""
    validate_node_partition(nodes)
    return {
        "site_count_semantics": SITE_COUNT_SEMANTICS,
        **_facet_summary(nodes),
        "country_counts": _country_counts(nodes),
        "time_density": build_time_density(nodes),
    }


def build_source_label_preset_metadata(
    nodes: Sequence[SourceChronologyNode],
    *,
    source_snapshot_id: str,
    build_id: str,
) -> dict[str, object]:
    """Bind literal preset definitions to exact observed facet denominators."""
    catalog = build_neotoma_source_label_preset_catalog(
        source_snapshot_id=source_snapshot_id,
        build_id=build_id,
    )
    presets = []
    for preset in NEOTOMA_SOURCE_LABEL_PRESETS:
        selected = [
            node
            for node in nodes
            if type(node.source_taxon_id) is int
            and node.source_taxon_id in preset.member_taxon_ids
        ]
        presets.append({**preset.as_dict(), **build_facet_accountability(selected)})

    union_ids = tuple(taxon.source_taxon_id for taxon in NEOTOMA_SOURCE_LABEL_TAXA)
    union_nodes = [
        node
        for node in nodes
        if type(node.source_taxon_id) is int and node.source_taxon_id in union_ids
    ]
    accountability = {
        "schema_version": PRESET_ACCOUNTABILITY_SCHEMA_VERSION,
        "catalog_content_sha256": catalog["content_sha256"],
        "membership_semantics": MEMBERSHIP_SEMANTICS,
        "accepted_classification": False,
        "aggregation_is_abundance": False,
        "propagation_allowed": False,
        "source_taxon_count": len(union_ids),
        "preset_count": len(NEOTOMA_SOURCE_LABEL_PRESETS),
        "membership_count": sum(
            len(preset.member_taxon_ids) for preset in NEOTOMA_SOURCE_LABEL_PRESETS
        ),
        "presets": presets,
        "union": {
            "key": "all-governed-source-labels",
            "label": "All governed crop and cereal source labels",
            "membership_semantics": MEMBERSHIP_SEMANTICS,
            "accepted_classification": False,
            "aggregation_is_abundance": False,
            "propagation_allowed": False,
            "member_taxon_count": len(union_ids),
            "member_taxon_ids": list(union_ids),
            **build_facet_accountability(union_nodes),
        },
    }
    return {
        "source_label_preset_catalog": catalog,
        "source_label_preset_accountability": accountability,
    }


def _facet_summary(nodes: Sequence[SourceChronologyNode]) -> _FacetAggregate:
    site_ids: set[str] = set()
    node_ids: set[str] = set()
    observation_ids: set[str] = set()
    younger: float | int | None = None
    older: float | int | None = None
    for node in nodes:
        site_ids.add(node.site_id)
        node_ids.add(node.node_id)
        observation_ids.update(node.observation_ids)
        if younger is None or node.younger_bp < younger:
            younger = node.younger_bp
        if older is None or node.older_bp > older:
            older = node.older_bp
    return {
        "site_count": len(site_ids),
        "node_count": len(node_ids),
        "observation_denominator": len(observation_ids),
        "time_min_bp": younger,
        "time_max_bp": older,
    }


def _country_counts(nodes: Sequence[SourceChronologyNode]) -> list[dict[str, object]]:
    return [
        {
            "country_code": country_code,
            "value": country_name,
            "site_count_semantics": SITE_COUNT_SEMANTICS,
            **_facet_summary(
                [node for node in nodes if node.country_code == country_code]
            ),
        }
        for country_code, country_name in COUNTRY_NAMES.items()
    ]


__all__ = [
    "COUNTRY_NAMES",
    "FACET_SCHEMA_VERSION",
    "PRESET_ACCOUNTABILITY_SCHEMA_VERSION",
    "SITE_COUNT_SEMANTICS",
    "build_facet_accountability",
    "build_source_label_preset_metadata",
    "validate_facet_accountability",
]
