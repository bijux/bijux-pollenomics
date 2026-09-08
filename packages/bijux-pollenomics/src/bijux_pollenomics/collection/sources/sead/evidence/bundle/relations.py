from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import cast

from .constants import (
    _ABUNDANCE_COMPONENTS,
    _ANALYSIS_VALUE_COMPONENTS,
    _DIMENSION_RELATION_TABLES,
    _OBSERVATION_TABLES,
)
from .serialization import _positive_int, _required_text, _stable_id


def _entity_relations(
    tables: Mapping[str, list[dict[str, object]]],
    *,
    country_by_site: Mapping[int, str],
) -> tuple[list[dict[str, object]], dict[int, dict[str, object]]]:
    sites = _unique_index(tables["tbl_sites"], "site_id")
    groups = _unique_index(tables["tbl_sample_groups"], "sample_group_id")
    samples = _unique_index(tables["tbl_physical_samples"], "physical_sample_id")
    rows: list[dict[str, object]] = []
    by_entity: dict[int, dict[str, object]] = {}
    for entity in tables["tbl_analysis_entities"]:
        entity_id = _positive_int(entity.get("analysis_entity_id"), "analysis entity")
        sample_id = _positive_int(entity.get("physical_sample_id"), "physical sample")
        source_dataset_id = entity.get("dataset_id")
        dataset_id = (
            None
            if source_dataset_id is None
            else _positive_int(source_dataset_id, "dataset")
        )
        sample = samples.get(sample_id)
        if sample is None:
            raise ValueError(f"SEAD entity lacks physical sample: {entity_id}")
        group_id = _positive_int(sample.get("sample_group_id"), "sample group")
        group = groups.get(group_id)
        if group is None:
            raise ValueError(f"SEAD sample lacks sample group: {sample_id}")
        site_id = _positive_int(group.get("site_id"), "site")
        site = sites.get(site_id)
        if site is None or site_id not in country_by_site:
            raise ValueError(f"SEAD group lacks governed site: {group_id}")
        row = {
            "entity_relation_id": f"sead-analysis-entity:{entity_id}",
            "analysis_entity_id": entity_id,
            "physical_sample_id": sample_id,
            "sample_group_id": group_id,
            "dataset_id": dataset_id,
            "site_id": site_id,
            "site_uuid": _required_text(site, "site_uuid"),
            "country_code": country_by_site[site_id],
            "latitude_dd": site.get("latitude_dd"),
            "longitude_dd": site.get("longitude_dd"),
        }
        rows.append(row)
        by_entity[entity_id] = row
    return rows, by_entity


def _component_indices(
    tables: Mapping[str, list[dict[str, object]]],
) -> dict[str, dict[int, list[dict[str, object]]]]:
    result: dict[str, dict[int, list[dict[str, object]]]] = {}
    for table in _ANALYSIS_VALUE_COMPONENTS:
        result[table] = _child_index(tables[table], "analysis_value_id")
    for table in _ABUNDANCE_COMPONENTS:
        result[table] = _child_index(tables[table], "abundance_id")
    return result


def _observation_components(
    table: str,
    *,
    source_id: int,
    components: Mapping[str, Mapping[int, list[dict[str, object]]]],
) -> dict[str, list[dict[str, object]]]:
    names = (
        _ANALYSIS_VALUE_COMPONENTS
        if table == "tbl_analysis_values"
        else (_ABUNDANCE_COMPONENTS if table == "tbl_abundances" else ())
    )
    return {name: components[name].get(source_id, []) for name in names}


