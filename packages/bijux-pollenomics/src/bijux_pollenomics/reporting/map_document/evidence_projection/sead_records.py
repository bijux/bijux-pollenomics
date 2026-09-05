"""Compact SEAD observation and relation records."""

from __future__ import annotations

from __future__ import annotations
from collections.abc import Mapping, Sequence
from typing import cast
from .constants import (
    _SEAD_OBSERVATION_DICTIONARY_FIELDS,
    _SEAD_OBSERVATION_FIELDS,
    _SEAD_OBSERVATION_LIST_DICTIONARY_FIELDS,
)
from .io import (
    _identifier_text,
    _mapping,
    _required_text,
)


def _compact_sead_observation(
    observation: Mapping[str, object],
    *,
    entity_by_id: Mapping[str, Mapping[str, object]],
    refusal_by_observation: Mapping[str, Mapping[str, object]],
    taxon_by_id: Mapping[str, Mapping[str, object]],
    dimension_by_id: Mapping[str, Mapping[str, object]],
    dataset_semantic_by_id: Mapping[str, Mapping[str, object]],
    value_semantic_by_id: Mapping[str, Mapping[str, object]],
) -> tuple[
    list[object],
    str,
    tuple[str | None, tuple[str, ...], str | None, str | None],
]:
    observation_id = _required_text(
        observation.get("observation_id"), "SEAD observation ID"
    )
    if observation.get("source_family") != "sead":
        raise ValueError("SEAD observation source family changed")
    entity_id = _required_text(
        observation.get("entity_relation_id"), "SEAD observation entity relation"
    )
    entity = entity_by_id.get(entity_id)
    if entity is None:
        raise ValueError("SEAD observation references unknown entity relation")
    site_id = _identifier_text(entity.get("site_id"), "SEAD entity site ID")
    if observation.get("country_code") != entity.get("country_code"):
        raise ValueError("SEAD observation country disagrees with entity relation")
    source_value = observation.get("source_value")
    source_value_state = _required_text(
        observation.get("source_value_state"), "SEAD observation value state"
    )
    if (source_value is None) is not (source_value_state == "source_null"):
        raise ValueError("SEAD source null and value state disagree")

    chronology = _mapping(
        observation.get("chronology_link"), "SEAD observation chronology link"
    )
    entity_chronology = _mapping(
        entity.get("chronology_link"), "SEAD entity chronology link"
    )
    claim_ids = entity_chronology.get("claim_ids")
    eligible_claim_ids = entity_chronology.get("eligible_claim_ids")
    if not isinstance(claim_ids, list) or not isinstance(eligible_claim_ids, list):
        raise ValueError("SEAD entity chronology IDs must be lists")
    if chronology.get("claim_count") != len(claim_ids) or chronology.get(
        "eligible_claim_count"
    ) != len(eligible_claim_ids):
        raise ValueError("SEAD observation chronology counts do not reconcile")
    if chronology.get("entity_relation_id") != entity_id:
        raise ValueError("SEAD observation chronology relation changed")

    refusal = refusal_by_observation.get(observation_id)
    if refusal is None or refusal.get("status") != "refused":
        raise ValueError("SEAD observation lacks its event refusal")
    refusal_reasons = observation.get("event_refusal_reason_codes")
    if not isinstance(refusal_reasons, list) or any(
        not isinstance(reason, str) or not reason for reason in refusal_reasons
    ):
        raise ValueError("SEAD event refusal reasons must be text rows")
    if refusal.get("reason_codes") != refusal_reasons:
        raise ValueError("SEAD observation and event refusal reasons differ")
    if "source_classification_not_accepted" not in refusal_reasons:
        raise ValueError("SEAD event refusal lacks classification reason")
    if observation.get("event_eligibility") != "refused":
        raise ValueError("SEAD observation event eligibility changed")

    semantics = _mapping(
        observation.get("source_semantics"), "SEAD observation semantics"
    )
    dataset_id_value = semantics.get("dataset_semantics_id")
    dataset_id = (
        None
        if dataset_id_value is None
        else _required_text(dataset_id_value, "SEAD dataset semantics ID")
    )
    dataset_status = _required_text(
        semantics.get("dataset_semantics_status"), "SEAD dataset semantics status"
    )
    if (dataset_id is None) is not (dataset_status == "not_exposed_by_relation"):
        raise ValueError("SEAD dataset semantics identity and status disagree")
    if dataset_id is not None and dataset_id not in dataset_semantic_by_id:
        raise ValueError("SEAD observation references unknown dataset semantics")
    value_id_value = semantics.get("value_semantics_id")
    value_id = (
        None
        if value_id_value is None
        else _required_text(value_id_value, "SEAD value semantics ID")
    )
    if value_id is not None and value_id not in value_semantic_by_id:
        raise ValueError("SEAD observation references unknown value semantics")
    taxon_id_value = observation.get("taxon_relation_id")
    taxon_id = (
        None
        if taxon_id_value is None
        else _required_text(taxon_id_value, "SEAD taxon relation ID")
    )
    if taxon_id is not None and taxon_id not in taxon_by_id:
        raise ValueError("SEAD observation references unknown taxon relation")
    raw_dimension_ids = observation.get("dimension_relation_ids")
    if not isinstance(raw_dimension_ids, list) or any(
        not isinstance(value, str) or not value for value in raw_dimension_ids
    ):
        raise ValueError("SEAD observation dimension relation IDs must be text rows")
    dimension_ids = tuple(cast(list[str], raw_dimension_ids))
    if len(dimension_ids) != len(set(dimension_ids)):
        raise ValueError("SEAD observation dimension relations are duplicated")
    if any(dimension_id not in dimension_by_id for dimension_id in dimension_ids):
        raise ValueError("SEAD observation references unknown dimension relation")

    compact = [
        observation_id,
        observation.get("source_table"),
        observation.get("source_record_id"),
        entity_id,
        entity.get("analysis_entity_id"),
        entity.get("physical_sample_id"),
        entity.get("sample_group_id"),
        entity.get("dataset_id"),
        source_value,
        observation.get("source_value_field"),
        source_value_state,
        semantics.get("source_unit_id"),
        semantics.get("unit_status"),
        value_id,
        dataset_id,
        dataset_status,
        taxon_id,
        observation.get("taxon_status"),
        list(dimension_ids),
        observation.get("dimension_status"),
        chronology.get("status"),
        chronology.get("claim_count"),
        chronology.get("eligible_claim_count"),
        observation.get("event_eligibility"),
        refusal_reasons,
        observation.get("source_payload_sha256"),
    ]
    return compact, site_id, (taxon_id, dimension_ids, dataset_id, value_id)


