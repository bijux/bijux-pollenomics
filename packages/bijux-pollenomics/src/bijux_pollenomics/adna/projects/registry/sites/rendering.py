"""Stable CSV fallback and human-review Markdown rendering."""

from __future__ import annotations

from typing import Any, Iterable, cast


def _empty_sample_site_row(project: object) -> dict[str, object]:
    project_row = cast(Any, project)
    return {
        "species_latin_name": project_row.species_latin_name,
        "species_common_name": "",
        "project_accession": project_row.project_accession,
        "repo_stable_sample_id": "",
        "preferred_sample_label": "",
        "sample_basis": "",
        "sample_evidence_status": "not_yet_recoverable",
        "sample_identity_resolution": "provisional",
        "sample_ambiguity_note": "",
        "locality_text": "",
        "locality_resolution_status": "unresolved",
        "location_evidence_artifact_path": "",
        "location_evidence_artifact_kind": "",
        "location_evidence_locator": "",
        "location_evidence_text": "",
        "site_name": "",
        "municipality_name": "",
        "region_name": "",
        "country_name": "",
        "broader_geography": "",
        "coordinate_basis": "",
        "coordinate_mapping_posture": "",
        "coordinate_confidence": "",
        "chronology_text": "",
        "review_note": "No recovered sample rows are published yet for this project.",
    }


def _render_sample_site_ambiguity_markdown(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Sample site ambiguity ledger",
        "",
        f"- Ambiguous or weak site rows: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No weak sample-site rows are currently published.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Sample id | Status | Locality | Note |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['repo_stable_sample_id']} | "
            f"{row['locality_resolution_status']} | {row['locality_text']} | {row['review_note']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sample_site_manual_queue_markdown(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Sample site manual curation queue",
        "",
        f"- Queued projects: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No project currently requires manual sample-site extraction.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Queued sample rows | Recommended next surface | Reasons |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for row in rows:
        queue_reasons = cast(Iterable[str], row["queue_reasons"])
        lines.append(
            f"| {row['project_accession']} | {row['queued_sample_count']} | "
            f"{row['recommended_next_surface']} | {', '.join(queue_reasons)} |"
        )
    lines.append("")
    return "\n".join(lines)
