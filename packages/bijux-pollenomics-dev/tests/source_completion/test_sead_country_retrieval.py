"""Per-site SEAD discovery, retrieval and consumer country checks."""

from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.sead_country_retrieval import (
    BOUNDARY,
    PINNED,
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
def documents(synthetic_historical_sead_review: dict[str, Any]) -> Documents:
    raw = REPOSITORY / RAW
    with (REPOSITORY / PUBLIC).open(encoding="utf-8", newline="") as handle:
        public = list(csv.DictReader(handle))
    return (
        json.loads((raw / "country-decisions.json").read_text()),
        synthetic_historical_sead_review,
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
    reconcile(*documents)
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


def test_default_refuses_current_boundary_review(tmp_path: Path) -> None:
    current = (REPOSITORY / BOUNDARY).read_bytes()
    assert hashlib.sha256(current).hexdigest() != PINNED[BOUNDARY]
    with pytest.raises(
        ValueError, match=f"^Pinned SEAD input changed: {re.escape(BOUNDARY.as_posix())}$"
    ):
        build(REPOSITORY, tmp_path / "country-retrieval")


def test_historical_report_is_byte_identical_when_git_object_is_retained(
    tmp_path: Path,
) -> None:
    revision = "28ffb5dd71fa03ec159f6a50a142c12402114593"
    git_env = dict(os.environ, GIT_NO_LAZY_FETCH="1", GIT_NO_REPLACE_OBJECTS="1")
    try:
        object_name = f"{revision}:{BOUNDARY.as_posix()}"
        present = subprocess.run(
            ["git", "cat-file", "-e", object_name],
            cwd=REPOSITORY,
            env=git_env,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError:
        pytest.skip("Git is unavailable; historical ledger replay not executed")
    if present.returncode:
        pytest.skip("Exact historical ledger Git object is unavailable")
    result = subprocess.run(
        ["git", "show", object_name],
        cwd=REPOSITORY,
        env=git_env,
        capture_output=True,
        timeout=30,
        check=True,
    )
    assert hashlib.sha256(result.stdout).hexdigest() == PINNED[BOUNDARY]
    scratch = tmp_path / "historical-repository"
    for relative in PINNED:
        target = scratch / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative == BOUNDARY:
            target.write_bytes(result.stdout)
        else:
            shutil.copyfile(REPOSITORY / relative, target)
    output = tmp_path / "country-retrieval"
    build(scratch, output)
    governed = REPOSITORY / "docs/report/source-relations/sead-country-retrieval"
    for name in ("countries.csv", "sites.csv", "report.json"):
        assert (output / name).read_bytes() == (governed / name).read_bytes()
