"""Sample-master human-review rendering."""

from __future__ import annotations


def _render_sample_identity_ambiguity_markdown(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Sample identity ambiguity ledger",
        "",
        f"- Ambiguous sample rows: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append(
            "No unresolved cross-source sample identity ambiguities are currently published."
        )
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Sample id | Preferred label | Ambiguity note |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['repo_stable_sample_id']} | "
            f"{row['preferred_sample_label']} | {row['sample_ambiguity_note']} |"
        )
    lines.append("")
    return "\n".join(lines)
