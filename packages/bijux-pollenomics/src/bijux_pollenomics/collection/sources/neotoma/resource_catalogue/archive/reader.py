"""Read one selected qualified or forensic entity using archive-owned resolvers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...client import positive_native_id
from ..reader import (
    read_neotoma_catalogue_resource,
    read_neotoma_catalogue_source_entity,
)
from .inventory import ArchiveInventory, read_archive_inventory


def _selection(dataset_id: int, version: str) -> int:
    dataset_id = positive_native_id(dataset_id)
    if not isinstance(version, str) or version not in {"current", "doi_frozen"}:
        raise ValueError("Selected Neotoma resource version is unsupported")
    return dataset_id


def _scope(inventory: ArchiveInventory, anchor: str) -> dict[str, Any]:
    return {
        "manifest_sha256": anchor,
        "catalogue_manifest_sha256": inventory.manifest["catalogue_manifest_sha256"],
        "integrity_scope": "archive_metadata_and_selected_source_entity",
        "unselected_source_bodies_verified": False,
    }


def read_neotoma_source_archive_resource(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    dataset_id: int,
    version: str,
    include_native_body: bool = False,
) -> dict[str, Any]:
    """Delegate typed source qualification after metadata-only archive binding.

    The maintained reader checks the selected role and original capture lineage
    before opening its numerical entity. Other source bodies remain unread;
    full archive verification is provided by load_neotoma_source_archive.
    """
    if type(include_native_body) is not bool:
        raise ValueError("include_native_body must be a literal boolean")
    dataset_id = _selection(dataset_id, version)
    inventory = read_archive_inventory(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    result = read_neotoma_catalogue_resource(
        inventory.root / "catalogue",
        expected_manifest_sha256=inventory.manifest["catalogue_manifest_sha256"],
        dataset_id=dataset_id,
        version=version,
        capture_sources=inventory.capture_sources,
        retained_sources=inventory.retained_sources,
        include_native_body=include_native_body,
    )
    result["archive"] = _scope(inventory, expected_manifest_sha256)
    return result


def read_neotoma_source_archive_entity(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    dataset_id: int,
    version: str,
) -> dict[str, Any]:
    """Return one complete source entity without scientific/schema admission."""
    dataset_id = _selection(dataset_id, version)
    inventory = read_archive_inventory(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    result = read_neotoma_catalogue_source_entity(
        inventory.root / "catalogue",
        expected_manifest_sha256=inventory.manifest["catalogue_manifest_sha256"],
        dataset_id=dataset_id,
        version=version,
        capture_sources=inventory.capture_sources,
        retained_sources=inventory.retained_sources,
        original_relational_root=inventory.original_relational_root,
    )
    result["archive"] = _scope(inventory, expected_manifest_sha256)
    return result
