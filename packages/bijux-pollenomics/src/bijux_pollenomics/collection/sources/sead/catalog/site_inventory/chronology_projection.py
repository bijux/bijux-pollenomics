"""Project SEAD chronology claims and intervals onto their owning sites."""

from __future__ import annotations

from dataclasses import dataclass

from bijux_pollenomics.core.bp_time import normalize_bp_interval

from .chronology_records import (
    _analysis_entity_age_interval,
    _analysis_entity_relation_identity,
    _build_analysis_entity_age_row,
    _build_dating_range_row,
    _build_dendro_date_row,
    _build_geochronology_row,
    _build_relative_period_row,
    _dendro_date_interval,
    _geochronology_interval,
)
from .source_data.lookups import SeadLookupIndex
from .source_data.relations import SeadRelationIndex
from .source_data.source_tables import SeadInventorySourceRows
from .temporal import (
    _relative_interval_from_range,
    sead_dating_interval,
    sead_interval_is_canonical,
)
from .values import parse_optional_int, parse_required_int

Row = dict[str, object]


@dataclass(frozen=True, slots=True)
class SeadChronologyProjection:
    relative_date_ids_by_site: dict[int, set[int]]
    site_ids_by_relative_age_id: dict[int, set[int]]
    dating_range_counts_by_site: dict[int, int]
    numeric_dating_intervals_by_site: dict[int, list[tuple[int, int]]]
    contextual_period_intervals_by_site: dict[int, list[tuple[int, int]]]
    relative_period_rows_by_site: dict[int, list[Row]]
    dating_range_rows_by_site: dict[int, list[Row]]
    analysis_entity_age_rows_by_site: dict[int, list[Row]]
    geochronology_rows_by_site: dict[int, list[Row]]
    dendro_date_rows_by_site: dict[int, list[Row]]


