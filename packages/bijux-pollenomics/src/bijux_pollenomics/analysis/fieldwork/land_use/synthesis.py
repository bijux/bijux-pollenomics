from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from .models import _Target as Target


def build_synthesis(
    *,
    context_root: Path,
    lake_report: Any,
    human_localities: Iterable[Any],
    animal_localities: Iterable[Any],
    load_features: Callable[[Path], list[dict[str, object]]],
    synthesis_targets: Callable[[Any], tuple[Target, ...]],
    target_landclim_features: Callable[
        [Target, list[dict[str, object]]], list[dict[str, object]]
    ],
    target_row: Callable[..., dict[str, object]],
    overlapping_geojson_context: Callable[..., dict[str, int]],
    overlapping_human_context: Callable[..., dict[str, int]],
    overlapping_animal_context: Callable[..., dict[str, int]],
    number: Callable[[Any], float],
    cross_proxy_posture: Callable[..., str],
    dataset_id: str,
    context_radius_km: int,
) -> dict[str, object]:
    landclim_features = load_features(
        context_root
        / "landclim"
        / "normalized"
        / "nordic_reveals_temporal_grid_cells.geojson"
    )
    sead_features = load_features(
        context_root / "sead" / "normalized" / "nordic_temporal_evidence.geojson"
    )
    lake_candidates = tuple(lake_report.assessments)
    targets = synthesis_targets(lake_report)
    landclim_by_target = {
        target: target_landclim_features(target, landclim_features)
        for target in targets
    }
    target_rows = [
        target_row(
            target,
            lake_candidates=lake_candidates,
            landclim_features=landclim_by_target[target],
        )
        for target in targets
    ]
    rows = []
    for target in targets:
        for feature in landclim_by_target[target]:
            properties: Any = feature["properties"]
            time_start_bp = int(properties["time_start_bp"])
            time_end_bp = int(properties["time_end_bp"])
            reconstruction = properties.get("reconstruction_values", {})
            sead_context = overlapping_geojson_context(
                target=target,
                features=sead_features,
                time_start_bp=time_start_bp,
                time_end_bp=time_end_bp,
            )
            human_context = overlapping_human_context(
                target=target,
                localities=human_localities,
                time_start_bp=time_start_bp,
                time_end_bp=time_end_bp,
            )
            animal_context = overlapping_animal_context(
                target=target,
                localities=animal_localities,
                time_start_bp=time_start_bp,
                time_end_bp=time_end_bp,
            )
            evergreen = number(reconstruction.get("ET"))
            summergreen = number(reconstruction.get("ST"))
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
                    "open_land_cover": number(reconstruction.get("OL")),
                    "agricultural_land_cover": number(reconstruction.get("AL")),
                    "grassland_cover": number(reconstruction.get("GL")),
                    "cereal_type_pollen_cover": number(
                        reconstruction.get("Cerealia.t")
                    ),
                    "rye_pollen_cover": number(reconstruction.get("Secale")),
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
                    "cross_proxy_posture": cross_proxy_posture(
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
        "landclim_dataset_id": dataset_id,
        "landclim_source_url": "https://doi.org/10.1594/PANGAEA.937075",
        "context_radius_km": context_radius_km,
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
