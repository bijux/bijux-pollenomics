"""Geometry declarations cannot imply source geography, extra sites or footprints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.lra_products.geometry import validate_geometry

from .support import geometry_fixture, product_fixture, sha


@pytest.mark.parametrize(
    "case",
    [
        "identity",
        "site",
        "duplicate",
        "crs",
        "order",
        "extra",
        "null",
        "bool",
        "nonfinite",
        "range",
        "unresolved_position",
    ],
)
def test_invalid_anchor_declarations_refuse(tmp_path: Path, case: str) -> None:
    product, request = product_fixture(tmp_path)
    geometry = geometry_fixture(product, request)
    site: dict[str, Any] = geometry["sites"][0]
    if case == "identity":
        geometry["product_manifest_sha256"] = "0" * 64
    elif case == "site":
        site["site_id"] = "unknown-site"
    elif case == "duplicate":
        geometry["sites"].append(dict(site))
    elif case == "crs":
        geometry["crs"] = "EPSG:3857"
    elif case == "order":
        geometry["coordinate_order"] = "latitude_longitude"
    elif case == "extra":
        site["polygon"] = [[0, 0], [1, 1]]
    elif case == "unresolved_position":
        site["disposition"] = "unresolved"
    else:
        site["position"] = [
            {"null": None, "bool": True, "nonfinite": float("nan"), "range": 181}[case],
            0,
        ]
    with pytest.raises(ValueError):
        validate_geometry(
            geometry,
            json.loads((product / "manifest.json").read_bytes()),
            request,
            product_manifest_sha256=sha((product / "manifest.json").read_bytes()),
        )