def _dimension_relation_index(
    tables: Mapping[str, list[dict[str, object]]],
    *,
    manifest_sha256: str,
) -> tuple[
    dict[int, dict[str, object]],
    list[dict[str, object]],
    dict[tuple[str, int], list[str]],
]:
    units = _unique_index(tables["tbl_units"], "unit_id")
    semantics: dict[int, dict[str, object]] = {}
    for dimension in tables["tbl_dimensions"]:
        dimension_id = _positive_int(dimension.get("dimension_id"), "dimension")
        raw_unit_id = dimension.get("unit_id")
        unit_id = (
            None
            if raw_unit_id is None
            else _positive_int(raw_unit_id, "dimension unit")
        )
        unit = units.get(unit_id) if unit_id is not None else None
        semantics[dimension_id] = {
            "dimension_semantics_id": f"sead-dimension:{dimension_id}",
            "dimension_id": dimension_id,
            "source_dimension": dimension,
            "source_unit": unit,
            "source_unit_id": unit_id,
            "unit_status": (
                "source_native_linked"
                if unit is not None
                else (
                    "source_unit_not_reported"
                    if unit_id is None
                    else "source_unit_relation_unavailable"
                )
            ),
        }

    relations: list[dict[str, object]] = []
    by_owner: dict[tuple[str, int], list[str]] = defaultdict(list)
    for table, primary_key, owner_field, owner_kind in _DIMENSION_RELATION_TABLES:
        for source_row in tables[table]:
            source_id = _positive_int(source_row.get(primary_key), f"{table} key")
            owner_id = _positive_int(source_row.get(owner_field), f"{table} owner")
            raw_dimension_id = source_row.get("dimension_id")
            relation_dimension_id = (
                None
                if raw_dimension_id is None
                else _positive_int(raw_dimension_id, f"{table} dimension")
            )
            semantic = (
                semantics.get(relation_dimension_id)
                if relation_dimension_id is not None
                else None
            )
            relation_id = _stable_id(
                "sead-dimension-relation",
                manifest_sha256,
                table,
                str(source_id),
            )
            relations.append(
                {
                    "dimension_relation_id": relation_id,
                    "source_table": table,
                    "source_record_id": str(source_id),
                    "source_row": dict(source_row),
                    "owner_kind": owner_kind,
                    "owner_id": owner_id,
                    "dimension_semantics_id": (
                        semantic["dimension_semantics_id"]
                        if semantic is not None
                        else None
                    ),
                    "dimension_status": (
                        "source_native_linked"
                        if semantic is not None
                        else "source_dimension_relation_unavailable"
                    ),
                    "unit_status": (
                        semantic["unit_status"]
                        if semantic is not None
                        else "source_dimension_relation_unavailable"
                    ),
                }
            )
            by_owner[(owner_kind, owner_id)].append(relation_id)
    for relation_ids in by_owner.values():
        relation_ids.sort()
    expected = sum(len(tables[table]) for table, *_ in _DIMENSION_RELATION_TABLES)
    if len(relations) != expected:
        raise ValueError("SEAD dimension relation rows do not reconcile")
    relation_ids = [
        cast(str, relation["dimension_relation_id"]) for relation in relations
    ]
    if len(relation_ids) != len(set(relation_ids)):
        raise ValueError("SEAD dimension relation identities are duplicated")
    return semantics, relations, dict(by_owner)


def _observation_dimension_relation_ids(
    table: str,
    *,
    source_id: int,
    analysis_value_id: int | None,
    entity_relation: Mapping[str, object],
    dimensions_by_owner: Mapping[tuple[str, int], list[str]],
) -> list[str]:
    owner_keys: list[tuple[str, int]] = []
    if table == "tbl_analysis_values":
        owner_keys.append(("analysis_value", source_id))
    elif table == "tbl_analysis_taxon_counts":
        if analysis_value_id is None:
            raise ValueError("SEAD taxon count must bind an analysis value")
        owner_keys.append(("analysis_value", analysis_value_id))
    elif table == "tbl_measured_values":
        owner_keys.append(("measured_value", source_id))
    for owner_kind, relation_field in (
        ("analysis_entity", "analysis_entity_id"),
        ("physical_sample", "physical_sample_id"),
        ("sample_group", "sample_group_id"),
    ):
        owner_keys.append(
            (
                owner_kind,
                _positive_int(entity_relation.get(relation_field), relation_field),
            )
        )
    return sorted(
        {
            relation_id
            for owner_key in owner_keys
            for relation_id in dimensions_by_owner.get(owner_key, [])
        }
    )


def _taxonomy_index(
    tables: Mapping[str, list[dict[str, object]]],
) -> dict[int, dict[str, object]]:
    authors = _unique_index(tables["tbl_taxa_tree_authors"], "author_id")
    genera = _unique_index(tables["tbl_taxa_tree_genera"], "genus_id")
    families = _unique_index(tables["tbl_taxa_tree_families"], "family_id")
    orders = _unique_index(tables["tbl_taxa_tree_orders"], "order_id")
    definitions = _unique_index(
        tables["tbl_ecocode_definitions"], "ecocode_definition_id"
    )
    groups = _unique_index(tables["tbl_ecocode_groups"], "ecocode_group_id")
    systems = _unique_index(tables["tbl_ecocode_systems"], "ecocode_system_id")
    ecocodes = _child_index(tables["tbl_ecocodes"], "taxon_id")
    result: dict[int, dict[str, object]] = {}
    for taxon in tables["tbl_taxa_tree_master"]:
        taxon_id = _positive_int(taxon.get("taxon_id"), "taxon")
        genus = genera.get(cast(int, taxon.get("genus_id")))
        family = families.get(cast(int, genus.get("family_id"))) if genus else None
        order = orders.get(cast(int, family.get("order_id"))) if family else None
        native_ecocodes = []
        for ecocode in ecocodes.get(taxon_id, []):
            definition = definitions.get(
                cast(int, ecocode.get("ecocode_definition_id"))
            )
            group = (
                groups.get(cast(int, definition.get("ecocode_group_id")))
                if definition
                else None
            )
            system = (
                systems.get(cast(int, group.get("ecocode_system_id")))
                if group
                else None
            )
            native_ecocodes.append(
                {
                    "ecocode": ecocode,
                    "definition": definition,
                    "group": group,
                    "system": system,
                }
            )
        result[taxon_id] = {
            "taxon_relation_id": f"sead-taxon:{taxon_id}",
            "taxon_id": taxon_id,
            "taxon": taxon,
            "author": authors.get(cast(int, taxon.get("author_id"))),
            "genus": genus,
            "family": family,
            "order": order,
            "source_ecocodes": native_ecocodes,
            "derived_classification_status": "not_accepted",
        }
    return result


