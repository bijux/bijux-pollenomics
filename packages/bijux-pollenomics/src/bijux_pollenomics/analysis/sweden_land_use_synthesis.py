from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from ..core import haversine_km

__all__ = [
    "build_sweden_land_use_synthesis",
    "render_sweden_land_use_synthesis_markdown",
    "write_sweden_land_use_synthesis_csv",
    "write_sweden_land_use_synthesis_json",
]

_LANDCLIM_DATASET_ID = "937075"
_CONTEXT_RADIUS_KM = 20
_HOJEA_REPORT_URL = (
    "https://hojea.se/rapporter/"
    "2003_Arkeologisk_foerundersoekning_Gullaakra_Vesums_mossar.pdf"
)


@dataclass(frozen=True)
class _Target:
    requested_name: str
    registry_name: str
    latitude: float
    longitude: float
    target_class: str
    lake_decision: str
    decision_reason: str
    coordinate_source: str


_TARGETS = (
    _Target(
        requested_name="Finjasjön",
        registry_name="Finjasjön",
        latitude=56.133926,
        longitude=13.703841,
        target_class="registered_lake",
        lake_decision="include_lake_review",
        decision_reason="Named project lake resolved to one official SVAR lake.",
        coordinate_source="project brief coordinate; official registry identity published separately",
    ),
    _Target(
        requested_name="Östra Ringsjön",
        registry_name="Östra Ringsjön",
        latitude=55.872216,
        longitude=13.536269,
        target_class="registered_lake",
        lake_decision="include_lake_review",
        decision_reason="Named project lake resolved to one official SVAR lake.",
        coordinate_source="project brief coordinate; official registry identity published separately",
    ),
    _Target(
        requested_name="Havgårdssjön",
        registry_name="Havgårdssjön",
        latitude=55.485801,
        longitude=13.354724,
        target_class="registered_lake",
        lake_decision="include_lake_review",
        decision_reason="Named project lake resolved to one official SVAR lake.",
        coordinate_source="project brief coordinate; official registry identity published separately",
    ),
    _Target(
        requested_name="Bjäresjösjön",
        registry_name="Bjäresjö",
        latitude=55.45927,
        longitude=13.751909,
        target_class="registered_lake",
        lake_decision="include_lake_review",
        decision_reason=(
            "Project name Bjäresjösjön resolved to the official SVAR water-surface "
            "name Bjäresjö."
        ),
        coordinate_source="project brief coordinate; official registry identity published separately",
    ),
    _Target(
        requested_name="Gullåkra",
        registry_name="",
        latitude=55.656945,
        longitude=13.210916,
        target_class="archaeological_wetland_context",
        lake_decision="exclude_lake_ranking_include_context",
        decision_reason=(
            "The named place is Gullåkra mosse in the archaeological report and has "
            "no unique SMHI SVAR lake match. It belongs in wetland and archaeology "
            "context, not the lake-sampling ranking."
        ),
        coordinate_source=(
            "Höje å report project coordinate converted from RT90 2.5 gon V; "
            "project-area precision"
        ),
    ),
    _Target(
        requested_name="Vesums mossar",
        registry_name="",
        latitude=55.659062,
        longitude=13.213319,
        target_class="archaeological_wetland_context",
        lake_decision="exclude_lake_ranking_include_context",
        decision_reason=(
            "The named place is Vesums mosse in the archaeological report and has "
            "no unique SMHI SVAR lake match. It belongs in wetland and archaeology "
            "context, not the lake-sampling ranking."
        ),
        coordinate_source=(
            "Höje å report project coordinate converted from RT90 2.5 gon V; "
            "project-area precision"
        ),
    ),
)


