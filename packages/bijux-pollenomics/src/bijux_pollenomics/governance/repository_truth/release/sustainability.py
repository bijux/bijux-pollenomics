"""Generated-output and repository balance sustainability review."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ..integrity import build_repository_governance_artifact_review
from ..metrics import _count_suffix_files, _count_tree_files


def build_repository_output_sustainability_review(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Review whether the balance of code, tracked data, and public outputs stays maintainable."""
    governance_review = build_repository_governance_artifact_review(
        data_root=data_root,
        report_root=report_root,
    )
    governance_summary = cast(dict[str, object], governance_review["summary"])
    rows = [
        {
            "surface_key": "report_root_navigation",
            "current_posture": "reader_portal_governed",
            "action": "keep",
            "finding": "the report root now routes readers through portal families instead of leaving them in a bare artifact spill",
            "evidence_anchor": "docs/report/report_surface_registry.json",
        },
        {
            "surface_key": "generated_root_diagnostics",
            "current_posture": "policy_gated",
            "action": "keep_only_with_explicit_role",
            "finding": "new root outputs are now governed by an explicit publication policy instead of being justified only by emitter convenience",
            "evidence_anchor": "docs/report/repository_generated_output_policy.json",
        },
        {
            "surface_key": "legacy_diagnostic_overlap",
            "current_posture": "one_retirement_still_named",
            "action": "retire_or_reframe",
            "finding": (
                f"the governance review still names {governance_summary['retire']} root artifact for retirement or reframing"
            ),
            "evidence_anchor": "docs/report/repository_governance_artifact_review.json",
        },
        {
            "surface_key": "world_to_country_publication_balance",
            "current_posture": "derived_scope_family",
            "action": "keep",
            "finding": "world, regional, and country outputs now share one scope lineage instead of multiplying separate product trees",
            "evidence_anchor": "docs/report/publication_geography_registry.json",
        },
    ]
    return {
        "schema_version": "repository-output-sustainability-review.v1",
        "balance_counts": {
            "runtime_python_file_count": _count_suffix_files(
                docs_root.parent / "packages" / "bijux-pollenomics" / "src", ".py"
            ),
            "tracked_data_file_count": _count_tree_files(data_root),
            "report_file_count": _count_tree_files(report_root),
            "maintainer_root_review_file_count": sum(
                1 for path in report_root.glob("repository_*.json")
            ),
        },
        "rows": rows,
    }


def render_repository_output_sustainability_review_markdown(
    payload: dict[str, object],
) -> str:
    lines = [
        "# Repository output sustainability review",
        "",
        "| Surface | Current posture | Action | Finding |",
        "| --- | --- | --- | --- |",
    ]
    for row in cast(list[dict[str, object]], payload["rows"]):
        lines.append(
            f"| `{row['surface_key']}` | `{row['current_posture']}` | `{row['action']}` | {row['finding']} |"
        )
    balance_counts = cast(dict[str, object], payload["balance_counts"])
    lines.extend(
        [
            "",
            "## Balance Counts",
            "",
            f"- Runtime Python files: `{balance_counts['runtime_python_file_count']}`",
            f"- Tracked data files: `{balance_counts['tracked_data_file_count']}`",
            f"- Report files: `{balance_counts['report_file_count']}`",
            f"- Maintainer root review files: `{balance_counts['maintainer_root_review_file_count']}`",
        ]
    )
    return "\n".join(lines) + "\n"
