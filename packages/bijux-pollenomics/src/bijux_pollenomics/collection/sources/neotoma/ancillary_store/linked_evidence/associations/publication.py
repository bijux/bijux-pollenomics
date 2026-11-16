"""Exclusive bounded publication of later source relationships, without source copies."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import (
    OwnedTreeWriter,
    validate_regular_namespace,
)
from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
)

from ....capture.linked_resources.models import NeotomaLinkedEvidence
from ....capture.receipts import _object, _safe_root
from ....publication.ownership import publish_owned_source_tree
from ....resource_catalogue.archive.files import _digest, encoded_json
from ....resource_catalogue.source_projection import _same
from ...selection.metadata import pinned
from .models import (
    MAX_BYTES,
    MAX_METADATA_BYTES,
    MAX_PART_BYTES,
    MAX_PARTS,
    MAX_TARGETS,
    PART_TARGET_BYTES,
    SCHEMA,
    NeotomaLinkedAssociationInputs,
)
from .projection import build_neotoma_linked_associations


def _buffers(document: dict[str, Any]) -> tuple[dict[str, Any], dict[str, bytes]]:
    targets = document["targets"]
    if not isinstance(targets, list) or len(targets) > MAX_TARGETS:
        raise ValueError("Association target population exceeds finite bound")
    parts: list[dict[str, Any]] = []
    buffers: dict[str, bytes] = {}
    pending: list[dict[str, Any]] = []

    def flush() -> None:
        if not pending:
            return
        raw = encoded_json({"schema_version": SCHEMA, "targets": pending})
        if len(raw) > MAX_PART_BYTES or len(parts) >= MAX_PARTS:
            raise ValueError("Association part exceeds finite publication bound")
        digest = sha256(raw).hexdigest()
        name = f"targets/{digest}.json"
        parts.append(
            {
                "path": name,
                "sha256": digest,
                "bytes": len(raw),
                "count": len(pending),
                "first_key": pending[0]["target_key"],
                "last_key": pending[-1]["target_key"],
            }
        )
        buffers[name] = raw
        pending.clear()

    for row in targets:
        candidate = encoded_json({"schema_version": SCHEMA, "targets": [*pending, row]})
        if pending and len(candidate) > PART_TARGET_BYTES:
            flush()
        pending.append(row)
    flush()
    manifest = {key: value for key, value in document.items() if key != "targets"}
    manifest["parts"] = parts
    if (
        len(encoded_json(manifest)) > MAX_METADATA_BYTES
        or sum(map(len, buffers.values())) + len(encoded_json(manifest)) > MAX_BYTES
    ):
        raise ValueError("Association publication exceeds finite byte budget")
    return manifest, buffers


def read_manifest(directory: Path, digest: str) -> dict[str, Any]:
    """Validate all declared part budgets before any selected part is opened."""
    root = _safe_root(directory)
    document = _object(pinned(root / "manifest.json", digest, bound=MAX_METADATA_BYTES))
    if (
        document.get("schema_version") != SCHEMA
        or not isinstance(document.get("parts"), list)
        or len(document["parts"]) > MAX_PARTS
    ):
        raise ValueError("Association manifest schema or part population differs")
    names, total, count, previous = set(), 0, 0, None
    for part in document["parts"]:
        if (
            not isinstance(part, dict)
            or set(part)
            != {"path", "sha256", "bytes", "count", "first_key", "last_key"}
            or not _digest(part.get("sha256"))
            or part.get("path") != f"targets/{part['sha256']}.json"
            or type(part.get("bytes")) is not int
            or not 0 < part["bytes"] <= MAX_PART_BYTES
            or type(part.get("count")) is not int
            or not 0 < part["count"] <= MAX_TARGETS
            or not isinstance(part.get("first_key"), str)
            or not isinstance(part.get("last_key"), str)
            or part["first_key"] > part["last_key"]
            or (previous is not None and previous >= part["first_key"])
            or part["path"] in names
        ):
            raise ValueError("Association part identity or key range differs")
        names.add(part["path"])
        previous = part["last_key"]
        total += part["bytes"]
        count += part["count"]
    if (
        total + len(encoded_json(document)) > MAX_BYTES
        or count > MAX_TARGETS
        or not isinstance(document.get("summary"), dict)
        or type(document["summary"].get("targets")) is not int
        or count != document["summary"]["targets"]
    ):
        raise ValueError("Association declared count or byte budget differs")
    return document


def read_part(directory: Path, part: dict[str, Any]) -> list[dict[str, Any]]:
    raw = pinned(
        _safe_root(directory) / part["path"],
        part["sha256"],
        part["bytes"],
        bound=MAX_PART_BYTES,
    )
    document = _object(raw)
    rows = document.get("targets")
    if (
        set(document) != {"schema_version", "targets"}
        or document["schema_version"] != SCHEMA
        or not isinstance(rows, list)
        or len(rows) != part["count"]
        or any(
            not isinstance(row, dict) or not isinstance(row.get("target_key"), str)
            for row in rows
        )
    ):
        raise ValueError("Association part target population differs")
    keys = [row["target_key"] for row in rows]
    if (
        keys != sorted(set(keys))
        or keys[0] != part["first_key"]
        or keys[-1] != part["last_key"]
    ):
        raise ValueError("Association part key closure differs")
    return rows


def load_neotoma_linked_associations(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    evidence: NeotomaLinkedEvidence,
    inputs: NeotomaLinkedAssociationInputs,
) -> dict[str, Any]:
    """Rederive the entire metadata projection; native entity buffers remain unopened."""
    manifest = read_manifest(directory, expected_manifest_sha256)
    sizes = validate_regular_namespace(
        _safe_root(directory),
        {"manifest.json", *(part["path"] for part in manifest["parts"])},
        max_files=MAX_PARTS + 1,
        max_bytes=MAX_BYTES,
    )
    rows = []
    for part in manifest["parts"]:
        if sizes[part["path"]] != part["bytes"]:
            raise ValueError("Association part physical size differs")
        rows.extend(read_part(directory, part))
    document = {key: value for key, value in manifest.items() if key != "parts"}
    document["targets"] = rows
    expected = build_neotoma_linked_associations(evidence, inputs=inputs)
    if not _same(document, expected):
        raise ValueError("Association source projection differs")
    return document


def publish_neotoma_linked_associations(
    directory: Path,
    *,
    document: dict[str, Any],
    evidence: NeotomaLinkedEvidence,
    inputs: NeotomaLinkedAssociationInputs,
) -> dict[str, Any]:
    """Refuse foreign output, authenticate inputs and validate the published tree."""
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Linked associations already exist: {final}")
    expected = build_neotoma_linked_associations(evidence, inputs=inputs)
    if not _same(document, expected):
        raise ValueError("Association source projection differs")
    manifest, buffers = _buffers(expected)
    raw = encoded_json(manifest)
    digest = sha256(raw).hexdigest()
    staging = build_staging_output_dir(final)
    kwargs: dict[str, Any] = {
        "expected_manifest_sha256": digest,
        "evidence": evidence,
        "inputs": inputs,
    }
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
            validate=lambda location: load_neotoma_linked_associations(
                location, **kwargs
            ),
        )
    return manifest
