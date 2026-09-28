"""Author name leads retain source counts without granting ecological admission."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.neotoma_author_taxonomy_candidates import (
    CONCEPTS,
    PRIORITY,
    derive,
)

REPOSITORY = Path(__file__).resolve().parents[4]
REPORT = Path(
    "docs/report/source-relations/neotoma/author-taxonomy-candidates/report.json"
)


def _inputs() -> tuple[dict[str, object], dict[str, object], dict[str, str]]:
    priority = json.loads((REPOSITORY / PRIORITY).read_text(encoding="utf-8"))
    concepts = json.loads((REPOSITORY / CONCEPTS).read_text(encoding="utf-8"))
    retained = json.loads((REPOSITORY / REPORT).read_text(encoding="utf-8"))
    lookup = {
        row["source_reported_name"]: row["author_lookup_target"]
        for row in retained["rows"]
        if row["author_lookup_target"] is not None
    }
    return priority, concepts, lookup


def test_literal_leads_close_priority_counts_without_admission() -> None:
    report = derive(*_inputs())
    assert report["priority_concept_count"] == 1006
    assert report["concept_counts_by_literal_status"] == {
        "author_excluded": 668,
        "author_target": 136,
        "unmatched": 202,
    }
    assert report["observation_counts_by_literal_status"] == {
        "author_excluded": 71836,
        "author_target": 150493,
        "unmatched": 5994,
    }
    assert report["lra_accepted_samples"] == 0
    assert report["scientific_admission_allowed"] is False
    betula = [row for row in report["rows"] if row["source_reported_name"] == "Betula"]
    assert {row["source_unit"] for row in betula} == {"NISP", "NISP digitized"}
    assert all(row["scientific_admission_allowed"] is False for row in betula)


def test_review_promotion_requires_new_decision() -> None:
    priority, concepts, lookup = _inputs()
    changed = deepcopy(concepts)
    by_id = {row["review_row_id"]: row for row in changed["rows"]}
    by_id[priority["rows"][0]["review_row_id"]]["review_state"] = "accepted"
    with pytest.raises(ValueError, match="review decision"):
        derive(priority, changed, lookup)
