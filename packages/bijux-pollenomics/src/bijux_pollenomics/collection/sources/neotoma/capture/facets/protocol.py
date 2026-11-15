"""Exact current facet routes, plan validation and distinct version identities."""

from __future__ import annotations

from dataclasses import fields
from typing import Any

from ..models import _Request
from ..resources.models import (
    NeotomaResourceLimits,
    NeotomaResourcePlan,
    NeotomaResourceSpec,
)
from ..resources.protocol import identity
from ..resources.protocol import validate_plan as validate_resource_plan
from .models import DATASET_FACETS, NeotomaFacetPlan


def validate_plan(plan: NeotomaFacetPlan, limits: NeotomaResourceLimits) -> None:
    if (
        not isinstance(plan, NeotomaFacetPlan)
        or not isinstance(plan.resources, tuple)
        or any(not isinstance(root, NeotomaResourceSpec) for root in plan.resources)
        or not isinstance(plan.facets, tuple)
        or not plan.facets
        or any(facet not in DATASET_FACETS for facet in plan.facets)
        or len(set(plan.facets)) != len(plan.facets)
    ):
        raise ValueError("Neotoma dataset facet plan is malformed")
    validate_resource_plan(
        NeotomaResourcePlan(plan.resources, plan.roster_sha256), limits
    )


def facet_identity(resource: NeotomaResourceSpec, facet: str) -> dict[str, Any]:
    return {
        "facet_key": f"dataset-{resource.dataset_id}-facet-{facet}-current",
        "root_identity": identity(resource),
        "facet": facet,
        "content_version": "current",
        "api_version": "v2.0",
    }


def request_for(resource: NeotomaResourceSpec, facet: str, attempt: int) -> _Request:
    return _Request(
        f"{facet_identity(resource, facet)['facet_key']}-attempt-{attempt}",
        f"dataset_facet_{facet}",
        f"/datasets/{resource.dataset_id}/{facet}",
        {},
        resource.site_id,
        resource.dataset_id,
    )


def plan_from_json(
    control: dict[str, Any],
) -> tuple[NeotomaFacetPlan, NeotomaResourceLimits]:
    try:
        raw = control["plan"]
        if (
            not isinstance(raw, dict)
            or set(raw) != {"resources", "roster_sha256", "facets"}
            or not isinstance(raw["resources"], list)
            or not isinstance(raw["facets"], list)
            or not isinstance(control["limits"], dict)
            or set(control["limits"])
            != {field.name for field in fields(NeotomaResourceLimits)}
        ):
            raise ValueError("Neotoma facet control fields differ")
        resources = []
        for item in raw["resources"]:
            if (
                not isinstance(item, dict)
                or set(item) != {field.name for field in fields(NeotomaResourceSpec)}
                or not isinstance(item["versions"], list)
            ):
                raise ValueError("Neotoma facet root specification is malformed")
            resources.append(
                NeotomaResourceSpec(**{**item, "versions": tuple(item["versions"])})
            )
        plan = NeotomaFacetPlan(
            tuple(resources), raw["roster_sha256"], tuple(raw["facets"])
        )
        limits = NeotomaResourceLimits(**control["limits"])
        validate_plan(plan, limits)
        return plan, limits
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Neotoma facet control is malformed") from error
