"""Identity and sampling review-posture tests."""

from dataclasses import replace

from bijux_pollenomics.analysis import build_lake_fieldwork_preparation_payload

from .support import _report


def test_lake_fieldwork_preparation_flags_non_official_registry_names() -> None:
    report = _report()
    flagged_candidate = replace(
        report.assessments[1].candidate,
        ambiguity_flags=("non_official_registry_name",),
        lake_name_status="water_surface_name",
    )
    flagged_assessment = replace(report.assessments[1], candidate=flagged_candidate)
    flagged_report = replace(
        report,
        assessments=(report.assessments[0], flagged_assessment),
    )

    payload = build_lake_fieldwork_preparation_payload(flagged_report)
    row = payload["rows"][1]

    assert row["identity_posture"] == "registry_name_review_required"
    assert (
        "confirm the official Swedish lake registry name before field planning"
        in row["required_actions"]
    )


def test_lake_fieldwork_preparation_flags_small_lake_sampling_review() -> None:
    report = _report()
    flagged_candidate = replace(
        report.assessments[0].candidate,
        lake_sampling_posture="small_lake_review",
        lake_sampling_fit=0.42,
        lake_area_km2=0.03,
    )
    flagged_assessment = replace(report.assessments[0], candidate=flagged_candidate)
    flagged_report = replace(
        report,
        assessments=(flagged_assessment, report.assessments[1]),
    )

    payload = build_lake_fieldwork_preparation_payload(flagged_report)
    row = next(
        candidate_row
        for candidate_row in payload["rows"]
        if candidate_row["lake_label"] == "Lake Clear"
    )

    assert row["sampling_posture"] == "small_lake_review"
    assert row["preparation_posture"] == "sampling_fit_review_required"
    assert (
        "verify basin depth, access, and sediment suitability before treating this small lake as a field target"
        in row["required_actions"]
    )
