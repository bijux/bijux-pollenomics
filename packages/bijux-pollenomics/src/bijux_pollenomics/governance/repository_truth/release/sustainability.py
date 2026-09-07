"""Generated-output and repository balance sustainability review."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import cast

from ..integrity import build_repository_governance_artifact_review
from ..metrics import _count_suffix_files, _count_tree_files

_GIT_REGULAR_FILE_MODES = frozenset({b"100644", b"100755"})


def _count_git_tracked_regular_files(
    path: Path, *, repository_root: Path
) -> int | None:
    """Count indexed regular files, or report unavailable outside a Git checkout."""
    try:
        # The executable and arguments are fixed repository-inspection probes.
        completed = subprocess.run(  # nosec B603
            (
                "git",
                "-C",
                str(repository_root),
                "ls-files",
                "--stage",
                "-z",
                "--full-name",
                "--",
                f":(literal){path.resolve().relative_to(repository_root.resolve())}",
            ),
            check=True,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            shell=False,
        )
    except (OSError, subprocess.CalledProcessError):
        return None

    count = 0
    for record in completed.stdout.split(b"\0"):
        if not record:
            continue
        metadata, separator, _tracked_path = record.partition(b"\t")
        fields = metadata.split(b" ")
        if not separator or len(fields) != 3 or fields[2] != b"0":
            raise RuntimeError("tracked data count found an invalid Git index entry")
        if fields[0] in _GIT_REGULAR_FILE_MODES:
            count += 1
    return count


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
            "tracked_data_file_count": _count_git_tracked_regular_files(
                data_root, repository_root=docs_root.parent
            ),
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
            "- Tracked data files: "
            + (
                "unavailable (Git index could not be inspected)"
                if balance_counts["tracked_data_file_count"] is None
                else f"`{balance_counts['tracked_data_file_count']}`"
            ),
            f"- Report files: `{balance_counts['report_file_count']}`",
            f"- Maintainer root review files: `{balance_counts['maintainer_root_review_file_count']}`",
        ]
    )
    return "\n".join(lines) + "\n"
