from __future__ import annotations

from typing import Any

from .constants import ADNA_INTAKE_STAGE_KEYS


def render_project_recovery_stage_review_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Project recovery stage review",
        "",
        f"- Tracked projects: `{payload['row_count']}`",
        f"- Ready for publication review: `{payload['summary']['ready_for_publication_review']}`",
        f"- Blocked projects: `{payload['summary']['blocked_projects']}`",
        "",
        "| Project | Species | Recovery status | Next required stage | Blocking stages |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['species_latin_name']}` | "
            f"`{row['overall_recovery_status']}` | `{row['next_required_stage'] or 'none'}` | "
            f"`{'; '.join(row['blocking_stages']) or 'none'}` |"
        )
    return "\n".join(lines) + "\n"


def render_project_expected_sample_yield_review_markdown(
    payload: dict[str, Any],
) -> str:
    lines = [
        "# Project expected sample yield review",
        "",
        f"- Tracked projects: `{payload['counts']['tracked_project_count']}`",
        f"- Projects with exact expected counts: `{payload['counts']['projects_with_exact_expected_count']}`",
        f"- Projects with a minimum expected floor: `{payload['counts']['projects_with_minimum_expected_floor']}`",
        f"- Implausibly low recovery projects: `{payload['counts']['projects_with_implausibly_low_recovery']}`",
        "",
        "| Project | Species | Exact expected | Minimum expected | Final rows | Gap status | Implausibly low |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['species_latin_name']}` | "
            f"{row['expected_sample_count'] if row['expected_sample_count'] is not None else '-'} | "
            f"{row['minimum_expected_sample_count'] if row['minimum_expected_sample_count'] is not None else '-'} | "
            f"{row['final_sample_count']} | `{row['recovery_gap_status']}` | "
            f"`{str(bool(row['implausibly_low_recovery'])).lower()}` |"
        )
    return "\n".join(lines) + "\n"


def render_paper_expected_sample_yield_review_markdown(
    payload: dict[str, Any],
) -> str:
    lines = [
        "# Paper expected sample yield review",
        "",
        f"- Paper rows: `{payload['row_count']}`",
        "",
        "| Paper DOI | Projects | Sample extractability | Recovered rows | Unknown expected totals | Implausibly low projects |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['paper_doi']}` | `{'; '.join(row['project_accessions'])}` | "
            f"`{row['sample_extractability']}` | `{row['recovered_final_sample_count']}` | "
            f"`{row['projects_with_unknown_expected_total']}` | "
            f"`{row['projects_with_implausibly_low_recovery']}` |"
        )
    return "\n".join(lines) + "\n"


def render_species_project_deficit_ledger_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Species project deficit ledger",
        "",
        f"- Project rows: `{payload['row_count']}`",
        "",
        "| Species | Project | Minimum sample gap | Site gap | Chronology gap | Publication status |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['species_latin_name']}` | `{row['project_accession']}` | "
            f"`{row['minimum_gap_count'] or 0}` | "
            f"`{row['lacking_defensible_site_assignment_count']}` | "
            f"`{row['missing_chronology_count']}` | "
            f"`{row['publication_readiness_status']}` |"
        )
    return "\n".join(lines) + "\n"


def render_manual_curation_worklist_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Manual curation worklist",
        "",
        f"- Work units: `{payload['row_count']}`",
        "",
        "| Project | Species | Work unit | State | Open items | Impact |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['species_latin_name']}` | "
            f"`{row['work_unit_type']}` | `{row['work_unit_state']}` | "
            f"`{row['open_item_count']}` | {row['downstream_impact']} |"
        )
    return "\n".join(lines) + "\n"


