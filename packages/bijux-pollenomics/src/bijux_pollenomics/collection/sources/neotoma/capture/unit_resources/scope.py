"""Authenticate whole native units and every known site/core exposure obligation."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
import re
from typing import Any

from ...client import positive_native_id
from .. import NeotomaMetadataLimits, replay_neotoma_metadata_capture
from ..receipts import _object, _read, _safe_root
from ..resources.models import (
    EXPOSURE_ROLES,
    NeotomaResourceLimits,
    NeotomaResourcePlan,
    NeotomaResourceSpec,
)
from ..resources.protocol import validate_plan as validate_resource_plan
from ..resources.replay import _same_json
from .models import NeotomaUnitResourcePlan
from .protocol import validate_selection

_POINTER = re.compile(r"/data/(0|[1-9][0-9]*)/site/datasets/(0|[1-9][0-9]*)\Z")
_RANK = {
    "development_resource_discovery": 0,
    "exposed_development": 1,
    "reserved_candidate_confirmation": 2,
    "heldout_no_numerical_access": 3,
}
_METADATA_LIMITS = NeotomaMetadataLimits(
    max_requests=256,
    max_pages_per_inventory=256,
    max_response_bytes=32 * 1024 * 1024,
    max_total_bytes=256 * 1024 * 1024,
)


def _pinned(path: Path, digest: str, bound: int) -> dict[str, Any]:
    content = _read(path, bound)
    if sha256(content).hexdigest() != digest:
        raise ValueError("Neotoma unit source identity differs")
    return _object(content)


def _roster(path: Path, digest: str) -> dict[str, Any]:
    roster = _pinned(path, digest, 16 * 1024 * 1024)
    rows = roster.get("resources")
    if (
        not isinstance(rows, list)
        or not rows
        or type(roster.get("resource_count")) is not int
        or roster["resource_count"] != len(rows)
        or not isinstance(roster.get("policy_sources"), list)
        or not roster["policy_sources"]
        or any(
            not isinstance(value, str) or not value.startswith("https://")
            for value in roster["policy_sources"]
        )
    ):
        raise ValueError("Neotoma unit roster population or policy differs")
    seen = set()
    parents: dict[int, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Neotoma unit roster row is malformed")
        ids = [
            positive_native_id(row.get(key))
            for key in ("dataset_id", "site_id", "collection_unit_id")
        ]
        if ids[0] in seen or (ids[2] in parents and parents[ids[2]] != ids[1]):
            raise ValueError("Neotoma unit roster identity or parent is ambiguous")
        seen.add(ids[0])
        parents[ids[2]] = ids[1]
        roles = row.get("exposure_roles")
        if (
            not isinstance(roles, dict)
            or set(roles) != {"current", "doi_frozen"}
            or any(
                not isinstance(role, str) or role not in EXPOSURE_ROLES
                for role in roles.values()
            )
        ):
            raise ValueError("Neotoma unit roster exposure roles are invalid")
        if (
            not isinstance(row.get("dataset_type"), str)
            or not row["dataset_type"].strip()
            or "database" not in row
            or row["database"] is not None
            and (not isinstance(row["database"], str) or not row["database"].strip())
        ):
            raise ValueError("Neotoma unit roster native type/database is invalid")
    return roster


def _metadata_sources(
    plan: NeotomaUnitResourcePlan, roots: Mapping[str, Path]
) -> dict[tuple[Any, ...], tuple[dict[str, Any], dict[str, Any]]]:
    bodies = {}
    for digest in sorted(plan.metadata_capture_manifest_sha256s):
        root = _safe_root(roots[digest])
        manifest = _pinned(root / "capture-manifest.json", digest, 16 * 1024 * 1024)
        control = _pinned(
            root / "request-plan.json", manifest["plan_sha256"], 4 * 1024 * 1024
        )
        if control.get("plan", {}).get("inventory_all_dataset_types") is not True:
            raise ValueError("Neotoma whole-unit scope requires an all-type inventory")
        replay_neotoma_metadata_capture(
            root, expected_manifest_sha256=digest, limits=_METADATA_LIMITS
        )
        for reference in manifest["records"]:
            receipt = _pinned(
                root / reference["receipt_file"],
                reference["receipt_sha256"],
                1024 * 1024,
            )
            if (
                receipt.get("role") != "dataset_inventory"
                or receipt.get("parameters", {}).get("limit") != "10000"
            ):
                continue
            content = _read(
                root / receipt["body_file"], _METADATA_LIMITS.max_response_bytes
            )
            body_digest = sha256(content).hexdigest()
            if body_digest != receipt["retained_body_sha256"]:
                raise ValueError("Neotoma unit actual metadata buffer differs")
            source = {
                "capture_manifest_sha256": digest,
                "receipt_file": reference["receipt_file"],
                "receipt_sha256": reference["receipt_sha256"],
                "body_file": receipt["body_file"],
                "body_sha256": body_digest,
            }
            key = tuple(
                source[field]
                for field in (
                    "capture_manifest_sha256",
                    "receipt_file",
                    "receipt_sha256",
                    "body_file",
                    "body_sha256",
                )
            )
            bodies[key] = (_object(content), source)
    return bodies


def prepare_unit_scopes(
    plan: NeotomaUnitResourcePlan,
    roster_path: Path,
    metadata_captures: Mapping[str, Path],
    limits: NeotomaResourceLimits,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Freeze whole current native units, plus historical and same-site role duties."""
    validate_selection(plan, metadata_captures)
    roster = _roster(roster_path, plan.roster_sha256)
    if not set(plan.metadata_capture_manifest_sha256s) <= set(
        roster.get("source_metadata_capture_manifest_sha256", [])
    ):
        raise ValueError("Neotoma unit metadata sources are outside the frozen roster")
    bodies = _metadata_sources(plan, metadata_captures)
    rows = roster["resources"]
    positions = {row["dataset_id"]: index for index, row in enumerate(rows)}
    result = []
    for unit_id in sorted(plan.collection_unit_ids):
        members = [row for row in rows if row["collection_unit_id"] == unit_id]
        if not members or not any(
            row["dataset_type"] == "speleothem" for row in members
        ):
            raise ValueError("Neotoma selected unit lacks a source speleothem dataset")
        site_id = members[0]["site_id"]
        obligations = [
            row
            for row in rows
            if row["site_id"] == site_id or row["collection_unit_id"] == unit_id
        ]
        role = max(
            (value for row in obligations for value in row["exposure_roles"].values()),
            key=lambda value: _RANK[value],
        )
        current = [
            row
            for row in members
            if row.get("metadata_locator", {}).get("source_kind")
            != "retained_relational_dataset_metadata_not_current_HTTP"
        ]
        native_site = None
        native_source = None
        specs = []
        for row in current:
            locator = row.get("metadata_locator", {})
            key = tuple(
                locator.get(field)
                for field in (
                    "capture_manifest_sha256",
                    "receipt_file",
                    "receipt_sha256",
                    "body_file",
                    "body_sha256",
                )
            )
            if key not in bodies or locator.get("response_sha256") != locator.get(
                "body_sha256"
            ):
                raise ValueError(
                    "Neotoma unit metadata receipt/body tuple is unverified"
                )
            match = _POINTER.fullmatch(locator.get("json_pointer", ""))
            if match is None:
                raise ValueError("Neotoma unit metadata parent pointer is unsupported")
            body, source = bodies[key]
            try:
                site = body["data"][int(match[1])]["site"]
                dataset = site["datasets"][int(match[2])]
            except (KeyError, IndexError, TypeError) as error:
                raise ValueError(
                    "Neotoma unit metadata pointer does not resolve"
                ) from error
            if (
                positive_native_id(site.get("siteid")) != site_id
                or positive_native_id(site.get("collectionunitid")) != unit_id
                or positive_native_id(dataset.get("datasetid")) != row["dataset_id"]
                or not _same_json(dataset.get("datasettype"), row["dataset_type"])
                or "database" not in dataset
                or not _same_json(dataset["database"], row["database"])
            ):
                raise ValueError(
                    "Neotoma native unit/dataset/site/type/database owner differs"
                )
            parent_source = {**source, "json_pointer": f"/data/{match[1]}/site"}
            if native_site is not None and (
                not _same_json(site, native_site)
                or not _same_json(parent_source, native_source)
            ):
                raise ValueError("Neotoma unit metadata parent source is ambiguous")
            native_site, native_source = site, parent_source
            specs.append(
                NeotomaResourceSpec(
                    row["dataset_id"],
                    site_id,
                    unit_id,
                    row["dataset_type"],
                    row["database"],
                    role,
                    source["body_sha256"],
                    locator["json_pointer"],
                    ("current",),
                )
            )
        if native_site is None or not isinstance(native_site.get("datasets"), list):
            raise ValueError("Neotoma whole-unit current source is unavailable")
        native_ids = []
        for dataset in native_site["datasets"]:
            if not isinstance(dataset, dict):
                raise ValueError("Neotoma unit native dataset population is malformed")
            native_ids.append(positive_native_id(dataset.get("datasetid")))
        if len(set(native_ids)) != len(native_ids) or set(native_ids) != {
            row["dataset_id"] for row in current
        }:
            raise ValueError(
                "Neotoma whole-unit native dataset scope differs from frozen current siblings"
            )
        validate_resource_plan(
            NeotomaResourcePlan(
                tuple(specs), plan.roster_sha256, tuple(roster["policy_sources"])
            ),
            limits,
        )
        result.append(
            {
                "unit_key": f"speleothem-unit-{unit_id}",
                "resource_kind": "speleothem",
                "collection_unit_id": unit_id,
                "site_id": site_id,
                "exposure_role": role,
                "roster_sha256": plan.roster_sha256,
                "native_dataset_ids": sorted(native_ids),
                "native_unit_metadata": native_site,
                "native_unit_source": native_source,
                "roster_obligations": [
                    {
                        "dataset_id": row["dataset_id"],
                        "site_id": row["site_id"],
                        "collection_unit_id": row["collection_unit_id"],
                        "dataset_type": row["dataset_type"],
                        "database": row["database"],
                        "exposure_roles": row["exposure_roles"],
                        "roster_row_pointer": f"/resources/{positions[row['dataset_id']]}",
                        "metadata_locator": row["metadata_locator"],
                    }
                    for row in sorted(obligations, key=lambda item: item["dataset_id"])
                ],
                "scientific_admission": "not_asserted",
            }
        )
    return result, roster["policy_sources"]
