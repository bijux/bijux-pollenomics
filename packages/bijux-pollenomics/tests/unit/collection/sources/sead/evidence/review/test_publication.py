from __future__ import annotations

import csv
import io
import json
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.sead.evidence.review.publication import (
    render_candidate_csv,
    render_review_json,
    render_review_markdown,
)
from bijux_pollenomics.collection.sources.sead.evidence.review.service import (
    build_sead_scientific_classification_review,
)
from tests.support.repository import REPOSITORY_ROOT

pytestmark = pytest.mark.generated_artifacts

_REVIEW_ROOT = REPOSITORY_ROOT / "data/sead/review"


def test_governed_review_outputs_are_a_fixed_point() -> None:
    packet = build_sead_scientific_classification_review(REPOSITORY_ROOT / "data")

    assert render_review_json(packet) == (
        _REVIEW_ROOT / "scientific_classification_review.json"
    ).read_text(encoding="utf-8")
    assert render_review_markdown(packet) == (
        _REVIEW_ROOT / "scientific_classification_review.md"
    ).read_text(encoding="utf-8")
    assert render_candidate_csv(packet) == (
        _REVIEW_ROOT / "scientific_classification_candidates.csv"
    ).read_text(encoding="utf-8")


def test_review_worksheet_has_one_non_accepting_row_per_taxon() -> None:
    rows = list(
        csv.DictReader(
            io.StringIO(
                (_REVIEW_ROOT / "scientific_classification_candidates.csv").read_text(
                    encoding="utf-8"
                )
            )
        )
    )

    assert len(rows) == 1_974
    assert len({row["taxon_id"] for row in rows}) == 1_974
    assert all(
        row["review_status"] == "pending_qualified_scientific_review" for row in rows
    )
    assert all(row["current_classification_status"] == "not_accepted" for row in rows)
    assert all(row["propagation_allowed"] == "False" for row in rows)
    assert all(row["proposed_accepted_taxon_concept_id"] == "" for row in rows)
    assert all(row["reviewer_id"] == "" and row["decision_date"] == "" for row in rows)
    assert len({row["source_run_id"] for row in rows}) == 1
    assert len({row["build_id"] for row in rows}) == 1
    assert len({row["acquisition_manifest_sha256"] for row in rows}) == 1
    assert len({row["parent_admission_sha256"] for row in rows}) == 1
    assert len({row["evidence_manifest_sha256"] for row in rows}) == 1
    assert len({row["evidence_file_set_sha256"] for row in rows}) == 1
    assert (
        sum(row["review_priority"] == "plant_ecocode_candidate" for row in rows) == 173
    )
    assert sum(int(row["source_ecocode_count"]) for row in rows) == 9_260


def test_review_markdown_names_nested_reasons_and_conflicting_citation() -> None:
    markdown = (_REVIEW_ROOT / "scientific_classification_review.md").read_text(
        encoding="utf-8"
    )
    packet = cast(
        dict[str, object],
        json.loads(
            (_REVIEW_ROOT / "scientific_classification_review.json").read_text(
                encoding="utf-8"
            )
        ),
    )

    assert "qualified human review" in markdown
    assert "Ptinidae beetles" in markdown
    assert "umbrella reason" in markdown
    assert "must not be added" in markdown
    assert (
        "does not establish arrival, migration, causation, or propagation" in markdown
    )
    assert (
        cast(dict[str, object], packet["review_posture"])["accepted_mapping_count"] == 0
    )
