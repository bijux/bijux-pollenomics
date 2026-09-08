from __future__ import annotations

from typing import Any

from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject


def _empty_sample_chronology_row(project: AdnaArchiveProject) -> dict[str, object]:
    return {
        "species_latin_name": project.species_latin_name,
        "species_common_name": "",
        "project_accession": project.project_accession,
        "repo_stable_sample_id": "",
        "preferred_sample_label": "",
        "sample_basis": "",
        "sample_evidence_status": "not_yet_recoverable",
        "sample_identity_resolution": "provisional",
        "sample_ambiguity_note": "",
        "chronology_text": "",
        "chronology_strength": "unresolved",
        "chronology_evidence_class": "unresolved",
        "chronology_precision_posture": "unresolved",
        "chronology_provenance_path": "",
        "chronology_provenance_kind": "",
        "chronology_provenance_locator": "",
        "chronology_provenance_text": "",
        "chronology_normalization_status": "unresolved",
        "time_start_bp": "",
        "time_end_bp": "",
        "time_mean_bp": "",
        "dating_basis": "",
        "chronology_conflict_note": "",
        "review_note": "No recovered sample rows are published yet for this project.",
    }


def _empty_sample_chronology_provenance_row(
    project: AdnaArchiveProject,
) -> dict[str, object]:
    return {
        "species_latin_name": str(getattr(project, "species_latin_name", "")),
        "species_common_name": str(getattr(project, "species_common_name", "")),
        "project_accession": str(getattr(project, "project_accession", "")),
        "repo_stable_sample_id": "",
        "preferred_sample_label": "",
        "published_wording": "",
        "source_wording_excerpt": "",
        "provenance_surface": "",
        "provenance_kind": "",
        "provenance_locator": "",
        "dating_basis": "",
        "evidence_class": "",
        "precision_posture": "",
        "normalization_status": "",
        "normalization_rule": "",
        "uncertainty_note": "",
        "time_start_bp": "",
        "time_end_bp": "",
        "time_mean_bp": "",
        "temporal_semantics": {},
    }


def _render_sample_chronology_audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Sample chronology normalization audit",
        "",
        f"- Sample rows: `{payload['sample_row_count']}`",
        f"- Normalized intervals: `{payload['normalized_interval_count']}`",
        f"- Normalized points: `{payload['normalized_point_count']}`",
        f"- Text-only rows: `{payload['text_only_unparsed_count']}`",
        f"- Unresolved rows: `{payload['unresolved_count']}`",
        f"- Direct radiocarbon rows: `{payload['evidence_counts']['direct_radiocarbon_date']}`",
        f"- Modeled sample-date rows: `{payload['evidence_counts']['modeled_sample_date']}`",
        f"- Archaeological-context rows: `{payload['evidence_counts']['archaeological_context_date']}`",
        f"- Broad period rows: `{payload['evidence_counts']['broad_period_label']}`",
        "",
    ]
    if payload["projects_requiring_manual_review"]:
        lines.append("## Projects requiring manual chronology review")
        lines.append("")
        for item in payload["projects_requiring_manual_review"]:
            lines.append(f"- `{item}`")
        lines.append("")
    lines.extend(
        [
            "| Project accession | Sample rows | Interval rows | Point rows | Text-only rows | Unresolved rows | Conflicts |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            f"| {row['project_accession']} | {row['recovered_sample_row_count']} | "
            f"{row['normalized_interval_count']} | {row['normalized_point_count']} | "
            f"{row['text_only_unparsed_count']} | {row['normalization_unresolved_count']} | "
            f"{row['conflicting_context_count']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sample_chronology_ambiguity_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Sample chronology ambiguity ledger",
        "",
        f"- Rows requiring chronology review: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No sample chronology rows currently require manual review.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Sample id | Strength | Normalization | Chronology | Note |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        note = row["chronology_conflict_note"] or row["review_note"]
        lines.append(
            f"| {row['project_accession']} | {row['repo_stable_sample_id']} | "
            f"{row['chronology_strength']} / {row['chronology_precision_posture']} | {row['chronology_normalization_status']} | "
            f"{row['chronology_text']} | {note} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sample_chronology_review_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Sample chronology review",
        "",
        f"- Sample chronology rows: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No sample chronology rows are currently published.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Species | Project accession | Sample id | Strength | Evidence class | Precision posture | Normalization | Chronology | Provenance |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['species_latin_name']} | {row['project_accession']} | "
            f"{row['repo_stable_sample_id']} | {row['chronology_strength']} | "
            f"{row['chronology_evidence_class']} | {row['chronology_precision_posture']} | "
            f"{row['chronology_normalization_status']} | {row['chronology_text']} | "
            f"{row['chronology_provenance_path']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sample_chronology_conflict_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Sample chronology conflict ledger",
        "",
        f"- Conflicting rows: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No cross-source chronology conflicts are currently published.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Sample id | Evidence class | Precision posture | Chronology | Conflict note |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['repo_stable_sample_id']} | "
            f"{row['chronology_evidence_class']} | {row['chronology_precision_posture']} | "
            f"{row['chronology_text']} | {row['chronology_conflict_note']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sample_chronology_provenance_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Sample chronology provenance review",
        "",
        f"- Provenance packets: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No chronology provenance packets are currently published.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Sample id | Published wording | Provenance surface | Provenance locator | Normalization rule | Uncertainty note |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['repo_stable_sample_id']} | "
            f"{row['published_wording']} | {row['provenance_surface']} | "
            f"{row['provenance_locator']} | {row['normalization_rule']} | "
            f"{row['uncertainty_note']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sample_chronology_precision_audit_markdown(
    payload: dict[str, Any],
) -> str:
    lines = [
        "# Sample chronology precision audit",
        "",
        f"- Rows audited: `{payload['row_count']}`",
        f"- Precise point rows: `{payload['precision_counts']['sample_precise_point']}`",
        f"- Precise interval rows: `{payload['precision_counts']['sample_precise_interval']}`",
        f"- Approximate or modeled rows: `{payload['precision_counts']['sample_approximate_or_modeled']}`",
        f"- Contextual rows: `{payload['precision_counts']['contextual_interval']}`",
        f"- Broad period rows: `{payload['precision_counts']['broad_period_only']}`",
        f"- Unresolved rows: `{payload['precision_counts']['unresolved']}`",
        "",
        "| Project accession | Sample id | Evidence class | Precision posture | Normalization | Chronology |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        if row["chronology_precision_posture"] in {
            "sample_precise_point",
            "sample_precise_interval",
        }:
            continue
        lines.append(
            f"| {row['project_accession']} | {row['repo_stable_sample_id']} | "
            f"{row['chronology_evidence_class']} | {row['chronology_precision_posture']} | "
            f"{row['chronology_normalization_status']} | {row['chronology_text']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_date_evidence_gap_queue_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Date evidence gap queue",
        "",
        f"- Projects still needing stronger sample-level chronology: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append(
            "All tracked projects currently publish defensible sample-level chronology surfaces."
        )
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Species | Sample rows | Exact sample dates | Contextual dates | Broad labels | Missing dates | Gap reasons |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['species_latin_name']} | "
            f"{row['recovered_sample_row_count']} | {row['exact_sample_date_count']} | "
            f"{row['contextual_date_count']} | {row['broad_label_count']} | "
            f"{row['missing_date_count']} | {', '.join(row['gap_reasons'])} |"
        )
    lines.append("")
    return "\n".join(lines)
