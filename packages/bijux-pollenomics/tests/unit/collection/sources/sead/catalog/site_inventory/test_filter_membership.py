"""Catalogue filter membership must agree with exact native returned owners."""

from typing import Any

import pytest

from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.source_data.table_readers import (
    ApiSeadTableReader,
)


def _reader(rows: list[dict[str, object]]) -> ApiSeadTableReader:
    def fetch(_url: str, **kwargs: Any) -> object:
        start = int(kwargs["headers"]["Range"].split("-", 1)[0])
        return rows if start == 0 else []

    return ApiSeadTableReader(fetch)


def _selected(
    reader: ApiSeadTableReader, ids: list[int] | None = None
) -> list[dict[str, object]]:
    return reader.rows_by_ids(
        "tbl_sample_groups",
        select="sample_group_id,site_id,sample_group_name",
        filter_field="site_id",
        ids=[1] if ids is None else ids,
        order_by=("site_id", "sample_group_id"),
    )


@pytest.mark.parametrize("foreign", [2, True, 0, 1.0, None])
def test_foreign_or_invalid_returned_filter_owner_is_refused(foreign: object) -> None:
    with pytest.raises(ValueError):
        _selected(
            _reader(
                [
                    {
                        "sample_group_id": 10,
                        "site_id": foreign,
                        "sample_group_name": "generated",
                    }
                ]
            )
        )


def test_mixed_selected_and_foreign_rows_do_not_return_a_partial_success() -> None:
    with pytest.raises(ValueError):
        _selected(
            _reader(
                [
                    {
                        "sample_group_id": 10,
                        "site_id": 1,
                        "sample_group_name": "selected",
                    },
                    {
                        "sample_group_id": 11,
                        "site_id": 2,
                        "sample_group_name": "foreign",
                    },
                ]
            )
        )


def test_owner_from_another_requested_batch_is_still_refused() -> None:
    def fetch(_url: str, **kwargs: Any) -> object:
        start = int(kwargs["headers"]["Range"].split("-", 1)[0])
        if start:
            return []
        second_batch = dict(kwargs["params"])["site_id"] == "in.(101)"
        return [
            {
                "sample_group_id": 20 if second_batch else 10,
                "site_id": 1,
                "sample_group_name": "generated",
            }
        ]

    with pytest.raises(ValueError):
        _selected(ApiSeadTableReader(fetch), list(range(1, 102)))


def test_exact_ascii_decimal_source_owner_preserves_native_representation() -> None:
    row = {"sample_group_id": 10, "site_id": "1", "sample_group_name": "selected"}
    assert _selected(_reader([row])) == [row]


def test_distinct_children_can_share_a_requested_owner() -> None:
    rows = [
        {"sample_group_id": 10, "site_id": 1, "sample_group_name": "first"},
        {"sample_group_id": 11, "site_id": 1, "sample_group_name": "second"},
    ]
    assert _selected(_reader(rows)) == rows


def test_duplicate_native_primary_keys_remain_refused() -> None:
    row = {"sample_group_id": 10, "site_id": 1, "sample_group_name": "selected"}
    with pytest.raises(ValueError, match="Duplicate"):
        _selected(_reader([row, row]))


def test_foreign_first_page_refuses_before_requesting_another_page() -> None:
    calls = []

    def fetch(_url: str, **kwargs: Any) -> object:
        calls.append(kwargs)
        return (
            [{"sample_group_id": 10, "site_id": 2, "sample_group_name": "foreign"}]
            if len(calls) == 1
            else []
        )

    with pytest.raises(ValueError):
        _selected(ApiSeadTableReader(fetch))
    assert len(calls) == 1


def test_api_and_mapping_projection_parity_when_filter_is_not_selected() -> None:
    from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.source_data.table_readers import (
        MappingSeadTableReader,
    )

    native = {"dataset_id": 5, "site_id": "001"}
    requests: list[str] = []

    def fetch(_url: str, **kwargs: Any) -> object:
        projection = dict(kwargs["params"])["select"]
        requests.append(projection)
        return (
            [{field: native[field] for field in projection.split(",")}]
            if len(requests) == 1
            else []
        )

    api = ApiSeadTableReader(fetch)
    mapping = MappingSeadTableReader({"tbl_datasets": [native]})
    assert (
        api.rows_by_ids(
            "tbl_datasets",
            select="dataset_id",
            filter_field="site_id",
            ids=[1],
            order_by=(),
        )
        == mapping.rows_by_ids(
            "tbl_datasets",
            select="dataset_id",
            filter_field="site_id",
            ids=[1],
            order_by=(),
        )
        == [{"dataset_id": 5}]
    )
    assert requests == ["dataset_id,site_id", "dataset_id,site_id"]


@pytest.mark.parametrize("owner", [None, 2])
def test_internal_verification_owner_must_be_present_and_selected_before_next_page(
    owner: object,
) -> None:
    calls = []

    def fetch(_url: str, **kwargs: Any) -> object:
        calls.append(kwargs)
        row: dict[str, object] = {"dataset_id": 5}
        if owner is not None:
            row["site_id"] = owner
        return [row]

    with pytest.raises(ValueError):
        ApiSeadTableReader(fetch).rows_by_ids(
            "tbl_datasets",
            select="dataset_id",
            filter_field="site_id",
            ids=[1],
            order_by=(),
        )
    assert len(calls) == 1


@pytest.mark.parametrize("projection", ["*", "dataset_id,site_id"])
def test_explicit_native_owner_and_wildcard_preserve_source_spelling(
    projection: str,
) -> None:
    native = {"dataset_id": 5, "site_id": "001"}
    requests = []

    def fetch(_url: str, **kwargs: Any) -> object:
        requests.append(dict(kwargs["params"])["select"])
        return [native] if len(requests) == 1 else []

    assert ApiSeadTableReader(fetch).rows_by_ids(
        "tbl_datasets", select=projection, filter_field="site_id", ids=[1], order_by=()
    ) == [native]
    assert requests == [projection, projection]


@pytest.mark.parametrize(
    "projection,field",
    [
        (" dataset_id , site_id ", "site_id"),
        ("dataset_id,", "site_id"),
        ("owner:site_id", "site_id"),
        ("dataset_id", "site_id,foreign"),
        ("dataset_id", "site_id->field"),
    ],
)
def test_nonliteral_verification_projection_refuses_before_callback(
    projection: str, field: str
) -> None:
    """Filtered queries require unspaced literal fields, including explicit owners."""
    calls = []

    def fetch(_url: str, **kwargs: Any) -> object:
        calls.append(kwargs)
        return []

    with pytest.raises(ValueError, match="literal"):
        ApiSeadTableReader(fetch).rows_by_ids(
            "tbl_datasets", select=projection, filter_field=field, ids=[1], order_by=()
        )
    assert calls == []
