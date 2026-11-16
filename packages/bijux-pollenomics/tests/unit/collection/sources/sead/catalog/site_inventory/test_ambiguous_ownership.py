"""Source owners cannot be replaced by a later row with the same native key."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.sead import (
    populate_sead_site_inventory_fields,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.source_data.table_readers import (
    ApiSeadTableReader,
    MappingSeadTableReader,
)
from tests.unit.collection.sources.sead.evidence.test_native_rows import _tables


def source_tables() -> dict[str, list[dict[str, object]]]:
    tables = _tables()
    tables["tbl_datasets"] = [
        {"dataset_id": 5, "dataset_name": "Dataset A", "biblio_id": 71}
    ]
    tables["tbl_biblio"] = [
        {
            "biblio_id": number,
            "title": f"Citation {letter}",
            "full_reference": f"Synthetic reference {letter}",
            "year": "2001",
            "doi": "",
            "url": "",
        }
        for number, letter in [(71, "A"), (72, "B")]
    ]
    return tables


def callback(tables: dict[str, list[dict[str, object]]], calls: list[str]) -> Any:
    def fetch(
        url: str, *, params: object, headers: dict[str, str], timeout: float
    ) -> object:
        del params, timeout
        table = url.rsplit("/", 1)[-1]
        calls.append(table)
        start = int(headers["Range"].split("-", 1)[0])
        return deepcopy(tables.get(table, [])) if start == 0 else []

    return fetch


@pytest.mark.parametrize("reversed_rows", [False, True])
@pytest.mark.parametrize("second_id", [5, "0005"])
def test_public_enrichment_refuses_conflicting_dataset_owner_before_mutation(
    reversed_rows: bool, second_id: object
) -> None:
    tables = source_tables()
    tables["tbl_datasets"].append(
        {"dataset_id": second_id, "dataset_name": "Dataset B", "biblio_id": 72}
    )
    if reversed_rows:
        tables["tbl_datasets"].reverse()
    sites = deepcopy(tables["tbl_sites"])
    before_sites, before_tables = deepcopy(sites), deepcopy(tables)
    calls: list[str] = []
    with pytest.raises(ValueError, match="Duplicate SEAD.*tbl_datasets.*dataset_id"):
        populate_sead_site_inventory_fields(
            sites, fetch_json_fn=callback(tables, calls)
        )
    assert "tbl_datasets" in calls
    assert sites == before_sites and tables == before_tables


def test_unique_public_enrichment_keeps_exact_site_dataset_and_citation() -> None:
    tables = source_tables()
    before_tables = deepcopy(tables)
    sites = deepcopy(tables["tbl_sites"])
    calls: list[str] = []
    summary = populate_sead_site_inventory_fields(
        sites, fetch_json_fn=callback(tables, calls)
    )
    assert summary["site_row_count"] == 1
    assert sites[0]["site_id"] == 1
    assert sites[0]["dataset_names"] == ["Dataset A"]
    citation = sites[0]["bibliography_rows"]
    assert isinstance(citation, list) and len(citation) == 1
    assert citation[0]["biblio_id"] == 71
    assert citation[0]["source_record_id"] == 5
    assert citation[0]["title"] == "Citation A"
    assert tables == before_tables and "tbl_biblio" in calls


@pytest.mark.parametrize("kind", ["api", "mapping"])
@pytest.mark.parametrize("mode", ["all", "selected"])
@pytest.mark.parametrize(
    ("table", "primary_key"),
    [
        ("tbl_sample_groups", "sample_group_id"),
        ("tbl_physical_samples", "physical_sample_id"),
        ("tbl_analysis_entities", "analysis_entity_id"),
        ("tbl_analysis_values", "analysis_value_id"),
        ("tbl_age_types", "age_type_id"),
        ("tbl_relative_ages", "relative_age_id"),
        ("tbl_dating_uncertainty", "dating_uncertainty_id"),
        ("tbl_methods", "method_id"),
        ("tbl_biblio", "biblio_id"),
    ],
)
def test_owned_reader_refuses_duplicate_primary_keys_before_any_index(
    kind: str, mode: str, table: str, primary_key: str
) -> None:
    tables: dict[str, list[dict[str, object]]] = {
        table: [
            {primary_key: 11, "owner_id": 1},
            {primary_key: "0011", "owner_id": 1},
        ]
    }
    before = deepcopy(tables)
    reader = (
        ApiSeadTableReader(callback(tables, []))
        if kind == "api"
        else MappingSeadTableReader(tables)
    )
    with pytest.raises(ValueError, match=f"Duplicate SEAD.*{table}.*{primary_key}"):
        if mode == "all":
            reader.all_rows(
                table, select=f"{primary_key},owner_id", order_by=(primary_key,)
            )
        else:
            reader.rows_by_ids(
                table,
                select=f"{primary_key},owner_id",
                filter_field="owner_id",
                ids=[1],
                order_by=(primary_key,),
            )
    assert tables == before


@pytest.mark.parametrize("kind", ["api", "mapping"])
def test_distinct_large_owners_share_foreign_reference_without_merging(
    kind: str,
) -> None:
    rows: list[dict[str, object]] = [
        {"dataset_id": "9007199254740992", "biblio_id": None},
        {"dataset_id": 9007199254740993, "biblio_id": None},
    ]
    tables = {"tbl_datasets": rows}
    before = deepcopy(rows)
    reader = (
        ApiSeadTableReader(callback(tables, []))
        if kind == "api"
        else MappingSeadTableReader(tables)
    )
    assert (
        reader.all_rows(
            "tbl_datasets", select="dataset_id,biblio_id", order_by=("dataset_id",)
        )
        == before
    )
    assert rows == before


def test_multiple_distinct_relationship_rows_may_share_the_same_site() -> None:
    rows = [
        {"site_reference_id": 11, "site_id": 1, "biblio_id": 71},
        {"site_reference_id": 12, "site_id": 1, "biblio_id": 72},
    ]
    reader = MappingSeadTableReader({"tbl_site_references": rows})
    assert (
        reader.rows_by_ids(
            "tbl_site_references",
            select="site_reference_id,site_id,biblio_id",
            filter_field="site_id",
            ids=[1],
            order_by=("site_reference_id",),
        )
        == rows
    )


def _projection_callback(rows: list[dict[str, object]]) -> Any:
    def fetch(
        url: str,
        *,
        params: list[tuple[str, str]],
        headers: dict[str, str],
        timeout: float,
    ) -> object:
        del url, timeout
        query = dict(params)
        if "site_id" in query:
            assert query["site_id"] == "in.(1)"
        fields = [field.strip() for field in query["select"].split(",")]
        start = int(headers["Range"].split("-", 1)[0])
        return [
            deepcopy(row)
            if "*" in fields
            else {field: deepcopy(row[field]) for field in fields if field in row}
            for row in rows[start : start + 1]
        ]

    return fetch


def _read_projection(
    reader: ApiSeadTableReader | MappingSeadTableReader, mode: str, select: str
) -> list[dict[str, object]]:
    if mode == "all":
        return reader.all_rows("tbl_datasets", select=select, order_by=("site_id",))
    return reader.rows_by_ids(
        "tbl_datasets",
        select=select,
        filter_field="site_id",
        ids=[1],
        order_by=("site_id",),
    )


@pytest.mark.parametrize("kind", ["api", "mapping"])
@pytest.mark.parametrize("mode", ["all", "selected"])
@pytest.mark.parametrize("owner_in_source", [False, True])
def test_known_table_nonowner_projection_preserves_repeated_foreign_values(
    kind: str, mode: str, owner_in_source: bool
) -> None:
    rows: list[dict[str, object]] = [{"site_id": 1}, {"site_id": 1}]
    if owner_in_source:
        for identity, row in enumerate(rows, 5):
            row["dataset_id"] = identity
    before = deepcopy(rows)
    reader = (
        ApiSeadTableReader(_projection_callback(rows))
        if kind == "api"
        else MappingSeadTableReader({"tbl_datasets": rows})
    )
    assert _read_projection(reader, mode, "site_id") == [{"site_id": 1}, {"site_id": 1}]
    assert rows == before


@pytest.mark.parametrize("kind", ["api", "mapping"])
@pytest.mark.parametrize("mode", ["all", "selected"])
@pytest.mark.parametrize("native_key", ["missing", None, True, 1.4, 0, "not-a-key"])
def test_explicit_owner_projection_never_skips_missing_or_invalid_keys(
    kind: str, mode: str, native_key: object
) -> None:
    row: dict[str, object] = {"site_id": 1}
    if native_key != "missing":
        row["dataset_id"] = native_key
    rows = [row]
    before = deepcopy(rows)
    reader = (
        ApiSeadTableReader(_projection_callback(rows))
        if kind == "api"
        else MappingSeadTableReader({"tbl_datasets": rows})
    )
    with pytest.raises(ValueError):
        _read_projection(reader, mode, "dataset_id,site_id")
    assert rows == before


@pytest.mark.parametrize("mode", ["all", "selected"])
@pytest.mark.parametrize("select", ["*", " dataset_id , site_id "])
def test_api_wildcard_or_spaced_owner_projection_retains_owner_validation(
    mode: str,
    select: str,
) -> None:
    rows: list[dict[str, object]] = [
        {"dataset_id": 5, "site_id": 1},
        {"dataset_id": "0005", "site_id": 1},
    ]
    reader = ApiSeadTableReader(_projection_callback(rows))
    with pytest.raises(ValueError, match="Duplicate SEAD.*dataset_id"):
        _read_projection(reader, mode, select)


def test_mapping_wildcard_projection_keeps_its_existing_refusal() -> None:
    reader = MappingSeadTableReader({"tbl_datasets": [{"dataset_id": 5, "site_id": 1}]})
    with pytest.raises(ValueError, match="misses projected fields"):
        _read_projection(reader, "all", "*")
