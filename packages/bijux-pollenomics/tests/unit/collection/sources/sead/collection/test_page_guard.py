"""Logical source pages remain bounded across capped responses and retries."""

from __future__ import annotations

from collections.abc import Sequence
from email.message import Message
from urllib.error import HTTPError

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.client import fetch_sead_rows
from bijux_pollenomics.collection.sources.sead.collection.validation import (
    StrictSeadPageFetcher,
)

URL = "https://example.invalid/tbl_sites"
PARAMS = [("select", "site_id"), ("latitude", "gte.55"), ("latitude", "lte.70")]


class SourcePages:
    def __init__(self, pages: Sequence[object]) -> None:
        self.pages = iter(pages)
        self.calls: list[tuple[str, object, object]] = []

    def __call__(self, url: str, **kwargs: object) -> object:
        self.calls.append((url, kwargs.get("params"), kwargs.get("headers")))
        page = next(self.pages)
        if isinstance(page, Exception):
            raise page
        return page


def request(
    guard: StrictSeadPageFetcher,
    start: int,
    *,
    params: object = None,
    url: str = URL,
    end: int | None = None,
) -> object:
    return guard(
        url,
        params=params,
        headers={"Range": f"{start}-{start + 999 if end is None else end}"},
    )


def test_server_capped_pages_reserve_budget_before_provider_call() -> None:
    source = SourcePages([[{"site_id": 1}], [{"site_id": 2}], [{"site_id": 3}]])
    guard = StrictSeadPageFetcher(source, max_pages=2)
    assert request(guard, 0) == [{"site_id": 1}]
    assert request(guard, 1) == [{"site_id": 2}]

    with pytest.raises(ValueError, match="pagination exceeded 2 pages"):
        request(guard, 2)
    assert len(source.calls) == 2


def test_terminal_empty_page_consumes_budget() -> None:
    source = SourcePages([[{"site_id": 1}], []])
    guard = StrictSeadPageFetcher(source, max_pages=1)
    request(guard, 0)
    with pytest.raises(ValueError, match="pagination exceeded 1 pages"):
        request(guard, 1)
    assert len(source.calls) == 1


@pytest.mark.parametrize("next_start", [0, 2])
def test_repeated_or_noncontiguous_successful_offsets_refuse(next_start: int) -> None:
    source = SourcePages([[{"site_id": 1}], [{"site_id": 2}]])
    guard = StrictSeadPageFetcher(source, max_pages=5)
    request(guard, 0)
    with pytest.raises(ValueError, match="contiguous|repeated"):
        request(guard, next_start)
    assert len(source.calls) == 1


def test_query_must_start_at_zero() -> None:
    source = SourcePages([[{"site_id": 1}]])
    guard = StrictSeadPageFetcher(source, max_pages=5)
    with pytest.raises(ValueError, match="contiguous"):
        request(guard, 1)
    assert not source.calls


def test_successful_empty_page_cannot_restart_query() -> None:
    source = SourcePages([[], [{"site_id": 1}]])
    guard = StrictSeadPageFetcher(source, max_pages=5)
    assert request(guard, 0) == []
    with pytest.raises(ValueError, match="completed|repeated"):
        request(guard, 0)
    assert len(source.calls) == 1


def test_transient_retry_reserves_one_page_not_two_attempts() -> None:
    error = TimeoutError("source unavailable")
    source = SourcePages([error, [{"site_id": 1}], []])
    guard = StrictSeadPageFetcher(source, max_pages=2)
    with pytest.raises(TimeoutError) as caught:
        request(guard, 0, params=PARAMS)
    assert caught.value is error
    assert request(guard, 0, params=list(PARAMS)) == [{"site_id": 1}]
    assert request(guard, 1, params=PARAMS) == []
    assert len(source.calls) == 3


@pytest.mark.parametrize("retry_start,retry_end", [(1, None), (0, 998)])
def test_failed_pending_range_cannot_be_skipped_or_replaced(
    retry_start: int, retry_end: int | None
) -> None:
    source = SourcePages([TimeoutError("source unavailable"), [{"site_id": 1}]])
    guard = StrictSeadPageFetcher(source, max_pages=2)
    with pytest.raises(TimeoutError):
        request(guard, 0)
    with pytest.raises(ValueError, match="pending|contiguous"):
        request(guard, retry_start, end=retry_end)
    assert len(source.calls) == 1


