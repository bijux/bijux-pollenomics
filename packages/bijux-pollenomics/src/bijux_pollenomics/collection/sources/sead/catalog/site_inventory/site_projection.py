"""Apply linked SEAD inventory evidence and coverage to site rows."""

from __future__ import annotations

from dataclasses import dataclass

from .bibliography_projection import SeadBibliographyProjection
from .chronology_projection import SeadChronologyProjection
from .source_data.lookups import SeadLookupIndex
from .source_data.relations import SeadRelationIndex
from .values import parse_required_int
from .temporal import (
    _normalized_period_labels,
    _uncertainty_labels,
    merge_sead_intervals,
)


@dataclass(frozen=True, slots=True)
class SeadSiteCoverage:
    numeric_interval_site_ids: set[int]
    contextual_interval_site_ids: set[int]


def apply_site_inventory_projection(
    rows: list[dict[str, object]],
    *,
    relations: SeadRelationIndex,
    lookups: SeadLookupIndex,
    chronology: SeadChronologyProjection,
    bibliography: SeadBibliographyProjection,
) -> SeadSiteCoverage:
    for row in rows:
        site_id = parse_required_int(row.get("site_id"))
        dataset_names = [
            name
            for name in sorted(
                {
                    lookups.dataset_name_by_id.get(dataset_id, "")
                    for dataset_id in relations.datasets_by_site.get(site_id, set())
                }
            )
            if name
        ]
        row["sample_group_count"] = len(
            relations.sample_groups_by_site.get(site_id, set())
        )
        row["physical_sample_count"] = len(
            relations.physical_samples_by_site.get(site_id, set())
        )
        row["analysis_entity_count"] = len(
            relations.analysis_entities_by_site.get(site_id, set())
        )
        row["dataset_count"] = len(relations.datasets_by_site.get(site_id, set()))
        row["dataset_names"] = dataset_names
        row["site_reference_count"] = len(
            bibliography.reference_ids_by_site.get(site_id, set())
        )
        row["reference_count"] = len(
            bibliography.bibliography_rows_by_site.get(site_id, [])
        )
        row["relative_date_count"] = len(
            chronology.relative_date_ids_by_site.get(site_id, set())
        )
        row["dating_range_count"] = chronology.dating_range_counts_by_site.get(
            site_id, 0
        )
        row["analysis_entity_age_count"] = len(
            chronology.analysis_entity_age_rows_by_site.get(site_id, [])
        )
        row["geochronology_count"] = len(
            chronology.geochronology_rows_by_site.get(site_id, [])
        )
        row["dendro_date_count"] = len(
            chronology.dendro_date_rows_by_site.get(site_id, [])
        )
        numeric_time_interval = merge_sead_intervals(
            chronology.numeric_dating_intervals_by_site.get(site_id, [])
        )
        contextual_time_interval = merge_sead_intervals(
            chronology.contextual_period_intervals_by_site.get(site_id, [])
        )
        time_interval = numeric_time_interval or contextual_time_interval
        row["time_start_bp"] = time_interval[0] if time_interval is not None else None
        row["time_end_bp"] = time_interval[1] if time_interval is not None else None
        row["numeric_time_start_bp"] = (
            numeric_time_interval[0] if numeric_time_interval is not None else None
        )
        row["numeric_time_end_bp"] = (
            numeric_time_interval[1] if numeric_time_interval is not None else None
        )
        row["contextual_time_start_bp"] = (
            contextual_time_interval[0]
            if contextual_time_interval is not None
            else None
        )
        row["contextual_time_end_bp"] = (
            contextual_time_interval[1]
            if contextual_time_interval is not None
            else None
        )
        row["relative_period_rows"] = chronology.relative_period_rows_by_site.get(
            site_id, []
        )
        row["dating_range_rows"] = chronology.dating_range_rows_by_site.get(site_id, [])
        row["analysis_entity_age_rows"] = (
            chronology.analysis_entity_age_rows_by_site.get(site_id, [])
        )
        row["geochronology_rows"] = chronology.geochronology_rows_by_site.get(
            site_id, []
        )
        row["dendro_date_rows"] = chronology.dendro_date_rows_by_site.get(site_id, [])
        row["bibliography_rows"] = bibliography.bibliography_rows_by_site.get(
            site_id, []
        )
        row["temporal_summary"] = {
            "relative_period_count": len(
                chronology.relative_period_rows_by_site.get(site_id, [])
            ),
            "dating_range_count": chronology.dating_range_counts_by_site.get(
                site_id, 0
            ),
            "analysis_entity_age_count": row["analysis_entity_age_count"],
            "geochronology_count": row["geochronology_count"],
            "dendro_date_count": row["dendro_date_count"],
            "bibliography_count": len(
                bibliography.bibliography_rows_by_site.get(site_id, [])
            ),
            "time_start_bp": row["time_start_bp"],
            "time_end_bp": row["time_end_bp"],
            "numeric_time_start_bp": row["numeric_time_start_bp"],
            "numeric_time_end_bp": row["numeric_time_end_bp"],
            "contextual_time_start_bp": row["contextual_time_start_bp"],
            "contextual_time_end_bp": row["contextual_time_end_bp"],
            "normalized_period_labels": _normalized_period_labels(
                chronology.relative_period_rows_by_site.get(site_id, [])
            ),
            "uncertainty_labels": _uncertainty_labels(
                chronology.relative_period_rows_by_site.get(site_id, []),
                chronology.dating_range_rows_by_site.get(site_id, []),
                chronology.analysis_entity_age_rows_by_site.get(site_id, []),
                chronology.geochronology_rows_by_site.get(site_id, []),
                chronology.dendro_date_rows_by_site.get(site_id, []),
            ),
        }
    numeric_interval_site_ids = {
        site_id
        for site_id, intervals in chronology.numeric_dating_intervals_by_site.items()
        if intervals
    }
    contextual_interval_site_ids = {
        site_id
        for site_id, intervals in chronology.contextual_period_intervals_by_site.items()
        if intervals
    }
    return SeadSiteCoverage(
        numeric_interval_site_ids=numeric_interval_site_ids,
        contextual_interval_site_ids=contextual_interval_site_ids,
    )


__all__ = ["SeadSiteCoverage", "apply_site_inventory_projection"]
