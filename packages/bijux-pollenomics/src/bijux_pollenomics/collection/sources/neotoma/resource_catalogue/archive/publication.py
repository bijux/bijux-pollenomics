"""Publish one complete archive through descriptor-bound writes and atomic no-replace."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
    publish_new_output_tree,
)

from ...capture.receipts import _read, _safe_root
from ...capture.resources import NeotomaRetainedSource
from ..custody import pinned_object, public_member
from ..publication import load_neotoma_resource_catalogue
from .files import (
    ARCHIVE_SCHEMA,
    MAX_BYTES,
    MAX_FILES,
    MAX_MANIFEST_BYTES,
    encoded_json,
)
from .index import build_download_index
from .validation import load_neotoma_source_archive


def write_neotoma_source_archive(
    directory: Path,
    *,
    catalogue_directory: Path,
    expected_catalogue_manifest_sha256: str,
    capture_sources: Mapping[str, Path],
    retained_sources: Mapping[str, NeotomaRetainedSource] | None = None,
    original_relational_root: Path | None = None,
) -> dict[str, Any]:
    """Copy verified original buffers once; downloads point to those same entities.

    Full maintained replay validates exposure roles before numerical entities.
    Complete capsules retain failures and original labels. The index provides
    download links only for successful complete public development entities.
    """
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Neotoma source archive already exists: {final}")
    catalogue_root = _safe_root(catalogue_directory)
    catalogue = load_neotoma_resource_catalogue(
        catalogue_root,
        expected_manifest_sha256=expected_catalogue_manifest_sha256,
        capture_sources=capture_sources,
        retained_sources=retained_sources,
        original_relational_root=original_relational_root,
        require_source_bodies=True,
    )
    staging = build_staging_output_dir(final)
    files: dict[str, dict[str, Any]] = {}
    total = 0

    def copy(content: bytes, relative: str, digest: str) -> None:
        nonlocal total
        if sha256(content).hexdigest() != digest:
            raise ValueError("Source archive input identity differs")
        writer.write_bytes(relative, content)
        total += len(content)
        files[relative] = {"bytes": len(content), "sha256": digest}

    with OwnedTreeWriter(staging, max_bytes=MAX_BYTES, max_files=MAX_FILES) as writer:
        public = pinned_object(
            catalogue_root / "manifest.json",
            expected_catalogue_manifest_sha256,
            16 * 1024 * 1024,
        )
        for relative, digest in {
            **public["files"],
            "manifest.json": expected_catalogue_manifest_sha256,
        }.items():
            copy(
                _read(catalogue_root / relative, 16 * 1024 * 1024),
                "catalogue/" + relative,
                digest,
            )
        for digest, descriptor in catalogue["capture_descriptors"].items():
            root = _safe_root(capture_sources[digest])
            for member in descriptor["files"]:
                name = public_member(member["name"])
                content = _read(root / name, 32 * 1024 * 1024 + 1)
                if len(content) != member["bytes"]:
                    raise ValueError("Source archive native member length differs")
                copy(content, f"captures/{digest}/{name}", member["sha256"])
        retained = {}
        retained_keys = {
            f"dataset-{resource['dataset_id']}-{version}"
            for resource in catalogue["resources"]
            for version, selected in resource["versions"].items()
            if isinstance(selected.get("source"), dict)
            and selected["source"].get("source_kind") == "retained_public_response"
        }
        for key in sorted(retained_keys):
            source = (retained_sources or {})[key]
            public_member(key)
            body = f"captures/retained/{key}/native.body"
            provenance = f"captures/retained/{key}/provenance.json"
            copy(
                _read(_safe_root(source.body_path), 32 * 1024 * 1024),
                body,
                source.body_sha256,
            )
            copy(
                _read(_safe_root(source.provenance_path), 100000),
                provenance,
                source.provenance_sha256,
            )
            retained[key] = {
                "body": body,
                "provenance": provenance,
                "body_sha256": source.body_sha256,
                "provenance_sha256": source.provenance_sha256,
            }
        index = build_download_index(catalogue, expected_catalogue_manifest_sha256)
        content = encoded_json(index)
        copy(content, "downloads/index.json", sha256(content).hexdigest())
        manifest = {
            "schema_version": ARCHIVE_SCHEMA,
            "catalogue_manifest_sha256": expected_catalogue_manifest_sha256,
            "files": files,
            "retained_sources": retained,
            "source_bytes": total,
            "scientific_admission": "not_asserted",
            "historical_snapshot_replaced": False,
        }
        content = encoded_json(manifest)
        if len(content) > MAX_MANIFEST_BYTES:
            raise ValueError("Source archive manifest exceeds its finite byte budget")
        digest = sha256(content).hexdigest()
        writer.write_bytes("manifest.json", content)
    load_neotoma_source_archive(
        staging,
        expected_manifest_sha256=digest,
        original_relational_root=original_relational_root,
    )
    publish_new_output_tree(final_output_root=final, staging_output_root=staging)
    load_neotoma_source_archive(
        final,
        expected_manifest_sha256=digest,
        original_relational_root=original_relational_root,
    )
    return manifest