def build_sweden_land_use_synthesis(
    *,
    context_root: Path,
    lake_report,
    human_localities,
    animal_localities,
) -> dict[str, object]:
    """Join modeled land cover with time-compatible governed context near targets."""
    context_root = Path(context_root)
    landclim_features = _load_features(
        context_root
        / "landclim"
        / "normalized"
        / "nordic_reveals_temporal_grid_cells.geojson"
    )
    sead_features = _load_features(
        context_root / "sead" / "normalized" / "nordic_temporal_evidence.geojson"
    )
    lake_candidates = {
        assessment.candidate.lake_name: assessment
        for assessment in lake_report.assessments
    }
    target_rows = [
        _target_row(target, lake_candidates=lake_candidates) for target in _TARGETS
    ]
    rows = []
    for target in _TARGETS:
        target_landclim = _target_landclim_features(target, landclim_features)
        for feature in target_landclim:
            properties = feature["properties"]
            time_start_bp = int(properties["time_start_bp"])
            time_end_bp = int(properties["time_end_bp"])
            reconstruction = properties.get("reconstruction_values", {})
            land_cover = reconstruction.get("land_cover_types", {})
            plant_types = reconstruction.get("plant_functional_types", {})
            sead_context = _overlapping_geojson_context(
                target=target,
                features=sead_features,
                time_start_bp=time_start_bp,
                time_end_bp=time_end_bp,
            )
            human_context = _overlapping_human_context(
                target=target,
                localities=human_localities,
                time_start_bp=time_start_bp,
                time_end_bp=time_end_bp,
            )
            animal_context = _overlapping_animal_context(
                target=target,
                localities=animal_localities,
                time_start_bp=time_start_bp,
                time_end_bp=time_end_bp,
            )
            evergreen = _number(land_cover.get("Evergreen Trees"))
            summergreen = _number(land_cover.get("Summergreen Trees"))
            rows.append(
                {
                    "target_name": target.requested_name,
                    "target_class": target.target_class,
                    "lake_decision": target.lake_decision,
                    "latitude": target.latitude,
                    "longitude": target.longitude,
                    "landclim_record_id": properties.get("record_id", ""),
                    "landclim_grid_record_id": properties.get(
                        "parent_grid_record_id", ""
                    ),
                    "time_start_bp": time_start_bp,
                    "time_end_bp": time_end_bp,
                    "time_mean_bp": properties.get("time_mean_bp"),
                    "time_label": properties.get("time_label", ""),
                    "forest_cover": round(evergreen + summergreen, 6),
                    "evergreen_tree_cover": evergreen,
                    "summergreen_tree_cover": summergreen,
                    "open_grass_herb_cover": _number(land_cover.get("Open Grass/Herb")),
                    "agricultural_land_cover": _number(plant_types.get("AL")),
                    "grassland_cover": _number(plant_types.get("GL")),
                    "cereal_specific_measure": None,
                    "cereal_interpretation_posture": (
                        "not_available; AL is agricultural land and must not be "
                        "relabeled as cereal"
                    ),
                    "sead_temporal_record_count_20km": sead_context["record_count"],
                    "sead_site_count_20km": sead_context["locality_count"],
                    "human_adna_locality_count_20km": human_context["locality_count"],
                    "human_adna_sample_count_20km": human_context["sample_count"],
                    "animal_adna_locality_count_20km": animal_context["locality_count"],
                    "animal_adna_sample_count_20km": animal_context["sample_count"],
                    "cross_proxy_posture": _cross_proxy_posture(
                        sead_count=sead_context["record_count"],
                        human_count=human_context["locality_count"],
                        animal_count=animal_context["locality_count"],
                    ),
                }
            )
    rows.sort(key=lambda row: (row["target_name"], row["time_start_bp"]))
    return {
        "schema_version": "sweden-land-use-synthesis.v1",
        "country": "Sweden",
        "landclim_dataset_id": _LANDCLIM_DATASET_ID,
        "landclim_source_url": "https://doi.org/10.1594/PANGAEA.937075",
        "context_radius_km": _CONTEXT_RADIUS_KM,
        "target_count": len(target_rows),
        "time_row_count": len(rows),
        "methodology": {
            "land_cover_rule": (
                "Forest is evergreen plus summergreen tree cover; open land is the "
                "published Open Grass/Herb value; agricultural land is PFT code AL."
            ),
            "cereal_rule": (
                "No cereal-specific series is present in this governed grid. AL remains "
                "agricultural land and is never relabeled as cereal."
            ),
            "temporal_join_rule": (
                "SEAD and aDNA context counts require both spatial proximity within 20 "
                "km and numeric interval overlap with the published LandClim window."
            ),
            "interpretation_rule": (
                "Cross-proxy alignment is descriptive context. It does not identify a "
                "cause, migration route, farming event, or viable coring location."
            ),
        },
        "target_decisions": target_rows,
        "rows": rows,
    }


