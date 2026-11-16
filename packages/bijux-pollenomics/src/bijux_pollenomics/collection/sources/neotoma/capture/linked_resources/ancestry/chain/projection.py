"""Compute all-root obligations and minimum hops from a frozen seed inventory."""

from __future__ import annotations

from collections import defaultdict, deque
from hashlib import sha256
from typing import Any

from ....resources.models import DEVELOPMENT_ROLES
from ...protocol import _RANK
from ..layers import cycle_components, propagate_roots
from ..models import SCHEMA as BASELINE_SCHEMA
from .models import SCHEMA, NeotomaTaxonAncestryChainLimits


def seed_digest(ids: list[int]) -> str:
    """Commit the sorted original seed IDs independently of capture grouping."""
    from .....resource_catalogue.archive.files import encoded_json

    return sha256(encoded_json(ids)).hexdigest()


def project(
    state: dict[str, Any],
    roles: dict[int, str],
    limits: NeotomaTaxonAncestryChainLimits,
) -> dict[str, Any]:
    """Project a source-authenticated graph; no caller dictionaries confer authority."""
    seeds, edges = state["seed_ids"], list(state["edges"].values())
    roots = propagate_roots(
        {key: set(state["direct_roots"][f"taxon-{key}"]) for key in seeds}, edges
    )
    parents: dict[int, set[int]] = defaultdict(set)
    for edge in edges:
        if edge["relation"] == "taxon_parent" and edge["native_id"] is not None:
            parents[edge["child_taxon_id"]].add(edge["native_id"])
    depths = dict.fromkeys(seeds, 0)
    pending = deque(seeds)
    while pending:
        child = pending.popleft()
        for parent in sorted(parents[child]):
            if parent not in depths or depths[parent] > depths[child] + 1:
                depths[parent] = depths[child] + 1
                pending.append(parent)
    if set(depths) != set(roots):
        raise ValueError("Ancestry graph contains an unreachable native node")
    cycles = cycle_components(edges)
    cyclic = {node for group in cycles for node in group}
    inherited_publications: dict[int, set[int]] = {}
    incident: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        incident[f"taxon-{edge['child_taxon_id']}"].add(edge["edge_id"])
        if edge["native_id"] is None:
            continue
        key = f"{edge['target_kind']}-{edge['native_id']}"
        incident[key].add(edge["edge_id"])
        if edge["target_kind"] == "publication":
            inherited_publications.setdefault(
                edge["native_id"], set(state["direct_roots"].get(key, []))
            ).update(roots[edge["child_taxon_id"]])
    nodes = {}
    for kind, memberships in (
        ("taxon", roots),
        ("publication", inherited_publications),
    ):
        for identity, root_ids in sorted(memberships.items()):
            if not root_ids or any(root not in roles for root in root_ids):
                raise ValueError("Ancestry complete current root duties are missing")
            key = f"{kind}-{identity}"
            result = state["results"].get(key)
            row = {
                "target_key": key,
                "target_kind": kind,
                "native_id": identity,
                "current_root_dataset_ids": sorted(root_ids),
                "current_use_role": max(
                    (roles[root] for root in root_ids), key=_RANK.__getitem__
                ),
                "edge_ids": sorted(incident[key]),
                "source_status": result["qualification_status"]
                if result
                else "not_captured_in_known_inventory",
                "source_result": result,
                "scientific_admission": "not_asserted",
                "native_entity_owner_verified": False,
            }
            if kind == "taxon":
                row.update(
                    declared_seed=identity in seeds,
                    additional_parent_hops_from_seed=depths[identity],
                    structural_cycle=identity in cyclic,
                    parent_values_require_review=len(parents[identity]) > 1,
                    biological_rank_asserted=False,
                )
            nodes[key] = row
    frontier = []
    additional = len(roots) - len(seeds)
    for key, node in sorted(nodes.items()):
        if key in state["results"] and (
            state["results"][key].get("attempted") or node.get("declared_seed")
        ):
            continue
        status = "not_attempted_capture_not_authorized"
        if node["current_use_role"] not in DEVELOPMENT_ROLES:
            status = "not_attempted_protected_scope"
        elif (
            node["target_kind"] == "taxon"
            and node["additional_parent_hops_from_seed"]
            > limits.max_additional_parent_hops
        ):
            status = "not_attempted_depth_bound"
        elif additional > limits.max_new_taxa:
            status = "not_attempted_node_bound"
        elif state["new_request_count"] >= limits.max_new_requests:
            status = "not_attempted_request_bound"
        frontier.append({**node, "status": status, "GET_authorized": False})
    if len(edges) > limits.max_literal_edges:
        raise ValueError("Ancestry literal edges exceed their finite bound")
    return {
        "nodes": nodes,
        "edges": dict(state["edges"]),
        "frontier": frontier,
        "cycle_components": cycles,
        "summary": {
            "declared_seed_taxa": len(seeds),
            "known_taxon_nodes": len(roots),
            "new_parent_taxa": additional,
            "known_publication_nodes": len(inherited_publications),
            "literal_field_occurrences": len(edges),
            "new_HTTP_requests": state["new_request_count"],
            "known_entity_results": len(state["results"]),
        },
    }


