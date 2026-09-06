"""Animal foundation rendering responsibilities."""

from __future__ import annotations
from typing import Any


def render_animal_foundation_validation_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Animal foundation validation",
        "",
        f"- Overall ok: `{str(payload['overall_ok']).lower()}`",
        f"- Sample rows: `{payload['sample_row_count']}`",
        f"- Site evidence rows: `{payload['site_evidence_row_count']}`",
        f"- Coordinate rows: `{payload['coordinate_row_count']}`",
        f"- Atlas rows: `{payload['atlas_row_count']}`",
        "",
        "| Check | Passed | Finding count |",
        "| --- | --- | ---: |",
    ]
    for row in payload["checks"]:
        lines.append(
            f"| {row['check_id']} | `{str(row['passed']).lower()}` | {row['finding_count']} |"
        )
    return "\n".join(lines) + "\n"


def render_animal_cross_surface_drift_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Animal cross-surface drift",
        "",
        f"- Drift detected: `{str(payload['drift_detected']).lower()}`",
        "",
        "| Species | Sample rows | Atlas rows | Country sample rows | Drift |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['species_latin_name']} | {row['normalized_sample_row_count']} | "
            f"{row['atlas_evidence_row_count']} | {row['published_country_sample_count']} | "
            f"`{str(row['drift_detected']).lower()}` |"
        )
    return "\n".join(lines) + "\n"


def render_animal_scientific_caveat_ledger_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join(
        [
            "# Animal scientific caveat ledger",
            "",
            f"- Missing supplements: `{summary['missing_supplement_count']}`",
            f"- Unreadable tables: `{summary['unreadable_table_count']}`",
            f"- Uncertain site assignments: `{summary['uncertain_site_assignment_count']}`",
            f"- Region-only geography rows: `{summary['region_only_geography_count']}`",
            f"- Comparator-only evidence rows: `{summary['comparator_only_evidence_count']}`",
            "",
        ]
    )


def render_animal_point_evidence_review_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Animal point evidence review",
        "",
        f"- Published point count: `{payload['row_count']}`",
        "",
    ]
    for row in payload["rows"]:
        lines.extend(
            [
                f"## {row['feature_id']}",
                "",
                f"- Species: `{row['species_latin_name']}`",
                f"- Project accession: `{row['project_accession']}`",
                f"- Paper DOI: `{row['paper_doi']}`",
                f"- Coordinate basis: `{row['coordinate_basis']}`",
                f"- Coordinate confidence: `{row['coordinate_confidence']}`",
                f"- Sample rows: `{len(row['sample_rows'])}`",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def render_animal_project_publication_gap_review_markdown(
    payload: dict[str, Any],
) -> str:
    lines = [
        "# Animal project publication gap review",
        "",
        f"- Non-published project count: `{payload['row_count']}`",
        "",
        "| Project | Species | Absence stage | Blockers |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['project_accession']} | {row['species_latin_name']} | "
            f"{row['absence_stage']} | {', '.join(row['blockers'])} |"
        )
    return "\n".join(lines) + "\n"


def render_animal_foundation_review_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Animal foundation review",
        "",
        f"- Public posture: `{payload['public_posture']}`",
        f"- Strongest claim allowed: `{str(payload['reference_grade_claim_allowed']).lower()}`",
        f"- Published point count: `{payload['counts']['published_point_count']}`",
        f"- Direct-coordinate point count: `{payload['counts']['direct_coordinate_point_count']}`",
        f"- Geocoded point count: `{payload['counts']['geocoded_point_count']}`",
        f"- Unresolved sample count: `{payload['counts']['unresolved_sample_count']}`",
        f"- Coordinate-provenance refusal count: `{payload['counts']['coordinate_provenance_refusal_count']}`",
        "",
    ]
    if payload["strengths"]:
        lines.append("## Strengths")
        lines.append("")
        for item in payload["strengths"]:
            lines.append(f"- {item}")
        lines.append("")
    if payload["blockers"]:
        lines.append("## Blockers")
        lines.append("")
        for item in payload["blockers"]:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines) + "\n"


