"""Authenticate selected attribution against its complete native metadata witness."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

from ..capture.receipts import _object, _read, _safe_root
from ..client import positive_native_id
from .custody import _pointer, _receipt_source, pinned_object, public_member
from .source_projection import _same, verify_native_metadata_projection


def validate_metadata_witness(
    root: Path,
    catalogue: dict[str, Any],
    row: dict[str, Any],
    capture_sources: Mapping[str, Path],
    original_relational_root: Path | None,
) -> None:
    """Read public metadata, never other resources' numerical bodies.

    Historical-only attribution requires its original relational source, not
    a substitute current response. Contemporary metadata uses its selected
    receipt, exact entity bytes and JSON pointer, including every native field.
    """
    metadata = row["metadata"]
    source = metadata["source"]
    if source.get("source_kind") == "original_relational_metadata":
        if original_relational_root is None:
            raise ValueError("Original metadata witness resolver is required")
        verify_native_metadata_projection(
            catalogue,
            root / "source-inventory.json",
            capture_sources,
            original_relational_root,
        )
        return
    if source.get("source_kind") != "current_http_metadata":
        raise ValueError("Selected metadata witness source kind is unsupported")
    digest = source["capture_manifest_sha256"]
    descriptor = catalogue["capture_descriptors"].get(digest)
    if not isinstance(descriptor, dict) or descriptor.get("capture_kind") != "metadata":
        raise ValueError("Selected metadata witness descriptor is unavailable")
    capsule = root / "captures" / public_member(digest)
    manifest = pinned_object(capsule / "capture-manifest.json", digest, 1024 * 1024)
    matches = [
        record
        for record in manifest["records"]
        if record["receipt_file"] == source["receipt_file"]
        and record["receipt_sha256"] == source["receipt_sha256"]
    ]
    if len(matches) != 1:
        raise ValueError("Selected metadata witness receipt is missing or ambiguous")
    reference = matches[0]
    receipt = pinned_object(
        capsule / public_member(reference["receipt_file"]),
        reference["receipt_sha256"],
        65536,
    )
    expected_source = {
        **_receipt_source(digest, reference, receipt),
        "source_kind": "current_http_metadata",
        "json_pointer": source["json_pointer"],
    }
    if (
        not _same(source, expected_source)
        or receipt.get("http_status") != 200
        or receipt.get("body_complete") is not True
    ):
        raise ValueError("Selected metadata witness source differs from receipt")
    name = public_member(receipt["body_file"])
    members = [member for member in descriptor["files"] if member["name"] == name]
    if len(members) != 1 or members[0]["source_entity"] is not True:
        raise ValueError("Selected metadata witness body descriptor differs")
    if digest not in capture_sources:
        raise ValueError("Selected metadata witness resolver is required")
    body = _read(_safe_root(capture_sources[digest]) / name, 32 * 1024 * 1024)
    if (
        len(body) != members[0]["bytes"]
        or sha256(body).hexdigest() != members[0]["sha256"]
        or members[0]["sha256"] != receipt["retained_body_sha256"]
        or receipt.get("retained_body_bytes") != len(body)
    ):
        raise ValueError("Selected metadata witness body identity differs")
    payload = _object(body)
    native = _pointer(payload, source["json_pointer"])
    if (
        not isinstance(native, dict)
        or positive_native_id(native.get("datasetid")) != row["dataset_id"]
        or native.get("datasettype") != row["dataset_type"]
        or "database" not in native
        or not _same(native["database"], row["database"])
        or not _same(native.get("doi", []), row["rights"]["dataset_doi_values"])
    ):
        raise ValueError("Selected metadata witness native dataset owner differs")
    site = _pointer(payload, "/".join(source["json_pointer"].split("/")[:-2]))
    if (
        not isinstance(site, dict)
        or positive_native_id(site.get("siteid")) != row["site_id"]
        or positive_native_id(site.get("collectionunitid")) != row["collection_unit_id"]
        or not _same(native, metadata["native_dataset"])
        or not _same(
            {key: value for key, value in site.items() if key != "datasets"},
            metadata["native_site"],
        )
    ):
        raise ValueError("Selected native metadata differs from authenticated witness")
