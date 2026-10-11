"""Profile sensitivity and grouped-context ranking behavior."""

from __future__ import annotations

from collections.abc import Iterable

import pytest

from bijux_pollenomics.adna import AdnaLocalitySummary
import bijux_pollenomics.analysis.fieldwork.ranking as ranking_module
from bijux_pollenomics.analysis.fieldwork.ranking import (
    build_ranking_sensitivity_report,
)
from bijux_pollenomics.analysis.propagation.candidates import CandidateSiteContext
from bijux_pollenomics.collection.contracts.models import ContextPointRecord

from .ranking_examples import _locality, _point


def test_sensitivity_report_shows_profile_rank_shifts() -> None:
    report = build_ranking_sensitivity_report(
        (
            _locality("Lake One", 59.0, 18.0, sample_count=3),
            _locality("Lake Two", 61.0, 15.0, sample_count=2),
        ),
        (
            _point("a", 59.01, 18.02, layer_key="neotoma-sites"),
            _point(
                "b",
                61.01,
                15.02,
                layer_key="sead-sites",
                time_start_bp=None,
                time_end_bp=None,
            ),
        ),
        radius_km=20.0,
    )

    assert report.schema_version == "candidate-site-sensitivity.v1"
    assert report.rows
    assert "fieldwork_triage" in report.rows[0].profile_ranks


def test_sensitivity_report_preserves_exact_profile_output() -> None:
    report = build_ranking_sensitivity_report(
        (
            _locality("Lake One", 59.0, 18.0, sample_count=3),
            _locality("Lake Two", 61.0, 15.0, sample_count=2),
        ),
        (
            _point("a", 59.01, 18.02, layer_key="neotoma-sites"),
            _point(
                "b",
                61.01,
                15.02,
                layer_key="sead-sites",
                time_start_bp=None,
                time_end_bp=None,
            ),
        ),
        radius_km=20.0,
    )

    assert report.as_dict() == {
        "schema_version": "candidate-site-sensitivity.v1",
        "baseline_profile": "atlas_exploration",
        "compared_profiles": [
            "atlas_exploration",
            "chronology_first",
            "context_first",
            "fieldwork_triage",
        ],
        "rows": [
            {
                "locality": "Lake One",
                "locality_token": "lake-one-59.0-18.0",
                "baseline_profile": "atlas_exploration",
                "baseline_rank": 1,
                "profile_ranks": {
                    "atlas_exploration": 1,
                    "chronology_first": 1,
                    "context_first": 1,
                    "fieldwork_triage": 1,
                },
                "profile_statuses": {
                    "atlas_exploration": "ranked",
                    "chronology_first": "ranked",
                    "context_first": "ranked",
                    "fieldwork_triage": "ranked",
                },
                "max_rank_shift": 0,
                "recommendation_ready_profiles": [],
            },
            {
                "locality": "Lake Two",
                "locality_token": "lake-two-61.0-15.0",
                "baseline_profile": "atlas_exploration",
                "baseline_rank": 2,
                "profile_ranks": {
                    "atlas_exploration": 2,
                    "chronology_first": 2,
                    "context_first": 2,
                    "fieldwork_triage": 2,
                },
                "profile_statuses": {
                    "atlas_exploration": "downgraded",
                    "chronology_first": "downgraded",
                    "context_first": "downgraded",
                    "fieldwork_triage": "downgraded",
                },
                "max_rank_shift": 0,
                "recommendation_ready_profiles": [],
            },
        ],
    }


def test_sensitivity_builds_each_grouped_context_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = ranking_module.build_candidate_context
    calls = 0

    def counted_build_candidate_context(
        locality: AdnaLocalitySummary,
        context_points: Iterable[ContextPointRecord],
        *,
        co_located_localities: Iterable[AdnaLocalitySummary] | None = None,
        radius_km: float = 25.0,
    ) -> CandidateSiteContext:
        nonlocal calls
        calls += 1
        return original(
            locality,
            context_points,
            co_located_localities=co_located_localities,
            radius_km=radius_km,
        )

    monkeypatch.setattr(
        ranking_module, "build_candidate_context", counted_build_candidate_context
    )

    report = build_ranking_sensitivity_report(
        (
            _locality("Lake One", 59.0, 18.0, token="shared:lake-one"),
            _locality(
                "Lake One",
                59.0,
                18.0,
                token="shared:lake-one",
                species_latin_name="Equus caballus",
                species_common_name="horse",
            ),
            _locality("Lake Two", 61.0, 15.0),
        ),
        (_point("context", 59.01, 18.02),),
    )

    assert report.compared_profiles == (
        "atlas_exploration",
        "chronology_first",
        "context_first",
        "fieldwork_triage",
    )
    assert calls == 2