def write_sweden_land_use_synthesis_json(
    path: Path, payload: dict[str, object]
) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_sweden_land_use_synthesis_csv(path: Path, payload: dict[str, object]) -> None:
    import csv

    rows = payload["rows"]
    fieldnames = tuple(rows[0]) if rows else ()
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def render_sweden_land_use_synthesis_markdown(payload: dict[str, object]) -> str:
    target_rows = "\n".join(
        f"| {row['requested_name']} | {row['target_class']} | {row['lake_decision']} | "
        f"{row['registry_id'] or 'not_applicable'} | {row['lake_area_km2'] if row['lake_area_km2'] is not None else 'not_applicable'} | "
        f"{row['decision_reason']} |"
        for row in payload["target_decisions"]
    )
    recent_rows = sorted(
        (row for row in payload["rows"] if int(row["time_start_bp"]) <= 700),
        key=lambda row: (row["target_name"], row["time_start_bp"]),
    )
    synthesis_rows = "\n".join(
        f"| {row['target_name']} | {row['time_label']} | {row['forest_cover']:.3f} | "
        f"{row['open_grass_herb_cover']:.3f} | {row['agricultural_land_cover']:.3f} | "
        f"{row['sead_site_count_20km']} | {row['human_adna_locality_count_20km']} | "
        f"{row['animal_adna_locality_count_20km']} | {row['cross_proxy_posture']} |"
        for row in recent_rows
    )
    methodology = payload["methodology"]
    return f"""# Southern Sweden temporal land-use synthesis

This surface joins published LandClim time windows to temporally compatible
archaeology and ancient-DNA context around six named southern Sweden targets.
It also makes the lake inclusion decision explicit instead of silently dropping
wetlands or treating every named place as a coring lake.

## Governed Target Decisions

| Requested target | Class | Decision | SVAR ID | Area km² | Reason |
| --- | --- | --- | --- | ---: | --- |
{target_rows}

Gullåkra and Vesums mossar remain in this synthesis because the Höje å
archaeological report documents them as wetland project areas with archaeological
context. They are excluded only from the lake-sampling ranking.

## Reading The Joined Evidence

- {methodology["land_cover_rule"]}
- {methodology["cereal_rule"]}
- {methodology["temporal_join_rule"]}
- {methodology["interpretation_rule"]}

## Recent And Late-Holocene Windows

| Target | Window | Forest | Open grass/herb | Agricultural land | SEAD sites | Human aDNA localities | Animal aDNA localities | Posture |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{synthesis_rows}

The machine-readable JSON and CSV retain every published window, not only the
recent subset shown here.
"""


def _target_row(target: _Target, *, lake_candidates) -> dict[str, object]:
    assessment = lake_candidates.get(target.registry_name)
    candidate = assessment.candidate if assessment is not None else None
    return {
        "requested_name": target.requested_name,
        "registry_name": target.registry_name,
        "target_class": target.target_class,
        "lake_decision": target.lake_decision,
        "decision_reason": target.decision_reason,
        "latitude": target.latitude,
        "longitude": target.longitude,
        "coordinate_source": target.coordinate_source,
        "registry_id": candidate.lake_registry_id if candidate is not None else "",
        "lake_area_km2": candidate.lake_area_km2 if candidate is not None else None,
        "lake_rank": assessment.aggregate_rank if assessment is not None else None,
        "sampling_readiness_posture": (
            candidate.lake_sampling_readiness_posture
            if candidate is not None
            else "not_applicable"
        ),
        "source_url": (
            candidate.representative_source_url
            if candidate is not None
            else _HOJEA_REPORT_URL
        ),
    }


def _load_features(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        feature for feature in payload.get("features", []) if isinstance(feature, dict)
    ]


def _target_landclim_features(
    target: _Target, features: list[dict[str, object]]
) -> list[dict[str, object]]:
    selected = []
    for feature in features:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        if properties.get("dataset_id") != _LANDCLIM_DATASET_ID:
            continue
        if _polygon_contains(
            geometry, longitude=target.longitude, latitude=target.latitude
        ):
            selected.append(feature)
    if not selected:
        raise ValueError(
            f"No LandClim {_LANDCLIM_DATASET_ID} grid covers {target.requested_name}"
        )
    selected.sort(key=lambda feature: int(feature["properties"]["time_start_bp"]))
    return selected