def delta(
    state: dict[str, Any],
    projected: dict[str, Any],
    previous: dict[str, Any],
    *,
    parent: str | None,
    captures: tuple[str, ...],
    context: str,
    native: str,
    limits: NeotomaTaxonAncestryChainLimits,
) -> dict[str, Any]:
    """Store changed node versions and added edges, never duplicate source bodies."""
    from dataclasses import asdict

    changed = [
        row
        for key, row in sorted(projected["nodes"].items())
        if previous["nodes"].get(key) != row
    ]
    return {
        "schema_version": SCHEMA,
        "baseline": {
            "schema_version": BASELINE_SCHEMA,
            "evidence_manifest_sha256": state["evidence_sha256"],
            "seed_projection_manifest_sha256": state["baseline_sha256"],
            "seed_taxon_ids": state["seed_ids"],
            "seed_taxon_ids_sha256": seed_digest(state["seed_ids"]),
        },
        "parent_chain_manifest_sha256": parent,
        "new_capture_manifest_sha256s": list(captures),
        "current_context_manifest_sha256": context,
        "current_native_archive_manifest_sha256": native,
        "limits": asdict(limits),
        "edges": [
            row
            for key, row in sorted(projected["edges"].items())
            if key not in previous["edges"]
        ],
        "taxa": [row for row in changed if row["target_kind"] == "taxon"],
        "publications": [row for row in changed if row["target_kind"] == "publication"],
        "frontier": projected["frontier"]
        if projected["frontier"] != previous["frontier"]
        else [],
        "cycle_components": projected["cycle_components"]
        if projected["cycle_components"] != previous["cycle_components"]
        else [],
        "known_entity_results": {
            key: row
            for key, row in sorted(state["results"].items())
            if previous["results"].get(key) != row
        },
        "summary": projected["summary"],
        "native_body_copies": 0,
        "new_GETs": 0,
        "scientific_admission": "not_asserted",
        "metadata_verification_scope": "complete_source_graph_current_root_metadata; not selected_native_body_authority",
    }


def native_edges(
    records: list[dict[str, Any]],
    entry: dict[str, Any],
    pin: str,
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    """Encode each authenticated literal field once, retaining null/self source values."""
    edges: list[dict[str, Any]] = []
    if entry["kind"] == "taxon":
        for index, record in enumerate(records):
            for field, kind, relation in (
                ("highertaxonid", "taxon", "taxon_parent"),
                ("publicationid", "publication", "taxon_reference_publication"),
            ):
                value = record[field]
                edge = {
                    "child_taxon_id": entry["native_id"],
                    "native_id": value,
                    "target_kind": kind,
                    "relation": relation,
                    "status": "explicit_null"
                    if value is None
                    else "self_edge"
                    if kind == "taxon" and value == entry["native_id"]
                    else "literal_parent"
                    if kind == "taxon"
                    else "literal_citation",
                    "json_pointer": f"/data/{index}/{field}",
                    "source_capture_manifest_sha256": pin,
                    "source_target_key": entry["target_key"],
                    "source": source,
                    "native_field_value_verified": True,
                }
                import json

                edge["edge_id"] = sha256(
                    json.dumps(edge, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()
                edges.append(edge)
    return edges
