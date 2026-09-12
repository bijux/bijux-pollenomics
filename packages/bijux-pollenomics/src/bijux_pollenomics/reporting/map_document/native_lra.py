"""Finite, byte-bound native model view and selection for the shared atlas."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from typing import Any

from .coordinates import point_coordinate_pair
from .temporal_admission import feature_interval


def native_view_bytes(view: dict[str, Any]) -> bytes:
    """Return the governed view bytes after checking row/site closure."""
    if view.get("schema_version") != "lra-atlas-view.v1":
        raise ValueError("Unsupported native LRA view")
    for key in (
        "product_manifest_sha256",
        "request_sha256",
        "scientific_content_sha256",
        "geometry_sha256",
    ):
        value = view.get(key)
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(char not in "0123456789abcdef" for char in value)
        ):
            raise ValueError(f"Invalid native view identity: {key}")
    if view.get("scientific_acceptance") != "not_evaluated":
        raise ValueError("Native view cannot authorize scientific acceptance")

    def browser_numbers(value: Any) -> None:
        if (
            isinstance(value, int)
            and not isinstance(value, bool)
            and abs(value) > 2**53 - 1
        ):
            raise ValueError("Native view integer exceeds exact browser range")
        if isinstance(value, dict):
            for item in value.values():
                browser_numbers(item)
        elif isinstance(value, list):
            for item in value:
                browser_numbers(item)

    browser_numbers(view)
    rows, sites = view.get("rows"), view.get("sites")
    if not isinstance(rows, list) or not isinstance(sites, list):
        raise ValueError("Native view requires rows and site accounting")
    for row in rows:
        if not isinstance(row, dict) or any(
            not isinstance(row.get(key), str) or not row[key].strip()
            for key in ("row_id", "role", "site_id", "taxon", "bin_id", "statistic")
        ):
            raise ValueError("Native row/filter identities must be nonempty strings")
    for site in sites:
        if (
            not isinstance(site, dict)
            or any(
                not isinstance(site.get(key), str) or not site[key].strip()
                for key in ("role", "site_id", "map_status")
            )
            or not isinstance(site.get("model_row_ids"), list)
            or any(
                not isinstance(row_id, str) or not row_id.strip()
                for row_id in site["model_row_ids"]
            )
        ):
            raise ValueError("Native site and membership identities must be strings")
        if site["map_status"] == "synthetic_anchor" and any(
            not isinstance(site.get(key), str) or not site[key].strip()
            for key in ("anchor_id", "layer_key")
        ):
            raise ValueError("Native anchor and layer identities must be strings")
    ids = [row["row_id"] for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate native row identity")
    membership = [row_id for site in sites for row_id in site["model_row_ids"]]
    if sorted(membership) != sorted(ids):
        raise ValueError("Native site membership does not account for every row once")
    row_by_id = {row["row_id"]: row for row in rows}
    site_keys = [(site["role"], site["site_id"]) for site in sites]
    anchor_ids = [
        site["anchor_id"] for site in sites if site.get("anchor_id") is not None
    ]
    if len(set(site_keys)) != len(site_keys) or len(set(anchor_ids)) != len(anchor_ids):
        raise ValueError("Duplicate native site or anchor identity")
    for site in sites:
        if site["map_status"] not in ("synthetic_anchor", "refused"):
            raise ValueError("Unsupported native map status")
        for row_id in site["model_row_ids"]:
            row = row_by_id[row_id]
            if (row["role"], row["site_id"]) != (site["role"], site["site_id"]):
                raise ValueError("Native row belongs to a different site")
        if site["map_status"] == "synthetic_anchor" and (
            not site.get("anchor_id") or not site.get("layer_key")
        ):
            raise ValueError(
                "Mapped native site requires exact anchor and layer identity"
            )
        if site["map_status"] == "synthetic_anchor" and (
            view["data_kind"] != "synthetic"
            or view["operation"] != "lra"
            or site["reason_codes"]
        ):
            raise ValueError(
                "Native anchors require admitted synthetic paired geometry"
            )
        if site["map_status"] == "refused" and (
            site.get("anchor_id") is not None
            or site.get("layer_key") is not None
            or not site["reason_codes"]
        ):
            raise ValueError("Refused native site cannot claim an admitted anchor")
    admitted_row_ids = {
        row_id
        for site in sites
        if site["map_status"] == "synthetic_anchor"
        for row_id in site["model_row_ids"]
    }
    for row in rows:
        window = row["declared_bin"]
        bounds = [window["younger_bp"], window["older_bp"]]
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in bounds
        ):
            raise ValueError("Native bin bounds require finite numbers")
        if row["row_id"] in admitted_row_ids:
            if (
                bounds[0] < 0
                or bounds[0] > bounds[1]
                or row.get("age_type") not in ("calendar_bp", "calibrated_bp")
            ):
                raise ValueError("Native anchor chronology is not admitted")
            support = row.get("age_support_bp")
            if (
                not isinstance(support, list)
                or len(support) != 1
                or len(support[0]) != 2
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    for value in support[0]
                )
                or not bounds[0] <= support[0][0] <= support[0][1] <= bounds[1]
            ):
                raise ValueError(
                    "Native anchor requires one contained typed age interval"
                )
        if row["role"] not in ("regional", "local") or row["native_unit"] != (
            "percent" if row["role"] == "regional" else "fraction"
        ):
            raise ValueError("Native role and unit disagree")
        if row["native_value"] is not None and not isinstance(row["native_value"], str):
            raise ValueError("Native estimates must retain original CSV text or null")
        if row["native_value"] is not None:
            try:
                if not Decimal(row["native_value"]).is_finite():
                    raise ValueError("Native estimate text must be finite")
            except InvalidOperation as error:
                raise ValueError(
                    "Native estimate text must represent a decimal"
                ) from error
    admitted = [row for row in rows if row["row_id"] in admitted_row_ids]
    if (
        len({row["bin_id"] for row in admitted}) > 1
        or len({row["age_type"] for row in admitted}) > 1
    ):
        raise ValueError("Native anchors require one comparable typed bin")
    return (
        json.dumps(
            view,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("ascii")


def bind_native_view(view: dict[str, Any]) -> dict[str, str]:
    encoded = native_view_bytes(view)
    return {
        "bytes": encoded.decode("ascii"),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def select_native_rows(
    view: dict[str, Any], selection: dict[str, Any], global_context: dict[str, Any]
) -> dict[str, Any]:
    """Select rows and anchors with separately counted geometry refusals."""
    fields = {
        "roles": "role",
        "site_ids": "site_id",
        "taxa": "taxon",
        "bin_ids": "bin_id",
    }
    if set(selection) != set(fields):
        raise ValueError("Native selection requires every declared filter")
    normalized = {}
    for name, field in fields.items():
        values = selection[name]
        allowed = {row[field] for row in view["rows"]}
        if (
            not isinstance(values, list)
            or any(
                not isinstance(value, str) or value not in allowed for value in values
            )
            or len(set(values)) != len(values)
        ):
            raise ValueError(f"Unknown or duplicate native selection: {name}")
        normalized[name] = sorted(values)
    if set(global_context) != {"time_window_bp", "active_layer_keys"}:
        raise ValueError("Native global context is incomplete")
    interval, layers = (
        global_context["time_window_bp"],
        global_context["active_layer_keys"],
    )
    if (
        not isinstance(interval, list)
        or len(interval) != 2
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
            for value in interval
        )
        or interval[0] > interval[1]
    ):
        raise ValueError("Invalid native global time window")
    if (
        not isinstance(layers, list)
        or any(not isinstance(value, str) for value in layers)
        or len(set(layers)) != len(layers)
    ):
        raise ValueError("Invalid native global layers")
    site_by_row = {
        row_id: site for site in view["sites"] for row_id in site["model_row_ids"]
    }
    selected = []
    for row in view["rows"]:
        if any(row[field] not in normalized[name] for name, field in fields.items()):
            continue
        site = site_by_row[row["row_id"]]
        if site["map_status"] == "synthetic_anchor":
            window = row["declared_bin"]
            if (
                site["layer_key"] not in layers
                or window["older_bp"] < interval[0]
                or window["younger_bp"] > interval[1]
            ):
                continue
        selected.append(row)
    ids = {row["row_id"] for row in selected}
    selected_sites = [
        site for site in view["sites"] if ids.intersection(site["model_row_ids"])
    ]
    anchors = sorted(
        site["anchor_id"]
        for site in selected_sites
        if site["map_status"] == "synthetic_anchor"
    )
    return {
        "selection": normalized,
        "global_context": {
            "time_window_bp": interval,
            "active_layer_keys": sorted(layers),
        },
        "selected_row_ids": [row["row_id"] for row in selected],
        "mapped_anchor_ids": anchors,
        "rows": selected,
        "sites": selected_sites,
        "counts": {
            "selected_rows": len(selected),
            "mapped_anchors": len(anchors),
            "refused_sites": sum(
                site["map_status"] == "refused" for site in selected_sites
            ),
            "missing_values": sum(row["native_value"] is None for row in selected),
        },
        "temporal_refusal_policy": "geometry-refused rows retained; global map time/layers apply only to admitted anchors",
    }


def validate_native_layers(view: dict[str, Any], layers: list[Any]) -> None:
    """Reconcile admitted row/anchor identities to the actual shared map payload."""
    expected = {
        site["anchor_id"]: site
        for site in view["sites"]
        if site["map_status"] == "synthetic_anchor"
    }
    observed = {}
    for layer in layers:
        if layer.get("semantic_role") != "exploratory_lra_model_anchor":
            continue
        for feature in layer["features"]:
            anchor_id = feature["record_id"]
            if anchor_id in observed or anchor_id not in expected:
                raise ValueError("Unknown or duplicate native map anchor")
            site = expected[anchor_id]
            if layer["key"] != site["layer_key"] or sorted(
                feature["model_row_ids"]
            ) != sorted(site["model_row_ids"]):
                raise ValueError("Native map anchor row membership differs from view")
            if (
                feature["product_manifest_sha256"] != view["product_manifest_sha256"]
                or feature["geometry_sha256"] != view["geometry_sha256"]
            ):
                raise ValueError("Native map anchor belongs to different evidence")
            interval = feature_interval(feature)
            if interval is None or point_coordinate_pair(feature) is None:
                raise ValueError("Native anchor fails shared coordinate/time admission")
            rows = [
                row for row in view["rows"] if row["row_id"] in site["model_row_ids"]
            ]
            if any(
                interval
                != (row["declared_bin"]["younger_bp"], row["declared_bin"]["older_bp"])
                or feature.get("age_type") != row["age_type"]
                for row in rows
            ):
                raise ValueError("Native anchor time differs from bound model bin")
            observed[anchor_id] = feature
    if set(observed) != set(expected):
        raise ValueError("Native view has no corresponding shared map anchor")