def _polygon_contains(geometry, *, longitude: float, latitude: float) -> bool:
    coordinates = geometry.get("coordinates", [])
    if geometry.get("type") != "Polygon" or not coordinates:
        return False
    ring = coordinates[0]
    longitudes = [float(point[0]) for point in ring]
    latitudes = [float(point[1]) for point in ring]
    return min(longitudes) <= longitude <= max(longitudes) and min(
        latitudes
    ) <= latitude <= max(latitudes)


def _overlapping_geojson_context(
    *, target: _Target, features, time_start_bp: int, time_end_bp: int
) -> dict[str, int]:
    records = []
    localities = set()
    for feature in features:
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        coordinates = geometry.get("coordinates", [])
        if geometry.get("type") != "Point" or len(coordinates) < 2:
            continue
        if not _within_radius(
            target, latitude=float(coordinates[1]), longitude=float(coordinates[0])
        ):
            continue
        if not _intervals_overlap(
            time_start_bp,
            time_end_bp,
            properties.get("time_start_bp"),
            properties.get("time_end_bp"),
        ):
            continue
        records.append(feature)
        localities.add(str(properties.get("source_url", "")))
    return {"record_count": len(records), "locality_count": len(localities)}


def _overlapping_human_context(
    *, target: _Target, localities, time_start_bp: int, time_end_bp: int
) -> dict[str, int]:
    matched = []
    for locality in localities:
        coordinates = locality.coordinates
        chronology = locality.chronology
        if not _within_radius(
            target,
            latitude=coordinates.latitude,
            longitude=coordinates.longitude,
        ):
            continue
        if _intervals_overlap(
            time_start_bp,
            time_end_bp,
            chronology.time_start_bp,
            chronology.time_end_bp,
        ):
            matched.append(locality)
    return {
        "locality_count": len(matched),
        "sample_count": sum(locality.sample_count for locality in matched),
    }


def _overlapping_animal_context(
    *, target: _Target, localities, time_start_bp: int, time_end_bp: int
) -> dict[str, int]:
    matched = []
    for locality in localities:
        chronology = locality.get("chronology", {})
        if not _within_radius(
            target,
            latitude=_number(locality.get("latitude")),
            longitude=_number(locality.get("longitude")),
        ):
            continue
        if _intervals_overlap(
            time_start_bp,
            time_end_bp,
            chronology.get("time_start_bp"),
            chronology.get("time_end_bp"),
        ):
            matched.append(locality)
    return {
        "locality_count": len(matched),
        "sample_count": sum(
            int(locality.get("sample_count", 0)) for locality in matched
        ),
    }


def _within_radius(target: _Target, *, latitude: float, longitude: float) -> bool:
    return (
        haversine_km(
            latitude_a=target.latitude,
            longitude_a=target.longitude,
            latitude_b=latitude,
            longitude_b=longitude,
        )
        <= _CONTEXT_RADIUS_KM
    )


def _intervals_overlap(start_a, end_a, start_b, end_b) -> bool:
    if not all(
        isinstance(value, (int, float)) for value in (start_a, end_a, start_b, end_b)
    ):
        return False
    low_a, high_a = sorted((float(start_a), float(end_a)))
    low_b, high_b = sorted((float(start_b), float(end_b)))
    return max(low_a, low_b) <= min(high_a, high_b)


def _cross_proxy_posture(
    *, sead_count: int, human_count: int, animal_count: int
) -> str:
    if sead_count and human_count and animal_count:
        return "pollen_archaeology_human_animal_context"
    if sead_count and human_count:
        return "pollen_archaeology_human_context"
    if sead_count and animal_count:
        return "pollen_archaeology_animal_context"
    if sead_count:
        return "pollen_archaeology_context"
    if human_count or animal_count:
        return "pollen_adna_context"
    return "pollen_model_only"


def _number(value) -> float:
    return round(float(value), 6) if isinstance(value, (int, float)) else 0.0
