"""Explicit native-view fixtures and existing Node semantics harness."""

from __future__ import annotations

import json
from typing import Any

from bijux_pollenomics.reporting.map_document.template import NATIVE_LRA_CONTROLLER

from ..browser_semantics.support import run_node_json


def view_fixture() -> dict[str, Any]:
    rows: list[dict[str, Any]] = [
        {
            "row_id": "r0",
            "role": "regional",
            "site_id": "site-r",
            "taxon": "Alnus🌿",
            "bin_id": "bin",
            "statistic": "mean",
            "native_value": "0",
            "native_unit": "percent",
            "declared_bin": {"younger_bp": 10, "older_bp": 20},
        },
        {
            "row_id": "r1",
            "role": "local",
            "site_id": "site-l",
            "taxon": "Betula",
            "bin_id": "bin",
            "statistic": "sd",
            "native_value": None,
            "native_unit": "fraction",
            "declared_bin": {"younger_bp": 10, "older_bp": 20},
        },
        {
            "row_id": "r2",
            "role": "local",
            "site_id": "refused",
            "taxon": "Betula",
            "bin_id": "bin",
            "statistic": "mean",
            "native_value": "0.25000000000000001",
            "native_unit": "fraction",
            "declared_bin": {"younger_bp": -10, "older_bp": 20},
        },
    ]
    for row in rows:
        row["age_type"] = "calendar_bp"
        row["age_support_bp"] = [[10, 20]]
    return {
        "schema_version": "lra-atlas-view.v1",
        "product_manifest_sha256": "a" * 64,
        "request_sha256": "b" * 64,
        "scientific_content_sha256": "c" * 64,
        "geometry_sha256": "d" * 64,
        "data_kind": "synthetic",
        "operation": "lra",
        "method": {"profile": "synthetic", "configuration": {}, "versions": {}},
        "scientific_acceptance": "not_evaluated",
        "uncertainty_omissions": ["source/parameter uncertainty"],
        "exclusions": [],
        "rows": rows,
        "sites": [
            {
                "role": "regional",
                "site_id": "site-r",
                "map_status": "synthetic_anchor",
                "reason_codes": [],
                "model_row_ids": ["r0"],
                "anchor_id": "anchor-r",
                "layer_key": "layer-r",
            },
            {
                "role": "local",
                "site_id": "site-l",
                "map_status": "synthetic_anchor",
                "reason_codes": [],
                "model_row_ids": ["r1"],
                "anchor_id": "anchor-l",
                "layer_key": "layer-l",
            },
            {
                "role": "local",
                "site_id": "refused",
                "map_status": "refused",
                "reason_codes": ["unsupported_signed_bp_map_chronology"],
                "model_row_ids": ["r2"],
                "anchor_id": None,
                "layer_key": None,
            },
        ],
    }


def selection_fixture(view: dict[str, Any]) -> dict[str, Any]:
    return {
        key: sorted({row[field] for row in view["rows"]})
        for key, field in (
            ("roles", "role"),
            ("site_ids", "site_id"),
            ("taxa", "taxon"),
            ("bin_ids", "bin_id"),
        )
    }


def run_controller(
    view: dict[str, Any], body: str, *, context: dict[str, Any] | None = None
) -> Any:
    if context is None:
        context = {
            "time_window_bp": [10, 20],
            "active_layer_keys": ["layer-r", "layer-l"],
        }
    return run_node_json(
        NATIVE_LRA_CONTROLLER
        + "\n(async () => {\n"
        + f"const view = {json.dumps(view)}; let context = {json.dumps(context)};"
        + "const controller = createNativeLraController(view, 'e'.repeat(64), {globalContext: () => context, changed: () => {}, sha256: async bytes => require('crypto').createHash('sha256').update(bytes).digest('hex')});\n"
        + body
        + "\n})().catch(error => {console.error(error); process.exit(1)});"
    )
