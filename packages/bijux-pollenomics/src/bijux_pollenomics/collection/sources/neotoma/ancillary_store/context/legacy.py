"""Authenticate original roster identities for literal legacy facet captures."""

from __future__ import annotations

from typing import Any

from ...capture.parent_scope import _roster
from ...resource_catalogue.archive.files import _digest
from ...resource_catalogue.source_projection import _same
from .validation import NeotomaAncillaryContext


def _legacy_roots(control: dict[str, Any], context: NeotomaAncillaryContext) -> None:
    plan = control["plan"]
    digest = plan["roster_sha256"]
    if digest not in context.legacy_rosters:
        raise ValueError("Ancillary legacy capture lacks its original roster identity")
    roster = _roster(context.legacy_rosters[digest], digest)
    rows = {row["dataset_id"]: row for row in roster["resources"]}
    for resource in plan["resources"]:
        row = rows.get(resource["dataset_id"])
        if row is None:
            raise ValueError("Ancillary legacy dataset is absent from original roster")
        locator = row.get("metadata_locator")
        if (
            not isinstance(locator, dict)
            or not _digest(locator.get("response_sha256"))
            or not isinstance(locator.get("json_pointer"), str)
        ):
            raise ValueError("Ancillary legacy original source locator is malformed")
        expected = {
            key: row[key]
            for key in (
                "dataset_id",
                "site_id",
                "collection_unit_id",
                "dataset_type",
                "database",
            )
        }
        expected.update(
            exposure_role=row["exposure_roles"]["current"],
            metadata_sha256=locator["response_sha256"],
            metadata_pointer=locator["json_pointer"],
        )
        if not _same({key: resource.get(key) for key in expected}, expected):
            raise ValueError(
                "Ancillary legacy native owner/role/source locator differs"
            )
