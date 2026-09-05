"""Index the source-key relationships that assign SEAD records to sites."""

from __future__ import annotations

from dataclasses import dataclass

from .source_tables import SeadInventorySourceRows
from .values import parse_optional_int, parse_required_int


@dataclass(frozen=True, slots=True)
class SeadRelationIndex:
    site_by_sample_group: dict[int, int]
    site_by_physical_sample: dict[int, int]
    sample_group_by_physical_sample: dict[int, int]
    physical_sample_by_analysis_entity: dict[int, int]
    dataset_by_analysis_entity: dict[int, int | None]
    analysis_entity_by_analysis_value: dict[int, int]
    site_by_analysis_entity: dict[int, int]
    sample_groups_by_site: dict[int, set[int]]
    physical_samples_by_site: dict[int, set[int]]
    analysis_entities_by_site: dict[int, set[int]]
    datasets_by_site: dict[int, set[int]]


def build_relation_index(source: SeadInventorySourceRows) -> SeadRelationIndex:
    site_by_sample_group = {
        parse_required_int(row["sample_group_id"]): parse_required_int(row["site_id"])
        for row in source.sample_groups
        if row.get("sample_group_id") is not None and row.get("site_id") is not None
    }
    site_by_physical_sample = {
        parse_required_int(row["physical_sample_id"]): site_by_sample_group.get(
            parse_required_int(row["sample_group_id"]), 0
        )
        for row in source.physical_samples
        if row.get("physical_sample_id") is not None
        and row.get("sample_group_id") is not None
    }
    sample_group_by_physical_sample = {
        parse_required_int(row["physical_sample_id"]): parse_required_int(
            row["sample_group_id"]
        )
        for row in source.physical_samples
        if row.get("physical_sample_id") is not None
        and row.get("sample_group_id") is not None
    }
    physical_sample_by_analysis_entity = {
        parse_required_int(row["analysis_entity_id"]): parse_required_int(
            row["physical_sample_id"]
        )
        for row in source.analysis_entities
        if row.get("analysis_entity_id") is not None
        and row.get("physical_sample_id") is not None
    }
    dataset_by_analysis_entity = {
        parse_required_int(row["analysis_entity_id"]): parse_optional_int(
            row.get("dataset_id")
        )
        for row in source.analysis_entities
        if row.get("analysis_entity_id") is not None
    }
    admitted_analysis_entities = set(physical_sample_by_analysis_entity)
    analysis_entity_by_analysis_value = {
        parse_required_int(row["analysis_value_id"]): parse_required_int(
            row["analysis_entity_id"]
        )
        for row in source.analysis_values
        if row.get("analysis_value_id") is not None
        and row.get("analysis_entity_id") is not None
        and parse_required_int(row["analysis_entity_id"])
        in admitted_analysis_entities
    }

    sample_groups_by_site: dict[int, set[int]] = {}
    for sample_group_id, site_id in site_by_sample_group.items():
        if site_id and sample_group_id:
            sample_groups_by_site.setdefault(site_id, set()).add(sample_group_id)
    physical_samples_by_site: dict[int, set[int]] = {}
    for physical_sample_id, site_id in site_by_physical_sample.items():
        if site_id:
            physical_samples_by_site.setdefault(site_id, set()).add(physical_sample_id)
    analysis_entities_by_site: dict[int, set[int]] = {}
    datasets_by_site: dict[int, set[int]] = {}
    for entity in source.analysis_entities:
        physical_sample_id = parse_required_int(entity.get("physical_sample_id"))
        analysis_entity_id = parse_required_int(entity.get("analysis_entity_id"))
        dataset_id = parse_required_int(entity.get("dataset_id"))
        site_id = site_by_physical_sample.get(physical_sample_id, 0)
        if not site_id:
            continue
        if analysis_entity_id:
            analysis_entities_by_site.setdefault(site_id, set()).add(
                analysis_entity_id
            )
        if dataset_id:
            datasets_by_site.setdefault(site_id, set()).add(dataset_id)
    site_by_analysis_entity = {
        analysis_entity_id: site_id
        for site_id, analysis_entity_ids in analysis_entities_by_site.items()
        for analysis_entity_id in analysis_entity_ids
    }
    return SeadRelationIndex(
        site_by_sample_group=site_by_sample_group,
        site_by_physical_sample=site_by_physical_sample,
        sample_group_by_physical_sample=sample_group_by_physical_sample,
        physical_sample_by_analysis_entity=physical_sample_by_analysis_entity,
        dataset_by_analysis_entity=dataset_by_analysis_entity,
        analysis_entity_by_analysis_value=analysis_entity_by_analysis_value,
        site_by_analysis_entity=site_by_analysis_entity,
        sample_groups_by_site=sample_groups_by_site,
        physical_samples_by_site=physical_samples_by_site,
        analysis_entities_by_site=analysis_entities_by_site,
        datasets_by_site=datasets_by_site,
    )


__all__ = ["SeadRelationIndex", "build_relation_index"]
