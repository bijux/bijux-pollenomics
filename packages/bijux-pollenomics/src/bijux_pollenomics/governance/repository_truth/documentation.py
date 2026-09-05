"""Repository documentation restoration and scope assessments."""

from __future__ import annotations

from pathlib import Path

from .metrics import _docs_breadth_expectations, _docs_restoration_expectations

__all__ = [
    "build_repository_docs_restoration_ledger",
    "render_repository_docs_restoration_ledger_markdown",
    "build_repository_docs_scope_validation",
    "render_repository_docs_scope_validation_markdown",
]


def build_repository_docs_restoration_ledger(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Track how missing origin/main docs pages were restored or merged."""
    _ = data_root
    _ = report_root
    rows = []
    repo_root = docs_root.parent
    for row in _docs_restoration_expectations():
        current_path = repo_root / row["current_path"]
        missing_snippets: list[str] = []
        if current_path.exists():
            text = current_path.read_text(encoding="utf-8")
            missing_snippets = [
                snippet for snippet in row["required_snippets"] if snippet not in text
            ]
        status = (
            "verified_replacement"
            if current_path.exists() and not missing_snippets
            else "replacement_incomplete"
        )
        notes = row["rationale"]
        if missing_snippets:
            notes += "; missing anchors: " + ", ".join(
                f"`{snippet}`" for snippet in missing_snippets
            )
        rows.append(
            {
                "legacy_path": row["legacy_path"],
                "decision": row["decision"],
                "current_path": row["current_path"],
                "status": status,
                "notes": notes,
            }
        )
    decision_counts = {
        "restored": sum(1 for row in rows if row["decision"] == "restored"),
        "merged": sum(1 for row in rows if row["decision"] == "merged"),
        "retired_with_replacement": sum(
            1 for row in rows if row["decision"] == "retired_with_replacement"
        ),
    }
    status_counts = {
        "verified_replacement": sum(
            1 for row in rows if row["status"] == "verified_replacement"
        ),
        "replacement_incomplete": sum(
            1 for row in rows if row["status"] == "replacement_incomplete"
        ),
    }
    return {
        "schema_version": "repository-docs-restoration-ledger.v1",
        "rule": (
            "missing origin/main handbook pages must be restored, merged, or retired only with a verified replacement"
        ),
        "row_count": len(rows),
        "decision_counts": decision_counts,
        "status_counts": status_counts,
        "rows": rows,
    }


def render_repository_docs_restoration_ledger_markdown(
    payload: dict[str, object],
) -> str:
    lines = [
        "# Repository docs restoration ledger",
        "",
        f"- Rule: {payload['rule']}",
        f"- Ledger rows: `{payload['row_count']}`",
        f"- Verified replacements: `{payload['status_counts']['verified_replacement']}`",
        f"- Replacement gaps: `{payload['status_counts']['replacement_incomplete']}`",
        "",
        "| Legacy page | Decision | Current replacement | Status |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['legacy_path']}` | `{row['decision']}` | `{row['current_path']}` | `{row['status']}` |"
        )
    return "\n".join(lines) + "\n"


def build_repository_docs_scope_validation(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Enforce that major handbook rewrites keep breadth present and linked."""
    _ = data_root
    _ = report_root
    repo_root = docs_root.parent
    rows = []
    for row in _docs_breadth_expectations():
        landing_path = repo_root / row["landing_path"]
        landing_text = (
            landing_path.read_text(encoding="utf-8") if landing_path.exists() else ""
        )
        missing_pages = [
            path for path in row["required_pages"] if not (repo_root / path).exists()
        ]
        missing_links = [
            snippet
            for snippet in row["required_link_snippets"]
            if snippet not in landing_text
        ]
        missing_snippets = [
            snippet
            for snippet in row["required_topic_snippets"]
            if snippet not in landing_text
        ]
        overall_ok = not missing_pages and not missing_links and not missing_snippets
        rows.append(
            {
                "section_key": row["section_key"],
                "display_name": row["display_name"],
                "landing_path": row["landing_path"],
                "required_page_count": len(row["required_pages"]),
                "missing_pages": missing_pages,
                "missing_links": missing_links,
                "missing_topic_snippets": missing_snippets,
                "overall_ok": overall_ok,
            }
        )
    return {
        "schema_version": "repository-docs-scope-validation.v1",
        "rule": (
            "no docs rewrite may destroy breadth in 01, 02, or 03 unless an equally informative replacement is already present and linked"
        ),
        "overall_ok": all(bool(row["overall_ok"]) for row in rows),
        "rows": rows,
    }


def render_repository_docs_scope_validation_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Repository docs scope validation",
        "",
        f"- Rule: {payload['rule']}",
        f"- Overall ok: `{str(payload['overall_ok']).lower()}`",
        "",
        "| Section | Landing | Required pages | Missing pages | Missing links |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['display_name']} | `{row['landing_path']}` | {row['required_page_count']} | "
            f"{', '.join(f'`{path}`' for path in row['missing_pages']) or '`none`'} | "
            f"{', '.join(f'`{path}`' for path in row['missing_links']) or '`none`'} |"
        )
    return "\n".join(lines) + "\n"
