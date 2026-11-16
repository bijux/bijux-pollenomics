"""Bounded content-addressed ancestry parts shared by explicit domain schemas."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import validate_regular_namespace

from ....resource_catalogue.archive.files import _digest, encoded_json
from ....resource_catalogue.source_projection import _same
from ...receipts import _object, _read, _safe_root
from .models import (
    HARD_PART_BYTES,
    MAX_BYTES,
    MAX_METADATA_BYTES,
    MAX_PARTS,
    PART_BYTES,
    SCHEMA,
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


def _pack(
    document: dict[str, Any],
    *,
    collections: tuple[str, ...] = COLLECTIONS,
    schema: str = SCHEMA,
    part_bytes: int = PART_BYTES,
    hard_part_bytes: int = HARD_PART_BYTES,
    encoder: Any = encoded_json,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    manifest = {key: value for key, value in document.items() if key not in collections}
    parts: list[dict[str, Any]] = []
    buffers = {}
    nodes = {}
    edges = {}
    for collection in collections:
        pending: list[Any] = []
        envelope_bytes = (
            len(
                encoder(
                    {"schema_version": schema, "collection": collection, "rows": []}
                )
            )
            + 2
        )
        pending_bytes = envelope_bytes

        def flush(collection: str, pending: list[Any]) -> None:
            if not pending:
                return
            raw = encoded_json(
                {"schema_version": schema, "collection": collection, "rows": pending}
            )
            if len(raw) > hard_part_bytes or len(parts) >= MAX_PARTS:
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
            if envelope_bytes + row_bytes > hard_part_bytes:
                raise ValueError("Taxon ancestry part exceeds finite publication bound")
            if pending and pending_bytes + row_bytes > part_bytes:
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


def _manifest(
    root: Path,
    digest: str,
    *,
    collections: tuple[str, ...] = COLLECTIONS,
    schema: str = SCHEMA,
) -> dict[str, Any]:
    raw = _pinned(root / "manifest.json", digest, MAX_METADATA_BYTES)
    manifest = _object(raw)
    if (
        manifest.get("schema_version") != schema
        or not isinstance(manifest.get("parts"), list)
        or len(manifest["parts"]) > MAX_PARTS
    ):
        raise ValueError("Taxon ancestry metadata schema or parts differ")
    total = len(raw)
    names = set()
    counts = dict.fromkeys(collections, 0)
    for part in manifest["parts"]:
        if (
            not isinstance(part, dict)
            or set(part) != {"collection", "path", "sha256", "bytes", "rows"}
            or part.get("collection") not in collections
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


def _part(root: Path, part: dict[str, Any], *, schema: str = SCHEMA) -> list[Any]:
    doc = _object(
        _pinned(root / part["path"], part["sha256"], part["bytes"], part["bytes"])
    )
    rows = doc.get("rows")
    if (
        set(doc) != {"schema_version", "collection", "rows"}
        or doc["schema_version"] != schema
        or doc["collection"] != part["collection"]
        or not isinstance(rows, list)
        or len(rows) != part["rows"]
    ):
        raise ValueError("Taxon ancestry part population differs")
    return rows


def _readback(
    root: Path,
    digest: str,
    *,
    collections: tuple[str, ...] = COLLECTIONS,
    schema: str = SCHEMA,
) -> dict[str, Any]:
    root = _safe_root(root)
    manifest = _manifest(root, digest, collections=collections, schema=schema)
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
    document.update({name: [] for name in collections})
    for part in manifest["parts"]:
        document[part["collection"]].extend(_part(root, part, schema=schema))
    expected, buffers = _pack(document, collections=collections, schema=schema)
    if not _same(expected, manifest):
        raise ValueError("Taxon ancestry index or part closure differs")
    for name, raw in buffers.items():
        if _read(root / name, len(raw)) != raw:
            raise ValueError("Taxon ancestry part bytes differ")
    return document
