"""Account every requested site before admitting synthetic display-only anchors."""

from __future__ import annotations

from typing import Any

from .contracts import canonical, digest


def project_sites(
    request: dict[str, Any],
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
    geometry: dict[tuple[str, str], dict[str, Any]],
    *,
    product_sha256: str,
    geometry_sha256: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    layers: list[dict[str, Any]] = []
    accounting: list[dict[str, Any]] = []
    bins = request["temporal_matching"]["bins"]
    age_types = {
        sample["age_type"]
        for role in ("regional", "local")
        if role in request
        for sample in request[role]["samples"]
    }
    for role in ("regional", "local"):
        if role not in request:
            continue
        samples = request[role]["samples"]
        for site_id in sorted({sample["site_id"] for sample in samples}):
            included = [sample for sample in samples if sample["site_id"] == site_id]
            values = [
                row for row in rows if row["role"] == role and row["site_id"] == site_id
            ]
            anchor = geometry.get((role, site_id))
            reasons = []
            if request["operation"] != "lra":
                reasons.append("unsupported_map_operation")
            if len(age_types) != 1:
                reasons.append("mixed_age_types_not_comparable_in_map")
            if request["data_kind"] != "synthetic":
                reasons.append("source_geography_not_admitted")
            if len(included) != 1 or len(bins) != 1:
                reasons.append("unsupported_multiple_sample_or_bin_profile")
            if any(len(sample["age_support_bp"]) != 1 for sample in included):
                reasons.append("unsupported_multimodal_map_chronology")
            if any(
                sample["age_type"] not in ("calendar_bp", "calibrated_bp")
                for sample in included
            ):
                reasons.append("unsupported_map_age_type")
            if any(
                boundary < 0
                for sample in included
                for interval in sample["age_support_bp"]
                for boundary in interval
            ) or any(row["younger_bp"] < 0 or row["older_bp"] < 0 for row in bins):
                reasons.append("unsupported_signed_bp_map_chronology")
            if any(
                interval[0] > interval[1]
                for sample in included
                for interval in sample["age_support_bp"]
            ) or any(row["younger_bp"] > row["older_bp"] for row in bins):
                reasons.append("invalid_map_chronology_bounds")
            if len(bins) == 1 and any(
                sample["bin_id"] != bins[0]["bin_id"]
                or any(
                    interval[0] < bins[0]["younger_bp"]
                    or interval[1] > bins[0]["older_bp"]
                    for interval in sample["age_support_bp"]
                )
                for sample in included
            ):
                reasons.append("source_support_outside_declared_map_bin")
            if anchor is None:
                reasons.append("missing_display_geometry")
            elif anchor["disposition"] == "unresolved":
                reasons.append("unresolved_display_geometry")
            elif anchor["basis"] != "synthetic_fixture":
                reasons.append("source_coordinate_basis_not_admitted")
            item = {
                "role": role,
                "site_id": site_id,
                "sample_ids": [sample["sample_id"] for sample in included],
                "model_row_ids": [row["row_id"] for row in values],
                "map_status": "refused" if reasons else "synthetic_anchor",
                "reason_codes": reasons,
            }
            accounting.append(item)
            if reasons or anchor is None:
                continue
            window = bins[0]
            feature = {
                "record_id": "lra-anchor:"
                + digest(
                    canonical(
                        {
                            "product_sha256": product_sha256,
                            "role": role,
                            "site_id": site_id,
                        }
                    )
                ),
                "site_id": site_id,
                "latitude": anchor["position"][1],
                "longitude": anchor["position"][0],
                "country": "UNASSIGNED",
                "title": f"Synthetic {role} model anchor: {site_id}",
                "subtitle": "Exploratory model output; not an observed pollen point",
                "evidence_role": "model_output",
                "data_kind": "synthetic",
                "scientific_acceptance": "not_evaluated",
                "contribution_role": "display_only",
                "candidate_ranking_eligible": False,
                "scientific_classification_eligible": False,
                "scientific_signal_ids": [],
                "model_row_ids": item["model_row_ids"],
                "time_start_bp": window["younger_bp"],
                "time_end_bp": window["older_bp"],
                "time_label": f"Declared stationary bin {window['bin_id']} ({included[0]['age_type']})",
                "source_age_support_bp": included[0]["age_support_bp"],
                "age_type": included[0]["age_type"],
                "product_manifest_sha256": product_sha256,
                "scientific_content_sha256": manifest["scientific_content_sha256"],
                "geometry_sha256": geometry_sha256,
                "spatial_support_posture": "display_anchor_not_estimate_footprint",
                "popup_rows": [
                    {
                        "label": "Evidence role",
                        "value": "Synthetic exploratory model; scientific acceptance not evaluated",
                    },
                    {
                        "label": "Geometry",
                        "value": "Declared synthetic anchor; not a regional footprint or ring polygon",
                    },
                    {
                        "label": "Native unit",
                        "value": "percent" if role == "regional" else "fraction",
                    },
                    {
                        "label": "Source age support",
                        "value": str(included[0]["age_support_bp"]),
                    },
                    {
                        "label": "Uncertainty omissions",
                        "value": ", ".join(manifest["uncertainty_omissions"]),
                    },
                    {"label": "Product SHA-256", "value": product_sha256},
                ],
            }
            for row in values:
                if row["statistic"] != "mean":
                    continue
                support = row["spatial_support"]
                ring_label = (
                    f" · ring {support['ring']['inner_m']}–{support['ring']['outer_m']} m"
                    if "ring" in support
                    else ""
                )
                feature["popup_rows"].append(
                    {
                        "label": f"Mean {row['taxon']}{ring_label} ({row['native_unit']})",
                        "value": row["native_value"]
                        if row["native_value"] is not None
                        else "N/A (source statistic unavailable)",
                    }
                )
            layers.append(
                {
                    "key": f"lra-{role}-{digest(site_id.encode())[:12]}",
                    "label": f"Synthetic {role} model anchors",
                    "group": "environmental-context",
                    "semantic_role": "exploratory_lra_model_anchor",
                    "default_enabled": True,
                    "applies_country_filter": False,
                    "applies_time_filter": True,
                    "circle_enabled": False,
                    "scientific_selection_enabled": False,
                    "candidate_ranking_eligible": False,
                    "contribution_role": "display_only",
                    "style": {
                        "fill": "#0f766e" if role == "regional" else "#b45309",
                        "stroke": "#111827",
                        "radius": 7,
                    },
                    "features": [feature],
                }
            )
    if sum(len(item["model_row_ids"]) for item in accounting) != len(rows):
        raise ValueError("Model rows do not reconcile to requested sites")
    return layers, accounting
