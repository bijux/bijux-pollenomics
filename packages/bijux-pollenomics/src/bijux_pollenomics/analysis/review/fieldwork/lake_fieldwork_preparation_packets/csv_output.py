"""Stable CSV serialization for lake preparation rows."""

from __future__ import annotations

from collections.abc import Callable
import csv
from pathlib import Path
from types import ModuleType
from typing import Any

from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceRichnessReport,
)

FIELDNAMES = (
    "fieldwork_rank",
    "fieldwork_shortlist_score",
    "aggregate_rank",
    "lake_label",
    "latitude",
    "longitude",
    "aggregate_score",
    "preparation_posture",
    "identity_posture",
    "sampling_posture",
    "sampling_fit",
    "sampling_readiness_posture",
    "sampling_missing_inputs",
    "lake_area_km2",
    "human_context_posture",
    "scenario_consistency_posture",
    "sead_context_posture",
    "palaeopen_alignment_posture",
    "scenario_top20_presence_count",
    "scenario_best_rank",
    "scenario_mean_rank",
    "rank_10km",
    "rank_20km",
    "rank_30km",
    "rank_40km",
    "rank_50km",
    "google_maps_url",
    "representative_source_record",
    "lake_registry_id",
    "lake_name_status",
    "coordinate_resolution_method",
    "direct_pollen_source_count",
    "time_aware_direct_pollen_records",
    "evidence_families_20km",
    "sead_sites_20km",
    "human_localities_10km",
    "human_samples_10km",
    "human_localities_20km",
    "human_samples_20km",
    "domesticated_animal_localities_50km",
    "ambiguity_flags",
    "required_actions",
)


def write_csv(
    path: Path,
    report: LakeEvidenceRichnessReport,
    *,
    top_n: int,
    build_payload: Callable[..., dict[str, Any]],
    csv_module: ModuleType = csv,
) -> None:
    payload = build_payload(report, top_n=top_n)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv_module.DictWriter(
            handle, fieldnames=FIELDNAMES, lineterminator="\n"
        )
        writer.writeheader()
        for row in payload["rows"]:
            writer.writerow(
                {
                    "fieldwork_rank": row["fieldwork_rank"],
                    "fieldwork_shortlist_score": row["fieldwork_shortlist_score"],
                    "aggregate_rank": row["aggregate_rank"],
                    "lake_label": row["lake_label"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "aggregate_score": row["aggregate_score"],
                    "preparation_posture": row["preparation_posture"],
                    "identity_posture": row["identity_posture"],
                    "sampling_posture": row["sampling_posture"],
                    "sampling_fit": row["sampling_fit"],
                    "sampling_readiness_posture": row["sampling_readiness_posture"],
                    "sampling_missing_inputs": "; ".join(
                        row["sampling_missing_inputs"]
                    ),
                    "lake_area_km2": row["lake_area_km2"],
                    "human_context_posture": row["human_context_posture"],
                    "scenario_consistency_posture": row["scenario_consistency_posture"],
                    "sead_context_posture": row["sead_context_posture"],
                    "palaeopen_alignment_posture": row["palaeopen_alignment_posture"],
                    "scenario_top20_presence_count": row[
                        "scenario_top20_presence_count"
                    ],
                    "scenario_best_rank": row["scenario_best_rank"],
                    "scenario_mean_rank": row["scenario_mean_rank"],
                    "rank_10km": row["scenario_ranks"]["10km"],
                    "rank_20km": row["scenario_ranks"]["20km"],
                    "rank_30km": row["scenario_ranks"]["30km"],
                    "rank_40km": row["scenario_ranks"]["40km"],
                    "rank_50km": row["scenario_ranks"]["50km"],
                    "google_maps_url": row["google_maps_url"],
                    "representative_source_record": row["representative_source_record"],
                    "lake_registry_id": row["lake_registry_id"],
                    "lake_name_status": row["lake_name_status"],
                    "coordinate_resolution_method": row["coordinate_resolution_method"],
                    "direct_pollen_source_count": row["direct_pollen_source_count"],
                    "time_aware_direct_pollen_records": row[
                        "time_aware_direct_pollen_records"
                    ],
                    "evidence_families_20km": row["evidence_families_20km"],
                    "sead_sites_20km": row["sead_sites_20km"],
                    "human_localities_10km": row["human_localities_10km"],
                    "human_samples_10km": row["human_samples_10km"],
                    "human_localities_20km": row["human_localities_20km"],
                    "human_samples_20km": row["human_samples_20km"],
                    "domesticated_animal_localities_50km": row[
                        "domesticated_animal_localities_50km"
                    ],
                    "ambiguity_flags": "; ".join(row["ambiguity_flags"]),
                    "required_actions": "; ".join(row["required_actions"]),
                }
            )
