from __future__ import annotations

from typing import cast

from ..text import escape_pipes
from .surfaces import _AUDIENCE_LABELS, _FAMILY_LABELS


def _render_report_surface_registry_markdown(payload: dict[str, object]) -> str:
    family_counts = cast(dict[str, object], payload.get("family_counts", {}))
    audience_counts = cast(dict[str, object], payload.get("audience_counts", {}))
    family_routes = {
        "maps": "maps/index.md",
        "scopes": "scopes/index.md",
        "reviews": "reviews/index.md",
        "caveats": "caveats/index.md",
        "maintenance": "maintenance/index.md",
        "portal": "index.md",
    }
    family_rows = "\n".join(
        f"| [{escape_pipes(_FAMILY_LABELS.get(str(key), str(key)))}]({family_routes[str(key)]}) | {value} |"
        for key, value in family_counts.items()
    )
    audience_rows = "\n".join(
        f"| {escape_pipes(_AUDIENCE_LABELS.get(str(key), str(key)))} | {value} |"
        for key, value in audience_counts.items()
    )
    return f"""# Report surface registry

We group the current `docs/report/` tree by reader question. Start at the
[report portal](index.md) for an explanation of the results and their limits.
The [machine-readable registry](report_surface_registry.json) lists every path
with its family, audience, geography and format when an exact file lookup is
needed.

- Surface count: `{payload["surface_count"]}`

## Report families

| Family | Count |
| --- | ---: |
{family_rows}

## Audience counts

| Audience | Count |
| --- | ---: |
{audience_rows}
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
