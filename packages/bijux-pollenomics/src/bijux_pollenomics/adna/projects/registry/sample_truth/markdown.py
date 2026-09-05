"""Markdown renderers for animal sample-truth products."""

from __future__ import annotations

from typing import cast


def render_animal_sample_product_contract_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Animal sample product contract",
        "",
        f"- Primary durable unit: `{payload['primary_durable_unit']}`",
        "",
        "## Required fields",
        "",
        "| Field | Meaning |",
        "| --- | --- |",
    ]
    for row in cast(list[dict[str, object]], payload["required_fields"]):
        lines.append(f"| {row['field']} | {row['meaning']} |")
    lines.extend(["", "## Reader questions answered", ""])
    for question in cast(list[str], payload["reader_questions_answered"]):
        lines.append(f"- {question}")
    lines.append("")
    return "\n".join(lines)


def render_animal_sample_foundation_truth_markdown(payload: dict[str, object]) -> str:
    summary = cast(dict[str, object], payload["summary"])
    lines = [
        "# Animal sample foundation truth",
        "",
        f"- Tracked species: `{summary['tracked_species_count']}`",
        f"- Tracked projects: `{summary['tracked_project_count']}`",
        f"- Sample rows: `{summary['sample_row_count']}`",
        f"- Fully grounded rows: `{summary['fully_grounded_count']}`",
        f"- Partially grounded rows: `{summary['partially_grounded_count']}`",
        f"- Blocked by missing metadata: `{summary['blocked_missing_metadata_count']}`",
        f"- Blocked by missing location detail: `{summary['blocked_missing_location_detail_count']}`",
        f"- Blocked by weak chronology: `{summary['blocked_weak_chronology_count']}`",
        "",
        "## Species rows",
        "",
        "| Species | Sample rows | Fully grounded | Missing metadata | Missing location detail | Weak chronology |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in cast(list[dict[str, object]], payload["species_rows"]):
        lines.append(
            f"| {row['species_latin_name']} | {row['sample_row_count']} | "
            f"{row['fully_grounded_count']} | {row['blocked_missing_metadata_count']} | "
            f"{row['blocked_missing_location_detail_count']} | {row['blocked_weak_chronology_count']} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_animal_sample_aggregation_warnings_markdown(
    payload: dict[str, object],
) -> str:
    summary = cast(dict[str, object], payload["summary"])
    lines = [
        "# Animal sample aggregation warnings",
        "",
        f"- Project accession anchors: `{summary['project_accession_anchor_count']}`",
        f"- Accession-range anchors: `{summary['accession_range_anchor_count']}`",
        f"- Sample accession anchors: `{summary['sample_accession_anchor_count']}`",
        f"- Project-locality summaries: `{summary['project_locality_summary_count']}`",
        f"- Projects with project-level sample anchors: `{summary['projects_with_project_level_sample_anchors']}`",
        f"- Projects with locality count drift: `{summary['projects_with_locality_count_drift']}`",
        f"- Species with summary count drift: `{summary['species_with_summary_count_drift']}`",
        "",
    ]
    for row in cast(list[dict[str, object]], payload["warning_rows"]):
        lines.append(f"- `{row['warning_class']}`: `{row['count']}`. {row['detail']}")
    lines.append("")
    return "\n".join(lines)