@pytest.mark.parametrize(
    "other_url,other_params",
    [
        (URL, [("select", "site_id"), ("site_id", "in.(2)")]),
        (URL, [("select", "site_id,latitude")]),
        (URL, list(reversed(PARAMS))),
        (URL, [("select", "site_id"), ("latitude", "gte.56"), ("latitude", "lte.70")]),
        ("https://different.invalid/tbl_sites", PARAMS),
    ],
)
def test_exact_queries_have_independent_page_budgets(
    other_url: str, other_params: object
) -> None:
    source = SourcePages([[{"site_id": 1}], [], [{"site_id": 2}], []])
    guard = StrictSeadPageFetcher(source, max_pages=2)
    request(guard, 0, params=PARAMS)
    assert request(guard, 1, params=PARAMS) == []
    assert request(guard, 0, params=other_params, url=other_url) == [{"site_id": 2}]
    assert request(guard, 1, params=other_params, url=other_url) == []


def test_copied_query_parameters_do_not_reset_page_budget() -> None:
    source = SourcePages([[{"site_id": 1}], [{"site_id": 2}]])
    guard = StrictSeadPageFetcher(source, max_pages=1)
    request(guard, 0, params=PARAMS)
    with pytest.raises(ValueError, match="pagination exceeded 1 pages"):
        request(guard, 1, params=tuple(PARAMS))
    assert len(source.calls) == 1


def test_query_snapshot_survives_caller_parameter_mutation() -> None:
    source = SourcePages([[{"site_id": 1}], [{"site_id": 2}], [{"site_id": 3}]])
    guard = StrictSeadPageFetcher(source, max_pages=1)
    params = list(PARAMS)
    request(guard, 0, params=params)
    params.append(("site_id", "in.(2)"))
    assert request(guard, 0, params=params) == [{"site_id": 2}]
    with pytest.raises(ValueError, match="pagination exceeded 1 pages"):
        request(guard, 1, params=PARAMS)
    assert len(source.calls) == 2


def test_different_queries_do_not_reset_capture_wide_native_identity_inventory() -> (
    None
):
    source = SourcePages([[{"site_id": 1}], [{"site_id": 1}]])
    guard = StrictSeadPageFetcher(source, max_pages=2)
    request(guard, 0, params=PARAMS)
    with pytest.raises(ValueError, match="Duplicate SEAD"):
        request(guard, 0, params=[("site_id", "in.(1)")])


@pytest.mark.parametrize("page", [{"error": "refused"}, [1], [{"site_id": 1.9}]])
def test_malformed_source_pages_remain_refused(page: object) -> None:
    guard = StrictSeadPageFetcher(SourcePages([page]), max_pages=2)
    with pytest.raises(ValueError, match="JSON array|non-object|Invalid required"):
        request(guard, 0)


def test_http_range_failure_preserves_original_object_and_distinct_batch() -> None:
    headers = Message()
    headers["Content-Range"] = "*/1"
    error = HTTPError(URL, 416, "range exhausted", headers, None)
    source = SourcePages([[{"site_id": 1}], error, [{"site_id": 2}], []])
    guard = StrictSeadPageFetcher(source, max_pages=2)
    request(guard, 0, params=PARAMS)
    with pytest.raises(HTTPError) as caught:
        request(guard, 1, params=PARAMS)
    assert caught.value is error
    assert request(guard, 0, params=[("site_id", "in.(2)")]) == [{"site_id": 2}]
    assert request(guard, 1, params=[("site_id", "in.(2)")]) == []


def test_outer_client_interprets_exact_range_eof_after_contiguous_prefix() -> None:
    headers = Message()
    headers["Content-Range"] = "*/1"
    error = HTTPError(URL, 416, "range exhausted", headers, None)
    source = SourcePages([[{"site_id": 1}], error])
    guard = StrictSeadPageFetcher(source, max_pages=2)
    assert fetch_sead_rows("tbl_sites", fetch_json_fn=guard, select="site_id") == [
        {"site_id": 1}
    ]
    assert len(source.calls) == 2
