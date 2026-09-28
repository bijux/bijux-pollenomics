"""Source-owned Rootsi/LandClim overlap and independence refusals."""

from __future__ import annotations

from copy import deepcopy
import csv
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.rootsi_landclim_overlap import (
    ROOTSI,
    SITES,
    build,
    reconcile,
)

REPOSITORY = Path(__file__).resolve().parents[4]


@pytest.fixture(scope="module")
def source_rows() -> tuple[
    list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]
]:
    publication = [
        json.loads(line)
        for line in (REPOSITORY / ROOTSI / "publication-candidates.jsonl")
        .read_text()
        .splitlines()
    ]
    with (REPOSITORY / ROOTSI / "rootsi-crosswalk.csv").open(newline="") as handle:
        crosswalk = list(csv.DictReader(handle))
    with (REPOSITORY / SITES).open(newline="") as handle:
        sites = list(csv.DictReader(handle))
    return publication, crosswalk, sites


def test_all_candidates_join_without_independent_truth(
    source_rows: tuple[
        list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]
    ],
) -> None:
    rows = reconcile(*source_rows)
    assert len(rows) == 79
    assert len({row["site_record_id"] for row in rows}) == 79
    assert all(
        row["independent_ground_truth"] == "refused_candidate_overlap" for row in rows
    )
    assert all(row["exact_grid_window_contribution"] == "unresolved" for row in rows)
    assert all(row["authenticated_workbook_identity"] == "unresolved" for row in rows)
    assert sum(row["coverage_comparability"] == "refused" for row in rows) == 44
    eke = next(row for row in rows if row["publication_sequence"] == "EKE")
    assert (
        eke["rootsi_samples"],
        eke["publication_samples"],
        eke["samples_agree"],
    ) == ("25", "42", "false")


def test_duplicate_site_candidate_is_refused(
    source_rows: tuple[
        list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]
    ],
) -> None:
    publication, crosswalk, sites = deepcopy(source_rows)
    candidate_ids = {
        f"937075:{row['publication_sequence_raw']}"
        for row in publication
        if row["candidate_status"] == "unique_rootsi_metadata_candidate"
    }
    other = next(
        row
        for row in sites
        if row["record_id"].startswith("937075:")
        and row["record_id"] not in candidate_ids
    )
    other["record_id"] = "937075:ABB"
    with pytest.raises(ValueError, match="site join is not unique"):
        reconcile(publication, crosswalk, sites)


def test_country_and_sample_drift_are_refused(
    source_rows: tuple[
        list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]
    ],
) -> None:
    publication, crosswalk, sites = deepcopy(source_rows)
    target = next(row for row in sites if row["record_id"] == "937075:ABB")
    target["country"] = "Finland"
    with pytest.raises(ValueError, match="site metadata"):
        reconcile(publication, crosswalk, sites)
    target["country"] = "Sweden"
    target["popup_rows_json"] = target["popup_rows_json"].replace(
        '["Pollen samples", "107"]', '["Pollen samples", "108"]'
    )
    with pytest.raises(ValueError, match="site metadata"):
        reconcile(publication, crosswalk, sites)


def test_refused_coverage_cannot_become_numeric_without_source_change(
    source_rows: tuple[
        list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]
    ],
) -> None:
    publication, crosswalk, sites = deepcopy(source_rows)
    alan = next(row for row in sites if row["record_id"] == "937075:ALAN")
    alan["time_start_bp"] = "0"
    with pytest.raises(ValueError, match="temporal meaning"):
        reconcile(publication, crosswalk, sites)


def test_governed_review_is_byte_identical_to_source_replay(tmp_path: Path) -> None:
    output = tmp_path / "overlap"
    build(REPOSITORY, output)
    governed = REPOSITORY / "docs/report/source-relations/rootsi-landclim-overlap"
    for name in ("overlap.csv", "report.json"):
        assert (output / name).read_bytes() == (governed / name).read_bytes()
