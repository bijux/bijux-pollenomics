"""Preflight the exact archive footprint before replaying external native bodies."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import stat
from typing import Any

from bijux_pollenomics.core.filesystem import validate_regular_namespace

from ...capture.receipts import _safe_root
from ...capture.resources import NeotomaRetainedSource
from ..custody import pinned_object, public_member
from ..publication import load_neotoma_resource_catalogue
from .files import ARCHIVE_SCHEMA, _digest, _member, encoded_json
from .index import build_download_index
from .original_metadata import _PREFIX, _SCOPE, preflight_metadata


@dataclass(frozen=True)
class ArchiveInputs:
    """Deterministic prospective publication; stat checks do not qualify sources."""

    manifest: dict[str, Any]
    paths: dict[str, tuple[Path, int]]
    index: bytes


def preflight_archive_inputs(
    catalogue_directory: Path,
    *,
    expected_catalogue_manifest_sha256: str,
    capture_sources: Mapping[str, Path],
    retained_sources: Mapping[str, NeotomaRetainedSource] | None,
    original_relational_root: Path | None,
    max_bytes: int,
    max_files: int,
    max_manifest_bytes: int,
) -> ArchiveInputs:
    """Read compact metadata only; bound every consumed file and generated member."""
    if any(
        type(value) is not int or value <= 0
        for value in (max_bytes, max_files, max_manifest_bytes)
    ):
        raise ValueError("Source archive requires positive native finite budgets")
    root = _safe_root(catalogue_directory)
    catalogue = load_neotoma_resource_catalogue(
        root, expected_manifest_sha256=expected_catalogue_manifest_sha256
    )
    public = pinned_object(
        root / "manifest.json", expected_catalogue_manifest_sha256, 16 * 1024 * 1024
    )
    files: dict[str, dict[str, Any]] = {}
    paths: dict[str, tuple[Path, int]] = {}
    total = 0

    def register(relative: str, size: int, digest: str) -> None:
        nonlocal total
        _member(relative)
        if relative in files or not _digest(digest):
            raise ValueError("Source archive input member identity is ambiguous")
        if len(files) + 2 > max_files or total + size > max_bytes:
            raise ValueError(
                "Source archive inputs exceed the finite publication budget"
            )
        total += size
        files[relative] = {"bytes": size, "sha256": digest}

    def source(
        path: Path,
        relative: str,
        digest: str,
        maximum: int,
        expected_bytes: int | None = None,
    ) -> None:
        path = _safe_root(path)
        try:
            node = path.stat(follow_symlinks=False)
        except OSError as error:
            raise ValueError("Source archive input member is unavailable") from error
        if (
            not stat.S_ISREG(node.st_mode)
            or node.st_nlink != 1
            or node.st_size > maximum
            or (expected_bytes is not None and node.st_size != expected_bytes)
        ):
            raise ValueError(
                "Source archive input member is not its bounded regular file"
            )
        register(relative, node.st_size, digest)
        paths[relative] = path, maximum

    for name, digest in {
        **public["files"],
        "manifest.json": expected_catalogue_manifest_sha256,
    }.items():
        source(root / name, "catalogue/" + name, digest, 16 * 1024 * 1024)
    for digest, descriptor in catalogue["capture_descriptors"].items():
        if digest not in capture_sources:
            raise ValueError("Source archive capture resolver is required")
        capture = _safe_root(capture_sources[digest])
        validate_regular_namespace(
            capture,
            {member["name"] for member in descriptor["files"]},
            max_files=max_files,
            max_bytes=max_bytes,
        )
        for member in descriptor["files"]:
            name = public_member(member["name"])
            source(
                capture / name,
                f"captures/{digest}/{name}",
                member["sha256"],
                32 * 1024 * 1024 + 1,
                member["bytes"],
            )
    retained = {}
    for resource in catalogue["resources"]:
        for version, selected in resource["versions"].items():
            reference = selected.get("source")
            if (
                not isinstance(reference, dict)
                or reference.get("source_kind") != "retained_public_response"
            ):
                continue
            key = f"dataset-{resource['dataset_id']}-{version}"
            public_member(key)
            original = (retained_sources or {}).get(key)
            if original is None or (
                original.body_sha256 != reference.get("body_sha256")
                or original.provenance_sha256 != reference.get("provenance_sha256")
            ):
                raise ValueError("Source archive retained input identity differs")
            body = f"captures/retained/{key}/native.body"
            provenance = f"captures/retained/{key}/provenance.json"
            source(original.body_path, body, original.body_sha256, 32 * 1024 * 1024)
            source(
                original.provenance_path, provenance, original.provenance_sha256, 100000
            )
            retained[key] = {
                "body": body,
                "provenance": provenance,
                "body_sha256": original.body_sha256,
                "provenance_sha256": original.provenance_sha256,
            }
    original_metadata = None
    if original_relational_root is not None:
        original_root = _safe_root(original_relational_root)
        surface, members = preflight_metadata(original_root)
        original_metadata = {
            "scope": _SCOPE,
            "manifest_path": _PREFIX + "manifest.json",
            "manifest_sha256": members["manifest.json"],
            "dataset_row_count": surface["row_count"],
            "dataset_part_count": len(surface["parts"]),
        }
        for name, digest in members.items():
            source(original_root / name, _PREFIX + name, digest, 16 * 1024 * 1024)
    index = encoded_json(
        build_download_index(catalogue, expected_catalogue_manifest_sha256)
    )
    register("downloads/index.json", len(index), sha256(index).hexdigest())
    manifest = {
        "schema_version": ARCHIVE_SCHEMA,
        "catalogue_manifest_sha256": expected_catalogue_manifest_sha256,
        "files": files,
        "retained_sources": retained,
        "source_bytes": total,
        "scientific_admission": "not_asserted",
        "historical_snapshot_replaced": False,
    }
    if original_metadata is not None:
        manifest["original_metadata"] = original_metadata
    content = encoded_json(manifest)
    if len(content) > max_manifest_bytes or total + len(content) > max_bytes:
        raise ValueError("Source archive inputs exceed the finite manifest/byte budget")
    return ArchiveInputs(manifest, paths, index)
