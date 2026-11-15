"""Pagination must terminate honestly and preserve collection-unit identity."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.client import fetch_neotoma_api_rows


def row(unit: int, *, site: int = 1, name: str = "source") -> dict[str, object]:
    return {"site": {"siteid": site, "collectionunitid": unit, "sitename": name}}


def fetch(pages: Iterable[list[dict[str, object]]], **options: Any) -> list[object]:
    iterator = iter(pages)

    def page(*_: object, **__: object) -> dict[str, object]:
        try:
            chunk = next(iterator)
        except StopIteration:
            pytest.fail("Paginator accessed another page after it should have refused")
        return {"status": "success", "data": chunk}

    return fetch_neotoma_api_rows(
        "datasets",
        fetch_neotoma_api_payload_fn=page,
        neotoma_datasettype="pollen",
        neotoma_limit=2,
        extra_params=None,
        **options,
    )


def test_repeated_full_page_refuses_before_requesting_a_third_page() -> None:
    page = [row(10), row(11)]
    with pytest.raises(ValueError, match="Neotoma.*duplicate"):
        fetch([page, page])


def test_partial_overlap_refuses_even_when_native_metadata_changes() -> None:
    with pytest.raises(ValueError, match="Neotoma.*collection unit"):
        fetch([[row(10), row(11)], [row(11, name="changed metadata")]])


def test_distinct_units_at_one_site_are_not_duplicate_sites() -> None:
    pages = [[row(10), row(11)], [row(12)]]
    assert fetch(pages) == [row(10), row(11), row(12)]


def test_page_budget_requires_successful_short_or_empty_termination() -> None:
    with pytest.raises(ValueError, match="Neotoma.*page budget"):
        fetch([[row(10), row(11)], [row(12), row(13)]], max_pages=2)
    assert fetch([[row(10), row(11)], []], max_pages=2) == [row(10), row(11)]


@pytest.mark.parametrize("name", ["limit", "offset"])
def test_extra_parameters_cannot_override_owned_pagination(name: str) -> None:
    calls: list[object] = []

    def request(*args: object, **kwargs: object) -> dict[str, object]:
        calls.append(args)
        return {"data": []}

    with pytest.raises(ValueError, match="Neotoma.*pagination"):
        fetch_neotoma_api_rows(
            "datasets",
            fetch_neotoma_api_payload_fn=request,
            neotoma_datasettype="pollen",
            neotoma_limit=2,
            extra_params={name: "1"},
        )
    assert calls == []


@pytest.mark.parametrize("limit", [True, 0, -1, 2.5, 10001])
def test_page_limit_is_a_positive_officially_bounded_integer(limit: Any) -> None:
    with pytest.raises(ValueError, match="Neotoma.*limit"):
        fetch_neotoma_api_rows(
            "datasets",
            fetch_neotoma_api_payload_fn=lambda *a, **k: {"data": []},
            neotoma_datasettype="pollen",
            neotoma_limit=limit,
            extra_params=None,
        )


@pytest.mark.parametrize("budget", [True, 0, -1, 2.5])
def test_page_budget_is_a_positive_integer(budget: Any) -> None:
    with pytest.raises(ValueError, match="Neotoma.*page budget"):
        fetch([[]], max_pages=budget)


def test_response_cannot_exceed_its_requested_page_limit() -> None:
    with pytest.raises(ValueError, match="Neotoma.*limit"):
        fetch([[row(10), row(11), row(12)]])
