from __future__ import annotations

from bijux_pollenomics.analysis.engine_manifest import build_ranking_engine_manifest
from bijux_pollenomics.analysis.ranking import build_ranking_sensitivity_report
from bijux_pollenomics.analysis.review import (
    build_candidate_sites_json_payload,
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
    assert "atlas_evidence_surface_json" in manifest.current_artifacts
    assert "atlas_scientific_review_json" in manifest.current_artifacts


def test_candidate_site_sensitivity_markdown_renders_table() -> None:
    report = build_ranking_sensitivity_report((), ())

    markdown = render_candidate_site_sensitivity_markdown(
        report,
        title="Nordic Evidence Atlas",
    )

    assert "# Nordic Evidence Atlas Candidate Site Sensitivity" in markdown
    assert "Fieldwork rank" in markdown


def test_candidate_sites_payload_carries_species_aware_evidence_boundary() -> None:
    payload = build_candidate_sites_json_payload([])

    species_boundary = payload["species_evidence_boundary"]

    assert species_boundary["animal_adna"].startswith(
        "Non-human ancient-DNA support is contextual review evidence"
    )
    assert "atlas proximity" in species_boundary["proximity_refusal"]
