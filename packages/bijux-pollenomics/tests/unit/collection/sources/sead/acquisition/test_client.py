"""Public SEAD collection must prove EOF without dropping provider members."""

from __future__ import annotations

from email.message import Message
from typing import cast
from urllib.error import HTTPError

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition import client


@pytest.mark.parametrize(
    "payload",
    [
        {"message": "provider error"},
        [{"site_id": 1}, "unread source member"],
        [{"site_id": value} for value in range(1001)],
    ],
)
def test_invalid_pages_refuse_instead_of_returning_partial_success(
    payload: object,
) -> None:
    calls = 0

    def fetch(_url: str, **_kwargs: object) -> object:
        nonlocal calls
        calls += 1
        if calls > 1:
            raise AssertionError(
                "malformed first page must refuse before another request"
            )
        return payload

    with pytest.raises(ValueError):
        client.fetch_sead_rows("tbl_sites", select="site_id", fetch_json_fn=fetch)


@pytest.mark.parametrize("population", [0, 1, 5])
def test_server_cap_advances_by_received_rows_until_empty_eof(population: int) -> None:
    source = [{"site_id": value} for value in range(1, population + 1)]
    ranges: list[str] = []

    def fetch(_url: str, **kwargs: object) -> object:
        requested = cast(dict[str, str], kwargs["headers"])["Range"]
        ranges.append(requested)
        start = int(requested.split("-")[0])
        return source[start : start + 2]

    assert (
        client.fetch_sead_rows("tbl_sites", select="site_id", fetch_json_fn=fetch)
        == source
    )
    assert (
        ranges
        == {
            0: ["0-999"],
            1: ["0-999", "1-1000"],
            5: ["0-999", "2-1001", "4-1003", "5-1004"],
        }[population]
    )


def test_invalid_response_after_short_page_refuses() -> None:
    responses: list[object] = [[{"site_id": 1}], {"message": "provider error"}]
    with pytest.raises(ValueError):
        client.fetch_sead_rows(
            "tbl_sites",
            select="site_id",
            fetch_json_fn=lambda *_args, **_kwargs: responses.pop(0),
        )


def _range_error(*ranges: str) -> HTTPError:
    headers = Message()
    for value in ranges:
        headers["Content-Range"] = value
    return HTTPError(
        "https://browser.sead.se/postgrest/tbl_sites",
        416,
        "range unsatisfied",
        headers,
        None,
    )


@pytest.mark.parametrize("population", [0, 2])
def test_exact_range_exhaustion_confirms_contiguous_source_prefix(
    population: int,
) -> None:
    source = [{"site_id": value} for value in range(1, population + 1)]

    def fetch(_url: str, **kwargs: object) -> object:
        start = int(cast(dict[str, str], kwargs["headers"])["Range"].split("-")[0])
        if start == population:
            raise _range_error(f"*/{population}")
        return source

    assert (
        client.fetch_sead_rows("tbl_sites", select="site_id", fetch_json_fn=fetch)
        == source
    )


@pytest.mark.parametrize(
    "ranges", [(), ("*/0",), ("*/2",), ("0-0/1",), ("*/1", "*/2"), ("*/1", "*/1")]
)
def test_ambiguous_or_noncontiguous_range_error_never_proves_eof(
    ranges: tuple[str, ...],
) -> None:
    responses: list[object] = [[{"site_id": 1}], _range_error(*ranges)]

    def fetch(_url: str, **_kwargs: object) -> object:
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    with pytest.raises(HTTPError):
        client.fetch_sead_rows("tbl_sites", select="site_id", fetch_json_fn=fetch)


def test_nonempty_source_cannot_exceed_page_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client, "SEAD_MAX_PAGES", 2, raising=False)
    calls = 0

    def fetch(_url: str, **_kwargs: object) -> object:
        nonlocal calls
        calls += 1
        return [{"site_id": calls}]

    with pytest.raises(ValueError, match="pagination exceeded"):
        client.fetch_sead_rows("tbl_sites", select="site_id", fetch_json_fn=fetch)
    assert calls == 2
