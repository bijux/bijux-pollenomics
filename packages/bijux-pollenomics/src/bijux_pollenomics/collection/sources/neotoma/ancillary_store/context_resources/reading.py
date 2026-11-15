"""Selected same-buffer context profiles; source candidates never establish basins."""

from __future__ import annotations

from hashlib import sha256
import math
from pathlib import Path
from typing import Any

from ...capture.context_resources.models import DEFAULT_CONTEXT_LIMITS, RESOURCE_KINDS
from ...capture.context_resources.protocol import assess_http, request_for
from ...capture.receipts import _object
from ...capture.resources.models import NeotomaResourceLimits
from ...capture.resources.replay import _same_json
from ...client import positive_native_id
from .metadata import (
    NeotomaContextResourceInventory,
    pinned,
    read_neotoma_context_resource_inventory,
)
from .scope import NeotomaContextArchiveBindings


def response_bound(
    inventory: NeotomaContextResourceInventory,
    selected: dict[str, Any],
    limits: NeotomaResourceLimits,
) -> int:
    effective: dict[str, int] = {
        key: min(
            getattr(inventory.source.limits, key),
            getattr(limits, key),
            getattr(DEFAULT_CONTEXT_LIMITS, key),
        )
        for key in (
            "max_requests",
            "max_attempts",
            "max_response_bytes",
            "max_total_bytes",
        )
    }
    count = total = 0
    for entry in inventory.source.document["resources"]:
        for ordinal, reference in enumerate(entry["attempts"], 1):
            count += 1
            if (
                count > effective["max_requests"]
                or ordinal > effective["max_attempts"]
                or total >= effective["max_total_bytes"]
            ):
                raise ValueError("Selected context attempt exceeds capture budget")
            bound = min(
                effective["max_response_bytes"], effective["max_total_bytes"] - total
            )
            record = inventory.source.receipts[reference["request_name"]]
            size = record.get("retained_body_bytes", 0)
            if size > bound + int(not record["body_complete"]):
                raise ValueError(
                    "Selected context entity exceeds remaining byte budget"
                )
            if entry is selected:
                return bound
            total += size
    raise ValueError("Selected context source attempt is absent")


def guard_all_bodies(
    inventory: NeotomaContextResourceInventory, limits: NeotomaResourceLimits
) -> None:
    for entry in inventory.source.document["resources"]:
        if entry["attempts"]:
            inventory.scopes.guard(entry["site_id"])
            response_bound(inventory, entry, limits)


