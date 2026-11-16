"""Read selected anchored graph metadata without native-body or GET authority."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .....client import positive_native_id
from .....resource_catalogue.archive.files import _digest
from ....receipts import _safe_root
from .. import publication as baseline_publication
from .. import storage
from .models import COLLECTIONS, SCHEMA


def read_neotoma_taxon_chain_target(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    kind: str,
    native_id: int,
    chain_sources: Mapping[str, Path],
) -> dict[str, Any]:
    """Return recorded incident rows, explicitly withholding source/current authority."""
    if kind not in {"taxon", "publication"}:
        raise ValueError("Ancestry selected target kind differs")
    positive_native_id(native_id)
    if not isinstance(chain_sources, Mapping):
        raise ValueError("Ancestry selected metadata needs explicit chain resolvers")
    key = f"{kind}-{native_id}"
    cursor, root = expected_manifest_sha256, _safe_root(directory)
    seen: set[str] = set()
    node: dict[str, Any] | None = None
    edges: dict[str, dict[str, Any]] = {}
    context = None
    baseline = None
    while True:
        if not _digest(cursor) or cursor in seen or len(seen) >= 10000:
            raise ValueError("Ancestry selected metadata parent closure differs")
        seen.add(cursor)
        manifest = storage._manifest(
            root, cursor, collections=COLLECTIONS, schema=SCHEMA
        )
        context = context or manifest["current_context_manifest_sha256"]
        if baseline is None:
            baseline = manifest["baseline"]
        elif manifest["baseline"] != baseline:
            raise ValueError("Ancestry selected metadata baseline changed")
        if node is None and key in manifest["node_index"]:
            location = manifest["node_index"][key]
            node = _selected(
                root, manifest, location, "taxa" if kind == "taxon" else "publications"
            )
            if (
                node.get("target_key") != key
                or type(node.get("native_id")) is not int
                or node["native_id"] != native_id
                or node.get("target_kind") != kind
            ):
                raise ValueError("Ancestry selected native identity differs")
        if node is not None:
            references = node.get("edge_ids")
            if (
                not isinstance(references, list)
                or any(not _digest(pin) for pin in references)
                or references != sorted(set(references))
            ):
                raise ValueError("Ancestry selected edge references differ")
            for pin in references:
                if pin not in edges and pin in manifest["edge_index"]:
                    row = _selected(
                        root, manifest, manifest["edge_index"][pin], "edges"
                    )
                    if row.get("edge_id") != pin or not (
                        row.get("source_target_key") == key
                        or row.get("target_kind") == kind
                        and type(row.get("native_id")) is int
                        and row["native_id"] == native_id
                    ):
                        raise ValueError("Ancestry selected edge incidence differs")
                    edges[pin] = row
        parent = manifest.get("parent_chain_manifest_sha256")
        if parent is None:
            break
        if not _digest(parent) or parent not in chain_sources:
            raise ValueError("Ancestry selected parent resolver is missing")
        cursor, root = parent, _safe_root(chain_sources[parent])
    baseline_pin = baseline["seed_projection_manifest_sha256"]
    if baseline_pin not in chain_sources:
        raise ValueError("Ancestry selected baseline resolver is missing")
    original = (
        baseline_publication.read_neotoma_taxon_ancestry_target(
            chain_sources[baseline_pin],
            expected_manifest_sha256=baseline_pin,
            kind=kind,
            native_id=native_id,
        )
        if node is None
        else None
    )
    if original:
        node = original["recorded_node"]
        edges.update({row["edge_id"]: row for row in original["recorded_edges"]})
    if node is None:
        raise ValueError("Ancestry selected target is absent")
    missing = set(node["edge_ids"]) - set(edges)
    if missing:
        baseline_root = chain_sources[baseline_pin]
        manifest = baseline_publication._manifest(baseline_root, baseline_pin)
        for pin in missing:
            if pin not in manifest["edge_index"]:
                raise ValueError("Ancestry selected edge closure is missing")
            row = _selected(
                baseline_root,
                manifest,
                manifest["edge_index"][pin],
                "edges",
                baseline=True,
            )
            if row.get("edge_id") != pin:
                raise ValueError("Ancestry selected baseline edge identity differs")
            edges[pin] = row
    return {
        "recorded_node": node,
        "recorded_edges": [
            {**edges[pin], "native_field_value_verified": False}
            for pin in node["edge_ids"]
        ],
        "recorded_context_sha256": context,
        "integrity_scope": "anchored_selected_metadata_parts_only",
        "current_roles_revalidated": False,
        "native_source_fields_revalidated": False,
        "native_entity_bodies_opened": 0,
        "GET_authorized": False,
        "scientific_admission": "not_asserted",
    }


def _selected(
    root: Path,
    manifest: dict[str, Any],
    location: Any,
    collection: str,
    *,
    baseline: bool = False,
) -> dict[str, Any]:
    if (
        not isinstance(location, dict)
        or set(location) != {"part_sha256", "row_offset"}
        or not _digest(location["part_sha256"])
        or type(location["row_offset"]) is not int
        or location["row_offset"] < 0
    ):
        raise ValueError("Ancestry selected locator is malformed")
    parts = [
        part
        for part in manifest["parts"]
        if part["sha256"] == location["part_sha256"]
        and part["collection"] == collection
    ]
    if len(parts) != 1:
        raise ValueError("Ancestry selected part is absent or ambiguous")
    rows = (
        baseline_publication._part(root, parts[0])
        if baseline
        else storage._part(root, parts[0], schema=SCHEMA)
    )
    offset = location["row_offset"]
    if offset >= len(rows) or not isinstance(rows[offset], dict):
        raise ValueError("Ancestry selected row is absent")
    return dict(rows[offset])
