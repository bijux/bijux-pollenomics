"""Validate a closed regular archive and replay its exact native source witnesses."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from ...capture.receipts import _object, _read, _safe_root
from ...capture.resources import NeotomaRetainedSource
from ..custody import pinned_object, public_member
from ..publication import load_neotoma_resource_catalogue
from ..source_projection import _same
from .files import MAX_BYTES, MAX_MANIFEST_BYTES, validate_manifest, validate_namespace
from .index import build_download_index
from .original_metadata import resolve_original_metadata


def load_neotoma_source_archive(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    original_relational_root: Path | None = None,
) -> dict[str, Any]:
    """Reconcile the complete portable publication and replay every source capsule."""
    root = _safe_root(directory)
    raw = _read(root / "manifest.json", MAX_MANIFEST_BYTES)
    if sha256(raw).hexdigest() != expected_manifest_sha256:
        raise ValueError("Neotoma source archive manifest identity differs")
    manifest = _object(raw)
    validate_manifest(manifest)
    validate_namespace(root, {"manifest.json", *manifest["files"]})
    total = len(raw)
    source_bytes = 0
    for relative, member in manifest["files"].items():
        bound = min(member["bytes"], 32 * 1024 * 1024 + 1, MAX_BYTES - total)
        body = _read(root / relative, bound)
        total += len(body)
        source_bytes += len(body)
        if len(body) != member["bytes"] or sha256(body).hexdigest() != member["sha256"]:
            raise ValueError("Neotoma source archive member identity differs")
        if total > MAX_BYTES:
            raise ValueError("Neotoma source archive exceeds its finite byte budget")
    if manifest["source_bytes"] != source_bytes:
        raise ValueError("Neotoma source archive source byte population differs")
    compact = load_neotoma_resource_catalogue(
        root / "catalogue",
        expected_manifest_sha256=manifest["catalogue_manifest_sha256"],
    )
    publication = pinned_object(
        root / "catalogue/manifest.json",
        manifest["catalogue_manifest_sha256"],
        16 * 1024 * 1024,
    )
    expected_files = {
        "downloads/index.json",
        "catalogue/manifest.json",
        *("catalogue/" + name for name in publication["files"]),
    }
    if "original_metadata" in manifest:
        original_relational_root, original_files = resolve_original_metadata(
            root, manifest["original_metadata"], original_relational_root
        )
        expected_files.update(original_files)
    for digest, descriptor in compact["capture_descriptors"].items():
        expected_files.update(
            f"captures/{digest}/{public_member(member['name'])}"
            for member in descriptor["files"]
        )
    expected_retained = {
        f"dataset-{resource['dataset_id']}-{version}"
        for resource in compact["resources"]
        for version, selected in resource["versions"].items()
        if isinstance(selected.get("source"), dict)
        and selected["source"].get("source_kind") == "retained_public_response"
    }
    if set(manifest["retained_sources"]) != expected_retained:
        raise ValueError("Neotoma source archive retained population differs")
    for key, value in manifest["retained_sources"].items():
        if (
            value.get("body") != f"captures/retained/{key}/native.body"
            or value.get("provenance") != f"captures/retained/{key}/provenance.json"
        ):
            raise ValueError("Neotoma source archive retained path identity differs")
        expected_files.update((value["body"], value["provenance"]))
    if set(manifest["files"]) != expected_files:
        raise ValueError("Neotoma source archive declared source population differs")
    sources = {
        digest: root / "captures" / digest for digest in compact["capture_descriptors"]
    }
    retained = {
        key: NeotomaRetainedSource(
            root / value["body"],
            root / value["provenance"],
            value["provenance_sha256"],
            value["body_sha256"],
        )
        for key, value in manifest["retained_sources"].items()
    }
    load_neotoma_resource_catalogue(
        root / "catalogue",
        expected_manifest_sha256=manifest["catalogue_manifest_sha256"],
        capture_sources=sources,
        retained_sources=retained,
        original_relational_root=original_relational_root,
        require_source_bodies=True,
    )
    index = _object(_read(root / "downloads/index.json", 16 * 1024 * 1024))
    if not _same(
        index, build_download_index(compact, manifest["catalogue_manifest_sha256"])
    ):
        raise ValueError("Neotoma source archive download partition differs")
    for row in index["resources"]:
        if "download_path" in row:
            member = manifest["files"].get(row["download_path"])
            if member is None or member["sha256"] != row["source"]["body_sha256"]:
                raise ValueError("Neotoma source archive download identity differs")
    return manifest
