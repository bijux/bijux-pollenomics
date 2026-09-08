"""Join SEAD bibliography evidence to its owning sites."""

from __future__ import annotations

from dataclasses import dataclass

from bijux_pollenomics.core.text import clean_optional_text

from .chronology_projection import SeadChronologyProjection
from .chronology_records import _build_bibliography_row, _deduplicate_bibliography_rows
from .source_data.lookups import SeadLookupIndex
from .source_data.relations import SeadRelationIndex
from .source_data.source_tables import SeadInventorySourceRows
from .values import parse_required_int

Row = dict[str, object]


@dataclass(frozen=True, slots=True)
class SeadBibliographyProjection:
    reference_ids_by_site: dict[int, set[int]]
    bibliography_rows_by_site: dict[int, list[Row]]


def project_site_bibliography(
    source: SeadInventorySourceRows,
    relations: SeadRelationIndex,
    lookups: SeadLookupIndex,
    chronology: SeadChronologyProjection,
) -> SeadBibliographyProjection:
    reference_ids_by_site: dict[int, set[int]] = {}
    bibliography_rows_by_site: dict[int, list[Row]] = {}
    for reference in source.site_references:
        site_id = parse_required_int(reference.get("site_id"))
        reference_id = parse_required_int(reference.get("site_reference_id"))
        if site_id and reference_id:
            reference_ids_by_site.setdefault(site_id, set()).add(reference_id)
            biblio = lookups.bibliography_by_id.get(
                parse_required_int(reference.get("biblio_id")), {}
            )
            if biblio:
                bibliography_rows_by_site.setdefault(site_id, []).append(
                    _build_bibliography_row(
                        biblio_id=parse_required_int(reference.get("biblio_id")),
                        source_kind="site_reference",
                        source_record_id=reference_id,
                        source_record_label="",
                        biblio=biblio,
                    )
                )
    for site_id, dataset_ids_for_site in relations.datasets_by_site.items():
        for dataset_id in dataset_ids_for_site:
            biblio = lookups.dataset_reference_by_id.get(dataset_id, {})
            if biblio:
                bibliography_rows_by_site.setdefault(site_id, []).append(
                    _build_bibliography_row(
                        biblio_id=lookups.dataset_bibliography_id_by_id.get(
                            dataset_id, 0
                        ),
                        source_kind="dataset_reference",
                        source_record_id=dataset_id,
                        source_record_label=lookups.dataset_name_by_id.get(
                            dataset_id, ""
                        ),
                        biblio=biblio,
                    )
                )
    for reference in source.sample_group_references:
        sample_group_id = parse_required_int(reference.get("sample_group_id"))
        site_id = relations.site_by_sample_group.get(sample_group_id, 0)
        biblio_id = parse_required_int(reference.get("biblio_id"))
        biblio = lookups.bibliography_by_id.get(biblio_id, {})
        if site_id and biblio:
            bibliography_rows_by_site.setdefault(site_id, []).append(
                _build_bibliography_row(
                    biblio_id=biblio_id,
                    source_kind="sample_group_reference",
                    source_record_id=sample_group_id,
                    source_record_label="",
                    biblio=biblio,
                )
            )
    for reference in source.relative_age_references:
        relative_age_id = parse_required_int(reference.get("relative_age_id"))
        biblio_id = parse_required_int(reference.get("biblio_id"))
        biblio = lookups.bibliography_by_id.get(biblio_id, {})
        relative_age = lookups.relative_age_by_id.get(relative_age_id, {})
        for site_id in chronology.site_ids_by_relative_age_id.get(
            relative_age_id, set()
        ):
            if biblio:
                bibliography_rows_by_site.setdefault(site_id, []).append(
                    _build_bibliography_row(
                        biblio_id=biblio_id,
                        source_kind="relative_age_definition",
                        source_record_id=relative_age_id,
                        source_record_label=clean_optional_text(
                            relative_age.get("label")
                        ),
                        biblio=biblio,
                    )
                )
    for site_id, site_rows in bibliography_rows_by_site.items():
        bibliography_rows_by_site[site_id] = _deduplicate_bibliography_rows(site_rows)
    for site_rows in bibliography_rows_by_site.values():
        site_rows.sort(
            key=lambda row: (
                str(row.get("source_kind", "")),
                str(row.get("title", "")),
                str(row.get("doi", "")),
            )
        )

    return SeadBibliographyProjection(
        reference_ids_by_site=reference_ids_by_site,
        bibliography_rows_by_site=bibliography_rows_by_site,
    )


__all__ = ["SeadBibliographyProjection", "project_site_bibliography"]
