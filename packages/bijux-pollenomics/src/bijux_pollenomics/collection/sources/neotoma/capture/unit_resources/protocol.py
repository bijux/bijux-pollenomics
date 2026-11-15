"""One exact collection-unit endpoint, separate from dataset download versions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields
from pathlib import Path
import re
from typing import Any

from ...client import positive_native_id
from ..models import _Request
from ..resources.models import NeotomaResourceLimits
from .models import NeotomaUnitResourcePlan

_HASH = re.compile(r"[0-9a-f]{64}\Z")


def validate_selection(
    plan: NeotomaUnitResourcePlan, metadata_captures: Mapping[str, Path]
) -> None:
    if (
        not isinstance(plan, NeotomaUnitResourcePlan)
        or not isinstance(plan.collection_unit_ids, tuple)
        or not plan.collection_unit_ids
        or not isinstance(plan.roster_sha256, str)
        or not _HASH.fullmatch(plan.roster_sha256)
        or not isinstance(plan.metadata_capture_manifest_sha256s, tuple)
        or not plan.metadata_capture_manifest_sha256s
        or any(
            not isinstance(digest, str) or not _HASH.fullmatch(digest)
            for digest in plan.metadata_capture_manifest_sha256s
        )
        or len(set(plan.metadata_capture_manifest_sha256s))
        != len(plan.metadata_capture_manifest_sha256s)
        or set(metadata_captures) != set(plan.metadata_capture_manifest_sha256s)
    ):
        raise ValueError("Neotoma unit source selection is malformed")
    for unit_id in plan.collection_unit_ids:
        positive_native_id(unit_id)
    if len(set(plan.collection_unit_ids)) != len(plan.collection_unit_ids):
        raise ValueError("Neotoma unit selection is duplicated")


def request_for(unit: dict[str, Any], attempt: int) -> _Request:
    return _Request(
        f"{unit['unit_key']}-current-attempt-{attempt}",
        "unit_resource_speleothem",
        f"/speleothems/{unit['collection_unit_id']}",
        {},
        unit["site_id"],
    )


def plan_from_json(
    control: dict[str, Any],
) -> tuple[NeotomaUnitResourcePlan, NeotomaResourceLimits]:
    try:
        raw = control["plan"]
        if (
            not isinstance(raw, dict)
            or set(raw)
            != {
                "collection_unit_ids",
                "roster_sha256",
                "metadata_capture_manifest_sha256s",
            }
            or not isinstance(raw["collection_unit_ids"], list)
            or not isinstance(raw["metadata_capture_manifest_sha256s"], list)
            or not isinstance(control["limits"], dict)
            or set(control["limits"])
            != {field.name for field in fields(NeotomaResourceLimits)}
        ):
            raise ValueError("Neotoma unit plan fields differ")
        return NeotomaUnitResourcePlan(
            tuple(raw["collection_unit_ids"]),
            raw["roster_sha256"],
            tuple(raw["metadata_capture_manifest_sha256s"]),
        ), NeotomaResourceLimits(**control["limits"])
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Neotoma unit plan is malformed") from error