def _dataset_semantics_index(
    tables: Mapping[str, list[dict[str, object]]],
) -> dict[int, dict[str, object]]:
    data_types = _unique_index(tables["tbl_data_types"], "data_type_id")
    groups = _unique_index(tables["tbl_data_type_groups"], "data_type_group_id")
    result: dict[int, dict[str, object]] = {}
    for dataset in tables["tbl_datasets"]:
        dataset_id = _positive_int(dataset.get("dataset_id"), "dataset")
        data_type = data_types.get(cast(int, dataset.get("data_type_id")))
        group = (
            groups.get(cast(int, data_type.get("data_type_group_id")))
            if data_type
            else None
        )
        result[dataset_id] = {
            "dataset_semantics_id": f"sead-dataset:{dataset_id}",
            "dataset": dataset,
            "source_data_type": data_type,
            "source_data_type_group": group,
        }
    return result


def _value_semantics_index(
    tables: Mapping[str, list[dict[str, object]]],
) -> dict[int, dict[str, object]]:
    value_types = _unique_index(tables["tbl_value_types"], "value_type_id")
    units = _unique_index(tables["tbl_units"], "unit_id")
    data_types = _unique_index(tables["tbl_data_types"], "data_type_id")
    result: dict[int, dict[str, object]] = {}
    for value_class in tables["tbl_value_classes"]:
        class_id = _positive_int(value_class.get("value_class_id"), "value class")
        value_type = value_types.get(cast(int, value_class.get("value_type_id")))
        result[class_id] = {
            "value_semantics_id": f"sead-value-class:{class_id}",
            "value_class": value_class,
            "source_value_type": value_type,
            "source_unit": units.get(cast(int, value_type.get("unit_id")))
            if value_type
            else None,
            "source_data_type": data_types.get(
                cast(int, value_type.get("data_type_id"))
            )
            if value_type
            else None,
        }
    return result


def _observation_semantics(
    table: str,
    *,
    source_row: Mapping[str, object],
    dataset_id: int | None,
    dataset_semantics: Mapping[int, Mapping[str, object]],
    value_semantics: Mapping[int, Mapping[str, object]],
) -> dict[str, object]:
    semantics = (
        value_semantics.get(cast(int, source_row.get("value_class_id")))
        if table in {"tbl_analysis_values", "tbl_analysis_taxon_counts"}
        else None
    )
    source_unit = semantics.get("source_unit") if semantics else None
    return {
        "dataset_semantics_id": (
            dataset_semantics[dataset_id]["dataset_semantics_id"]
            if dataset_id is not None and dataset_id in dataset_semantics
            else None
        ),
        "dataset_semantics_status": (
            "source_native_linked"
            if dataset_id is not None and dataset_id in dataset_semantics
            else "not_exposed_by_relation"
        ),
        "value_semantics_id": (
            semantics["value_semantics_id"] if semantics is not None else None
        ),
        "source_unit_id": (
            source_unit.get("unit_id") if isinstance(source_unit, Mapping) else None
        ),
        "unit_status": (
            "source_native_linked"
            if source_unit is not None
            else "not_exposed_by_relation"
        ),
    }


def _assert_observation_reconciliation(
    tables: Mapping[str, list[dict[str, object]]],
    observations: Sequence[Mapping[str, object]],
    dispositions: Sequence[Mapping[str, object]],
    *,
    component_indices: Mapping[str, Mapping[int, list[dict[str, object]]]],
) -> None:
    expected = sum(len(tables[table]) for table, _, _ in _OBSERVATION_TABLES)
    if len(observations) != expected or len(dispositions) != expected:
        raise ValueError("SEAD observation/event disposition counts do not reconcile")
    identities = [item.get("observation_id") for item in observations]
    if len(identities) != len(set(identities)):
        raise ValueError("SEAD source-native observation identities are duplicated")
    disposition_ids = [item.get("observation_id") for item in dispositions]
    if identities != disposition_ids:
        raise ValueError("SEAD observation and event disposition identities diverge")
    for table, index in component_indices.items():
        linked_count = sum(len(rows) for rows in index.values())
        if linked_count != len(tables[table]):
            raise ValueError(f"SEAD component rows do not reconcile: {table}")


def _unique_index(
    rows: Sequence[dict[str, object]], key: str
) -> dict[int, dict[str, object]]:
    result = {}
    for row in rows:
        identifier = _positive_int(row.get(key), key)
        if identifier in result:
            raise ValueError(f"Duplicate SEAD source identifier: {key}={identifier}")
        result[identifier] = row
    return result


def _child_index(
    rows: Sequence[dict[str, object]], key: str
) -> dict[int, list[dict[str, object]]]:
    result: dict[int, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        result[_positive_int(row.get(key), key)].append(row)
    return dict(result)


def _four_country_counts(counts: Mapping[str, int]) -> dict[str, int]:
    return {code: counts.get(code, 0) for code in ("SE", "DK", "NO", "FI")}
