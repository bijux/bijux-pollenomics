"""Keep feature/site/claim, chronology and geography denominators separate."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .geodesic import inside, spherical_km, wgs84_km
from .source import BIN_IDS, Record, overlap


def identities(records: list[Record]) -> dict[str, Any]:
    """Record exact support identities as well as counts; never sum site hulls."""
    features = sorted(row.identifier for row in records)
    sites = sorted({row.site_uuid for row in records})
    claims = sorted({claim for row in records for claim in row.claim_ids})
    return {
        "feature_count": len(features),
        "site_count": len(sites),
        "distinct_claim_count": len(claims),
        "feature_ids_sha256": hashlib.sha256(
            json.dumps(features, separators=(",", ":")).encode()
        ).hexdigest(),
        "site_ids_sha256": hashlib.sha256(
            json.dumps(sites, separators=(",", ":")).encode()
        ).hexdigest(),
        "claim_ids_sha256": hashlib.sha256(
            json.dumps(claims, separators=(",", ":")).encode()
        ).hexdigest(),
        "qualified_or_uncertain_feature_count": sum(
            bool(row.uncertainty_notes) for row in records
        ),
    }


def evaluate(
    records: list[Record],
    centres: dict[str, tuple[float, float]],
    original: dict[str, Any],
) -> tuple[
    dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]
]:
    distances: list[dict[str, Any]] = []
    cells: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []
    spatial: list[dict[str, Any]] = []
    pairs: dict[tuple[str, str], tuple[float, float]] = {}
    for centre, location in centres.items():
        for row in records:
            sphere, ellipsoid = (
                spherical_km(location, row.coordinate),
                wgs84_km(location, row.coordinate),
            )
            pairs[(centre, row.identifier)] = (sphere, ellipsoid)
            distances.append(
                {
                    "centre": centre,
                    "record_id": row.identifier,
                    "site_uuid": row.site_uuid,
                    "latitude": row.coordinate[0],
                    "longitude": row.coordinate[1],
                    "time_start_bp": row.lower,
                    "time_end_bp": row.upper,
                    "chronology_status": row.status,
                    "precision_posture": row.precision,
                    "comparability_posture": row.comparability,
                    "uncertainty_note_count": len(row.uncertainty_notes),
                    "source_properties_sha256": row.properties_sha256,
                    "sphere_km": sphere,
                    "wgs84_km": ellipsoid,
                    "wgs84_minus_sphere_metres": (ellipsoid - sphere) * 1000,
                    "distance_to_10km_boundary_metres": (ellipsoid - 10) * 1000,
                    "distance_to_20km_boundary_metres": (ellipsoid - 20) * 1000,
                    "sphere_inside10": inside(sphere, 10),
                    "wgs84_inside10": inside(ellipsoid, 10),
                    "sphere_inside20": inside(sphere, 20),
                    "wgs84_inside20": inside(ellipsoid, 20),
                }
            )
        for radius in (10, 20):
            for row in records:
                sphere, ellipsoid = pairs[(centre, row.identifier)]
                if inside(sphere, radius) != inside(ellipsoid, radius):
                    changes.append(
                        {
                            "centre": centre,
                            "radius_km": radius,
                            "record_id": row.identifier,
                            "site_uuid": row.site_uuid,
                            "chronology_status": row.status,
                            "sphere_inside": inside(sphere, radius),
                            "wgs84_inside": inside(ellipsoid, radius),
                            "sphere_km": sphere,
                            "wgs84_km": ellipsoid,
                        }
                    )
            for method, position in [("retained_sphere", 0), ("WGS84", 1)]:
                nearby = [
                    row
                    for row in records
                    if inside(pairs[(centre, row.identifier)][position], radius)
                ]
                spatial.append(
                    {
                        "centre": centre,
                        "radius_km": radius,
                        "method": method,
                        **identities(nearby),
                        "numeric_feature_count": sum(
                            row.status == "numeric" for row in nearby
                        ),
                        "unresolved_feature_count": sum(
                            row.status != "numeric" for row in nearby
                        ),
                    }
                )
                for bin_id in BIN_IDS:
                    selected = [
                        row
                        for row in nearby
                        if overlap(
                            row.lower, row.upper, bin_id * 500, (bin_id + 1) * 500
                        )
                    ]
                    cell = {
                        "centre": centre,
                        "radius_km": radius,
                        "method": method,
                        "bin_id": bin_id,
                        "lower_bp": bin_id * 500,
                        "upper_bp_exclusive": (bin_id + 1) * 500,
                        **identities(selected),
                    }
                    if method == "retained_sphere":
                        source = next(
                            w for w in original["windows"] if w["bin_index"] == bin_id
                        )
                        site = "BUS" if centre == "BUS_inventory" else centre
                        name = f"{radius}km_" + (
                            "inventory_point"
                            if centre == "BUS_inventory"
                            else "neotoma_point"
                        )
                        expected = source["observations"][site][
                            "sead_chronology_context"
                        ][name]
                        if (cell["feature_count"], cell["site_count"]) != (
                            expected["dated_feature_count"],
                            expected["distinct_site_count"],
                        ):
                            raise ValueError(
                                "Original spherical context count is not reproduced"
                            )
                    cells.append(cell)
    differences = []
    for cell in cells:
        if cell["method"] != "WGS84":
            continue
        old = next(
            r
            for r in cells
            if r["method"] == "retained_sphere"
            and all(r[k] == cell[k] for k in ["centre", "radius_km", "bin_id"])
        )
        differences.append(
            {
                **{k: cell[k] for k in ["centre", "radius_km", "bin_id"]},
                "feature_count_delta": cell["feature_count"] - old["feature_count"],
                "site_count_delta": cell["site_count"] - old["site_count"],
                "claim_count_delta": cell["distinct_claim_count"]
                - old["distinct_claim_count"],
                "feature_membership_changed": cell["feature_ids_sha256"]
                != old["feature_ids_sha256"],
            }
        )
    summary = {
        "schema_version": "landscape-geodesic-sensitivity.v1",
        "source_feature_count": len(records),
        "source_numeric_feature_count": sum(row.status == "numeric" for row in records),
        "source_unresolved_feature_count": sum(
            row.status != "numeric" for row in records
        ),
        "centre_count": len(centres),
        "bin_count": len(BIN_IDS),
        "radius_count": 2,
        "method_count": 2,
        "window_cell_count": len(cells),
        "original_spherical_cells_verified": sum(
            row["method"] == "retained_sphere" for row in cells
        ),
        "membership_change_count": len(changes),
        "window_differences": differences,
        "spatial_membership": spatial,
        "minimum_wgs84_boundary_margin_metres": min(
            abs(d[key])
            for d in distances
            for key in [
                "distance_to_10km_boundary_metres",
                "distance_to_20km_boundary_metres",
            ]
        ),
        "numerically_near_boundary_feature_centre_pairs_1mm": sum(
            min(
                abs(d["distance_to_10km_boundary_metres"]),
                abs(d["distance_to_20km_boundary_metres"]),
            )
            <= 0.001
            for d in distances
        ),
        "centres": centres,
        "source_model_grid": 779,
        "shared_lineage_target_count": 5,
        "ecological_event_admission": False,
        "rights_admission": False,
        "untouched_confirmation": False,
        "chronology_refit": False,
        "interpretation": "Geography-method/coordinate sensitivity of dated source-feature context only. Original half-open bins and per-record intervals remain unchanged; no site hull, new event, land-use magnitude, vegetation measurement, selected best centre or right to scientific reuse.",
    }
    return summary, distances, cells, changes
