"""Explicit synthetic signed calendar view and layer fixture for map contracts."""

from __future__ import annotations

from typing import Any

from bijux_pollenomics.core.calendar_support import (
    SIGNED_CALENDAR_PROFILE,
    SignedCalendarSupport,
)

from .support import view_fixture


def signed_fixture(
    younger: int | float = -50.75, older: int | float = -49.25
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    view = view_fixture()
    view["rows"] = view["rows"][:2]
    view["sites"] = view["sites"][:2]
    view.update(
        schema_version="lra-atlas-view.v2",
        temporal_profile=SIGNED_CALENDAR_PROFILE,
        temporal_axis="BP1950",
    )
    for row in view["rows"]:
        row["sample_id"] = "sample-" + row["role"]
        row["declared_bin"] = {
            "bin_id": row["bin_id"],
            "younger_bp": younger,
            "older_bp": older,
        }
        row["age_support_bp"] = [[younger, older]]
        row["source_calendar_support"] = SignedCalendarSupport(
            younger, older, support_kind="closed_age_support"
        ).as_dict()
        row["declared_calendar_support"] = SignedCalendarSupport(
            younger, older, support_kind="declared_stationarity_envelope"
        ).as_dict()
    layers = []
    for site in view["sites"]:
        if site["map_status"] != "synthetic_anchor":
            continue
        row = next(
            row for row in view["rows"] if row["row_id"] in site["model_row_ids"]
        )
        feature = {
            "record_id": site["anchor_id"],
            "model_row_ids": site["model_row_ids"],
            "product_manifest_sha256": view["product_manifest_sha256"],
            "geometry_sha256": view["geometry_sha256"],
            "data_kind": "synthetic",
            "evidence_role": "model_output",
            "scientific_acceptance": "not_evaluated",
            "age_type": "calendar_bp",
            "source_age_support_bp": [[younger, older]],
            "source_calendar_support": row["source_calendar_support"].copy(),
            "declared_calendar_support": row["declared_calendar_support"].copy(),
            "time_start_bp": younger,
            "time_end_bp": older,
            "latitude": 55.5,
            "longitude": 13.0,
            "country": "UNASSIGNED",
        }
        layers.append(
            {
                "key": site["layer_key"],
                "semantic_role": "exploratory_lra_model_anchor",
                "features": [feature],
            }
        )
    return view, layers
