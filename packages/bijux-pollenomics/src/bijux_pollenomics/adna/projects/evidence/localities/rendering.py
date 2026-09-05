from __future__ import annotations

from typing import cast


def _render_sample_locality_conflict_ledger_markdown(
    rows: list[dict[str, object]],
) -> str:
    lines = [
        "# Sample locality conflict ledger",
        "",
        f"- Conflicting rows: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No sample-locality conflicts are currently published.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Sample id | Sample locality | Conflicting surface | Conflicting locality | Reason |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['repo_stable_sample_id']} | "
            f"{row['sample_locality_text']} | {row['conflicting_source_surface']} | "
            f"{row['conflicting_locality_text']} | {row['conflict_reason']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sample_locality_manual_curation_workflow_markdown(
    rows: list[dict[str, object]],
) -> str:
    lines = [
        "# Sample locality manual curation workflow",
        "",
        f"- Queued locality strings: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No locality strings currently require manual curation.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Status | Unresolved place string | Candidate matches | Queued samples |",
            "| --- | --- | --- | --- | ---: |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['locality_resolution_status']} | "
            f"{row['unresolved_place_string']} | "
            f"{', '.join(cast(list[str], row['candidate_matches'])) or '-'} | "
            f"{row['queued_sample_count']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_project_locality_substitution_ledger_markdown(
    rows: list[dict[str, object]],
) -> str:
    lines = [
        "# Project locality substitution ledger",
        "",
        f"- Flagged projects: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No project currently relies on a locality substitution posture.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Publication blocked | Reason | Distinct sample-owned localities | Blocked sample count |",
            "| --- | --- | --- | ---: | ---: |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {str(row['publication_blocked']).lower()} | "
            f"{row['reason']} | {row['distinct_sample_owned_locality_count']} | "
            f"{row['blocked_sample_count']} |"
        )
    lines.append("")
    return "\n".join(lines)
