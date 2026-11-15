"""Authenticate one selected native resource for methods without loading a cohort."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

from ..capture.receipts import _object, _read, _safe_root, _validate_receipt
from ..capture.resources import NeotomaResourceSpec, NeotomaRetainedSource
from ..capture.resources.current.profiles import (
    CURRENT_SOURCE_TYPES,
    parse_neotoma_current_source,
    summarize_current_source,
)
from ..capture.resources.frozen import _summary as frozen_native_summary
from ..capture.resources.frozen import parse_neotoma_frozen_snapshot
from ..capture.resources.models import (
    DEVELOPMENT_ROLES,
    RESOURCE_SCHEMA,
    NeotomaResourceLimits,
)
from ..capture.resources.profiles import classify_body
from ..capture.resources.protocol import (
    identity,
    plan_from_json,
    request_for,
    resource_key,
)
from ..capture.resources.retained import read_retained_source
from ..client import positive_native_id
from .current_profiles import current_profiles_enabled
from .custody import pinned_object, public_member
from .publication import load_neotoma_resource_catalogue
from .source_projection import _same


def _capsule(
    root: Path,
    catalogue: dict[str, Any],
    resource: NeotomaResourceSpec,
    version: str,
    digest: str,
) -> tuple[dict[str, Any], dict[str, Any], NeotomaResourceLimits]:
    """Check only public source metadata for this resource and its owning plan."""
    descriptor = catalogue["capture_descriptors"].get(digest)
    if descriptor is None or descriptor["capture_kind"] != "resources":
        raise ValueError("Selected resource capture descriptor is unavailable")
    directory = root / "captures" / public_member(digest)
    manifest = pinned_object(
        directory / "capture-manifest.json", digest, 16 * 1024 * 1024
    )
    control = pinned_object(
        directory / "request-plan.json", manifest["plan_sha256"], 4 * 1024 * 1024
    )
    if (
        manifest.get("schema_version") != RESOURCE_SCHEMA
        or manifest.get("status") != "closed"
        or manifest.get("scientific_admission") != "not_asserted"
        or control.get("schema_version") != RESOURCE_SCHEMA
        or control.get("historical_snapshot_replaced") is not False
    ):
        raise ValueError("Selected resource source schema, epoch or admission differs")
    plan, limits = plan_from_json(control)
    specifications = [
        item for item in plan.resources if item.dataset_id == resource.dataset_id
    ]
    if (
        len(specifications) != 1
        or version not in specifications[0].versions
        or not _same(identity(specifications[0]), identity(resource))
    ):
        raise ValueError("Selected resource plan owner or exposure identity differs")
    key = resource_key(resource, version)
    entries = [
        entry for entry in manifest["resources"] if entry.get("resource_key") == key
    ]
    if (
        len(entries) != 1
        or type(entries[0].get("dataset_id")) is not int
        or entries[0]["dataset_id"] != resource.dataset_id
        or entries[0].get("version") != version
        or entries[0].get("scientific_admission") != "not_asserted"
        or not _same(entries[0].get("identity"), identity(resource))
    ):
        raise ValueError("Selected native entry owner, role or version differs")
    return entries[0], control, limits


def _origin(
    root: Path,
    catalogue: dict[str, Any],
    resource: NeotomaResourceSpec,
    version: str,
    digest: str,
    visited: frozenset[str] = frozenset(),
) -> tuple[str, dict[str, Any], NeotomaResourceLimits]:
    """Authenticate selected reuse/retry ancestry without opening other entities."""
    if digest in visited:
        raise ValueError("Cyclic selected resource ancestry")
    entry, control, limits = _capsule(root, catalogue, resource, version, digest)
    key = resource_key(resource, version)
    for field in ("reused_from", "predecessor_result"):
        if field not in entry:
            continue
        reference = entry[field]
        expected_keys = {"manifest_sha256", "resource_key"}
        if field == "predecessor_result":
            expected_keys.add("terminal_status")
        if (
            not isinstance(reference, dict)
            or set(reference) != expected_keys
            or reference["resource_key"] != key
            or reference["manifest_sha256"] not in control["input_captures"]
        ):
            raise ValueError("Selected resource ancestor reference differs")
        prior_digest = reference["manifest_sha256"]
        previous, _, _ = _capsule(root, catalogue, resource, version, prior_digest)
        if field == "reused_from":
            expected = deepcopy(previous)
            expected["attempts"] = []
            expected["reused_from"] = reference
            if not _same(entry, expected):
                raise ValueError("Selected reused entry differs from original source")
            return _origin(
                root, catalogue, resource, version, prior_digest, visited | {digest}
            )
        if (
            control["retry_failed"] is not True
            or reference["terminal_status"] != previous["terminal_status"]
        ):
            raise ValueError("Selected resource predecessor status differs")
        _origin(root, catalogue, resource, version, prior_digest, visited | {digest})
    return digest, entry, limits


def _selected_body(
    root: Path,
    catalogue: dict[str, Any],
    resource: NeotomaResourceSpec,
    version: str,
    digest: str,
    entry: dict[str, Any],
    limits: NeotomaResourceLimits,
    source: dict[str, Any],
    capture_sources: Mapping[str, Path],
    retained_sources: Mapping[str, NeotomaRetainedSource] | None,
) -> bytes:
    """Use the exact authenticated buffer passed to native decoding."""
    maximum = min(limits.max_response_bytes, 32 * 1024 * 1024)
    if "retained_source" in entry:
        key = resource_key(resource, version)
        retained = (retained_sources or {}).get(key)
        if retained is None:
            raise ValueError("Selected retained source resolver is required")
        reference, summary = read_retained_source(resource, version, retained, maximum)
        if (
            not _same(entry["retained_source"], reference)
            or not _same(entry["summary"], summary)
            or not _same(
                source,
                {
                    "source_kind": "retained_public_response",
                    "epoch_kind": "original_timed_public_response",
                    **reference,
                },
            )
        ):
            raise ValueError("Selected original retained provenance identity differs")
        body = _read(_safe_root(retained.body_path), maximum)
        if sha256(body).hexdigest() != reference["body_sha256"]:
            raise ValueError("Selected retained body identity differs")
        return body
    if not entry["attempts"]:
        raise ValueError("Selected resource has no retained native source entity")
    attempt = entry["attempts"][-1]
    if digest not in capture_sources:
        raise ValueError("Selected resource body resolver is required")
    receipt = pinned_object(
        root / "captures" / digest / public_member(attempt["receipt_file"]),
        attempt["receipt_sha256"],
        65536,
    )
    name = public_member(attempt["body_file"])
    members = [
        item
        for item in catalogue["capture_descriptors"][digest]["files"]
        if item["name"] == name and item["source_entity"]
    ]
    if len(members) != 1:
        raise ValueError("Selected resource body descriptor differs")
    body = _read(_safe_root(capture_sources[digest]) / name, maximum)
    if (
        len(body) != members[0]["bytes"]
        or sha256(body).hexdigest() != members[0]["sha256"]
    ):
        raise ValueError("Selected resource body identity differs")
    request = request_for(resource, version, len(entry["attempts"]))
    _validate_receipt(receipt, request, body, maximum)
    expected_source = {
        "capture_manifest_sha256": digest,
        "resource_key": entry["resource_key"],
        "epoch_kind": "provider_frozen_response"
        if version == "doi_frozen"
        else "timed_live_api_response",
        "source_kind": "source_http_attempt",
        "receipt_file": attempt["receipt_file"],
        "receipt_sha256": attempt["receipt_sha256"],
        "requested_url": receipt["requested_url"],
        "utc_start": receipt["utc_start"],
        "utc_end": receipt["utc_end"],
        "tls_mode": receipt["tls_mode"],
        "body_file": name,
        "body_sha256": receipt["retained_body_sha256"],
        "body_bytes": len(body),
        "http_status": receipt["http_status"],
        "body_complete": receipt["body_complete"],
    }
    if not _same(source, expected_source):
        raise ValueError("Selected resource source/receipt projection differs")
    return body


def read_neotoma_catalogue_resource(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    dataset_id: int,
    version: str,
    capture_sources: Mapping[str, Path],
    retained_sources: Mapping[str, NeotomaRetainedSource] | None = None,
    include_native_body: bool = False,
) -> dict[str, Any]:
    """Read one qualified development source in its native current or frozen shape.

    The trusted compact publication supplies the selected entry and original
    receipt/ancestor closure. Explicit content-addressed resolvers supply only
    the selected entity. This reader does not assert scientific admission or
    turn a historical DOI snapshot into a current download or original paper.
    Explicit native-body access returns that same authenticated byte buffer;
    the default result remains JSON compatible.
    """
    if type(include_native_body) is not bool:
        raise ValueError("include_native_body must be a literal boolean")
    dataset_id = positive_native_id(dataset_id)
    if not isinstance(version, str) or version not in {"current", "doi_frozen"}:
        raise ValueError("Selected Neotoma resource version is unsupported")
    catalogue = load_neotoma_resource_catalogue(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    rows = [row for row in catalogue["resources"] if row["dataset_id"] == dataset_id]
    if len(rows) != 1:
        raise ValueError("Selected dataset is outside the declared catalogue inventory")
    row = rows[0]
    if row["exposure_role"] not in DEVELOPMENT_ROLES:
        raise ValueError("Selected resource exposure role refuses numerical access")
    selected = row["versions"][version]
    derived_current = (
        version == "current"
        and current_profiles_enabled(catalogue)
        and row["dataset_type"] in CURRENT_SOURCE_TYPES
        and selected.get("current_source_qualification_status")
        == "parsed_current_source"
    )
    qualification = (
        "qualification_status"
        if version == "current"
        else "snapshot_qualification_status"
    )
    accepted = "parsed_native" if version == "current" else "parsed_frozen_snapshot"
    if not derived_current and selected.get(qualification) != accepted:
        raise ValueError(
            f"Selected source is not qualified: {selected.get(qualification, 'not_qualified')} "
            f"(acquisition: {selected['acquisition_status']})"
        )
    resource = NeotomaResourceSpec(
        dataset_id,
        row["site_id"],
        row["collection_unit_id"],
        row["dataset_type"],
        row["database"],
        row["exposure_role"],
        row["metadata"]["source"]["body_sha256"],
        row["metadata"]["source"]["json_pointer"],
    )
    key = resource_key(resource, version)
    root = _safe_root(directory)
    owners = []
    for digest in catalogue["selected_resource_capture_manifest_sha256"]:
        manifest = pinned_object(
            root / "captures" / digest / "capture-manifest.json",
            digest,
            16 * 1024 * 1024,
        )
        if any(entry.get("resource_key") == key for entry in manifest["resources"]):
            owners.append(digest)
    if len(owners) != 1:
        raise ValueError(
            "Selected resource native owner capture is missing or ambiguous"
        )
    original_entry, _, _ = _capsule(root, catalogue, resource, version, owners[0])
    if (
        selected.get("source_terminal_status") != original_entry["terminal_status"]
        or selected.get("acquisition_status") != original_entry["terminal_status"]
        or (
            version == "current"
            and original_entry["terminal_status"]
            not in (
                {"unsupported_dataset_type"}
                if derived_current
                else {"parsed_native", "reused_qualified_native"}
            )
        )
    ):
        raise ValueError("Selected source terminal qualification is not qualified")
    digest, entry, limits = _origin(root, catalogue, resource, version, owners[0])
    body = _selected_body(
        root,
        catalogue,
        resource,
        version,
        digest,
        entry,
        limits,
        selected["source"],
        capture_sources,
        retained_sources,
    )
    result = {
        "dataset_id": dataset_id,
        "site_id": resource.site_id,
        "collection_unit_id": resource.collection_unit_id,
        "dataset_type": resource.dataset_type,
        "database": resource.database,
        "exposure_role": resource.exposure_role,
        "version": version,
        "source": selected["source"],
        "epoch_kind": selected["source"]["epoch_kind"],
        "scientific_admission": "not_asserted",
        "units_interpreted": False,
    }
    if derived_current:
        parsed_current = parse_neotoma_current_source(
            resource, body, expected_body_sha256=selected["source"]["body_sha256"]
        )
        summary = summarize_current_source(parsed_current)
        if not _same(summary, selected["current_source_summary"]):
            raise ValueError(
                "Current source summary differs from authenticated native buffer"
            )
        result.update(
            native_payload=parsed_current.payload,
            parser_profile=parsed_current.parser_profile,
            source_units=summary["source_units"],
            qualification_status="parsed_current_source",
            source_terminal_status=original_entry["terminal_status"],
        )
    elif version == "current":
        status, summary = classify_body(resource, version, body)
        if status != "parsed_native":
            raise ValueError("Selected current native owner/schema is not qualified")
        result.update(
            native_payload=_object(body),
            parser_profile=summary["parser_profile"],
            source_units=summary["source_units"],
            qualification_status=status,
        )
    else:
        snapshot = parse_neotoma_frozen_snapshot(
            resource, body, expected_body_sha256=selected["source"]["body_sha256"]
        )
        result.update(
            native_payload=snapshot.native.payload,
            parser_profile=snapshot.native.parser_profile,
            source_units=frozen_native_summary(snapshot.native)["source_units"],
            qualification_status="parsed_frozen_snapshot",
            strict_current_binding_status=snapshot.strict_current_binding_status,
            snapshot_database_metadata=snapshot.database_metadata,
        )
    if include_native_body:
        result["native_body"] = body
    return result
