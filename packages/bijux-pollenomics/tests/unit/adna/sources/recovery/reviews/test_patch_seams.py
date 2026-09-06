"""Call-time dependency seams retained by the compatibility facade."""

from __future__ import annotations

from pathlib import Path

import pytest
from bijux_pollenomics.adna.sources.recovery import reviews


def test_stage_review_resolves_project_rows_from_the_facade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(reviews, "_project_recovery_rows", lambda output_root: [])

    payload = reviews.build_project_recovery_stage_review(Path("unused"))

    assert payload["row_count"] == 0
    assert payload["summary"] == {
        "complete_projects": 0,
        "blocked_projects": 0,
        "in_progress_projects": 0,
        "ready_for_publication_review": 0,
    }


def test_release_guard_resolves_expected_yield_review_from_the_facade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failing_row = {
        "project_accession": "project",
        "species_latin_name": "Species example",
        "recovery_gap_status": "under_recovered",
        "implausibly_low_recovery": True,
        "implausibly_low_recovery_reason": "fixture refusal",
    }
    monkeypatch.setattr(
        reviews,
        "build_project_expected_sample_yield_review",
        lambda output_root: {"rows": [failing_row]},
    )

    payload = reviews.build_source_recovery_release_guard(Path("unused"))

    assert payload == {
        "schema_version": "animal-source-recovery-release-guard.v1",
        "passing": False,
        "implausibly_low_recovery_project_count": 1,
        "failing_projects": [
            {
                "project_accession": "project",
                "species_latin_name": "Species example",
                "recovery_gap_status": "under_recovered",
                "implausibly_low_recovery_reason": "fixture refusal",
            }
        ],
    }


def test_manual_worklist_resolves_cache_key_and_cached_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = {"schema_version": "fixture", "rows": []}
    monkeypatch.setattr(reviews, "_cache_key", lambda output_root: "stable-key")
    monkeypatch.setattr(
        reviews,
        "_build_manual_curation_worklist_cached",
        lambda output_root_key: expected if output_root_key == "stable-key" else {},
    )

    assert reviews.build_manual_curation_worklist(Path("unused")) is expected
