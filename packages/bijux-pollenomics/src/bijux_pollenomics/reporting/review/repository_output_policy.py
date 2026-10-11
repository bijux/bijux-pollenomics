"""Repository-truth generated-output policy and renderer contract."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypedDict


class _RepositoryOutputSpec(TypedDict):
    stem: str
    payload: dict[str, object]
    render_markdown: Callable[[dict[str, object]], str]
    audience: str
    information_role: str
    root_location: str
    coexistence_rule: str
    docs_anchor: str
    test_anchor: str


def _build_repository_generated_output_policy(
    specs: list[_RepositoryOutputSpec],
) -> dict[str, object]:
    rows = [
        {
            "stem": str(spec["stem"]),
            "json_path": f"docs/report/{spec['stem']}.json",
            "markdown_path": f"docs/report/{spec['stem']}.md",
            "audience": str(spec["audience"]),
            "information_role": str(spec["information_role"]),
            "root_location": str(spec["root_location"]),
            "coexistence_rule": str(spec["coexistence_rule"]),
            "docs_anchor": str(spec["docs_anchor"]),
            "test_anchor": str(spec["test_anchor"]),
        }
        for spec in specs
    ]
    rows.append(
        {
            "stem": "repository_generated_output_policy",
            "json_path": "docs/report/repository_generated_output_policy.json",
            "markdown_path": "docs/report/repository_generated_output_policy.md",
            "audience": "maintainer_diagnostic",
            "information_role": "generated-output publication policy",
            "root_location": "docs/report",
            "coexistence_rule": "coexists with the report portal and repository truth reviews as the rule that governs new root outputs",
            "docs_anchor": "docs/internal/pollenomics-dev/release-support.md",
            "test_anchor": "packages/bijux-pollenomics/tests/unit/governance/repository_truth/test_assessments.py",
        }
    )
    return {
        "schema_version": "repository-generated-output-policy.v1",
        "rule": (
            "no generated root output may be published unless its audience, information role, root location, and coexistence rule are explicit in code, docs, and tests"
        ),
        "row_count": len(rows),
        "rows": rows,
    }


def _render_repository_generated_output_policy_markdown(
    payload: dict[str, object],
) -> str:
    rows = "\n".join(
        f"| `{row['stem']}` | `{row['audience']}` | {row['information_role']} | `{row['root_location']}` | {row['coexistence_rule']} | `{row['docs_anchor']}` | `{row['test_anchor']}` |"
        for row in _policy_rows(payload.get("rows"))
    )
    return f"""# Repository generated output policy

This policy exists to stop `docs/report/` from turning back into a root-level
artifact spill. A new generated output is allowed only when its audience,
information role, root location, and coexistence logic are explicit in the code
that publishes it, in reader or maintainer documentation, and in tests that
will fail if the contract drifts.

- Rule: {payload["rule"]}
- Governed outputs: `{payload["row_count"]}`

## Governed Root Outputs

| Stem | Audience | Information role | Root location | Coexistence rule | Docs anchor | Test anchor |
| --- | --- | --- | --- | --- | --- | --- |
{rows}
"""


def _policy_rows(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ValueError("Repository generated output policy rows must be a list")
    rows: list[dict[str, str]] = []
    required = (
        "stem",
        "audience",
        "information_role",
        "root_location",
        "coexistence_rule",
        "docs_anchor",
        "test_anchor",
    )
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("Repository generated output policy row must be an object")
        row: dict[str, str] = {}
        for field in required:
            member = item.get(field)
            if not isinstance(member, str):
                raise ValueError(
                    f"Repository generated output policy {field} must be text"
                )
            row[field] = member
        rows.append(row)
    return rows
