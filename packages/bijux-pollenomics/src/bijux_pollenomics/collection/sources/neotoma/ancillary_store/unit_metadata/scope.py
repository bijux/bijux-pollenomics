"""Original whole-unit identity and fresh current site/geography obligations."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from ...capture.facets.models import NeotomaFacetPlan
from ...capture.facets.scope import prepare_facet_parent_scope
from ...capture.parent_scope import _roster
from ...capture.receipts import _object, _read, _safe_root
from ...capture.resources.models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    NeotomaResourceLimits,
    NeotomaResourcePlan,
    NeotomaResourceSpec,
)
from ...capture.resources.protocol import validate_plan
from ...capture.unit_resources.models import NeotomaUnitResourcePlan
from ...capture.unit_resources.scope import prepare_unit_scopes
from ...resource_catalogue.archive.files import encoded_json
from ...resource_catalogue.source_projection import _same
from ..context import load_neotoma_ancillary_context

_RANK = {
    "development_resource_discovery": 0,
    "exposed_development": 1,
    "reserved_candidate_confirmation": 2,
    "heldout_no_numerical_access": 3,
}


def _resource(row: dict[str, Any]) -> NeotomaResourceSpec:
    return NeotomaResourceSpec(
        row["dataset_id"],
        row["site_id"],
        row["collection_unit_id"],
        row["dataset_type"],
        row["database"],
        row["exposure_roles"]["current"],
        row["metadata_locator"]["response_sha256"],
        row["metadata_locator"]["json_pointer"],
        ("current",),
    )


def _owners(unit: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        (
            {key: row[key] for key in ("datasetid", "datasettype", "database")}
            for row in unit["native_unit_metadata"]["datasets"]
        ),
        key=lambda row: row["datasetid"],
    )


@dataclass(frozen=True)
class UnitScopes:
    original: dict[int, dict[str, Any]]
    current: dict[int, dict[str, Any]]
    current_roles: dict[int, str]
    current_roster_sha256: str
    current_basis_sha256: str
    original_metadata: dict[str, Path]

    def account(self, unit_id: int) -> dict[str, Any]:
        original, current = self.original[unit_id], self.current[unit_id]
        same = (
            original["collection_unit_id"] == current["collection_unit_id"]
            and original["site_id"] == current["site_id"]
            and original["native_dataset_ids"] == current["native_dataset_ids"]
            and _same(_owners(original), _owners(current))
        )
        role = self.current_roles[unit_id]
        return {
            "collection_unit_id": unit_id,
            "site_id": original["site_id"],
            "original_native_dataset_ids": original["native_dataset_ids"],
            "current_native_dataset_ids": current["native_dataset_ids"],
            "original_role": original["exposure_role"],
            "current_role": role,
            "current_owner_matches_original": same,
            "current_access": "blocked_owner_change"
            if not same
            else "blocked_current_scope"
            if role not in DEVELOPMENT_ROLES
            else "requires_selected_source_guard",
            "current_scope_verification": "authenticated_native_whole_unit_site_and_facet_parent_obligations",
            "scientific_admission": "not_asserted",
        }

    def guard(self, unit_id: int) -> None:
        row = self.account(unit_id)
        if (
            self.original[unit_id]["exposure_role"] not in DEVELOPMENT_ROLES
            or row["current_access"] != "requires_selected_source_guard"
        ):
            raise ValueError(
                "Unit original/current owner or protected scope forbids body access"
            )


def prepare_scopes(
    plan: NeotomaUnitResourcePlan,
    control: dict[str, Any],
    original_roster: Path,
    recorded: NeotomaResourceLimits,
    *,
    context_directory: Path,
    expected_context_sha256: str,
    native_archive_directory: Path,
    expected_native_archive_sha256: str,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> UnitScopes:
    if not isinstance(limits, NeotomaResourceLimits):
        raise ValueError("Unit capture limits have an invalid type")
    context = load_neotoma_ancillary_context(
        context_directory,
        expected_manifest_sha256=expected_context_sha256,
        native_archive_directory=native_archive_directory,
    )
    if (
        context.manifest["native_archive"]["manifest_sha256"]
        != expected_native_archive_sha256
    ):
        raise ValueError("Unit archive independently expected native anchor differs")
    native = _safe_root(native_archive_directory)
    archive = _object(_read(native / "manifest.json", 16 * 1024 * 1024))
    original_inputs = {}
    for digest in plan.metadata_capture_manifest_sha256s:
        relative = f"captures/{digest}/capture-manifest.json"
        if archive["files"].get(relative, {}).get("sha256") != digest:
            raise ValueError(
                "Original unit metadata resolver is absent from native archive"
            )
        original_inputs[digest] = native / "captures" / digest
    original, policies = prepare_unit_scopes(
        plan, original_roster, original_inputs, recorded
    )
    if not _same(control["units"], original) or not _same(
        control["policy_sources"], policies
    ):
        raise ValueError("Original unit roster/native scope or policy proof differs")
    roster = _roster(original_roster, plan.roster_sha256)
    validate_plan(
        NeotomaResourcePlan(
            tuple(_resource(row) for row in roster["resources"]),
            plan.roster_sha256,
            tuple(policies),
        ),
        limits,
    )
    current_pin, inputs = next(iter(context.current_scope_inputs.items()))
    current_roster = _roster(inputs.roster_path, current_pin)
    all_type = {}
    for digest, directory in inputs.metadata_captures.items():
        manifest = _object(_read(directory / "capture-manifest.json", 16 * 1024 * 1024))
        raw = _read(directory / "request-plan.json", 4 * 1024 * 1024)
        if sha256(raw).hexdigest() != manifest["plan_sha256"]:
            raise ValueError("Current unit metadata source plan differs")
        if _object(raw).get("plan", {}).get("inventory_all_dataset_types") is True:
            all_type[digest] = directory
    current, _ = prepare_unit_scopes(
        NeotomaUnitResourcePlan(
            plan.collection_unit_ids, current_pin, tuple(sorted(all_type))
        ),
        inputs.roster_path,
        all_type,
        DEFAULT_RESOURCE_LIMITS,
    )
    native_ids = {
        identity for unit in current for identity in unit["native_dataset_ids"]
    }
    facets = prepare_facet_parent_scope(
        NeotomaFacetPlan(
            tuple(
                _resource(row)
                for row in current_roster["resources"]
                if row["dataset_id"] in native_ids
            ),
            current_pin,
            ("taxa",),
        ),
        inputs,
    )
    parent_roles = {
        row["dataset_id"]: row["effective_scope_role"] for row in facets["parents"]
    }
    roles = {
        unit["collection_unit_id"]: max(
            (
                unit["exposure_role"],
                *(parent_roles[identity] for identity in unit["native_dataset_ids"]),
            ),
            key=lambda role: _RANK[role],
        )
        for unit in current
    }
    return UnitScopes(
        {row["collection_unit_id"]: row for row in original},
        {row["collection_unit_id"]: row for row in current},
        roles,
        current_pin,
        sha256(
            encoded_json({"units": current, "facet_parent_obligations": facets})
        ).hexdigest(),
        original_inputs,
    )
