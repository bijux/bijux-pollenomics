from __future__ import annotations

from urllib.error import HTTPError, URLError

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    SeadAcquisitionError,
)

from .support import _acquire


def test_rate_limit_retry_honors_server_delay() -> None:
    from bijux_pollenomics.collection.sources.sead.acquisition.full import (
        acquire_sead_table,
    )

    waits: list[float] = []
    responses: list[object] = [
        HTTPError(
            "https://browser.sead.se", 429, "rate limited", {"Retry-After": "7"}, None
        ),
        [{"site_id": 1}],
    ]

    def fetch_json(_url: str, **_kwargs: object) -> object:
        value = responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    result = acquire_sead_table(
        "tbl_sites",
        fetch_json_fn=fetch_json,
        select="site_id",
        order_by=("site_id",),
        country_scope=("SE", "DK", "NO", "FI"),
        spatial_scope={"bbox": [4, 54, 35, 72]},
        parent_run_id="rate-limit-test",
        build_id="rate-limit-test",
        sleep_fn=waits.append,
    )
    assert waits == [7.0]
    assert result.receipt["status"] == "complete"
    assert result.receipt["result"]["retry_count"] == 1


def test_long_server_delay_fails_closed_without_early_retry() -> None:
    calls = 0

    def fetch_json(_url: str, **_kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise HTTPError(
            "https://browser.sead.se", 429, "rate limited", {"Retry-After": "120"}, None
        )

    with pytest.raises(SeadAcquisitionError) as raised:
        _acquire(fetch_json)

    assert calls == 1
    assert raised.value.result.receipt["status"] == "failed"
    assert raised.value.result.receipt["failure_reason"] == "terminal_request_failure"


def test_complete_paginated_receipt_captures_retry_schema_and_content() -> None:
    calls: list[dict[str, object]] = []
    responses: list[object] = [
        URLError("transient"),
        [{"site_id": 1, "site_name": "A"}, {"site_id": 2, "site_name": None}],
        [{"site_id": 3, "site_name": "C"}],
    ]

    def fetch_json(_url: str, **kwargs: object) -> object:
        calls.append(kwargs)
        value = responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    result = _acquire(fetch_json)

    assert [row["site_id"] for row in result.rows] == [1, 2, 3]
    assert [call["headers"] for call in calls] == [
        {"Range-Unit": "items", "Range": "0-1"},
        {"Range-Unit": "items", "Range": "0-1"},
        {"Range-Unit": "items", "Range": "2-3"},
    ]
    receipt = result.receipt
    assert receipt["status"] == "complete"
    assert receipt["row_count"] == 3
    assert receipt["source_schema_version"] is None
    assert receipt["source_schema_version_status"] == "not_reported_by_endpoint"
    assert receipt["pagination"] == {
        "page_size": 2,
        "max_pages": 3,
        "pages": [
            {"page": 1, "range": "0-1", "row_count": 2},
            {"page": 2, "range": "2-3", "row_count": 1},
        ],
        "complete": True,
    }
    fields = receipt["canonical_schema"]["fields"]  # type: ignore[index]
    assert fields == [
        {
            "name": "site_id",
            "presence_count": 3,
            "null_count": 0,
            "json_types": ["integer"],
        },
        {
            "name": "site_name",
            "presence_count": 3,
            "null_count": 1,
            "json_types": ["null", "string"],
        },
    ]


def test_terminal_page_failure_carries_partial_receipt() -> None:
    responses: list[object] = [
        [{"site_id": 1}, {"site_id": 2}],
        URLError("still unavailable"),
        URLError("still unavailable"),
    ]

    def fetch_json(_url: str, **_kwargs: object) -> object:
        value = responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    with pytest.raises(SeadAcquisitionError) as raised:
        _acquire(fetch_json)

    result = raised.value.result
    assert result.receipt["status"] == "partial"
    assert result.receipt["failure_reason"] == "terminal_request_failure"
    assert result.receipt["pagination"]["complete"] is False  # type: ignore[index]
    assert result.receipt["row_count"] == 2
    assert len(result.receipt["failures"]) == 2  # type: ignore[arg-type]