def render_animal_sample_chronology_review_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Animal sample chronology review",
        "",
        f"- Sample chronology rows: `{payload['row_count']}`",
        f"- Normalized intervals: `{payload['normalization_counts']['normalized_interval']}`",
        f"- Normalized points: `{payload['normalization_counts']['normalized_point']}`",
        f"- Text-only rows: `{payload['normalization_counts']['text_only_unparsed']}`",
        f"- Unresolved rows: `{payload['normalization_counts']['unresolved']}`",
        f"- Direct radiocarbon rows: `{payload['evidence_counts']['direct_radiocarbon_date']}`",
        f"- Modeled rows: `{payload['evidence_counts']['modeled_sample_date']}`",
        f"- Contextual rows: `{payload['evidence_counts']['archaeological_context_date']}`",
        f"- Broad period rows: `{payload['evidence_counts']['broad_period_label']}`",
        f"- Numeric interval rows: `{payload['comparability_counts'].get('numeric_interval', 0)}`",
        f"- Numeric rows with caveat: `{payload['comparability_counts'].get('numeric_interval_with_caveat', 0)}`",
        f"- Context-only rows: `{payload['comparability_counts'].get('contextual_label_only', 0)}`",
        "",
        "| Species | Project accession | Sample id | Strength | Evidence class | Precision posture | Normalization | Chronology |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['species_latin_name']} | {row['project_accession']} | "
            f"{row['repo_stable_sample_id']} | {row['chronology_strength']} | "
            f"{row['chronology_evidence_class']} | {row['chronology_precision_posture']} | "
            f"{row['chronology_normalization_status']} | {row['chronology_text']} |"
        )
    lines.extend(["", "## Direct Links", ""])
    for label, target in payload["direct_links"].items():
        lines.append(f"- {label}: `{target}`")
    return "\n".join(lines) + "\n"


def render_animal_temporal_comparison_review_markdown(
    payload: dict[str, Any],
) -> str:
    lines = [
        "# Animal temporal comparison review",
        "",
        "This review names the temporal comparisons that remain safe and the ones that would overclaim if direct aDNA rows and contextual archaeology rows were treated as one date model.",
        "",
        "| Family | Rows | Comparison policy |",
        "| --- | ---: | --- |",
    ]
    for row in payload["family_rows"]:
        lines.append(
            f"| {row['display_name']} | {row['row_count']} | {row['comparison_policy']} |"
        )
    lines.extend(["", "## Unsafe Comparison Findings", ""])
    findings = payload.get("unsafe_comparison_findings", [])
    if isinstance(findings, list) and findings:
        for finding in findings:
            lines.append(f"- {finding}")
    else:
        lines.append("- No unsafe comparison findings are currently published.")
    lines.extend(["", "## Direct Links", ""])
    for label, target in payload["direct_links"].items():
        lines.append(f"- {label}: `{target}`")
    return "\n".join(lines) + "\n"


