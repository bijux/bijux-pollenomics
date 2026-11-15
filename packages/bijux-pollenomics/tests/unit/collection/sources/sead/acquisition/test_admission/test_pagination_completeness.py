"""Source EOF receipt admission and immutable legacy pagination boundaries."""

from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy
from email.message import Message
from typing import cast
from urllib.error import HTTPError

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.admission.validation import (
    receipts as admission_receipts,
)
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    acquire_sead_table,
)

from .fixtures import (
    _BUILD_ID,
    _PARENT_RUN_ID,
    _RUN_ID,
    _SCOPE_ID,
    _query_receipt,
    _refresh_query_receipt,
)


def _source_eof_receipt(*, unsatisfied_range: bool) -> dict[str, object]:
    source = [{"site_id": 1}, {"site_id": 2}]

    def fetch(_url: str, **kwargs: object) -> object:
        start = int(cast(dict[str, str], kwargs["headers"])["Range"].split("-")[0])
        if start == 2 and unsatisfied_range:
            headers = Message()
            headers["Content-Range"] = "*/2"
            raise HTTPError(
                "https://browser.sead.se/postgrest/tbl_sites",
                416,
                "range unsatisfied",
                headers,
                None,
            )
        return source[start : start + 1]

    return acquire_sead_table(
        "tbl_sites",
        fetch_json_fn=fetch,
        select="site_id",
        order_by=("site_id",),
        country_scope=("SE", "DK", "NO", "FI"),
        spatial_scope={"scope_id": _SCOPE_ID},
        parent_run_id=_PARENT_RUN_ID,
        build_id=_BUILD_ID,
    ).receipt


def _validate_query_profile(query: dict[str, object]) -> int:
    return admission_receipts._validate_acquisition_receipt(
        query,
        table="tbl_sites",
        identities={
            "scope_id": _SCOPE_ID,
            "run_id": _RUN_ID,
            "parent_run_id": _PARENT_RUN_ID,
            "build_id": _BUILD_ID,
        },
        label="source EOF query",
        require_orchestration_identity=False,
        expected_parameters=cast(Sequence[Sequence[str]], query["parameters"]),
        expected_order=cast(Sequence[str], query["order_by"]),
        expected_max_pages=10_000,
        expected_rows=[{"site_id": 1}, {"site_id": 2}],
    )


@pytest.mark.parametrize("unsatisfied_range", [False, True])
def test_produced_eof_receipt_admits_its_exact_contiguous_population(
    unsatisfied_range: bool,
) -> None:
    assert (
        _validate_query_profile(
            _source_eof_receipt(unsatisfied_range=unsatisfied_range)
        )
        == 2
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_profile",
        "removed_profile",
        "removed_profile_and_proofs",
        "wrong_offset",
        "nonempty_terminal",
        "missing_terminal_proof",
        "wrong_terminal_status",
        "wrong_terminal_header",
        "nonterminal_eof",
    ],
)
def test_rehashed_eof_profile_mutations_refuse(mutation: str) -> None:
    query = _source_eof_receipt(unsatisfied_range=True)
    pagination = cast(dict[str, object], query["pagination"])
    pages = cast(list[dict[str, object]], pagination["pages"])
    proof = cast(dict[str, object], pages[-1]["eof"])
    if mutation == "unknown_profile":
        pagination["profile"] = "legacy"
    elif mutation.startswith("removed_profile"):
        del pagination["profile"]
        if mutation == "removed_profile_and_proofs":
            for page in pages:
                page.pop("eof", None)
    elif mutation == "wrong_offset":
        pages[1]["range"] = "1000-1999"
    elif mutation == "nonempty_terminal":
        pages[-1]["row_count"] = 1
    elif mutation == "missing_terminal_proof":
        del pages[-1]["eof"]
    elif mutation == "wrong_terminal_status":
        proof["response_status"] = 200
    elif mutation == "wrong_terminal_header":
        proof["content_range"] = "*/1"
    elif mutation == "nonterminal_eof":
        pages[0]["eof"] = {"kind": "empty_json_array"}
    _refresh_query_receipt(query)
    with pytest.raises(ValueError):
        _validate_query_profile(query)


def test_legacy_short_page_receipt_remains_unchanged_without_modern_eof_claim() -> None:
    query = _query_receipt(
        "tbl_sites",
        rows=[{"site_id": 1}, {"site_id": 2}],
        spatial_scope={"scope_id": _SCOPE_ID},
    )
    original = deepcopy(query)
    assert _validate_query_profile(query) == 2
    assert query == original
    assert "profile" not in cast(dict[str, object], query["pagination"])