def _sead_observation_table(rows: Sequence[Sequence[object]]) -> dict[str, object]:
    field_indexes = {
        field: index for index, field in enumerate(_SEAD_OBSERVATION_FIELDS)
    }
    dictionaries: dict[str, list[str]] = {}
    dictionary_indexes: dict[str, dict[str, int]] = {}
    for field in sorted(_SEAD_OBSERVATION_DICTIONARY_FIELDS):
        index = field_indexes[field]
        values = sorted(
            {_required_text(row[index], f"SEAD observation {field}") for row in rows}
        )
        dictionaries[field] = values
        dictionary_indexes[field] = {
            value: value_index for value_index, value in enumerate(values)
        }
    list_values = sorted(
        {
            value
            for field in _SEAD_OBSERVATION_LIST_DICTIONARY_FIELDS
            for row in rows
            for value in cast(list[str], row[field_indexes[field]])
        }
    )
    list_value_indexes = {
        value: value_index for value_index, value in enumerate(list_values)
    }
    encoded_rows: list[list[object]] = []
    for row in rows:
        if len(row) != len(_SEAD_OBSERVATION_FIELDS):
            raise ValueError("SEAD compact observation fields changed")
        encoded = list(row)
        for field, indexes in dictionary_indexes.items():
            index = field_indexes[field]
            encoded[index] = indexes[cast(str, encoded[index])]
        for field in _SEAD_OBSERVATION_LIST_DICTIONARY_FIELDS:
            index = field_indexes[field]
            encoded[index] = [
                list_value_indexes[value] for value in cast(list[str], encoded[index])
            ]
        encoded_rows.append(encoded)
    return {
        "record_count": len(encoded_rows),
        "fields": list(_SEAD_OBSERVATION_FIELDS),
        "records": encoded_rows,
        "encoding": "sead-source-native-observation-table.v1",
        "column_dictionaries": dictionaries,
        "list_dictionary_fields": sorted(_SEAD_OBSERVATION_LIST_DICTIONARY_FIELDS),
        "list_value_dictionary": list_values,
    }