def render_animal_intake_recovery_review_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Animal intake recovery review",
        "",
        f"- Public posture: `{payload['public_posture']}`",
        f"- Tracked projects: `{payload['stage_review']['tracked_project_count']}`",
        f"- Ready for publication review: `{payload['stage_review']['ready_for_publication_review']}`",
        f"- Blocked projects: `{payload['stage_review']['blocked_projects']}`",
        f"- Implausibly low recovery projects: `{payload['release_guard']['implausibly_low_recovery_project_count']}`",
        "",
        "## Sample Evidence Depth",
        "",
    ]
    for key, value in payload["sample_evidence_depth_counts"].items():
        lines.append(f"- {key.replace('_', ' ')}: `{value}`")
    lines.extend(
        [
            "",
            "## Top Gap Projects",
            "",
            "| Project | Species | Gap status | Minimum gap | Reasons |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )
    for row in payload["top_gap_projects"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['species_latin_name']}` | "
            f"`{row['recovery_gap_status']}` | `{row['minimum_gap_count'] or 0}` | "
            f"`{'; '.join(row['major_deficit_reasons'])}` |"
        )
    lines.extend(["", "## Direct Links", ""])
    for label, target in payload["direct_links"].items():
        lines.append(f"- {label}: `{target}`")
    return "\n".join(lines) + "\n"


def render_animal_sample_database_review_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Animal sample database review",
        "",
        f"- Public posture: `{payload['public_posture']}`",
        f"- Sample database claim supported: `{str(payload['sample_database_claim_supported']).lower()}`",
        f"- Nordic view supported now: `{str(payload['nordic_view_supported_now']).lower()}`",
        f"- Region-agnostic contract ready: `{str(payload['region_agnostic_contract_ready']).lower()}`",
        f"- World-map expansion posture: `{payload['world_map_expansion_posture']}`",
        "",
        "## Counts",
        "",
        f"- Tracked projects: `{payload['counts']['tracked_project_count']}`",
        f"- Tracked papers: `{payload['counts']['tracked_paper_count']}`",
        f"- Tracked supplements: `{payload['counts']['tracked_supplement_count']}`",
        f"- Sample rows: `{payload['counts']['sample_row_count']}`",
        f"- Site evidence rows: `{payload['counts']['site_evidence_row_count']}`",
        f"- Sample site rows: `{payload['counts']['sample_site_row_count']}`",
        f"- Chronology rows: `{payload['counts']['chronology_row_count']}`",
        f"- Coordinate rows: `{payload['counts']['coordinate_row_count']}`",
        f"- Published atlas points: `{payload['counts']['published_atlas_point_count']}`",
        f"- Published country bundles: `{payload['counts']['published_country_bundle_count']}`",
        f"- Papers with archived supplements: `{payload['counts']['papers_with_archived_supplements']}`",
        f"- Mapped sample share: `{payload['counts']['mapped_sample_share']}`",
        f"- Projects blocked in intake recovery: `{payload['intake_recovery_counts']['blocked_projects']}`",
        f"- Projects ready for publication review: `{payload['intake_recovery_counts']['ready_for_publication_review']}`",
        f"- Implausibly low recovery projects: `{payload['intake_recovery_counts']['implausibly_low_recovery_project_count']}`",
        "",
        "## Thresholds",
        "",
        f"- Minimum published atlas points: `{payload['readiness_thresholds']['minimum_published_atlas_points']}`",
        f"- Minimum supplement-backed papers: `{payload['readiness_thresholds']['minimum_supplement_backed_papers']}`",
        f"- Minimum mapped sample share: `{payload['readiness_thresholds']['minimum_mapped_sample_share']}`",
        f"- Minimum normalized chronology rows: `{payload['readiness_thresholds']['minimum_normalized_chronology_rows']}`",
        f"- Minimum region-agnostic point floor: `{payload['readiness_thresholds']['minimum_region_agnostic_point_floor']}`",
        f"- Minimum region-agnostic mapped share: `{payload['readiness_thresholds']['minimum_region_agnostic_mapped_share']}`",
        "",
        "## Posture Findings",
        "",
    ]
    for finding in payload["posture_findings"]:
        lines.append(f"- {finding}")
    lines.extend(
        [
            "",
            "## Direct Links",
            "",
        ]
    )
    for label, target in payload["direct_links"].items():
        lines.append(f"- {label}: `{target}`")
    if payload["blockers"]:
        lines.extend(
            [
                "",
                "## Current Blockers",
                "",
            ]
        )
        for blocker in payload["blockers"]:
            lines.append(f"- {blocker}")
    return "\n".join(lines) + "\n"


def render_animal_publication_release_gate_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Animal publication release gate",
        "",
        f"- Overall ok: `{str(payload['overall_ok']).lower()}`",
        f"- Strongest claim allowed: `{str(payload['reference_grade_claim_allowed']).lower()}`",
        f"- Strongest claim support ready: `{str(payload['reference_grade_support_ready']).lower()}`",
        "",
        "## Strongest-Claim Support Requirements",
        "",
        f"- Sample database artifacts present: `{str(payload['reference_grade_support_requirements']['sample_database_artifacts_present']).lower()}`",
        f"- Sample evidence reviews present: `{str(payload['reference_grade_support_requirements']['sample_evidence_reviews_present']).lower()}`",
        f"- Map outputs present: `{str(payload['reference_grade_support_requirements']['map_outputs_present']).lower()}`",
        "",
        "| Check | Passed | Finding count |",
        "| --- | --- | ---: |",
    ]
    for row in payload["checks"]:
        lines.append(
            f"| {row['check_id']} | `{str(row['passed']).lower()}` | {row['finding_count']} |"
        )
    return "\n".join(lines) + "\n"
