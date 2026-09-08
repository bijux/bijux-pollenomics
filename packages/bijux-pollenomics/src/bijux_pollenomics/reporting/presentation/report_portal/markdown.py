from __future__ import annotations

from typing import cast

from ..text import escape_pipes
from .surfaces import _AUDIENCE_LABELS, _FAMILY_LABELS


def _render_report_surface_registry_markdown(payload: dict[str, object]) -> str:
    family_counts = cast(dict[str, object], payload.get("family_counts", {}))
    audience_counts = cast(dict[str, object], payload.get("audience_counts", {}))
    rows = cast(list[dict[str, object]], payload.get("rows", []))
    family_rows = "\n".join(
        f"| {escape_pipes(_FAMILY_LABELS.get(str(key), str(key)))} | {value} |"
        for key, value in family_counts.items()
    )
    audience_rows = "\n".join(
        f"| {escape_pipes(_AUDIENCE_LABELS.get(str(key), str(key)))} | {value} |"
        for key, value in audience_counts.items()
    )
    artifact_rows = "\n".join(
        f"| `{row['repository_path']}` | {escape_pipes(str(row['family_label']))} | {escape_pipes(str(row['audience_label']))} | `{row['geography']}` | `{row['format']}` | {escape_pipes(str(row['explanation']))} |"
        for row in rows
    )
    return f"""# Report surface registry

This registry classifies the current `docs/report/` tree by family, audience,
scope, and explanation role so the publication system can be navigated as one
coherent report surface instead of a loose artifact dump.

- Surface count: `{payload["surface_count"]}`

## Family Counts

| Family | Count |
| --- | ---: |
{family_rows}

## Audience Counts

| Audience | Count |
| --- | ---: |
{audience_rows}

## Classified Surfaces

| Path | Family | Audience | Geography | Format | Explanation |
| --- | --- | --- | --- | --- | --- |
{artifact_rows}
"""


def _render_report_narrative_quality_review_markdown(payload: dict[str, object]) -> str:
    posture_counts = cast(dict[str, object], payload.get("quality_posture_counts", {}))
    rows = cast(list[dict[str, object]], payload.get("rows", []))
    posture_rows = "\n".join(
        f"| `{key}` | {value} |" for key, value in posture_counts.items()
    )
    review_rows = "\n".join(
        f"| `{row['repository_path']}` | `{row['quality_posture']}` | {row['prose_paragraph_count']} | {row['link_bullet_count']} | {row['bullet_sentence_count']} | {row['table_line_count']} | {row['heading_count']} | {escape_pipes(str(row['note']))} |"
        for row in rows
    )
    return f"""# Report narrative quality review

This review checks whether the report-facing Markdown surfaces explain
themselves in prose or structured reference form instead of behaving like bare
link farms or coded operator notes.

- Reviewed markdown pages: `{payload["page_count"]}`

## Quality Postures

| Posture | Count |
| --- | ---: |
{posture_rows}

## Reviewed Pages

| Path | Posture | Prose paragraphs | Link bullets | Sentence bullets | Table lines | Headings | Note |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
{review_rows}
"""
