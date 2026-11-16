"""Exclusive bounded ancestry metadata parts with explicit full-source readback."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import (
    OwnedTreeWriter,
)
from bijux_pollenomics.core.owned_tree import build_staging_output_dir

from ....client import positive_native_id
from ....publication.ownership import publish_owned_source_tree
from ....resource_catalogue.archive.files import _digest, encoded_json
from ....resource_catalogue.source_projection import _same
from ...receipts import _safe_root
from . import storage
from .layers import _derive_taxon_ancestry, derive_neotoma_taxon_ancestry
from .models import (
    HARD_PART_BYTES,
    MAX_BYTES,
    MAX_PARTS,
    PART_BYTES,
    NeotomaTaxonAncestryLimits,
    NeotomaTaxonAncestrySources,
)

COLLECTIONS = ("seeds", "edges", "taxa", "publications", "frontier", "cycle_components")


def _pinned(path: Path, digest: str, bound: int, size: int | None = None) -> bytes:
    return storage._pinned(path, digest, bound, size)


def _pack(document: dict[str, Any]) -> tuple[dict[str, Any], dict[str, bytes]]:
    return storage._pack(
        document,
        part_bytes=PART_BYTES,
        hard_part_bytes=HARD_PART_BYTES,
        encoder=encoded_json,
    )


def _manifest(root: Path, digest: str) -> dict[str, Any]:
    return storage._manifest(root, digest)


def _part(root: Path, part: dict[str, Any]) -> list[Any]:
    return storage._part(root, part)


def _readback(root: Path, digest: str) -> dict[str, Any]:
    return storage._readback(root, digest)


def load_neotoma_taxon_ancestry(
    root: Path, *, expected_manifest_sha256: str, sources: NeotomaTaxonAncestrySources
) -> dict[str, Any]:
    """Explicitly replay complete declared sources; no current-schema fallback."""
    return _load_taxon_ancestry(
        root, expected_manifest_sha256=expected_manifest_sha256, sources=sources
    )


def _load_taxon_ancestry(
    root: Path,
    *,
    expected_manifest_sha256: str,
    sources: NeotomaTaxonAncestrySources,
    _before_body_read: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Preserve independent outer current-epoch duties inside recorded replay."""
    document = _readback(root, expected_manifest_sha256)
    limits = NeotomaTaxonAncestryLimits(**document["limits"])
    expected = (
        derive_neotoma_taxon_ancestry(sources, limits=limits)
        if _before_body_read is None
        else _derive_taxon_ancestry(
            sources, limits=limits, _before_body_read=_before_body_read
        )
    )
    if not _same(document, expected):
        raise ValueError("Taxon ancestry full source projection differs")
    return document


def publish_neotoma_taxon_ancestry(
    root: Path, *, document: dict[str, Any], sources: NeotomaTaxonAncestrySources
) -> dict[str, Any]:
    """Keep the ownership descriptor live through full staged and final source readback."""
    final = _safe_root(root)
    if final.exists():
        raise FileExistsError(f"Taxon ancestry already exists: {final}")
    limits = NeotomaTaxonAncestryLimits(**document["limits"])
    expected = derive_neotoma_taxon_ancestry(sources, limits=limits)
    if not _same(document, expected):
        raise ValueError("Taxon ancestry source projection differs")
    manifest, buffers = _pack(expected)
    raw = encoded_json(manifest)
    digest = sha256(raw).hexdigest()
    staging = build_staging_output_dir(final)
    with OwnedTreeWriter(
        staging, max_bytes=MAX_BYTES, max_files=MAX_PARTS + 1
    ) as writer:
        for name, content in buffers.items():
            writer.write_bytes(name, content)
        writer.write_bytes("manifest.json", raw)
        publish_owned_source_tree(
            writer,
            staging=staging,
            final=final,
            validate=lambda path: load_neotoma_taxon_ancestry(
                path, expected_manifest_sha256=digest, sources=sources
            ),
        )
    return manifest


def read_neotoma_taxon_ancestry_target(
    root: Path, *, expected_manifest_sha256: str, kind: str, native_id: int
) -> dict[str, Any]:
    """Read one recorded metadata node; no current-role or source-body claim is added."""
    if kind not in {"taxon", "publication"}:
        raise ValueError("Taxon ancestry target kind is invalid")
    identity = positive_native_id(native_id)
    root = _safe_root(root)
    manifest = _manifest(root, expected_manifest_sha256)
    key = f"{kind}-{identity}"
    locator = manifest["node_index"].get(key)
    if (
        not isinstance(locator, dict)
        or set(locator) != {"part_sha256", "row_offset"}
        or type(locator["row_offset"]) is not int
        or locator["row_offset"] < 0
    ):
        raise ValueError("Taxon ancestry target is absent or malformed")
    collection = "taxa" if kind == "taxon" else "publications"
    parts = [
        part
        for part in manifest["parts"]
        if part["collection"] == collection and part["sha256"] == locator["part_sha256"]
    ]
    if len(parts) != 1:
        raise ValueError("Taxon ancestry selected part is absent or ambiguous")
    rows = _part(root, parts[0])
    if (
        locator["row_offset"] >= len(rows)
        or not isinstance(rows[locator["row_offset"]], dict)
        or rows[locator["row_offset"]].get("target_key") != key
    ):
        raise ValueError("Taxon ancestry selected native identity differs")
    node = rows[locator["row_offset"]]
    if (
        type(node.get("native_id")) is not int
        or node["native_id"] != identity
        or node.get("target_kind") != kind
    ):
        raise ValueError("Taxon ancestry selected native identity differs")
    references = node.get("edge_ids")
    if (
        not isinstance(references, list)
        or any(not _digest(value) for value in references)
        or references != sorted(set(references))
    ):
        raise ValueError("Taxon ancestry selected edge references are malformed")
    cached: dict[str, list[Any]] = {}
    selected_edges = []
    for edge_id in references:
        reference = manifest["edge_index"].get(edge_id)
        if (
            not isinstance(reference, dict)
            or set(reference) != {"part_sha256", "row_offset"}
            or type(reference["row_offset"]) is not int
            or reference["row_offset"] < 0
        ):
            raise ValueError("Taxon ancestry selected edge locator differs")
        digest = reference["part_sha256"]
        candidates = [
            part
            for part in manifest["parts"]
            if part["collection"] == "edges" and part["sha256"] == digest
        ]
        if len(candidates) != 1:
            raise ValueError("Taxon ancestry selected edge part differs")
        if digest not in cached:
            cached[digest] = _part(root, candidates[0])
        offset = reference["row_offset"]
        if offset >= len(cached[digest]) or not isinstance(
            cached[digest][offset], dict
        ):
            raise ValueError("Taxon ancestry selected edge row differs")
        edge = cached[digest][offset]
        if edge.get("edge_id") != edge_id or not (
            kind == "taxon"
            and edge.get("child_taxon_id") == identity
            or edge.get("target_kind") == kind
            and type(edge.get("native_id")) is int
            and edge["native_id"] == identity
        ):
            raise ValueError("Taxon ancestry selected edge native incidence differs")
        selected_edges.append(edge)
    return {
        "recorded_node": node,
        "recorded_edges": selected_edges,
        "recorded_context_sha256": manifest["authority"]["context_manifest_sha256"],
        "integrity_scope": "anchored_selected_metadata_parts_only",
        "current_roles_revalidated": False,
        "native_source_fields_revalidated": False,
        "native_entity_bodies_opened": 0,
        "GET_authorized": False,
        "scientific_admission": "not_asserted",
    }
