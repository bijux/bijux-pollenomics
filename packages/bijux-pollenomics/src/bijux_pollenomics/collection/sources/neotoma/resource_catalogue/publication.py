"""Exclusive compact catalogue publication with portable native source readback."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
    publish_new_output_tree,
)

from ..capture import replay_neotoma_metadata_capture
from ..capture.receipts import _object, _read, _safe_root, _write_json
from ..capture.resources import NeotomaRetainedSource, replay_neotoma_resource_capture
from .coverage import verify_catalogue_source_projection
from .custody import (
    METADATA_REPLAY_LIMITS,
    describe_capture,
    pinned_object,
    public_member,
)
from .source_projection import (
    verify_derived_projection,
    verify_native_metadata_projection,
    verify_roster_projection,
)


def _validate(catalogue: dict[str, Any]) -> None:
    if catalogue.get("schema_version") != "neotoma-resource-catalogue.v1":
        raise ValueError("Unsupported native resource catalogue")
    rows = catalogue.get("resources")
    if not isinstance(rows, list) or len({row["dataset_id"] for row in rows}) != len(
        rows
    ):
        raise ValueError("Catalogue resource identity population differs")
    if any(set(row["versions"]) != {"current", "doi_frozen"} for row in rows):
        raise ValueError("Catalogue source version partition differs")
    if catalogue["summary"].get("resource_count") != len(rows) or catalogue[
        "summary"
    ].get("version_status_count") != 2 * len(rows):
        raise ValueError("Catalogue declared coverage population differs")
    verify_derived_projection(catalogue)
    for digest, descriptor in catalogue["capture_descriptors"].items():
        if (
            not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or descriptor.get("capture_manifest_sha256") != digest
        ):
            raise ValueError(
                "Catalogue descriptor identity is not a portable capture digest"
            )
        if (
            set(descriptor)
            != {
                "schema_version",
                "capture_manifest_sha256",
                "capture_kind",
                "native_schema_version",
                "files",
                "body_resolver",
                "source_bodies_in_descriptor",
            }
            or descriptor["schema_version"] != "neotoma-resource-source-descriptor.v1"
            or descriptor["source_bodies_in_descriptor"] is not False
            or descriptor["body_resolver"]
            != "explicit capture_sources mapping keyed by capture_manifest_sha256"
        ):
            raise ValueError(
                "Catalogue descriptor fields differ from its source contract"
            )
        names = set()
        for member in descriptor["files"]:
            if (
                set(member) != {"name", "bytes", "sha256", "source_entity"}
                or type(member["bytes"]) is not int
                or member["bytes"] < 0
                or not isinstance(member["sha256"], str)
                or re.fullmatch(r"[0-9a-f]{64}", member["sha256"]) is None
            ):
                raise ValueError("Catalogue descriptor member fields are invalid")
            name = public_member(member["name"])
            if (
                name in names
                or type(member["source_entity"]) is not bool
                or member["source_entity"] != name.endswith(".body")
            ):
                raise ValueError("Catalogue descriptor member identity is ambiguous")
            names.add(name)


def write_neotoma_resource_catalogue(
    directory: Path,
    *,
    catalogue: dict[str, Any],
    capture_sources: Mapping[str, Path],
    roster_path: Path,
    original_relational_root: Path | None = None,
    retained_sources: Mapping[str, NeotomaRetainedSource] | None = None,
) -> dict[str, Any]:
    """Publish a new compact tree; native full entities remain resolver inputs.

    Source plans, manifests and receipts are copied byte-for-byte. Descriptors
    pin every entity member so any archive/directory resolver can supply the
    exact original capture to the existing maintained replay API.
    """
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Neotoma resource catalogue already exists: {final}")
    _validate(catalogue)
    roster_bytes = _read(roster_path, 16 * 1024 * 1024)
    if sha256(roster_bytes).hexdigest() != catalogue["expected_roster_sha256"]:
        raise ValueError("Catalogue source inventory identity differs")
    verify_roster_projection(catalogue, _object(roster_bytes))
    staging = build_staging_output_dir(final)
    staging.mkdir(exist_ok=False)
    files = {"source-inventory.json": sha256(roster_bytes).hexdigest()}
    with (staging / "source-inventory.json").open("xb") as stream:
        stream.write(roster_bytes)
    files["catalogue.json"] = _write_json(staging / "catalogue.json", catalogue)
    for digest, descriptor in catalogue["capture_descriptors"].items():
        if digest not in capture_sources:
            raise ValueError(
                "Catalogue publication requires every source capture resolver"
            )
        root = _safe_root(capture_sources[digest])
        destination = staging / "captures" / digest
        destination.mkdir(parents=True, exist_ok=False)
        relative = f"captures/{digest}/descriptor.json"
        files[relative] = _write_json(staging / relative, descriptor)
        for member in descriptor["files"]:
            name = public_member(member["name"])
            if member["source_entity"]:
                continue
            content = _read(root / name, 16 * 1024 * 1024)
            if (
                len(content) != member["bytes"]
                or sha256(content).hexdigest() != member["sha256"]
            ):
                raise ValueError("Catalogue source metadata identity differs")
            relative = f"captures/{digest}/{name}"
            with (staging / relative).open("xb") as stream:
                stream.write(content)
            files[relative] = member["sha256"]
    manifest = {
        "schema_version": "neotoma-resource-catalogue-publication.v1",
        "status": "published_native_coverage",
        "catalogue_file": "catalogue.json",
        "source_inventory_file": "source-inventory.json",
        "country_validation_scope": "Authenticated committed boundary-derived projection; no independent country derivation without original bound geometry",
        "resource_count": len(catalogue["resources"]),
        "version_status_count": 2 * len(catalogue["resources"]),
        "expected_roster_sha256": catalogue["expected_roster_sha256"],
        "files": files,
        "source_bodies": "required explicit content-addressed capture_sources resolver; not reconstructed from current API",
        "historical_snapshot_replaced": False,
        "scientific_admission": "not_asserted",
    }
    manifest_digest = _write_json(staging / "manifest.json", manifest)
    load_neotoma_resource_catalogue(
        staging,
        expected_manifest_sha256=manifest_digest,
        original_relational_root=original_relational_root,
        capture_sources=capture_sources,
        retained_sources=retained_sources,
        require_source_bodies=True,
    )
    publish_new_output_tree(final_output_root=final, staging_output_root=staging)
    load_neotoma_resource_catalogue(
        final,
        expected_manifest_sha256=manifest_digest,
        original_relational_root=original_relational_root,
        capture_sources=capture_sources,
        retained_sources=retained_sources,
        require_source_bodies=True,
    )
    return manifest


def load_neotoma_resource_catalogue(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    original_relational_root: Path | None = None,
    capture_sources: Mapping[str, Path] | None = None,
    retained_sources: Mapping[str, NeotomaRetainedSource] | None = None,
    require_source_bodies: bool = False,
) -> dict[str, Any]:
    """Authenticate public metadata and optionally the complete external raw closure."""
    root = _safe_root(directory)
    manifest_bytes = _read(root / "manifest.json", 16 * 1024 * 1024)
    if sha256(manifest_bytes).hexdigest() != expected_manifest_sha256:
        raise ValueError("Catalogue publication manifest identity differs")
    manifest = _object(manifest_bytes)
    if (
        manifest.get("schema_version") != "neotoma-resource-catalogue-publication.v1"
        or manifest.get("historical_snapshot_replaced") is not False
    ):
        raise ValueError("Unsupported catalogue publication or source epoch")
    expected_files = {"manifest.json"}
    for relative, digest in manifest["files"].items():
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or "\\" in relative:
            raise ValueError("Catalogue public path escapes its owned tree")
        content = _read(root / relative, 16 * 1024 * 1024)
        if sha256(content).hexdigest() != digest:
            raise ValueError("Catalogue public file identity differs")
        expected_files.add(relative)
    if {
        str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()
    } != expected_files:
        raise ValueError("Catalogue public file population differs")
    catalogue = pinned_object(
        root / "catalogue.json", manifest["files"]["catalogue.json"], 16 * 1024 * 1024
    )
    _validate(catalogue)
    if (
        type(manifest.get("resource_count")) is not int
        or manifest["resource_count"] != len(catalogue["resources"])
        or type(manifest.get("version_status_count")) is not int
        or manifest["version_status_count"] != 2 * len(catalogue["resources"])
        or manifest.get("scientific_admission") != "not_asserted"
        or manifest.get("status") != "published_native_coverage"
        or manifest.get("expected_roster_sha256") != catalogue["expected_roster_sha256"]
    ):
        raise ValueError(
            "Catalogue publication account differs from resource projection"
        )
    roster = pinned_object(
        root / "source-inventory.json",
        catalogue["expected_roster_sha256"],
        16 * 1024 * 1024,
    )
    verify_roster_projection(catalogue, roster)
    if require_source_bodies:
        sources = capture_sources or {}
        for digest, descriptor in catalogue["capture_descriptors"].items():
            if digest not in sources:
                raise ValueError("Catalogue source body resolver is required")
            if descriptor["capture_kind"] == "metadata":
                replay_neotoma_metadata_capture(
                    sources[digest],
                    expected_manifest_sha256=digest,
                    limits=METADATA_REPLAY_LIMITS,
                )
            elif descriptor["capture_kind"] == "resources":
                replay_neotoma_resource_capture(
                    sources[digest],
                    expected_manifest_sha256=digest,
                    source_captures=sources,
                    retained_sources=retained_sources,
                )
            else:
                raise ValueError("Unsupported catalogue capture descriptor kind")
            expected = describe_capture(
                sources[digest], digest, descriptor["capture_kind"]
            )
            if json.dumps(expected, sort_keys=True, allow_nan=False) != json.dumps(
                descriptor, sort_keys=True, allow_nan=False
            ):
                raise ValueError(
                    "Catalogue descriptor differs from the retained source"
                )
        verify_native_metadata_projection(
            catalogue, root / "source-inventory.json", sources, original_relational_root
        )
        verify_catalogue_source_projection(catalogue, sources, retained_sources)
    return catalogue
