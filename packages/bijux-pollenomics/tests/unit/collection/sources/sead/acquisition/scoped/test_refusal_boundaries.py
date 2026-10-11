"""Scoped acquisition refusal and completeness boundaries."""

from __future__ import annotations

from copy import deepcopy
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    SeadAcquisitionError,
)

from .source_tables import _source_tables
from .support import _PostgrestFixture, _run


def test_scoped_acquisition_rejects_a_source_that_ignores_dependency_filter(
    tmp_path: Path,
) -> None:
    fetcher = _PostgrestFixture(
        _source_tables(), ignore_filter_table="tbl_sample_groups"
    )

    with pytest.raises(ValueError, match="ignored dependency filter"):
        _run(tmp_path.resolve(), fetcher)

    assert not (tmp_path / "run-fixture-001").exists()


def test_scoped_acquisition_refuses_an_unresolved_lookup_reference(
    tmp_path: Path,
) -> None:
    tables = deepcopy(_source_tables())
    tables["tbl_age_types"] = []

    with pytest.raises(ValueError, match="age_types.analysis_dating_ranges"):
        _run(tmp_path.resolve(), _PostgrestFixture(tables))

    assert not (tmp_path / "run-fixture-001").exists()


def test_scoped_acquisition_refuses_unproven_page_completion(tmp_path: Path) -> None:
    fetcher = _PostgrestFixture(
        _source_tables(), never_finish_table="tbl_sample_groups"
    )

    with pytest.raises(SeadAcquisitionError) as exc_info:
        _run(
            tmp_path.resolve(),
            fetcher,
            id_batch_size=10,
            page_size=3,
            max_pages=2,
        )

    assert exc_info.value.result.table == "tbl_sample_groups"
    assert exc_info.value.result.receipt["status"] == "partial"
    assert exc_info.value.result.receipt["failure_reason"] == "page_limit_exceeded"
    assert not (tmp_path / "run-fixture-001").exists()


def test_scoped_acquisition_requires_an_explicit_disposition_for_every_bbox_site(
    tmp_path: Path,
) -> None:
    assignments = {1: "SE", 2: "DK", 3: "NO", 4: "FI"}

    with pytest.raises(ValueError, match="must exactly cover bbox sites"):
        _run(
            tmp_path.resolve(),
            _PostgrestFixture(_source_tables()),
            governed_country_by_site_id=assignments,
        )

    assert not (tmp_path / "run-fixture-001").exists()


@pytest.mark.parametrize(
    "failure",
    [
        HTTPError("https://browser.sead.se", 403, "denied", Message(), None),
        URLError("source unavailable"),
    ],
)
def test_linked_source_failure_preserves_site_input_without_publishing_dates(
    tmp_path: Path, failure: Exception
) -> None:
    tables = _source_tables()
    fetcher = _PostgrestFixture(tables)

    def interrupted_fetch(
        endpoint: str,
        *,
        params: list[tuple[str, str]],
        headers: dict[str, str],
        timeout: float,
    ) -> object:
        if endpoint.endswith("/tbl_analysis_entity_ages"):
            raise failure
        return fetcher(endpoint, params=params, headers=headers, timeout=timeout)

    with pytest.raises(SeadAcquisitionError) as raised:
        _run(tmp_path.resolve(), interrupted_fetch, request_retries=1)

    assert raised.value.result.table == "tbl_analysis_entity_ages"
    assert raised.value.result.receipt["status"] == "failed"
    assert raised.value.result.receipt["failure_reason"] == "terminal_request_failure"
    assert len(tables["tbl_sites"]) == 6
    assert not (tmp_path / "run-fixture-001").exists()


def test_empty_bbox_response_cannot_replace_governed_site_inventory(
    tmp_path: Path,
) -> None:
    tables = _source_tables()
    fetcher = _PostgrestFixture(tables)

    def empty_sites(
        endpoint: str,
        *,
        params: list[tuple[str, str]],
        headers: dict[str, str],
        timeout: float,
    ) -> object:
        if endpoint.endswith("/tbl_sites"):
            return []
        return fetcher(endpoint, params=params, headers=headers, timeout=timeout)

    with pytest.raises(ValueError, match="must exactly cover bbox sites"):
        _run(tmp_path.resolve(), empty_sites)

    assert len(tables["tbl_sites"]) == 6
    assert not (tmp_path / "run-fixture-001").exists()
