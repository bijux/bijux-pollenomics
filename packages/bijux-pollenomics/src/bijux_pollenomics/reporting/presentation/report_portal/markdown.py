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
    posture_rows = "\n".join(
        f"| `{key}` | {value} |" for key, value in posture_counts.items()
    )
    return f"""# Report narrative quality review

We count prose paragraphs, headings, tables and links in report Markdown to
identify pages that merit editorial reading. These automated layout signals
do not establish scientific validity or decide whether a reference table needs
more prose. Start with the [report portal](index.md) for the results and their
limits; use the [machine-readable review](report_narrative_quality_review.json)
for an exact page lookup.

- Reviewed markdown pages: `{payload["page_count"]}`

## Layout signals

| Posture | Count |
| --- | ---: |
{posture_rows}
"""
