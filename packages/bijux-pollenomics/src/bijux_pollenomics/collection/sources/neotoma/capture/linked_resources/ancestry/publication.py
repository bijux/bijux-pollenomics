"""Exclusive bounded ancestry metadata parts with explicit full-source readback."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import (
    OwnedTreeWriter,
    validate_regular_namespace,
)
from bijux_pollenomics.core.owned_tree import build_staging_output_dir

from ....client import positive_native_id
from ....publication.ownership import publish_owned_source_tree
from ....resource_catalogue.archive.files import _digest, encoded_json
from ....resource_catalogue.source_projection import _same
from ...receipts import _object, _read, _safe_root
from .layers import derive_neotoma_taxon_ancestry
from .models import (
    HARD_PART_BYTES,
    MAX_BYTES,
    MAX_METADATA_BYTES,
    MAX_PARTS,
    PART_BYTES,
    SCHEMA,
    NeotomaTaxonAncestryLimits,
    NeotomaTaxonAncestrySources,
)

COLLECTIONS = ("seeds", "edges", "taxa", "publications", "frontier", "cycle_components")


def _pinned(path: Path, digest: str, bound: int, size: int | None = None) -> bytes:
    raw = _read(_safe_root(path), bound)
    if (
        not _digest(digest)
        or sha256(raw).hexdigest() != digest
        or size is not None
        and len(raw) != size
    ):
        raise ValueError("Taxon ancestry metadata identity or size differs")
    return raw


def _pack(document: dict[str, Any]) -> tuple[dict[str, Any], dict[str, bytes]]:
    manifest = {key: value for key, value in document.items() if key not in COLLECTIONS}
    parts: list[dict[str, Any]] = []
    buffers = {}
    nodes = {}
    edges = {}
    for collection in COLLECTIONS:
        pending: list[Any] = []
        envelope_bytes = (
            len(
                encoded_json(
                    {"schema_version": SCHEMA, "collection": collection, "rows": []}
                )
            )
            + 2
        )
        pending_bytes = envelope_bytes

        def flush(collection: str, pending: list[Any]) -> None:
            if not pending:
                return
            raw = encoded_json(
                {"schema_version": SCHEMA, "collection": collection, "rows": pending}
            )
            if len(raw) > HARD_PART_BYTES or len(parts) >= MAX_PARTS:
                raise ValueError("Taxon ancestry part exceeds finite publication bound")
            digest = sha256(raw).hexdigest()
            path = f"parts/{collection}/{digest}.json"
            parts.append(
                {
                    "collection": collection,
                    "path": path,
                    "sha256": digest,
                    "bytes": len(raw),
                    "rows": len(pending),
                }
            )
            buffers[path] = raw
            for offset, row in enumerate(pending):
                locator = {"part_sha256": digest, "row_offset": offset}
                if collection in {"taxa", "publications"}:
                    if row["target_key"] in nodes:
                        raise ValueError("Taxon ancestry target is duplicated")
                    nodes[row["target_key"]] = locator
                elif collection == "edges":
                    if row["edge_id"] in edges:
                        raise ValueError("Taxon ancestry edge is duplicated")
                    edges[row["edge_id"]] = locator
            pending.clear()

        for row in document[collection]:
            raw_row = encoded_json(row)
            # Array membership adds four spaces to every encoded row line.
            # The final newline becomes a separator; account for its comma once.
            row_bytes = len(raw_row) + 4 * raw_row.count(b"\n") + 1
            if envelope_bytes + row_bytes > HARD_PART_BYTES:
                raise ValueError("Taxon ancestry part exceeds finite publication bound")
            if pending and pending_bytes + row_bytes > PART_BYTES:
                flush(collection, pending)
                pending_bytes = envelope_bytes
            pending.append(row)
            pending_bytes += row_bytes
        flush(collection, pending)
    manifest.update(parts=parts, node_index=nodes, edge_index=edges)
    raw = encoded_json(manifest)
    if (
        len(raw) > MAX_METADATA_BYTES
        or len(raw) + sum(map(len, buffers.values())) > MAX_BYTES
    ):
        raise ValueError("Taxon ancestry exceeds finite publication byte budget")
    return manifest, buffers


def _manifest(root: Path, digest: str) -> dict[str, Any]:
    raw = _pinned(root / "manifest.json", digest, MAX_METADATA_BYTES)
    manifest = _object(raw)
    if (
        manifest.get("schema_version") != SCHEMA
        or not isinstance(manifest.get("parts"), list)
        or len(manifest["parts"]) > MAX_PARTS
    ):
        raise ValueError("Taxon ancestry metadata schema or parts differ")
    total = len(raw)
    names = set()
    counts = dict.fromkeys(COLLECTIONS, 0)
    for part in manifest["parts"]:
        if (
            not isinstance(part, dict)
            or set(part) != {"collection", "path", "sha256", "bytes", "rows"}
            or part.get("collection") not in COLLECTIONS
            or not _digest(part.get("sha256"))
            or part.get("path") != f"parts/{part['collection']}/{part['sha256']}.json"
            or part["path"] in names
            or type(part.get("bytes")) is not int
            or not 0 < part["bytes"] <= HARD_PART_BYTES
            or type(part.get("rows")) is not int
            or not 0 < part["rows"] <= 100000
        ):
            raise ValueError("Taxon ancestry part contract differs")
        names.add(part["path"])
        total += part["bytes"]
        counts[part["collection"]] += part["rows"]
    if (
        total > MAX_BYTES
        or not isinstance(manifest.get("node_index"), dict)
        or not isinstance(manifest.get("edge_index"), dict)
    ):
        raise ValueError("Taxon ancestry index or aggregate byte budget differs")
    return manifest


def _part(root: Path, part: dict[str, Any]) -> list[Any]:
    doc = _object(
        _pinned(root / part["path"], part["sha256"], part["bytes"], part["bytes"])
    )
    rows = doc.get("rows")
    if (
        set(doc) != {"schema_version", "collection", "rows"}
        or doc["schema_version"] != SCHEMA
        or doc["collection"] != part["collection"]
        or not isinstance(rows, list)
        or len(rows) != part["rows"]
    ):
        raise ValueError("Taxon ancestry part population differs")
    return rows


def _readback(root: Path, digest: str) -> dict[str, Any]:
    root = _safe_root(root)
    manifest = _manifest(root, digest)
    validate_regular_namespace(
        root,
        {"manifest.json", *(part["path"] for part in manifest["parts"])},
        max_files=MAX_PARTS + 1,
        max_bytes=MAX_BYTES,
    )
    document = {
        key: value
        for key, value in manifest.items()
        if key not in {"parts", "node_index", "edge_index"}
    }
    document.update({name: [] for name in COLLECTIONS})
    for part in manifest["parts"]:
        document[part["collection"]].extend(_part(root, part))
    expected, buffers = _pack(document)
    if not _same(expected, manifest):
        raise ValueError("Taxon ancestry index or part closure differs")
    for name, raw in buffers.items():
        if _read(root / name, len(raw)) != raw:
            raise ValueError("Taxon ancestry part bytes differ")
    return document


def load_neotoma_taxon_ancestry(
    root: Path, *, expected_manifest_sha256: str, sources: NeotomaTaxonAncestrySources
) -> dict[str, Any]:
    """Explicitly replay complete declared sources; no current-schema fallback."""
    document = _readback(root, expected_manifest_sha256)
    limits = NeotomaTaxonAncestryLimits(**document["limits"])
    if not _same(document, derive_neotoma_taxon_ancestry(sources, limits=limits)):
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