def qualify_profile(
    inventory: NeotomaContextResourceInventory, entry: dict[str, Any], body: bytes
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Qualify literal observed fields, with explicit endpoint/physical limitations."""
    native = _object(body)
    if native.get("status") != "success" or not isinstance(native.get("data"), list):
        raise ValueError("Context native success envelope or source rows differ")
    rows = native["data"]
    kind = entry["resource_kind"]
    expected_fields = (
        {"status", "data"}
        if kind == "depositional_environment"
        else {"status", "data", "message"}
    )
    if (
        set(native) != expected_fields
        or kind == "lake_candidates"
        and not isinstance(native["message"], str)
    ):
        raise ValueError("Context observed native envelope fields differ")
    profile: dict[str, Any] = {
        "scientific_admission": "not_asserted",
        "dated_basin_geometry_admitted": False,
        "absence_certified": False,
        "source_payload_preserved": True,
        "related_resource_graph_complete": False,
    }
    if kind == "depositional_environment":
        parent = next(
            row
            for row in inventory.scopes.original["requested_sites"]
            if row["site_id"] == entry["site_id"]
        )
        owners = {
            (entry["site_id"], unit["collection_unit_id"], row["datasetid"])
            for unit in parent["current_native_units"]
            for row in unit["datasets"]
        }
        observed = set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != {
                "siteid",
                "collectionunitid",
                "datasetid",
                "depenvt",
            }:
                raise ValueError("Context native environment row fields differ")
            owner = tuple(
                positive_native_id(row[key])
                for key in ("siteid", "collectionunitid", "datasetid")
            )
            if owner not in owners:
                raise ValueError(
                    "Context source has foreign native parent environment rows"
                )
            if (
                owner in observed
                or row["depenvt"] is not None
                and not isinstance(row["depenvt"], str)
            ):
                raise ValueError("Context native environment owner/value is ambiguous")
            observed.add(owner)
        profile.update(
            qualification_status="qualified_native_environment_rows",
            native_payload_owner_verified=bool(rows),
            native_row_count=len(rows),
            complete_environment_coverage_established=False,
            environment_inferred_from_prose_or_collection_type=False,
        )
    else:
        fields = {
            "hydrolakeid",
            "lakename",
            "laketype",
            "lakearea",
            "shorelen",
            "volume",
            "avgdepth",
            "watershedarea",
            "wkt_shape",
            "distance",
        }
        identities = set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != fields:
                raise ValueError("Context observed modern lake candidate fields differ")
            identity = positive_native_id(row["hydrolakeid"])
            if (
                identity in identities
                or type(row["laketype"]) is not int
                or not isinstance(row["lakename"], str)
                or not isinstance(row["wkt_shape"], str)
            ):
                raise ValueError("Context modern lake identity or native tokens differ")
            identities.add(identity)
            for field in (
                "lakearea",
                "shorelen",
                "volume",
                "avgdepth",
                "watershedarea",
                "distance",
            ):
                if type(row[field]) not in (int, float) or (
                    type(row[field]) is float and not math.isfinite(row[field])
                ):
                    raise ValueError("Context modern lake source number is invalid")
            if row["distance"] < 0:
                raise ValueError(
                    "Context modern lake distance contradicts the geography-distance contract"
                )
        profile.update(
            qualification_status="qualified_modern_lake_candidates"
            if rows
            else "qualified_empty_lake_candidate_query",
            candidate_count=len(rows),
            native_payload_site_owner_verified=False,
            endpoint_owner_basis="authenticated_site_request_only",
            core_basin_match="not_established",
            distance_reference_unit="m",
            distance_unit_basis="published_api_SQL_geography_distance_contract",
            distance_SQL_source="https://raw.githubusercontent.com/NeotomaDB/api_nodetest/49c76b4c77c73025a8c0017f7b7842437161f6c1/v2.0/helpers/lakes/hydrolake_query.sql",
            distance_SQL_sha256="22c90dd16ac9f0c97d962cfcb0ca9b3eb1a744498f90c926a470c266f3a8319a",
            distance_unit_definition="https://postgis.net/docs/ST_Distance.html",
            deployed_mapping_equivalence="not_established",
            laketype_codebook_interpretation="not_asserted",
            native_unit_field_present=False,
            geometry_parsed_or_matched=False,
            physical_measurement_validated=False,
            source_quantity_float_coercion=False,
            contemporaneity="not_established",
        )
    return native, profile


def read_entry(
    inventory: NeotomaContextResourceInventory,
    entry: dict[str, Any],
    limits: NeotomaResourceLimits,
) -> dict[str, Any]:
    inventory.scopes.guard(entry["site_id"])
    if not entry["attempts"] or "body_file" not in entry["attempts"][0]:
        raise ValueError("Selected context source has no retained HTTP entity")
    reference = entry["attempts"][0]
    record = inventory.source.receipts[reference["request_name"]]
    bound = response_bound(inventory, entry, limits)
    relative = "capture/" + reference["body_file"]
    body = pinned(
        inventory.root / relative,
        inventory.manifest["files"][relative],
        bound + int(not record["body_complete"]),
    )
    assessed = assess_http(
        record, request_for(entry["resource_kind"], entry["site_id"]), body, bound
    )
    if not _same_json({key: entry.get(key) for key in assessed}, assessed):
        raise ValueError("Selected context source buffer assessment differs")
    return {
        "site_id": entry["site_id"],
        "resource_kind": entry["resource_kind"],
        "body": body,
        "body_sha256": sha256(body).hexdigest(),
        "receipt_sha256": reference["receipt_sha256"],
        "capture_manifest_sha256": inventory.manifest["capture_manifest_sha256"],
        "terminal_status": entry["terminal_status"],
        "http_status": record["http_status"],
        "body_complete": record["body_complete"],
        "current_scope": inventory.scopes.account(entry["site_id"]),
        "integrity_scope": "archive_metadata_original_and_current_scope_and_selected_context_entity",
        "unselected_source_bodies_verified": False,
        "source_capture_history_replayed": False,
        "related_resource_graph_complete": False,
        "scientific_admission": "not_asserted",
    }


def _selected(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    site_id: int,
    resource_kind: str,
    original: NeotomaContextArchiveBindings,
    current: NeotomaContextArchiveBindings,
    limits: NeotomaResourceLimits,
    typed: bool = False,
) -> tuple[NeotomaContextResourceInventory, dict[str, Any], dict[str, Any]]:
    positive_native_id(site_id)
    if not isinstance(resource_kind, str) or resource_kind not in RESOURCE_KINDS:
        raise ValueError("Selected context kind is unsupported")
    inventory = read_neotoma_context_resource_inventory(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        original=original,
        current=current,
        limits=limits,
    )
    selected = [
        row
        for row in inventory.source.document["resources"]
        if row["site_id"] == site_id and row["resource_kind"] == resource_kind
    ]
    if len(selected) != 1:
        raise ValueError("Selected context identity is absent or ambiguous")
    if (
        typed
        and selected[0]["terminal_status"]
        != "received_complete_unqualified_context_resource"
    ):
        raise ValueError("Typed context requires a complete successful source entity")
    return inventory, selected[0], read_entry(inventory, selected[0], limits)


def read_neotoma_context_resource_entity(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    site_id: int,
    resource_kind: str,
    original: NeotomaContextArchiveBindings,
    current: NeotomaContextArchiveBindings,
    limits: NeotomaResourceLimits = DEFAULT_CONTEXT_LIMITS,
) -> dict[str, Any]:
    """Return original forensic bytes, including foreign-owner or unavailable responses."""
    return _selected(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        site_id=site_id,
        resource_kind=resource_kind,
        original=original,
        current=current,
        limits=limits,
    )[2]


def read_neotoma_context_resource(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    site_id: int,
    resource_kind: str,
    original: NeotomaContextArchiveBindings,
    current: NeotomaContextArchiveBindings,
    limits: NeotomaResourceLimits = DEFAULT_CONTEXT_LIMITS,
) -> dict[str, Any]:
    """Read a source-native profile with no basin, temporal or scientific admission."""
    inventory, entry, result = _selected(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        site_id=site_id,
        resource_kind=resource_kind,
        original=original,
        current=current,
        limits=limits,
        typed=True,
    )
    if entry["terminal_status"] != "received_complete_unqualified_context_resource":
        raise ValueError("Typed context requires a complete successful source entity")
    native, profile = qualify_profile(inventory, entry, result["body"])
    return {**result, "source_payload": native, "profile": profile}
