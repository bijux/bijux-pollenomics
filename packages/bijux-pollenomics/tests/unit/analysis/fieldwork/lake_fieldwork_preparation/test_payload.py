"""Fieldwork preparation payload and Markdown contract tests."""

from bijux_pollenomics.analysis import (
    build_lake_fieldwork_preparation_payload,
    render_lake_fieldwork_preparation_markdown,
    render_lake_fieldwork_preparation_section,
)

from .support import _report


def test_lake_fieldwork_preparation_payload_keeps_identity_and_interoperability_visible() -> (
    None
):
    payload = build_lake_fieldwork_preparation_payload(_report())
    markdown = render_lake_fieldwork_preparation_markdown(payload)
    section = render_lake_fieldwork_preparation_section(
        json_name="sweden_lake_fieldwork_preparation_v66.json",
        csv_name="sweden_lake_fieldwork_preparation_v66.csv",
        markdown_name="sweden_lake_fieldwork_preparation_v66.md",
    )

    assert payload["schema_version"] == "sweden-lake-fieldwork-preparation.v2"
    assert payload["row_count"] == 2
    assert payload["rows"][0]["fieldwork_rank"] == 1
    assert payload["rows"][1]["fieldwork_rank"] == 2
    assert payload["rows"][0]["fieldwork_shortlist_score"] > 0.0
    assert payload["rows"][0]["lake_registry_id"] == "test-lake-clear"
    assert payload["rows"][0]["lake_name_status"] == "official_register_name"
    assert payload["rows"][0]["preparation_posture"] == "fieldwork_review_ready"
    assert payload["rows"][0]["human_context_posture"] == "core_human_adna_context"
    assert payload["rows"][0]["palaeopen_alignment_posture"] == "high"
    assert payload["rows"][0]["scenario_consistency_posture"] == "high"
    assert payload["rows"][0]["scenario_top20_presence_count"] == 6
    assert payload["rows"][0]["sampling_posture"] == "sampling_lake_candidate"
    assert payload["rows"][0]["google_maps_url"].startswith(
        "https://www.google.com/maps/search/"
    )
    assert (
        payload["rows"][1]["identity_posture"] == "duplicate_name_resolution_required"
    )
    assert payload["rows"][1]["preparation_posture"] == "identity_resolution_required"
    assert "Fieldwork ordering rule" in markdown
    assert "Fieldwork rank" in markdown
    assert "Fieldwork shortlist score" in markdown
    assert "Lake registry id" in markdown
    assert "official_register_name" in markdown
    assert "Sweden lake fieldwork preparation" in markdown
    assert "Sampling rule" in markdown
    assert "Human context rule" in markdown
    assert "Scenario consistency rule" in markdown
    assert "Lake Fieldwork Preparation" in section
