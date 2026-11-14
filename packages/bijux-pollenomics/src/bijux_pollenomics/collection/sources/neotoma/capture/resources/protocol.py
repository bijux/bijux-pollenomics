"""Finite resource request identities, exposure plans and version endpoints."""

from __future__ import annotations

from dataclasses import asdict
import math
import re
from typing import Any

from ...site_inventory.connected_resources import positive_native_id
from ..models import _Request
from .models import (
    EXPOSURE_ROLES,
    NeotomaResourceLimits,
    NeotomaResourcePlan,
    NeotomaResourceSpec,
)

_HASH = re.compile(r"[0-9a-f]{64}\Z")


def validate_plan(plan: NeotomaResourcePlan, limits: NeotomaResourceLimits) -> None:
    for field in (
        "max_requests",
        "max_attempts",
        "max_response_bytes",
        "max_total_bytes",
    ):
        positive_native_id(getattr(limits, field))
    for field in ("timeout_seconds", "wall_seconds", "retry_delay_seconds"):
        value = getattr(limits, field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
            or (field != "retry_delay_seconds" and value == 0)
        ):
            raise ValueError("Neotoma resource time limit is invalid")
    if (
        not isinstance(plan.roster_sha256, str)
        or not _HASH.fullmatch(plan.roster_sha256)
        or not plan.resources
    ):
        raise ValueError("Neotoma resource plan lacks a bound roster")
    if (
        not isinstance(plan.policy_sources, tuple)
        or not plan.policy_sources
        or any(
            not isinstance(url, str) or not url.startswith("https://")
            for url in plan.policy_sources
        )
    ):
        raise ValueError("Neotoma resource source policy references are invalid")
    seen = set()
    for resource in plan.resources:
        for value in (
            resource.dataset_id,
            resource.site_id,
            resource.collection_unit_id,
        ):
            positive_native_id(value)
        if resource.dataset_id in seen:
            raise ValueError("Duplicate Neotoma resource dataset")
        seen.add(resource.dataset_id)
        if (
            not isinstance(resource.dataset_type, str)
            or not resource.dataset_type.strip()
            or (
                resource.database is not None
                and (
                    not isinstance(resource.database, str)
                    or not resource.database.strip()
                )
            )
        ):
            raise ValueError("Neotoma resource source type/database is invalid")
        if (
            resource.exposure_role not in EXPOSURE_ROLES
            or not isinstance(resource.metadata_sha256, str)
            or not _HASH.fullmatch(resource.metadata_sha256)
            or not isinstance(resource.metadata_pointer, str)
            or not resource.metadata_pointer.startswith("/")
        ):
            raise ValueError("Neotoma resource role or metadata authority is invalid")
        if (
            not resource.versions
            or any(
                version not in {"current", "doi_frozen"}
                for version in resource.versions
            )
            or len(set(resource.versions)) != len(resource.versions)
        ):
            raise ValueError("Neotoma resource versions are invalid or duplicate")


def resource_key(resource: NeotomaResourceSpec, version: str) -> str:
    return f"dataset-{resource.dataset_id}-{version}"


def request_for(resource: NeotomaResourceSpec, version: str, attempt: int) -> _Request:
    endpoint = "downloads" if version == "current" else "frozen"
    return _Request(
        f"{resource_key(resource, version)}-attempt-{attempt}",
        f"native_{version}",
        f"/{endpoint}/{resource.dataset_id}",
        {},
        resource.site_id,
        resource.dataset_id,
    )


def identity(resource: NeotomaResourceSpec) -> dict[str, Any]:
    result = asdict(resource)
    result.pop("versions")
    return result


def plan_from_json(
    spec: dict[str, Any],
) -> tuple[NeotomaResourcePlan, NeotomaResourceLimits]:
    try:
        if (
            not isinstance(spec.get("input_captures"), list)
            or any(
                not isinstance(value, str) or not _HASH.fullmatch(value)
                for value in spec["input_captures"]
            )
            or len(spec["input_captures"]) != len(set(spec["input_captures"]))
            or type(spec.get("retry_failed")) is not bool
        ):
            raise ValueError("Malformed resource reuse controls")
        raw = spec["plan"]
        resources = []
        if (
            not isinstance(raw, dict)
            or set(raw) != {"resources", "roster_sha256", "policy_sources"}
            or not isinstance(raw["resources"], list)
        ):
            raise ValueError("Malformed resource plan")
        for item in raw["resources"]:
            if not isinstance(item, dict):
                raise ValueError("Malformed resource specification")
            resources.append(
                NeotomaResourceSpec(**{**item, "versions": tuple(item["versions"])})
            )
        result = NeotomaResourcePlan(
            tuple(resources), raw["roster_sha256"], tuple(raw["policy_sources"])
        )
        limits = NeotomaResourceLimits(**spec["limits"])
        validate_plan(result, limits)
        return result, limits
    except (TypeError, KeyError) as error:
        raise ValueError("Malformed Neotoma resource control") from error
