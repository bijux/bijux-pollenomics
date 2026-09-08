"""Chronology-selection accounting independent of source measurement units."""

from __future__ import annotations

from collections.abc import Sequence

from .models import SourceChronologyNode


def selected_samples(
    nodes: Sequence[SourceChronologyNode],
) -> tuple[SourceChronologyNode, ...]:
    """Return one chronology-bearing node per selected source sample."""
    selected: dict[str, SourceChronologyNode] = {}
    for node in nodes:
        if node.node_level != "source_sample_presence":
            continue
        existing = selected.get(node.source_record_id)
        if existing is None:
            selected[node.source_record_id] = node
            continue
        identity = (
            node.chronology_claim_id,
            node.chronology_id,
            node.chronology_name,
            node.is_default_chronology,
            node.chronology_selection_posture,
            node.younger_bp,
            node.older_bp,
        )
        existing_identity = (
            existing.chronology_claim_id,
            existing.chronology_id,
            existing.chronology_name,
            existing.is_default_chronology,
            existing.chronology_selection_posture,
            existing.younger_bp,
            existing.older_bp,
        )
        if identity != existing_identity:
            raise AssertionError("source sample has conflicting chronology selections")
    return tuple(selected[key] for key in sorted(selected))


__all__ = ["selected_samples"]
