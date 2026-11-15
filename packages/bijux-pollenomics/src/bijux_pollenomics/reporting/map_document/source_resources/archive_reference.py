"""Authenticate shared download metadata without opening source entities."""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import re
import stat
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _object
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
    MAX_MANIFEST_BYTES,
    validate_manifest,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.index import (
    build_download_index,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.source_projection import (
    _same,
)

from .models import AtlasResourceArchiveInput, _published_base_url

_SCHEMA = "atlas-source-resource-archive-reference.v1"


def _pinned(
    root: Path, member: str, digest: str, *, expected_size: int | None = None
) -> tuple[dict[str, Any], int]:
    path = root / member
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("Atlas source archive metadata path is redirected")
    before = path.stat(follow_symlinks=False)
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
        or before.st_size > MAX_MANIFEST_BYTES
    ):
        raise ValueError(
            "Atlas source archive metadata is not a bounded unaliased file"
        )
    if expected_size is not None and before.st_size != expected_size:
        raise ValueError("Atlas source archive metadata declared byte count differs")
    identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if (opened.st_dev, opened.st_ino) != identity[:2]:
            raise ValueError("Atlas source archive metadata changed while opening")
        content = stream.read(before.st_size + 1)
    after = path.stat(follow_symlinks=False)
    if (
        len(content) != before.st_size
        or (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        != identity
        or not stat.S_ISREG(after.st_mode)
        or after.st_nlink != 1
        or sha256(content).hexdigest() != digest
    ):
        raise ValueError("Atlas source archive metadata identity differs")
    return _object(content), len(content)


def validate_archive_reference(
    value: object, *, catalogue_manifest_sha256: str
) -> None:
    """Validate a portable metadata-only binding carried by an Atlas context part."""
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "catalogue_manifest_sha256",
        "manifest_sha256",
        "published_base_url",
        "index",
        "validation_scope",
        "file_protocol_downloads",
        "scientific_admission",
    }:
        raise ValueError("Atlas source archive reference fields differ")
    index = value["index"]
    if (
        value["schema_version"] != _SCHEMA
        or value["catalogue_manifest_sha256"] != catalogue_manifest_sha256
        or not isinstance(value["manifest_sha256"], str)
        or re.fullmatch(r"[a-f0-9]{64}", value["manifest_sha256"]) is None
        or value["validation_scope"] != "manifest_and_download_index_only"
        or value["file_protocol_downloads"] != "unavailable_requires_local_http"
        or value["scientific_admission"] != "not_asserted"
        or not isinstance(index, dict)
        or set(index) != {"path", "sha256", "bytes"}
        or index["path"] != "downloads/index.json"
        or type(index["bytes"]) is not int
        or not 0 < index["bytes"] <= MAX_MANIFEST_BYTES
        or not isinstance(index["sha256"], str)
        or re.fullmatch(r"[a-f0-9]{64}", index["sha256"]) is None
    ):
        raise ValueError("Atlas source archive reference identity or scope differs")
    _published_base_url(value["published_base_url"])


def load_archive_reference(
    source: AtlasResourceArchiveInput,
    *,
    catalogue: dict[str, Any],
    catalogue_manifest_sha256: str,
) -> dict[str, Any]:
    """Verify only manifest/index; the shared producer owns full archive replay."""
    root = source.directory.absolute()
    if root.resolve(strict=True) != root or not root.is_dir():
        raise ValueError("Atlas source archive root must be physical")
    manifest, _ = _pinned(root, "manifest.json", source.expected_manifest_sha256)
    validate_manifest(manifest)
    if manifest["catalogue_manifest_sha256"] != catalogue_manifest_sha256:
        raise ValueError("Atlas source archive catalogue identity differs")
    member = manifest["files"].get("downloads/index.json")
    if not isinstance(member, dict):
        raise ValueError("Atlas source archive download index is undeclared")
    index, size = _pinned(
        root, "downloads/index.json", member["sha256"], expected_size=member["bytes"]
    )
    if size != member["bytes"] or not _same(
        index, build_download_index(catalogue, catalogue_manifest_sha256)
    ):
        raise ValueError("Atlas source archive download index differs from catalogue")
    for row in index["resources"]:
        if "download_path" in row:
            file = manifest["files"].get(row["download_path"])
            declared_size = row["source"].get("body_bytes")
            if (
                file is None
                or file["sha256"] != row["source"]["body_sha256"]
                or (
                    "body_bytes" in row["source"]
                    and (
                        type(declared_size) is not int or declared_size != file["bytes"]
                    )
                )
            ):
                raise ValueError("Atlas source archive download body identity differs")
    reference = {
        "schema_version": _SCHEMA,
        "catalogue_manifest_sha256": catalogue_manifest_sha256,
        "manifest_sha256": source.expected_manifest_sha256,
        "published_base_url": source.published_base_url,
        "index": {
            "path": "downloads/index.json",
            "bytes": size,
            "sha256": member["sha256"],
        },
        "validation_scope": "manifest_and_download_index_only",
        "file_protocol_downloads": "unavailable_requires_local_http",
        "scientific_admission": "not_asserted",
    }
    validate_archive_reference(
        reference, catalogue_manifest_sha256=catalogue_manifest_sha256
    )
    return reference
