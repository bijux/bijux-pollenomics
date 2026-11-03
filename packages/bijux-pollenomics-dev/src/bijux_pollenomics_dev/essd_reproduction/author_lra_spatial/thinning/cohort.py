"""Select nominal geographic coverage without consulting scientific outcomes."""

from __future__ import annotations

import math
from typing import Any

from bijux_pollenomics.core.geospatial.distance import wgs84_inverse_geodesic


def select_cohort(
    geometries: dict[str, dict[str, Any]], size: int = 10
) -> dict[str, Any]:
    """Seed at the medoid and extend maximin; exact metric ties use record ID."""
    if (
        type(geometries) is not dict
        or not geometries
        or any(type(record) is not str or not record for record in geometries)
        or type(size) is not int
        or not 1 <= size <= len(geometries)
    ):
        raise ValueError(
            "A nonempty named geometry universe and valid size are required"
        )
    records = sorted(geometries)
    coordinates = {}
    for record in records:
        geometry = geometries[record]
        if type(geometry) is not dict:
            raise ValueError("Original source geometry mapping required")
        latitude, longitude = geometry["latitude"], geometry["longitude"]
        wgs84_inverse_geodesic(
            latitude_a=latitude,
            longitude_a=longitude,
            latitude_b=latitude,
            longitude_b=longitude,
        )
        coordinates[record] = {"latitude": latitude, "longitude": longitude}
    distances = {record: {record: 0.0} for record in records}
    for index, left in enumerate(records):
        for right in records[index + 1 :]:
            value = (
                wgs84_inverse_geodesic(
                    latitude_a=coordinates[left]["latitude"],
                    longitude_a=coordinates[left]["longitude"],
                    latitude_b=coordinates[right]["latitude"],
                    longitude_b=coordinates[right]["longitude"],
                ).distance_km_unrounded
                * 1000.0
            )
            distances[left][right] = distances[right][left] = value
    scores = {
        record: math.fsum(distances[record][other] for other in records)
        for record in records
    }
    seed = min(records, key=lambda record: (scores[record], record))
    selected = [seed]
    steps = [
        {
            "step": 1,
            "record_id": seed,
            "criterion": "minimum_total_distance",
            "value_m": scores[seed],
            "candidate_values_m": scores,
        }
    ]
    while len(selected) < size:
        nearest = {
            record: min(distances[record][owner] for owner in selected)
            for record in records
            if record not in selected
        }
        choice = min(nearest, key=lambda record: (-nearest[record], record))
        selected.append(choice)
        steps.append(
            {
                "step": len(selected),
                "record_id": choice,
                "criterion": "maximum_nearest_selected_distance",
                "value_m": nearest[choice],
                "candidate_values_m": nearest,
            }
        )
    nearest_all = {
        record: min(distances[record][owner] for owner in selected)
        for record in records
    }
    return {
        "distance_model": "nominal_wgs84_inverse",
        "tie_policy": "exact_metric_then_lexicographic_record_id",
        "coordinates": coordinates,
        "distance_matrix_m": {
            record: {other: distances[record][other] for other in records}
            for record in records
        },
        "selection_order": selected,
        "selected": sorted(selected),
        "excluded": sorted(set(records) - set(selected)),
        "steps": steps,
        "nearest_selected_distance_m": nearest_all,
        "coverage_m": max(nearest_all.values()),
        "min_separation_m": min(
            distances[left][right]
            for index, left in enumerate(selected)
            for right in selected[index + 1 :]
        )
        if size > 1
        else None,
    }
