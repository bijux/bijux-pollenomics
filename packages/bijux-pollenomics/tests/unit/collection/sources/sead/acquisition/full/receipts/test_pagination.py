"""Receipts distinguish source EOF from a server-capped short page."""

from __future__ import annotations

from collections.abc import Callable
from email.message import Message
from typing import cast
from urllib.error import HTTPError

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    SeadAcquisitionError,
    SeadTableAcquisition,
    acquire_sead_table,
)


def _acquire(
    fetch: Callable[..., object], *, max_pages: int = 10000
) -> SeadTableAcquisition:
    return acquire_sead_table(
        "tbl_sites",
        fetch_json_fn=fetch,
        select="site_id",
        order_by=("site_id",),
        country_scope=("SE", "DK", "NO", "FI"),
        spatial_scope={"scope_id": "scope"},
        parent_run_id="parent",
        build_id="build",
        max_pages=max_pages,
        request_retries=1,
    )


def _range_error(*values: str) -> HTTPError:
    headers = Message()
    for value in values:
        headers["Content-Range"] = value
    return HTTPError(
        "https://browser.sead.se/postgrest/tbl_sites",
        416,
        "range unsatisfied",
        headers,
        None,
    )


def test_capped_pages_keep_every_row_and_record_contiguous_eof() -> None:
    source = [{"site_id": value} for value in range(1, 6)]

    def fetch(_url: str, **kwargs: object) -> object:
        start = int(cast(dict[str, str], kwargs["headers"])["Range"].split("-")[0])
        return source[start : start + 2]

    result = _acquire(fetch)
    assert list(result.rows) == source
    assert result.receipt["pagination"] == {
        "profile": "received_rows_source_eof",
        "page_size": 1000,
        "max_pages": 10000,
        "complete": True,
        "pages": [
            {"page": 1, "range": "0-999", "row_count": 2},
            {"page": 2, "range": "2-1001", "row_count": 2},
            {"page": 3, "range": "4-1003", "row_count": 1},
            {
                "page": 4,
                "range": "5-1004",
                "row_count": 0,
                "eof": {"kind": "empty_json_array"},
            },
        ],
    }


@pytest.mark.parametrize("population", [0, 2])
def test_exact_unsatisfied_range_retains_terminal_status_and_header(
    population: int,
) -> None:
    source = [{"site_id": value} for value in range(1, population + 1)]

    def fetch(_url: str, **kwargs: object) -> object:
        start = int(cast(dict[str, str], kwargs["headers"])["Range"].split("-")[0])
        if start == population:
            raise _range_error(f"*/{population}")
        return source

    result = _acquire(fetch)
    pages = cast(dict[str, object], result.receipt["pagination"])["pages"]
    terminal = cast(list[dict[str, object]], pages)[-1]
    assert terminal["row_count"] == 0
    assert terminal["eof"] == {
        "kind": "unsatisfied_range",
        "response_status": 416,
        "content_range": f"*/{population}",
    }
    assert result.receipt["failures"] == []


@pytest.mark.parametrize(
    "headers", [(), ("*/0",), ("*/2",), ("0-0/1",), ("*/1", "*/2"), ("*/1", "*/1")]
)
def test_unbound_range_refusal_preserves_failed_partial_receipt(
    headers: tuple[str, ...],
) -> None:
    responses: list[object] = [[{"site_id": 1}], _range_error(*headers)]

    def fetch(_url: str, **_kwargs: object) -> object:
        value = responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    with pytest.raises(SeadAcquisitionError) as raised:
        _acquire(fetch)
    assert raised.value.result.rows == ({"site_id": 1},)
    assert raised.value.result.receipt["status"] == "partial"
    assert raised.value.result.receipt["failure_reason"] == "terminal_request_failure"


def test_page_budget_does_not_promote_an_unconfirmed_short_page() -> None:
    with pytest.raises(SeadAcquisitionError) as raised:
        _acquire(lambda *_args, **_kwargs: [{"site_id": 1}], max_pages=1)
    assert raised.value.result.rows == ({"site_id": 1},)
    assert raised.value.result.receipt["status"] == "partial"
    assert raised.value.result.receipt["failure_reason"] == "page_limit_exceeded"


def test_oversized_page_refuses_without_archiving_any_rows() -> None:
    with pytest.raises(SeadAcquisitionError) as raised:
        _acquire(
            lambda *_args, **_kwargs: [{"site_id": value} for value in range(1001)]
        )
    assert raised.value.result.rows == ()
    assert raised.value.result.receipt["status"] == "failed"
    assert (
        raised.value.result.receipt["failure_reason"] == "page_size_contract_violation"
    )