def project_site_chronology(
    source: SeadInventorySourceRows,
    relations: SeadRelationIndex,
    lookups: SeadLookupIndex,
) -> SeadChronologyProjection:
    relative_date_ids_by_site: dict[int, set[int]] = {}
    site_ids_by_relative_age_id: dict[int, set[int]] = {}
    dating_range_counts_by_site: dict[int, int] = {}
    numeric_dating_intervals_by_site: dict[int, list[tuple[int, int]]] = {}
    contextual_period_intervals_by_site: dict[int, list[tuple[int, int]]] = {}
    relative_period_rows_by_site: dict[int, list[Row]] = {}
    dating_range_rows_by_site: dict[int, list[Row]] = {}
    analysis_entity_age_rows_by_site: dict[int, list[Row]] = {}
    geochronology_rows_by_site: dict[int, list[Row]] = {}
    dendro_date_rows_by_site: dict[int, list[Row]] = {}
    for entity_age in source.analysis_entity_ages:
        analysis_entity_id = parse_required_int(entity_age.get("analysis_entity_id"))
        site_id = relations.site_by_analysis_entity.get(analysis_entity_id, 0)
        interval = _analysis_entity_age_interval(entity_age)
        if not site_id:
            continue
        analysis_entity_age_rows_by_site.setdefault(site_id, []).append(
            _build_analysis_entity_age_row(
                entity_age,
                interval=interval,
                relation_identity=_analysis_entity_relation_identity(
                    analysis_entity_id,
                    physical_sample_id_by_analysis_entity_id=relations.physical_sample_by_analysis_entity,
                    sample_group_id_by_physical_sample_id=relations.sample_group_by_physical_sample,
                    dataset_id_by_analysis_entity_id=relations.dataset_by_analysis_entity,
                ),
            )
        )
        if interval is not None and sead_interval_is_canonical(interval):
            numeric_dating_intervals_by_site.setdefault(site_id, []).append(interval)
    for geochronology_row in source.geochronology_rows:
        analysis_entity_id = parse_required_int(
            geochronology_row.get("analysis_entity_id")
        )
        site_id = relations.site_by_analysis_entity.get(analysis_entity_id, 0)
        interval = _geochronology_interval(geochronology_row)
        if not site_id:
            continue
        geochronology_rows_by_site.setdefault(site_id, []).append(
            _build_geochronology_row(
                geochronology_row,
                interval=interval,
                uncertainty=lookups.uncertainty_by_id.get(
                    parse_required_int(geochronology_row.get("dating_uncertainty_id")),
                    {},
                ),
                relation_identity=_analysis_entity_relation_identity(
                    analysis_entity_id,
                    physical_sample_id_by_analysis_entity_id=relations.physical_sample_by_analysis_entity,
                    sample_group_id_by_physical_sample_id=relations.sample_group_by_physical_sample,
                    dataset_id_by_analysis_entity_id=relations.dataset_by_analysis_entity,
                ),
            )
        )
        if interval is not None and sead_interval_is_canonical(interval):
            numeric_dating_intervals_by_site.setdefault(site_id, []).append(interval)
    for dendro_date in source.dendro_dates:
        analysis_entity_id = parse_required_int(dendro_date.get("analysis_entity_id"))
        site_id = relations.site_by_analysis_entity.get(analysis_entity_id, 0)
        age_type = lookups.age_type_by_id.get(
            parse_required_int(dendro_date.get("age_type_id")), ""
        )
        interval = _dendro_date_interval(dendro_date, age_type=age_type)
        if not site_id:
            continue
        dendro_date_rows_by_site.setdefault(site_id, []).append(
            _build_dendro_date_row(
                dendro_date,
                age_type=age_type,
                interval=interval,
                uncertainty=lookups.uncertainty_by_id.get(
                    parse_required_int(dendro_date.get("dating_uncertainty_id")),
                    {},
                ),
                relation_identity=_analysis_entity_relation_identity(
                    analysis_entity_id,
                    physical_sample_id_by_analysis_entity_id=relations.physical_sample_by_analysis_entity,
                    sample_group_id_by_physical_sample_id=relations.sample_group_by_physical_sample,
                    dataset_id_by_analysis_entity_id=relations.dataset_by_analysis_entity,
                ),
            )
        )
        if interval is not None and sead_interval_is_canonical(interval):
            numeric_dating_intervals_by_site.setdefault(site_id, []).append(interval)
    for relative_date in source.relative_dates:
        analysis_entity_id = parse_required_int(relative_date.get("analysis_entity_id"))
        relative_date_id = parse_required_int(relative_date.get("relative_date_id"))
        site_id = relations.site_by_analysis_entity.get(analysis_entity_id, 0)
        if site_id and relative_date_id:
            relative_date_ids_by_site.setdefault(site_id, set()).add(relative_date_id)
            relative_age_id = parse_required_int(relative_date.get("relative_age_id"))
            if relative_age_id:
                site_ids_by_relative_age_id.setdefault(relative_age_id, set()).add(
                    site_id
                )
            relative_period_rows_by_site.setdefault(site_id, []).append(
                _build_relative_period_row(
                    relative_date,
                    site_id=site_id,
                    relative_age=lookups.relative_age_by_id.get(
                        parse_required_int(relative_date.get("relative_age_id")),
                        {},
                    ),
                    method=lookups.method_by_id.get(
                        parse_required_int(relative_date.get("method_id")),
                        {},
                    ),
                    uncertainty=lookups.uncertainty_by_id.get(
                        parse_required_int(relative_date.get("dating_uncertainty_id")),
                        {},
                    ),
                    relation_identity=_analysis_entity_relation_identity(
                        analysis_entity_id,
                        physical_sample_id_by_analysis_entity_id=relations.physical_sample_by_analysis_entity,
                        sample_group_id_by_physical_sample_id=relations.sample_group_by_physical_sample,
                        dataset_id_by_analysis_entity_id=relations.dataset_by_analysis_entity,
                    ),
                )
            )
    for dating_range in source.dating_ranges:
        analysis_value_id = parse_required_int(dating_range.get("analysis_value_id"))
        analysis_entity_id = relations.analysis_entity_by_analysis_value.get(
            analysis_value_id, 0
        )
        site_id = relations.site_by_analysis_entity.get(analysis_entity_id, 0)
        age_type = lookups.age_type_by_id.get(
            parse_required_int(dating_range.get("age_type_id")), ""
        )
        interval = sead_dating_interval(dating_range, age_type=age_type)
        if not site_id or interval is None:
            interval = _relative_interval_from_range(
                dating_range,
                age_type=age_type,
            )
        if site_id:
            dating_range_rows_by_site.setdefault(site_id, []).append(
                _build_dating_range_row(
                    dating_range,
                    age_type=age_type,
                    age_type_description=lookups.age_type_description_by_id.get(
                        parse_required_int(dating_range.get("age_type_id")), ""
                    ),
                    uncertainty=lookups.uncertainty_by_id.get(
                        parse_required_int(dating_range.get("dating_uncertainty_id")),
                        {},
                    ),
                    relation_identity=_analysis_entity_relation_identity(
                        analysis_entity_id,
                        physical_sample_id_by_analysis_entity_id=relations.physical_sample_by_analysis_entity,
                        sample_group_id_by_physical_sample_id=relations.sample_group_by_physical_sample,
                        dataset_id_by_analysis_entity_id=relations.dataset_by_analysis_entity,
                    ),
                )
            )
        if site_id and interval is not None and sead_interval_is_canonical(interval):
            numeric_dating_intervals_by_site.setdefault(site_id, []).append(interval)
        if site_id:
            dating_range_counts_by_site[site_id] = (
                dating_range_counts_by_site.get(site_id, 0) + 1
            )
    for relative_rows in relative_period_rows_by_site.values():
        for row in relative_rows:
            interval = normalize_bp_interval(
                parse_optional_int(row.get("time_start_bp")),
                parse_optional_int(row.get("time_end_bp")),
            )
            site_id = parse_required_int(row.get("site_id"))
            if (
                site_id
                and interval is not None
                and sead_interval_is_canonical(interval)
            ):
                contextual_period_intervals_by_site.setdefault(site_id, []).append(
                    interval
                )
    return SeadChronologyProjection(
        relative_date_ids_by_site=relative_date_ids_by_site,
        site_ids_by_relative_age_id=site_ids_by_relative_age_id,
        dating_range_counts_by_site=dating_range_counts_by_site,
        numeric_dating_intervals_by_site=numeric_dating_intervals_by_site,
        contextual_period_intervals_by_site=contextual_period_intervals_by_site,
        relative_period_rows_by_site=relative_period_rows_by_site,
        dating_range_rows_by_site=dating_range_rows_by_site,
        analysis_entity_age_rows_by_site=analysis_entity_age_rows_by_site,
        geochronology_rows_by_site=geochronology_rows_by_site,
        dendro_date_rows_by_site=dendro_date_rows_by_site,
    )


__all__ = ["SeadChronologyProjection", "project_site_chronology"]
