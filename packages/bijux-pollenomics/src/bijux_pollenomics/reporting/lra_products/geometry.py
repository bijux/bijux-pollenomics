"""Hash-bound display anchors, distinct from numerical basin and ring geometry."""

from __future__ import annotations

import math
from typing import Any


def _keys(value: object, expected: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError("Display geometry fields differ from lra-display-geometry.v1")
    return value


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def validate_geometry(
    value: dict[str, Any],
    manifest: dict[str, Any],
    request: dict[str, Any],
    *,
    product_manifest_sha256: str,
) -> dict[tuple[str, str], dict[str, Any]]:
    """Validate declared identity/shape; source coordinate admission is unsupported.

    Missing/unresolved declared sites are accounted by the projection. Unknown or
    duplicate sites and inconsistent product identities are invalid inputs.
    """
    _keys(
        value,
        {
            "schema_version",
            "product_manifest_sha256",
            "request_sha256",
            "scientific_content_sha256",
            "data_kind",
            "crs",
            "coordinate_order",
            "sites",
        },
    )
    if (
        value["schema_version"] != "lra-display-geometry.v1"
        or value["product_manifest_sha256"] != product_manifest_sha256
        or value["request_sha256"] != manifest["request_sha256"]
        or value["scientific_content_sha256"] != manifest["scientific_content_sha256"]
        or value["data_kind"] != request["data_kind"]
        or value["crs"] != "OGC:CRS84"
        or value["coordinate_order"] != "longitude_latitude"
        or not isinstance(value["sites"], list)
    ):
        raise ValueError("Display geometry identity or CRS differs from the product")
    known = {
        (role, sample["site_id"])
        for role in ("regional", "local")
        if role in request
        for sample in request[role]["samples"]
    }
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for raw in value["sites"]:
        site = _keys(
            raw,
            {
                "role",
                "site_id",
                "disposition",
                "position",
                "basis",
                "source_locator",
            },
        )
        if not all(_text(site[key]) for key in ("role", "site_id", "source_locator")):
            raise ValueError("Display geometry requires exact role/site/locator text")
        key = (site["role"], site["site_id"])
        if key not in known or key in result:
            raise ValueError("Unknown or duplicate display site")
        if site["disposition"] not in ("declared_anchor", "unresolved"):
            raise ValueError("Unknown display geometry disposition")
        if site["basis"] not in ("synthetic_fixture", "source_reported", "unresolved"):
            raise ValueError("Unknown coordinate basis")
        if site["disposition"] == "unresolved":
            if site["position"] is not None or site["basis"] != "unresolved":
                raise ValueError(
                    "Unresolved display geometry cannot contain a position"
                )
        else:
            position = site["position"]
            if not isinstance(position, list) or len(position) != 2:
                raise ValueError("Display anchor must be one CRS84 coordinate pair")
            if any(
                isinstance(number, bool)
                or not isinstance(number, (int, float))
                or not math.isfinite(number)
                or not lower <= number <= upper
                for number, lower, upper in zip(
                    position, (-180, -90), (180, 90), strict=True
                )
            ):
                raise ValueError("Display anchor coordinates are invalid")
            if site["basis"] == "unresolved":
                raise ValueError(
                    "Declared anchor requires an explicit coordinate basis"
                )
        result[key] = dict(site)
    return result
