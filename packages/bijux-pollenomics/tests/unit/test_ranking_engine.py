from __future__ import annotations

from bijux_pollenomics.analysis.engine_manifest import build_ranking_engine_manifest
from bijux_pollenomics.analysis.ranking import build_ranking_sensitivity_report
from bijux_pollenomics.analysis.reporting import (
    render_candidate_site_sensitivity_markdown,
)


def test_ranking_engine_manifest_states_future_lake_selection_requirements() -> None:
    manifest = build_ranking_engine_manifest()

    assert manifest.schema_version == "candidate-ranking-engine-manifest.v1"
    assert manifest.default_profile == "atlas_exploration"
    assert "fieldwork_triage" in {
        profile.profile_name for profile in manifest.supported_profiles
    }
    assert any(
        requirement.requirement == "cross-species direct evidence at the same locality anchor"
        for requirement in manifest.future_lake_selection_requirements
    )


def test_candidate_site_sensitivity_markdown_renders_table() -> None:
    report = build_ranking_sensitivity_report((), ())

    markdown = render_candidate_site_sensitivity_markdown(
        report,
        title="Nordic Evidence Atlas",
    )

    assert "# Nordic Evidence Atlas Candidate Site Sensitivity" in markdown
    assert "Fieldwork rank" in markdown