def _compact_sead_entity(row: Mapping[str, object]) -> list[object]:
    chronology = _mapping(row.get("chronology_link"), "SEAD entity chronology")
    return [
        row.get("entity_relation_id"),
        row.get("analysis_entity_id"),
        row.get("physical_sample_id"),
        row.get("sample_group_id"),
        row.get("dataset_id"),
        chronology.get("claim_ids"),
        chronology.get("eligible_claim_ids"),
    ]


def _compact_sead_taxon(row: Mapping[str, object]) -> list[object]:
    taxon = _mapping(row.get("taxon"), "SEAD native taxon")
    genus = _optional_mapping(row.get("genus"), "SEAD native taxon genus")
    family = _optional_mapping(row.get("family"), "SEAD native taxon family")
    order = _optional_mapping(row.get("order"), "SEAD native taxon order")
    author = _optional_mapping(row.get("author"), "SEAD native taxon author")
    return [
        row.get("taxon_relation_id"),
        row.get("taxon_id"),
        taxon.get("species"),
        genus.get("genus_name"),
        family.get("family_name"),
        order.get("order_name"),
        author.get("author_name"),
        row.get("source_ecocodes"),
        row.get("derived_classification_status"),
    ]


def _compact_sead_dimension(row: Mapping[str, object]) -> list[object]:
    source_row = _mapping(row.get("source_row"), "SEAD dimension source row")
    return [
        row.get("dimension_relation_id"),
        row.get("owner_kind"),
        row.get("owner_id"),
        row.get("source_table"),
        row.get("source_record_id"),
        row.get("dimension_semantics_id"),
        source_row.get("dimension_value"),
        source_row.get("qualifier_id"),
        row.get("unit_status"),
    ]


def _compact_sead_dimension_semantics(row: Mapping[str, object]) -> list[object]:
    dimension = _mapping(row.get("source_dimension"), "SEAD dimension semantics")
    unit = _mapping(row.get("source_unit"), "SEAD dimension unit")
    return [
        row.get("dimension_semantics_id"),
        row.get("dimension_id"),
        dimension.get("dimension_name"),
        dimension.get("dimension_abbrev"),
        dimension.get("dimension_description"),
        row.get("source_unit_id"),
        unit.get("unit_name"),
        unit.get("unit_abbrev"),
        unit.get("description"),
        row.get("unit_status"),
    ]


def _compact_sead_dataset_semantics(row: Mapping[str, object]) -> list[object]:
    dataset = _mapping(row.get("dataset"), "SEAD dataset semantics")
    data_type = _mapping(row.get("source_data_type"), "SEAD source data type")
    group = _mapping(row.get("source_data_type_group"), "SEAD source data type group")
    return [
        row.get("dataset_semantics_id"),
        dataset.get("dataset_id"),
        dataset.get("dataset_uuid"),
        dataset.get("dataset_name"),
        dataset.get("data_type_id"),
        data_type.get("data_type_name"),
        group.get("data_type_group_name"),
    ]


def _compact_sead_value_semantics(row: Mapping[str, object]) -> list[object]:
    value_class = _mapping(row.get("value_class"), "SEAD value class")
    value_type = _mapping(row.get("source_value_type"), "SEAD value type")
    raw_unit = row.get("source_unit")
    unit = raw_unit if isinstance(raw_unit, Mapping) else {}
    return [
        row.get("value_semantics_id"),
        value_class.get("value_class_id"),
        value_class.get("name"),
        value_class.get("description"),
        value_type.get("value_type_id"),
        value_type.get("name"),
        value_type.get("base_type"),
        unit.get("unit_id"),
        unit.get("unit_name"),
        unit.get("unit_abbrev"),
        unit.get("description"),
    ]


def _optional_mapping(value: object, label: str) -> Mapping[str, object]:
    if value is None:
        return {}
    return _mapping(value, label)
