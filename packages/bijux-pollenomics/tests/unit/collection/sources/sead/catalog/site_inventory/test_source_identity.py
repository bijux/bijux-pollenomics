"""Source-key precision must survive site, dataset and citation joins."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, fields

import pytest

from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.bibliography_projection import (
    project_site_bibliography,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.chronology_projection import (
    SeadChronologyProjection,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.source_data.lookups import (
    build_lookup_index,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.source_data.relations import (
    build_relation_index,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.source_data.source_tables import (
    SeadInventorySourceRows,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.values import (
    parse_optional_int,
    parse_required_int,
)


def _source() -> SeadInventorySourceRows:
    source = SeadInventorySourceRows(
        **{field.name: [] for field in fields(SeadInventorySourceRows)}
    )
    first, second = "9007199254740992", "9007199254740993"
    source.sample_groups.extend(
        [
            {"sample_group_id": first, "site_id": 1},
            {"sample_group_id": second, "site_id": 2},
        ]
    )
    source.physical_samples.extend(
        [
            {"physical_sample_id": 11, "sample_group_id": first},
            {"physical_sample_id": 12, "sample_group_id": second},
        ]
    )
    source.analysis_entities.extend(
        [
            {"analysis_entity_id": 21, "physical_sample_id": 11, "dataset_id": first},
            {"analysis_entity_id": 22, "physical_sample_id": 12, "dataset_id": second},
        ]
    )
    source.datasets.extend(
        [
            {
                "dataset_id": first,
                "dataset_name": "first native dataset",
                "biblio_id": first,
            },
            {
                "dataset_id": second,
                "dataset_name": "second native dataset",
                "biblio_id": second,
            },
        ]
    )
    source.bibliography_rows.extend(
        [
            {"biblio_id": first, "title": "first native citation"},
            {"biblio_id": second, "title": "second native citation"},
        ]
    )
    source.site_references.extend(
        [
            {"site_reference_id": 1, "site_id": 1, "biblio_id": first},
            {"site_reference_id": 2, "site_id": 2, "biblio_id": second},
        ]
    )
    return source


def test_adjacent_large_keys_keep_each_physical_sample_with_its_native_site() -> None:
    source = _source()
    before = deepcopy(asdict(source))
    relations = build_relation_index(source)
    assert relations.site_by_physical_sample == {11: 1, 12: 2}
    assert relations.datasets_by_site == {1: {9007199254740992}, 2: {9007199254740993}}
    assert asdict(source) == before


def test_adjacent_large_citation_keys_never_attach_another_sites_reference() -> None:
    source = _source()
    before = deepcopy(asdict(source))
    relations, lookups = build_relation_index(source), build_lookup_index(source)
    chronology = SeadChronologyProjection(
        **{field.name: {} for field in fields(SeadChronologyProjection)}
    )
    bibliography = project_site_bibliography(source, relations, lookups, chronology)
    assert lookups.dataset_name_by_id == {
        9007199254740992: "first native dataset",
        9007199254740993: "second native dataset",
    }
    assert {row["title"] for row in bibliography.bibliography_rows_by_site[1]} == {
        "first native citation"
    }
    assert {row["title"] for row in bibliography.bibliography_rows_by_site[2]} == {
        "second native citation"
    }
    assert asdict(source) == before


@pytest.mark.parametrize("invalid", [True, 1.4, "1.4", 0])
def test_invalid_native_sample_key_refuses_instead_of_reassigning_ownership(
    invalid: object,
) -> None:
    source = _source()
    source.sample_groups[0]["sample_group_id"] = invalid
    with pytest.raises(ValueError):
        build_relation_index(source)


@pytest.mark.parametrize("invalid", [True, 1.4, "1.4", 0])
def test_invalid_native_bibliography_key_refuses_instead_of_matching_a_citation(
    invalid: object,
) -> None:
    source = _source()
    source.datasets[0]["biblio_id"] = invalid
    with pytest.raises(ValueError):
        build_lookup_index(source)


def test_nullable_dataset_reference_stays_absent_and_numeric_parsers_are_unchanged() -> (
    None
):
    source = _source()
    source.datasets[0]["biblio_id"] = None
    lookups = build_lookup_index(source)
    assert lookups.dataset_reference_by_id[9007199254740992] == {}
    assert lookups.dataset_bibliography_id_by_id[9007199254740992] is None
    assert source.datasets[0]["biblio_id"] is None
    assert parse_optional_int(1.4) == 1
    assert parse_required_int(0) == 0
