"""Bounded physical collection parts reconstruct the unchanged logical catalogue."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import OwnedTreeWriter

from ..capture.receipts import _object, _read, _write_json

TARGET_PART_BYTES = 2 * 1024 * 1024
MAX_PART_BYTES = 3 * 1024 * 1024
MAX_COLLECTION_BYTES = 64 * 1024 * 1024
_INDEX_SCHEMA = "neotoma-resource-catalogue-storage.v1"
_PART_SCHEMA = "neotoma-resource-catalogue-part.v1"
_COLLECTIONS = ("resources", "sites", "capture_descriptors")


def _encode(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)
        + "\n"
    ).encode()


def _part(name: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    return {"schema_version": _PART_SCHEMA, "collection": name, "records": records}


def write_partitioned_catalogue(
    root: Path, catalogue: dict[str, Any], *, writer: OwnedTreeWriter | None = None
) -> dict[str, str]:
    """Retain indivisible native rows and their order; refuse oversized records."""
    files = {}
    collections = {}
    total_bytes = 0

    def emit(
        name: str, pending: list[dict[str, Any]], parts: list[dict[str, Any]]
    ) -> None:
        nonlocal total_bytes
        content = _encode(_part(name, pending))
        if len(content) > MAX_PART_BYTES:
            raise ValueError("Catalogue partition contains an oversized native record")
        total_bytes += len(content)
        if total_bytes > MAX_COLLECTION_BYTES:
            raise ValueError("Catalogue partitions exceed the cumulative byte bound")
        digest = sha256(content).hexdigest()
        relative = f"parts/{name}/{digest}.json"
        target = root / relative
        if writer is None:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(content)
        else:
            writer.write_bytes(target.relative_to(writer.root).as_posix(), content)
        files[relative] = digest
        parts.append(
            {
                "path": relative,
                "sha256": digest,
                "bytes": len(content),
                "row_count": len(pending),
            }
        )

    for name in _COLLECTIONS:
        records = (
            catalogue[name]
            if name != "capture_descriptors"
            else [
                {"capture_manifest_sha256": key, "descriptor": value}
                for key, value in sorted(catalogue[name].items())
            ]
        )
        parts: list[dict[str, Any]] = []
        pending: list[dict[str, Any]] = []
        pending_bytes = 256

        for record in records:
            content = _encode(record)
            cost = len(content) + 4 * (content.count(b"\n") + 1) + 2
            if pending and pending_bytes + cost > TARGET_PART_BYTES:
                emit(name, pending, parts)
                pending = []
                pending_bytes = 256
            pending.append(record)
            pending_bytes += cost
        if pending:
            emit(name, pending, parts)
        collections[name] = {"row_count": len(records), "parts": parts}
    index = {
        "schema_version": _INDEX_SCHEMA,
        "catalogue_context": {
            key: value for key, value in catalogue.items() if key not in _COLLECTIONS
        },
        "collections": collections,
    }
    if len(_encode(index)) > MAX_PART_BYTES:
        raise ValueError("Catalogue partition index exceeds its bounded file size")
    files["catalogue.json"] = _write_json(root / "catalogue.json", index, writer=writer)
    return files


def load_partitioned_catalogue(
    root: Path, index: dict[str, Any], files: dict[str, str]
) -> dict[str, Any]:
    """Require a closed content-addressed join before exposing logical records."""
    if (
        set(index) != {"schema_version", "catalogue_context", "collections"}
        or index["schema_version"] != _INDEX_SCHEMA
        or not isinstance(index["catalogue_context"], dict)
        or set(index["catalogue_context"]).intersection(_COLLECTIONS)
        or not isinstance(index["collections"], dict)
        or set(index["collections"]) != set(_COLLECTIONS)
        or len(_encode(index)) > MAX_PART_BYTES
    ):
        raise ValueError("Catalogue partition index or collection set differs")
    catalogue = dict(index["catalogue_context"])
    selected_parts: set[str] = set()
    total_bytes = 0
    for name in _COLLECTIONS:
        collection = index["collections"][name]
        if (
            not isinstance(collection, dict)
            or set(collection) != {"row_count", "parts"}
            or type(collection["row_count"]) is not int
            or collection["row_count"] < 0
            or not isinstance(collection["parts"], list)
            or len(collection["parts"]) > 4096
        ):
            raise ValueError("Catalogue collection partition population is invalid")
        records = []
        for member in collection["parts"]:
            if (
                not isinstance(member, dict)
                or set(member) != {"path", "sha256", "bytes", "row_count"}
                or type(member["bytes"]) is not int
                or not 0 < member["bytes"] <= MAX_PART_BYTES
                or type(member["row_count"]) is not int
                or member["row_count"] <= 0
                or member["path"] != f"parts/{name}/{member['sha256']}.json"
                or member["path"] in selected_parts
                or files.get(member["path"]) != member["sha256"]
            ):
                raise ValueError("Catalogue part identity, size or membership differs")
            selected_parts.add(member["path"])
            total_bytes += member["bytes"]
            if total_bytes > MAX_COLLECTION_BYTES:
                raise ValueError(
                    "Catalogue partitions exceed the cumulative byte bound"
                )
            body = _read(root / member["path"], member["bytes"])
            if (
                len(body) != member["bytes"]
                or sha256(body).hexdigest() != member["sha256"]
            ):
                raise ValueError("Catalogue partition content identity differs")
            part = _object(body)
            if (
                set(part) != {"schema_version", "collection", "records"}
                or part["schema_version"] != _PART_SCHEMA
                or part["collection"] != name
                or not isinstance(part["records"], list)
                or len(part["records"]) != member["row_count"]
                or any(not isinstance(row, dict) for row in part["records"])
            ):
                raise ValueError("Catalogue partition native row population differs")
            records.extend(part["records"])
        if len(records) != collection["row_count"]:
            raise ValueError("Catalogue collection count differs from ordered parts")
        if name != "capture_descriptors":
            catalogue[name] = records
            continue
        descriptors = {}
        for record in records:
            if (
                set(record) != {"capture_manifest_sha256", "descriptor"}
                or not isinstance(record["capture_manifest_sha256"], str)
                or record["capture_manifest_sha256"] in descriptors
            ):
                raise ValueError(
                    "Catalogue descriptor partition identity repeats or differs"
                )
            descriptors[record["capture_manifest_sha256"]] = record["descriptor"]
        catalogue[name] = descriptors
    if {name for name in files if name.startswith("parts/")} != selected_parts:
        raise ValueError("Catalogue partition file inventory is not closed")
    return catalogue
