"""Publish one portable source archive, shared by numerical readers and Atlas."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
    publish_new_output_tree,
)

from ..capture.receipts import _object, _read, _safe_root, _write_json
from ..capture.resources import NeotomaRetainedSource
from ..capture.resources.models import DEVELOPMENT_ROLES
from .custody import pinned_object, public_member
from .publication import load_neotoma_resource_catalogue
from .source_projection import _same

_SCHEMA = "neotoma-source-resource-archive.v1"
_MAX_TOTAL_BYTES = 512 * 1024 * 1024
_MAX_FILES = 20000


def _download_index(catalogue: dict[str, Any], anchor: str) -> dict[str, Any]:
    rows = []
    for resource in catalogue["resources"]:
        for version, selected in resource["versions"].items():
            row: dict[str, Any] = {
                "dataset_id": str(resource["dataset_id"]),
                "site_id": str(resource["site_id"]),
                "collection_unit_id": str(resource["collection_unit_id"]),
                "version": version,
                "exposure_role": resource["exposure_role"],
                "statuses": {
                    key: deepcopy(value)
                    for key, value in selected.items()
                    if key.endswith("_status")
                },
                "use_scope": "source_entity_download_only",
                "scientific_admission": "not_asserted",
            }
            rows.append(row)
            if resource["exposure_role"] not in DEVELOPMENT_ROLES:
                row["state"] = "blocked_exposure_role"
                continue
            source = selected.get("source")
            row["state"] = "unavailable_source_entity"
            if not isinstance(source, dict):
                continue
            row["source"] = deepcopy(source)
            if source.get("source_kind") == "retained_public_response":
                key = f"dataset-{resource['dataset_id']}-{version}"
                path = f"captures/retained/{key}/native.body"
            elif (
                source.get("source_kind") == "source_http_attempt"
                and source.get("http_status") == 200
                and source.get("body_complete") is True
            ):
                path = f"captures/{public_member(source['capture_manifest_sha256'])}/{public_member(source['body_file'])}"
            else:
                continue
            row.update(state="available_source_entity", download_path=path)
    return {
        "schema_version": "neotoma-source-download-index.v1",
        "catalogue_manifest_sha256": anchor,
        "resources": rows,
        "partitions": dict(sorted(Counter(row["state"] for row in rows).items())),
        "scientific_admission": "not_asserted",
        "attribution": "Exact source metadata and rights in the pinned catalogue; source epochs and native receipts remain separate",
    }


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
    staging.mkdir(exist_ok=False)
    files: dict[str, dict[str, Any]] = {}
    total = 0

    def copy(content: bytes, relative: str, digest: str) -> None:
        nonlocal total
        if sha256(content).hexdigest() != digest:
            raise ValueError("Source archive input identity differs")
        total += len(content)
        if total > _MAX_TOTAL_BYTES or len(files) >= _MAX_FILES:
            raise ValueError("Source archive exceeds its finite publication budget")
        target = staging / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(content)
        files[relative] = {"bytes": len(content), "sha256": digest}

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
        if selected.get("source", {}).get("source_kind") == "retained_public_response"
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
    index = _download_index(catalogue, expected_catalogue_manifest_sha256)
    content = (
        json.dumps(index, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode()
    copy(content, "downloads/index.json", sha256(content).hexdigest())
    manifest = {
        "schema_version": _SCHEMA,
        "catalogue_manifest_sha256": expected_catalogue_manifest_sha256,
        "files": files,
        "retained_sources": retained,
        "source_bytes": total,
        "scientific_admission": "not_asserted",
        "historical_snapshot_replaced": False,
    }
    digest = _write_json(staging / "manifest.json", manifest)
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


def load_neotoma_source_archive(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    original_relational_root: Path | None = None,
) -> dict[str, Any]:
    """Reconcile the complete portable publication and replay every source capsule."""
    root = _safe_root(directory)
    manifest = pinned_object(
        root / "manifest.json", expected_manifest_sha256, 16 * 1024 * 1024
    )
    if (
        manifest.get("schema_version") != _SCHEMA
        or manifest.get("scientific_admission") != "not_asserted"
        or manifest.get("historical_snapshot_replaced") is not False
        or not isinstance(manifest.get("files"), dict)
        or len(manifest["files"]) > _MAX_FILES
    ):
        raise ValueError("Unsupported Neotoma source archive identity")
    total = 0
    for relative, member in manifest["files"].items():
        if (
            not isinstance(relative, str)
            or not isinstance(member, dict)
            or set(member) != {"bytes", "sha256"}
            or type(member["bytes"]) is not int
            or member["bytes"] < 0
        ):
            raise ValueError("Neotoma source archive member identity is malformed")
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or "\\" in relative:
            raise ValueError("Neotoma source archive member escapes publication")
        body = _read(root / path, 32 * 1024 * 1024 + 1)
        total += len(body)
        if len(body) != member["bytes"] or sha256(body).hexdigest() != member["sha256"]:
            raise ValueError("Neotoma source archive member identity differs")
        if total > _MAX_TOTAL_BYTES:
            raise ValueError("Neotoma source archive exceeds its finite byte budget")
    if (
        type(manifest.get("source_bytes")) is not int
        or manifest["source_bytes"] != total
        or {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
        != {"manifest.json", *manifest["files"]}
        or any(p.is_symlink() for p in root.rglob("*"))
    ):
        raise ValueError("Neotoma source archive file population differs")
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
    for digest, descriptor in compact["capture_descriptors"].items():
        expected_files.update(
            f"captures/{digest}/{public_member(member['name'])}"
            for member in descriptor["files"]
        )
    expected_retained = {
        f"dataset-{resource['dataset_id']}-{version}"
        for resource in compact["resources"]
        for version, selected in resource["versions"].items()
        if selected.get("source", {}).get("source_kind") == "retained_public_response"
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
        index, _download_index(compact, manifest["catalogue_manifest_sha256"])
    ):
        raise ValueError("Neotoma source archive download partition differs")
    for row in index["resources"]:
        if "download_path" in row:
            member = manifest["files"].get(row["download_path"])
            if member is None or member["sha256"] != row["source"]["body_sha256"]:
                raise ValueError("Neotoma source archive download identity differs")
    return manifest
