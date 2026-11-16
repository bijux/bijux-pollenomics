"""Finite fixed-point obligations over literal directed taxon source edges."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from ...resources.models import DEVELOPMENT_ROLES
from ..protocol import _RANK
from .models import (
    DEFAULT_ANCESTRY_LIMITS,
    SCHEMA,
    NeotomaTaxonAncestryLimits,
    NeotomaTaxonAncestrySources,
)
from .proofs import source_facts


def propagate_roots(
    initial: dict[int, set[int]], edges: list[dict[str, Any]]
) -> dict[int, set[int]]:
    """Every known edge propagates obligations, including self and cycle edges."""
    roots = {key: set(values) for key, values in initial.items()}
    parents: dict[int, set[int]] = defaultdict(set)
    for edge in edges:
        if (
            edge["relation"] == "taxon_parent"
            and type(edge["native_id"]) is int
            and edge["native_id"] > 0
        ):
            child, parent = edge["child_taxon_id"], edge["native_id"]
            parents[child].add(parent)
            roots.setdefault(parent, set())
    pending = deque(roots)
    queued = set(roots)
    while pending:
        child = pending.popleft()
        queued.remove(child)
        for parent in parents[child]:
            missing = roots[child] - roots[parent]
            if missing:
                roots[parent].update(missing)
                if parent not in queued:
                    pending.append(parent)
                    queued.add(parent)
    return roots


def cycle_components(edges: list[dict[str, Any]]) -> list[list[int]]:
    """Report structural multi-node cycles; self edges retain their own literal status."""
    graph: dict[int, set[int]] = defaultdict(set)
    reverse: dict[int, set[int]] = defaultdict(set)
    for edge in edges:
        if (
            edge["relation"] == "taxon_parent"
            and type(edge["native_id"]) is int
            and edge["native_id"] > 0
        ):
            child, parent = edge["child_taxon_id"], edge["native_id"]
            graph[child].add(parent)
            reverse[parent].add(child)
            graph.setdefault(parent, set())
            reverse.setdefault(child, set())
    visited = set()
    finish = []
    for node in sorted(graph):
        if node in visited:
            continue
        stack = [(node, False)]
        while stack:
            current, done = stack.pop()
            if done:
                finish.append(current)
                continue
            if current in visited:
                continue
            visited.add(current)
            stack.append((current, True))
            stack.extend(
                (parent, False)
                for parent in sorted(graph[current], reverse=True)
                if parent not in visited
            )
    visited.clear()
    components = []
    for node in reversed(finish):
        if node in visited:
            continue
        group = []
        pending = [node]
        visited.add(node)
        while pending:
            current = pending.pop()
            group.append(current)
            for child in reverse[current]:
                if child not in visited:
                    visited.add(child)
                    pending.append(child)
        if len(group) > 1:
            components.append(sorted(group))
    return sorted(components)


def _role(roots: set[int], roles: dict[int, str]) -> str:
    if not roots or any(root not in roles for root in roots):
        raise ValueError("Taxon ancestry inherited native root obligations are missing")
    return max((roles[root] for root in roots), key=_RANK.__getitem__)


def derive_neotoma_taxon_ancestry(
    sources: NeotomaTaxonAncestrySources,
    *,
    limits: NeotomaTaxonAncestryLimits = DEFAULT_ANCESTRY_LIMITS,
) -> dict[str, Any]:
    """Derive known source edges and an unapproved, finite next parent frontier."""
    return _derive_taxon_ancestry(sources, limits=limits)


def _derive_taxon_ancestry(
    sources: NeotomaTaxonAncestrySources,
    *,
    limits: NeotomaTaxonAncestryLimits = DEFAULT_ANCESTRY_LIMITS,
    _before_body_read: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Compose outer current-epoch refusals with the complete source derivation."""
    facts = source_facts(sources, limits, _before_body_read=_before_body_read)
    seeds = sorted(facts["seeds"], key=lambda row: row["native_id"])
    seed_ids = {row["native_id"] for row in seeds}
    edges = sorted(
        facts["edges"], key=lambda row: (row["child_taxon_id"], row["json_pointer"])
    )
    initial = {
        identity: set(facts["roots"][f"taxon-{identity}"]) for identity in seed_ids
    }
    roots = propagate_roots(initial, edges)
    cycles = cycle_components(edges)
    cyclic = {node for group in cycles for node in group}
    parents: dict[int, set[int]] = defaultdict(set)
    for edge in edges:
        if edge["relation"] == "taxon_parent" and edge["native_id"] is not None:
            parents[edge["child_taxon_id"]].add(edge["native_id"])
    conflicts = sorted(child for child, values in parents.items() if len(values) > 1)
    seed_rows = {row["native_id"]: row for row in seeds}
    taxa = []
    new_taxa = set(roots) - seed_ids
    for identity in sorted(roots):
        taxa.append(
            {
                "target_key": f"taxon-{identity}",
                "native_id": identity,
                "target_kind": "taxon",
                "declared_seed": identity in seed_ids,
                "additional_parent_hops_from_seed": 0 if identity in seed_ids else 1,
                "current_root_dataset_ids": sorted(roots[identity]),
                "current_use_role": _role(roots[identity], facts["roles"]),
                "source_status": seed_rows[identity]["qualification_status"]
                if identity in seed_rows
                else "not_captured_in_direct_inventory",
                "structural_cycle": identity in cyclic,
                "parent_values_require_review": identity in conflicts,
                "biological_rank_asserted": False,
                "scientific_admission": "not_asserted",
            }
        )
    citations: dict[int, set[int]] = {}
    for edge in edges:
        if (
            edge["relation"] == "taxon_reference_publication"
            and edge["native_id"] is not None
        ):
            identity = edge["native_id"]
            citations.setdefault(
                identity, set(facts["roots"].get(f"publication-{identity}", set()))
            ).update(roots[edge["child_taxon_id"]])
    publications = [
        {
            "target_key": f"publication-{identity}",
            "native_id": identity,
            "target_kind": "publication",
            "current_root_dataset_ids": sorted(inherited),
            "current_use_role": _role(inherited, facts["roles"]),
            "source_request_status": facts["source_results"].get(
                f"publication-{identity}", "not_captured_in_direct_inventory"
            ),
            "native_entity_owner_verified": False,
            "scientific_admission": "not_asserted",
        }
        for identity, inherited in sorted(citations.items())
    ]
    incident: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        incident[f"taxon-{edge['child_taxon_id']}"].add(edge["edge_id"])
        if edge["native_id"] is not None:
            incident[f"{edge['target_kind']}-{edge['native_id']}"].add(edge["edge_id"])
    for row in [*taxa, *publications]:
        row["edge_ids"] = sorted(incident[row["target_key"]])
        if row["target_kind"] == "taxon" and row["declared_seed"]:
            seed = seed_rows[row["native_id"]]
            row["source_capture_manifest_sha256"] = seed[
                "source_capture_manifest_sha256"
            ]
            row["source"] = seed.get("source")
    frontier = []
    for row in taxa:
        if row["declared_seed"]:
            continue
        status = "not_attempted_capture_not_authorized"
        if limits.max_additional_parent_hops < 1:
            status = "not_attempted_depth_bound"
        elif len(new_taxa) > limits.max_new_taxa:
            status = "not_attempted_node_bound"
        frontier.append({**row, "status": status, "GET_authorized": False})
    for row in publications:
        if row["source_request_status"] == "not_captured_in_direct_inventory":
            frontier.append(
                {
                    **row,
                    "status": "not_attempted_capture_not_authorized",
                    "GET_authorized": False,
                }
            )
    summary = {
        "declared_seed_taxa": len(seeds),
        "qualified_literal_taxon_records": sum(
            row.get("literal_record_count") or 0 for row in seeds
        ),
        "literal_field_occurrences": len(edges),
        "known_taxon_nodes": len(taxa),
        "new_parent_taxa": len(new_taxa),
        "new_citation_publications": sum(
            row["target_kind"] == "publication" for row in frontier
        ),
        "self_edges": sum(row["status"] == "self_edge" for row in edges),
        "multi_node_cycles": len(cycles),
        "conflicting_parent_taxa": len(conflicts),
        "qualified_seed_sources": sum(
            row["qualification_status"] == "qualified_native_taxon_detail"
            for row in seeds
        ),
    }
    return {
        "schema_version": SCHEMA,
        "authority": {
            "evidence_manifest_sha256": sources.evidence.manifest_sha256,
            "context_manifest_sha256": sources.expected_context_sha256,
            "native_archive_manifest_sha256": sources.expected_native_archive_sha256,
            "roster_sha256": facts["header"]["authority"]["roster_sha256"],
            "declared_seed_taxon_ids": sorted(seed_ids),
            "source_captures": facts["source_snapshot"],
        },
        "limits": asdict(limits),
        "seeds": seeds,
        "edges": edges,
        "taxa": taxa,
        "publications": publications,
        "frontier": sorted(frontier, key=lambda row: row["target_key"]),
        "cycle_components": cycles,
        "summary": summary,
        "source_entity_slot_count": len(facts["header"]["targets"]),
        "source_capture_entry_count": len(facts["source_results"]),
        "source_entity_attempted_target_count": facts["attempted_targets"],
        "source_received_HTTP_entity_count": facts["received_entities"],
        "source_blocked_target_keys": sorted(
            key
            for key, role in facts["target_roles"].items()
            if role not in DEVELOPMENT_ROLES
        ),
        "additional_hop_basis": "declared_taxon_detail_seed; not biological rank or distance from every measured leaf",
        "capture_scope": "individually timed current detail sources; not a transaction or frozen numerical taxonomy",
        "native_body_copies": 0,
        "new_GETs": 0,
        "scientific_admission": "not_asserted",
        "original_preget_scope_reconstructed": False,
        "global_taxonomy_complete": False,
    }
