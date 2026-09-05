from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from ...core import haversine_km
from ...core.temporal_semantics import (
    InvalidBpIntervalError,
    canonical_bp_interval,
    closed_bp_intervals_overlap,
)

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


_GOVERNED_NAMED_TARGETS = (
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
    lake_candidates = tuple(lake_report.assessments)
    targets = _synthesis_targets(lake_report)
    landclim_by_target = {
        target: _target_landclim_features(target, landclim_features)
        for target in targets
    }
    target_rows = [
        _target_row(
            target,
            lake_candidates=lake_candidates,
            landclim_features=landclim_by_target[target],
        )
        for target in targets
    ]
    rows = []
    for target in targets:
        target_landclim = landclim_by_target[target]
        for feature in target_landclim:
            properties = feature["properties"]
            time_start_bp = int(properties["time_start_bp"])
            time_end_bp = int(properties["time_end_bp"])
            reconstruction = properties.get("reconstruction_values", {})
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
            evergreen = _number(reconstruction.get("ET"))
            summergreen = _number(reconstruction.get("ST"))
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
                    "open_land_cover": _number(reconstruction.get("OL")),
                    "agricultural_land_cover": _number(reconstruction.get("AL")),
                    "grassland_cover": _number(reconstruction.get("GL")),
                    "cereal_type_pollen_cover": _number(
                        reconstruction.get("Cerealia.t")
                    ),
                    "rye_pollen_cover": _number(reconstruction.get("Secale")),
                    "cereal_interpretation_posture": (
                        "Cerealia.t and Secale are modeled pollen-cover estimates; "
                        "they are not observed crop acreage or proof of cultivation "
                        "at the target"
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
        "landclim_covered_target_count": sum(
            row["landclim_coverage_posture"] == "covered_by_governed_grid"
            for row in target_rows
        ),
        "landclim_uncovered_target_count": sum(
            row["landclim_coverage_posture"] == "outside_governed_grid"
            for row in target_rows
        ),
        "time_row_count": len(rows),
        "methodology": {
            "land_cover_rule": (
                "Forest is published ET plus ST cover; open land is OL; grassland is "
                "GL; and agricultural land is AL. Values are percentage cover."
            ),
            "cereal_rule": (
                "Cerealia.t and Secale retain their published modeled pollen-cover "
                "values. They are not observed crop acreage or proof of cultivation "
                "at the named target."
            ),
            "temporal_join_rule": (
                "SEAD and aDNA context counts require both spatial proximity within 20 "
                "km and numeric interval overlap with the published LandClim window."
            ),
            "target_coverage_rule": (
                "Every ranked SVAR lake is evaluated. Named archaeological wetland "
                "contexts remain alongside the lake set. Targets outside the "
                "governed LandClim grid retain an explicit decision row and receive "
                "no fabricated temporal values."
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
        f"{row['landclim_coverage_posture']} | {row['landclim_window_count']} | "
        f"{row['decision_reason']} |"
        for row in payload["target_decisions"]
    )
    most_recent_rows = {}
    for row in payload["rows"]:
        target_name = str(row["target_name"])
        if target_name not in most_recent_rows or int(row["time_start_bp"]) < int(
            most_recent_rows[target_name]["time_start_bp"]
        ):
            most_recent_rows[target_name] = row
    recent_rows = sorted(most_recent_rows.values(), key=lambda row: row["target_name"])
    synthesis_rows = "\n".join(
        f"| {row['target_name']} | {row['time_label']} | {row['forest_cover']:.3f} | "
        f"{row['open_land_cover']:.3f} | {row['agricultural_land_cover']:.3f} | "
        f"{row['cereal_type_pollen_cover']:.3f} | {row['rye_pollen_cover']:.3f} | "
        f"{row['sead_site_count_20km']} | {row['human_adna_locality_count_20km']} | "
        f"{row['animal_adna_locality_count_20km']} | {row['cross_proxy_posture']} |"
        for row in recent_rows
    )
    methodology = payload["methodology"]
    return f"""# Southern Sweden temporal land-use synthesis

This surface joins published LandClim time windows to temporally compatible
archaeology and ancient-DNA context around the complete ranked Sweden lake set
and the governed southern Sweden wetland contexts. It makes both modeled-grid
coverage and lake inclusion explicit instead of silently dropping targets.

The governed LandClim grid covers **{payload["landclim_covered_target_count"]} of
{payload["target_count"]} targets**. The remaining
**{payload["landclim_uncovered_target_count"]} targets** stay visible below with
zero modeled windows rather than receiving inferred values.

## Governed Target Decisions

| Requested target | Class | Decision | SVAR ID | Area km² | LandClim coverage | Windows | Reason |
| --- | --- | --- | --- | ---: | --- | ---: | --- |
{target_rows}

Gullåkra and Vesums mossar remain in this synthesis because the Höje å
archaeological report documents them as wetland project areas with archaeological
context. They are excluded only from the lake-sampling ranking.

## Reading The Joined Evidence

- {methodology["land_cover_rule"]}
- {methodology["cereal_rule"]}
- {methodology["temporal_join_rule"]}
- {methodology["target_coverage_rule"]}
- {methodology["interpretation_rule"]}

## Most Recent Modeled Window

| Target | Window | Forest | Open land | Agricultural land | Cerealia-type pollen | Rye pollen | SEAD sites | Human aDNA localities | Animal aDNA localities | Posture |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{synthesis_rows}

This compact table shows one recent modeled window per covered target. The
machine-readable JSON and CSV retain all **{payload["time_row_count"]}** published
target-window rows for time navigation and analysis.
"""


def _synthesis_targets(lake_report) -> tuple[_Target, ...]:
    named_lake_targets = {
        target.registry_name: target
        for target in _GOVERNED_NAMED_TARGETS
        if target.registry_name
    }
    ranked_targets = []
    for assessment in lake_report.assessments:
        candidate = assessment.candidate
        governed_target = named_lake_targets.get(candidate.lake_name)
        if governed_target is not None:
            ranked_targets.append(governed_target)
            continue
        ranked_targets.append(
            _Target(
                requested_name=candidate.lake_name,
                registry_name=candidate.lake_name,
                latitude=candidate.latitude,
                longitude=candidate.longitude,
                target_class="registered_lake",
                lake_decision="include_lake_review",
                decision_reason=(
                    "Ranked SVAR lake retained in the time-aware synthesis so the "
                    "published ranking and temporal comparison have the same scope."
                ),
                coordinate_source="official SVAR lake representative point",
            )
        )
    context_targets = [
        target
        for target in _GOVERNED_NAMED_TARGETS
        if target.target_class == "archaeological_wetland_context"
    ]
    return (*ranked_targets, *context_targets)


def _target_row(
    target: _Target,
    *,
    lake_candidates,
    landclim_features: list[dict[str, object]],
) -> dict[str, object]:
    matching_assessments = tuple(
        assessment
        for assessment in lake_candidates
        if assessment.candidate.lake_name == target.registry_name
    )
    assessment = min(
        matching_assessments,
        key=lambda item: haversine_km(
            latitude_a=target.latitude,
            longitude_a=target.longitude,
            latitude_b=item.candidate.latitude,
            longitude_b=item.candidate.longitude,
        ),
        default=None,
    )
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
        "landclim_coverage_posture": (
            "covered_by_governed_grid" if landclim_features else "outside_governed_grid"
        ),
        "landclim_window_count": len(landclim_features),
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


def _intervals_overlap(
    start_a: float | int | None,
    end_a: float | int | None,
    start_b: float | int | None,
    end_b: float | int | None,
) -> bool:
    try:
        left = canonical_bp_interval(start_a, end_a)
        right = canonical_bp_interval(start_b, end_b)
    except InvalidBpIntervalError:
        return False
    if left is None or right is None:
        return False
    return closed_bp_intervals_overlap(left, right)


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