def render_source_recovery_progress_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Source recovery progress",
        "",
        f"- Tracked projects: `{payload['project_count']}`",
        f"- Sample identity rows present: `{payload['project_counts']['projects_with_sample_identity_rows']}`",
        f"- Defensible site rows present: `{payload['project_counts']['projects_with_defensible_site_rows']}`",
        f"- Sample-owned chronology present: `{payload['project_counts']['projects_with_sample_owned_chronology']}`",
        f"- Mappable coordinate projects: `{payload['project_counts']['projects_with_mappable_coordinates']}`",
        f"- Ready for publication review: `{payload['project_counts']['projects_ready_for_publication_review']}`",
        "",
        "## Sample Evidence Depth",
        "",
    ]
    for key, value in payload["sample_evidence_depth_counts"].items():
        lines.append(f"- {key.replace('_', ' ')}: `{value}`")
    lines.extend(
        [
            "",
            "| Project | Species | Completed stages | Required stages | Recovery depth score |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['species_latin_name']}` | "
            f"`{row['completed_stage_count']}` | `{row['required_stage_count']}` | "
            f"`{row['recovery_depth_score']}` |"
        )
    return "\n".join(lines) + "\n"


def render_missing_source_queue_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Missing source queue",
        "",
        f"- Queued rows: `{payload['row_count']}`",
        "",
        "| Project | Species | Queue category | Expected contributions | Reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['species_latin_name']}` | "
            f"`{row['queue_category']}` | `{'; '.join(row['expected_contributions'])}` | "
            f"{row['queue_reason']} |"
        )
    return "\n".join(lines) + "\n"


def render_source_recovery_release_guard_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Source recovery release guard",
        "",
        f"- Passing: `{str(payload['passing']).lower()}`",
        f"- Implausibly low recovery projects: `{payload['implausibly_low_recovery_project_count']}`",
    ]
    if payload["failing_projects"]:
        lines.extend(
            [
                "",
                "| Project | Species | Gap status | Reason |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in payload["failing_projects"]:
            lines.append(
                f"| `{row['project_accession']}` | `{row['species_latin_name']}` | "
                f"`{row['recovery_gap_status']}` | {row['implausibly_low_recovery_reason']} |"
            )
    return "\n".join(lines) + "\n"


def render_project_recovery_dossier_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['project_accession']} recovery dossier",
        "",
        f"- Species: `{payload['species_latin_name']}`",
        f"- Archive status: `{payload['archive_status']}`",
        f"- Inventory disposition: `{payload['inventory_disposition']}`",
        f"- Paper DOI: `{payload['paper_doi'] or 'none'}`",
        f"- Publication readiness: `{payload['publication_readiness_status']}`",
        f"- Next required stage: `{payload['next_required_stage'] or 'none'}`",
        f"- Exact expected sample count: `{payload['expected_sample_count'] if payload['expected_sample_count'] is not None else 'unknown'}`",
        f"- Minimum expected sample count: `{payload['minimum_expected_sample_count'] if payload['minimum_expected_sample_count'] is not None else 'unknown'}`",
        f"- Final recovered sample rows: `{payload['final_sample_count']}`",
        f"- Minimum recovery gap: `{payload['minimum_gap_count'] or 0}`",
        f"- Implausibly low recovery: `{str(bool(payload['implausibly_low_recovery'])).lower()}`",
        "",
        "## Stage Statuses",
        "",
    ]
    for stage in ADNA_INTAKE_STAGE_KEYS:
        lines.append(f"- `{stage}`: `{payload['stage_statuses'][stage]}`")
    lines.extend(
        [
            "",
            "## Expected Contributions",
            "",
        ]
    )
    for item in payload["expected_contributions"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Known Assets",
            "",
        ]
    )
    for item in payload["known_assets"] or ["none"]:
        lines.append(f"- `{item}`" if item != "none" else "- none")
    lines.extend(
        [
            "",
            "## Missing Assets",
            "",
        ]
    )
    for item in payload["missing_assets"] or ["none"]:
        lines.append(f"- {item}" if item != "none" else "- none")
    if payload["contradictory_evidence"]:
        lines.extend(["", "## Contradictory Evidence", ""])
        for item in payload["contradictory_evidence"]:
            lines.append(f"- {item}")
    if payload["inferred_claims"]:
        lines.extend(["", "## Inferred Claims", ""])
        for item in payload["inferred_claims"]:
            lines.append(f"- {item}")
    if payload["manual_curation_work_units"]:
        lines.extend(["", "## Manual Curation Work Units", ""])
        for item in payload["manual_curation_work_units"]:
            lines.append(
                f"- `{item['work_unit_type']}`: {item['open_item_count']} item(s), {item['downstream_impact']}"
            )
    return "\n".join(lines) + "\n"
