"""Recompute frontier targets from independent complete graph and source epochs."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .....resources.models import DEVELOPMENT_ROLES
from ...models import SCHEMA as BASELINE_SCHEMA
from ..authority import ChainOperation
from ..models import (
    CAPTURE_SCHEMA,
    MAX_ENTITY_BYTES,
    SCHEMA,
    NeotomaTaxonAncestryChainLimits,
    NeotomaTaxonAncestryChainSources,
    strongest_roles,
)
from ..projection import project
from .models import MAX_REQUESTS, NeotomaTaxonFrontierCaptureLimits


def validate_selection(
    keys: tuple[str, ...], limits: NeotomaTaxonFrontierCaptureLimits
) -> None:
    """Reject implicit, duplicate or unbounded target sets before source access."""
    if (
        not isinstance(keys, tuple)
        or not keys
        or len(keys) > MAX_REQUESTS
        or any(not isinstance(key, str) for key in keys)
        or len(set(keys)) != len(keys)
    ):
        raise ValueError("Frontier capture requires explicit unique finite target keys")
    limits.validate(len(keys))


def prepare_targets(
    operation: ChainOperation,
    parent: str | None,
    keys: tuple[str, ...],
    limits: NeotomaTaxonAncestryChainLimits,
    *,
    native_replay: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Require current all-root duties and a native child witness for every target."""
    state, _ = operation.resolve(parent, limits, native_replay=native_replay)
    operation.epoch(
        operation.sources.expected_current_context_sha256,
        operation.sources.expected_current_native_archive_sha256,
    )
    roles = strongest_roles(
        operation.history, *(epoch["roles"] for epoch in operation.epochs.values())
    )
    graph = project(state, roles, limits)
    frontier = {row["target_key"]: row for row in graph["frontier"]}
    if state["new_request_count"] + len(keys) > limits.max_new_requests:
        raise ValueError("Frontier capture cumulative request bound exceeded")
    targets = []
    for key in keys:
        node = frontier.get(key)
        if (
            node is None
            or node["status"] != "not_attempted_capture_not_authorized"
            or node["current_use_role"] not in DEVELOPMENT_ROLES
        ):
            raise ValueError(
                "Frontier target is foreign, protected or beyond its bound"
            )
        witnesses = [
            edge
            for edge in state["edges"].values()
            if edge["native_id"] == node["native_id"]
            and edge["target_kind"] == node["target_kind"]
            and edge["status"] in {"literal_parent", "literal_citation"}
            and graph["nodes"][f"taxon-{edge['child_taxon_id']}"]["current_use_role"]
            in DEVELOPMENT_ROLES
        ]
        if not witnesses:
            raise ValueError("Frontier target has no permitted native child witness")
        witness = min(witnesses, key=lambda edge: edge["edge_id"])
        targets.append(
            {
                "target_key": key,
                "kind": node["target_kind"],
                "native_id": node["native_id"],
                "root_dataset_ids": node["current_root_dataset_ids"],
                "recorded_role": node["current_use_role"],
                "recorded_hop": node.get("additional_parent_hops_from_seed"),
                "witness_edge_id": witness["edge_id"],
            }
        )
    return targets, {
        "schema_version": CAPTURE_SCHEMA,
        "source_ancestry": {
            "schema_version": SCHEMA if parent else BASELINE_SCHEMA,
            "manifest_sha256": parent
            or operation.sources.expected_baseline_projection_sha256,
        },
        "current_context_manifest_sha256": operation.sources.expected_current_context_sha256,
        "current_native_archive_manifest_sha256": operation.sources.expected_current_native_archive_sha256,
        "frontier_target_keys": list(keys),
        "limits": {"max_response_bytes": MAX_ENTITY_BYTES, "max_attempts": 1},
    }


def require_separate_output(operation: ChainOperation, destination: Path) -> None:
    """Never create a candidate inside a consumed source namespace."""
    if any(
        destination.is_relative_to(root) or root.is_relative_to(destination)
        for root in operation.trees
    ):
        raise ValueError("Frontier output overlaps a consumed source namespace")


def source_signature(sources: NeotomaTaxonAncestryChainSources) -> tuple[Any, ...]:
    """Pin literal resolver identities without copying or mutating caller mappings."""

    def path(value: Path) -> str:
        return str(Path(value).absolute())

    def mapping(values: Mapping[str, Path]) -> tuple[tuple[str, str], ...]:
        if not isinstance(values, Mapping) or len(values) > 10000:
            raise ValueError("Frontier source resolver population exceeds finite bound")
        return tuple(
            sorted((pin, path(directory)) for pin, directory in values.items())
        )

    recorded = sources.recorded_baseline_sources
    return (
        path(recorded.evidence.directory),
        recorded.evidence.manifest_sha256,
        mapping(recorded.capture_sources),
        mapping(recorded.source_facets),
        path(recorded.context_directory),
        recorded.expected_context_sha256,
        path(recorded.native_archive_directory),
        recorded.expected_native_archive_sha256,
        path(sources.baseline_projection_directory),
        sources.expected_baseline_projection_sha256,
        mapping(sources.chain_sources),
        mapping(sources.ancestry_capture_sources),
        path(sources.current_context_directory),
        sources.expected_current_context_sha256,
        path(sources.current_native_archive_directory),
        sources.expected_current_native_archive_sha256,
        mapping(sources.context_sources),
        mapping(sources.native_archive_sources),
    )
