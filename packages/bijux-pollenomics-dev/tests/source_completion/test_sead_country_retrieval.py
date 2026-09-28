"""Per-site SEAD discovery, retrieval and consumer country checks."""

from __future__ import annotations

from copy import deepcopy
import csv
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.sead_country_retrieval import (
    BOUNDARY,
    PUBLIC,
    RAW,
    build,
    reconcile,
)

REPOSITORY = Path(__file__).resolve().parents[4]
Documents = tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    list[dict[str, str]],
    dict[str, Any],
]


@pytest.fixture(scope="module")
def documents() -> Documents:
    raw = REPOSITORY / RAW
    with (REPOSITORY / PUBLIC).open(encoding="utf-8", newline="") as handle:
        public = list(csv.DictReader(handle))
    return (
        json.loads((raw / "country-decisions.json").read_text()),
        json.loads((REPOSITORY / BOUNDARY).read_text()),
        json.loads((raw / "receipts/tbl_sites.json").read_text()),
        json.loads((raw / "payloads/tbl_sites.json").read_text()),
        public,
        json.loads((raw / "reconciliation/countries.json").read_text()),
    )


def test_governed_discovery_retrieval_and_public_consumer(documents: Documents) -> None:
    countries, sites = reconcile(*documents)
    assert len(sites) == 2195
    assert [
        (
            row["group"],
            row["discovered_with_governed_country"],
            row["retrieved_payload"],
        )
        for row in countries
    ] == [
        ("SE", 1925, 1925),
        ("DK", 59, 59),
        ("NO", 45, 45),
        ("FI", 40, 40),
        ("REVIEW", 103, 0),
        ("UNASSIGNED", 23, 0),
    ]
    assert {row["source_country"] for row in sites} == {"not_supplied"}
    assert sum(row["retrieved_payload"] == "true" for row in sites) == 2069
    assert all(
        row["governed_country_code"] == "" and row["normalized_country"] == ""
        for row in sites
        if row["country_decision_status"] != "assigned"
    )


def test_excluded_coordinate_cannot_enter_retrieved_payload(
    documents: Documents,
) -> None:
    inputs = deepcopy(documents)
    excluded = next(
        row
        for row in inputs[0]["decisions"]
        if row["decision"]["decision_status"] == "review"
    )
    inputs[3]["rows"][0]["site_id"] = excluded["site_id"]
    with pytest.raises(ValueError, match="Excluded coordinates entered retrieval"):
        reconcile(*inputs)


def test_boundary_review_cannot_be_promoted_to_country(documents: Documents) -> None:
    inputs = deepcopy(documents)
    review = next(
        row
        for row in inputs[1]["decisions"]
        if row["country_decision_status"] == "review"
    )
    review["published_country"] = "SE"
    with pytest.raises(ValueError, match="source/governed country divergence"):
        reconcile(*inputs)


def test_normalized_uuid_drift_is_refused(documents: Documents) -> None:
    inputs = deepcopy(documents)
    inputs[4][0]["site_uuid"] = "changed-uuid"
    with pytest.raises(ValueError, match="retrieved/public identity diverged"):
        reconcile(*inputs)


def test_governed_report_is_byte_identical_to_source_replay(tmp_path: Path) -> None:
    output = tmp_path / "country-retrieval"
    build(REPOSITORY, output)
    governed = REPOSITORY / "docs/report/source-relations/sead-country-retrieval"
    for name in ("countries.csv", "sites.csv", "report.json"):
        assert (output / name).read_bytes() == (governed / name).read_bytes()
