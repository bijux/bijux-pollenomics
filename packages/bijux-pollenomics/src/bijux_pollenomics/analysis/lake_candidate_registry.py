from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
import json
from pathlib import Path
import unicodedata

from ..core import haversine_km
from ..collection.spatial.representative_points import (
    geometry_to_representative_point,
)

__all__ = [
    "SOUTHERN_SWEDEN_LAKE_REVIEW_TARGETS",
    "build_sweden_lake_candidate_registry",
    "write_sweden_lake_candidate_registry",
]

SOUTHERN_SWEDEN_LAKE_REVIEW_TARGETS = (
    "Bjäresjösjön",
    "Havgårdssjön",
    "Finjasjön",
    "Östra Ringsjön",
    "Gullåkra",
    "Vesums mossar",
)
_TARGET_REGISTRY_ALIASES = {"bjaresjosjon": ("bjaresjo",)}
_MAX_POLLEN_MATCH_DISTANCE_KM = 2.5
_SAMPLING_MISSING_INPUTS = (
    "bathymetry and basin depth",
    "sediment preservation and prior coring history",
    "shore access and landowner contact",
    "permit requirements",
    "field hazards and logistics",
)


def build_sweden_lake_candidate_registry(
    *,
    svar_geojson_path: Path,
    pollen_geojson_paths: Sequence[Path],
    generated_on: str,
    named_targets: Sequence[str] = SOUTHERN_SWEDEN_LAKE_REVIEW_TARGETS,
) -> tuple[dict[str, object], dict[str, object]]:
    """Derive a compact official registry for evidence-linked and named lakes."""
    svar_features = _load_features(svar_geojson_path)
    lake_rows = _lake_rows(svar_features)
    pollen_points = _load_pollen_points(pollen_geojson_paths)
    pollen_matches = _match_pollen_points(lake_rows, pollen_points)
    target_matches, unresolved_targets = _match_named_targets(lake_rows, named_targets)

    selection_reasons: dict[str, set[str]] = defaultdict(set)
    for lake_id in pollen_matches:
        selection_reasons[lake_id].add("direct_pollen_proximity")
    for lake_id in target_matches.values():
        selection_reasons[lake_id].add("named_target_review")

    features = []
    for row in lake_rows:
        lake_id = row["lake_id"]
        if lake_id not in selection_reasons:
            continue
        feature = row["feature"]
        properties = dict(feature["properties"])
        pollen_evidence = sorted(pollen_matches.get(lake_id, ()))
        sampling_screen = _sampling_area_screen(
            lake_name=str(properties.get("name", "")),
            area_km2=_optional_float(properties.get("area_km2")),
        )
        properties.update(
            {
                "candidate_selection_reasons": sorted(selection_reasons[lake_id]),
                "matched_pollen_records": [record for _, record in pollen_evidence],
                "nearest_pollen_distance_km": (
                    round(min(distance for distance, _ in pollen_evidence), 4)
                    if pollen_evidence
                    else None
                ),
                "source_geometry_type": row["source_geometry_type"],
                "representative_point_method": "official_geometry_representative_point",
                "sampling_area_screen": sampling_screen,
                "sampling_readiness_posture": "site_review_required",
                "sampling_known_inputs": [
                    "official lake identity",
                    "official geometry-derived location",
                    "mapped water-surface area",
                ],
                "sampling_missing_inputs": list(_SAMPLING_MISSING_INPUTS),
                "temporal_posture": "current_hydrographic_identity_only",
            }
        )
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row["longitude"], row["latitude"]],
                },
                "properties": properties,
            }
        )

    features.sort(
        key=lambda feature: (
            _normalize_name(str(feature["properties"].get("name", ""))),
            str(feature["properties"].get("sjoid", "")),
        )
    )
    target_rows = [
        {
            "requested_name": target,
            "registry_match": target_matches.get(target, ""),
            "registry_status": (
                "matched" if target in target_matches else "not_present_in_svar_lakes"
            ),
        }
        for target in named_targets
    ]
    registry = {
        "type": "FeatureCollection",
        "schema_version": "sweden-lake-candidate-registry.v1",
        "generated_on": generated_on,
        "source": "SMHI SVAR",
        "source_snapshot": svar_geojson_path.name,
        "selection": {
            "pollen_match_distance_km": _MAX_POLLEN_MATCH_DISTANCE_KM,
            "rule": (
                "retain the nearest official SVAR lake to each governed pollen point "
                "within 2.5 km, plus exact named-target registry matches"
            ),
            "pollen_point_count": len(pollen_points),
            "candidate_count": len(features),
        },
        "features": features,
    }
    review = {
        "schema_version": "sweden-lake-candidate-registry-review.v1",
        "generated_on": generated_on,
        "source": "SMHI SVAR",
        "source_lake_count": len(lake_rows),
        "candidate_count": len(features),
        "pollen_linked_lake_count": len(pollen_matches),
        "named_target_match_count": len(target_matches),
        "unresolved_named_target_count": len(unresolved_targets),
        "named_targets": target_rows,
        "sampling_readiness_rule": (
            "registry identity, representative location, and mapped area complete an "
            "area screen only; every retained lake still requires bathymetry, sediment, "
            "access, permit, hazard, and logistics review"
        ),
        "temporal_rule": (
            "SVAR represents current hydrographic identity. Dated evidence remains on "
            "the linked pollen, archaeology, and ancient-DNA records."
        ),
    }
    return registry, review


