from __future__ import annotations

from datetime import date
from typing import Any, cast

from bijux_pollenomics.collection.sources.sead.acquisition.access import (
    build_sead_site_access_model,
)


def build_sead_access_model_packet(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build one global explanation packet for SEAD access posture."""
    review_rows: list[dict[str, object]] = []
    access_visibility_counts: dict[str, int] = {}
    for row in rows:
        access_model = build_sead_site_access_model(row)
        visibility = str(access_model["access_visibility"])
        access_visibility_counts[visibility] = (
            access_visibility_counts.get(visibility, 0) + 1
        )
        reference_links = access_model.get("reference_links", [])
        access_limits = access_model.get("access_limits", [])
        review_rows.append(
            {
                "site_id": str(row.get("site_id", "")).strip(),
                "site_name": str(row.get("site_name", "")).strip(),
                "access_visibility": visibility,
                "site_page_url": str(access_model.get("site_page_url", "")).strip(),
                "reference_link_count": len(reference_links)
                if isinstance(reference_links, list)
                else 0,
                "redistribution_posture": str(
                    access_model.get("redistribution_posture", "")
                ).strip(),
                "reader_action": str(access_model.get("reader_action", "")).strip(),
                "access_limits": list(access_limits)
                if isinstance(access_limits, list)
                else [],
            }
        )
    review_rows.sort(
        key=lambda row: (
            str(row["access_visibility"]),
            str(row["site_name"]).casefold(),
        )
    )
    return {
        "schema_version": "sead-access-model.v1",
        "generated_on": str(date.today()),
        "row_count": len(review_rows),
        "repository_posture": "mirrored_relational_inventory_and_temporal_context",
        "what_the_repository_mirrors": [
            "raw site inventory capture under data/sead/raw/",
            "linked chronology and bibliography relations under data/sead/raw/",
            "normalized site and temporal-evidence point layers under data/sead/normalized/",
            "review packets under data/sead/review/",
        ],
        "what_the_repository_references": [
            "stable SEAD site pages when site identifiers are present",
            "stable bibliography or DOI links when they survive linked-table capture",
        ],
        "what_the_repository_does_not_redistribute": [
            "the full upstream relational SEAD database",
            "full source browsing experience beyond the linked site and reference pages",
        ],
        "access_visibility_counts": access_visibility_counts,
        "rows": review_rows,
    }


def render_sead_access_model_markdown(payload: dict[str, object]) -> str:
    mirrors = cast(list[object], payload["what_the_repository_mirrors"])
    references = cast(list[object], payload["what_the_repository_references"])
    exclusions = cast(
        list[object], payload["what_the_repository_does_not_redistribute"]
    )
    review_rows = cast(list[dict[str, Any]], payload["rows"])
    lines = [
        "# SEAD access model",
        "",
        "This packet states what the repository mirrors from SEAD, what it only references, and where readers still need to inspect upstream SEAD surfaces directly.",
        "",
        f"- Reviewed sites: `{payload['row_count']}`",
        f"- Repository posture: `{payload['repository_posture']}`",
        "",
        "## Repository Mirrors",
        "",
    ]
    for row in mirrors:
        lines.append(f"- {row}")
    lines.extend(["", "## Repository References", ""])
    for row in references:
        lines.append(f"- {row}")
    lines.extend(["", "## Repository Does Not Redistribute", ""])
    for row in exclusions:
        lines.append(f"- {row}")
    lines.extend(["", "## Access Visibility", ""])
    counts = payload.get("access_visibility_counts", {})
    if isinstance(counts, dict):
        for key in sorted(counts):
            lines.append(f"- {key.replace('_', ' ')}: `{counts[key]}`")
    lines.extend(
        [
            "",
            "| Site | Access visibility | Reference links | Stable site page |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for row in review_rows:
        lines.append(
            f"| {row['site_name']} (`{row['site_id']}`) | {row['access_visibility']} | "
            f"{row['reference_link_count']} | {row['site_page_url'] or 'None'} |"
        )
    lines.append("")
    return "\n".join(lines)
