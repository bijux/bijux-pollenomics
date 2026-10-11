from __future__ import annotations

from bijux_pollenomics.analysis.fieldwork.engine_manifest import (
    build_ranking_engine_manifest,
)
from bijux_pollenomics.analysis.fieldwork.ranking import (
    build_ranking_sensitivity_report,
)
from bijux_pollenomics.analysis.review.fieldwork import (
    build_candidate_sites_json_payload,
    render_candidate_site_sensitivity_markdown,
)
from tests.unit.analysis.fieldwork.payload_views import require_mapping


def test_ranking_engine_manifest_states_future_lake_selection_requirements() -> None:
    manifest = build_ranking_engine_manifest()

    assert manifest.schema_version == "candidate-ranking-engine-manifest.v1"
    assert manifest.default_profile == "atlas_exploration"
    assert "fieldwork_triage" in {
        profile.profile_name for profile in manifest.supported_profiles
    }
    assert any(
        requirement.requirement
        == "cross-species direct evidence at the same locality anchor"
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

    species_boundary = require_mapping(payload["species_evidence_boundary"])

    animal_adna = species_boundary["animal_adna"]
    proximity_refusal = species_boundary["proximity_refusal"]
    assert isinstance(animal_adna, str)
    assert isinstance(proximity_refusal, str)
    assert animal_adna.startswith(
        "Non-human ancient-DNA support is contextual review evidence"
    )
    assert "atlas proximity" in proximity_refusal