def write_sweden_lake_candidate_registry(
    *,
    registry_path: Path,
    review_path: Path,
    registry: dict[str, object],
    review: dict[str, object],
) -> None:
    """Write the compact registry and its governed selection review."""
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    review_path.write_text(json.dumps(review, indent=2), encoding="utf-8")


def _load_features(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    if not isinstance(features, list):
        raise ValueError(f"{path} does not contain a GeoJSON feature list")
    return [feature for feature in features if isinstance(feature, dict)]


def _lake_rows(features: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for feature in features:
        properties = feature.get("properties")
        geometry = feature.get("geometry")
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            continue
        representative_point = geometry_to_representative_point(geometry)
        if representative_point is None:
            continue
        longitude, latitude, geometry_type = representative_point
        lake_id = str(properties.get("sjoid") or properties.get("record_id") or "")
        lake_name = str(properties.get("name", "")).strip()
        if not lake_id or not lake_name:
            continue
        rows.append(
            {
                "lake_id": lake_id,
                "name_key": _normalize_name(lake_name),
                "latitude": round(latitude, 6),
                "longitude": round(longitude, 6),
                "source_geometry_type": geometry_type,
                "feature": feature,
            }
        )
    return rows


def _load_pollen_points(paths: Sequence[Path]) -> list[dict[str, object]]:
    points = []
    for path in paths:
        for feature in _load_features(path):
            properties = feature.get("properties")
            geometry = feature.get("geometry")
            if not isinstance(properties, dict) or not isinstance(geometry, dict):
                continue
            if str(properties.get("country", "")).strip() != "Sweden":
                continue
            coordinates = geometry.get("coordinates")
            if geometry.get("type") != "Point" or not isinstance(coordinates, list):
                continue
            if len(coordinates) < 2:
                continue
            points.append(
                {
                    "latitude": float(coordinates[1]),
                    "longitude": float(coordinates[0]),
                    "source_record": (
                        f"{properties.get('layer_key', '')}:"
                        f"{properties.get('record_id', '')}"
                    ),
                }
            )
    return points


def _match_pollen_points(
    lake_rows: Sequence[dict[str, object]],
    pollen_points: Sequence[dict[str, object]],
) -> dict[str, list[tuple[float, str]]]:
    matches: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for point in pollen_points:
        nearest = min(
            (
                haversine_km(
                    latitude_a=float(point["latitude"]),
                    longitude_a=float(point["longitude"]),
                    latitude_b=float(lake["latitude"]),
                    longitude_b=float(lake["longitude"]),
                ),
                lake,
            )
            for lake in lake_rows
        )
        distance, lake = nearest
        if distance <= _MAX_POLLEN_MATCH_DISTANCE_KM:
            matches[str(lake["lake_id"])].append(
                (round(distance, 4), str(point["source_record"]))
            )
    return dict(matches)


def _match_named_targets(
    lake_rows: Sequence[dict[str, object]],
    named_targets: Sequence[str],
) -> tuple[dict[str, str], tuple[str, ...]]:
    by_name: dict[str, list[str]] = defaultdict(list)
    for lake in lake_rows:
        by_name[str(lake["name_key"])].append(str(lake["lake_id"]))
    matches: dict[str, str] = {}
    unresolved = []
    for target in named_targets:
        target_key = _normalize_name(target)
        candidate_keys = (target_key, *_TARGET_REGISTRY_ALIASES.get(target_key, ()))
        lake_ids = [
            lake_id for key in candidate_keys for lake_id in by_name.get(key, ())
        ]
        if len(lake_ids) == 1:
            matches[target] = lake_ids[0]
        else:
            unresolved.append(target)
    return matches, tuple(unresolved)


def _sampling_area_screen(*, lake_name: str, area_km2: float | None) -> str:
    normalized_name = _normalize_name(lake_name)
    if any(term in normalized_name for term in ("mosse", "myr", "karr")):
        return "wetland_identity_review"
    if area_km2 is None:
        return "mapped_area_unresolved"
    if area_km2 < 0.05:
        return "micro_basin_review"
    if area_km2 < 0.15:
        return "compact_lake_review"
    if area_km2 > 20:
        return "large_lake_site_selection_required"
    return "lake_area_screen_complete"


def _normalize_name(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in folded if character.isalnum())


def _optional_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None
