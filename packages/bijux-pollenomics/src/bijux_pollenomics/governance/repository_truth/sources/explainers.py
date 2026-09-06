"""Repository-facing source explainer availability audits."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TypedDict, cast

from ..metrics import (
    _build_source_explainer_audit_row as _untyped_source_explainer_audit_row,
)

__all__ = [
    "build_repository_source_explainer_audit",
    "render_repository_source_explainer_audit_markdown",
]


class _ExplainerRow(TypedDict):
    page_path: str
    surface_kind: str
    status: str
    notes: str


class _ExplainerStatusCounts(TypedDict):
    present_useful_form: int
    restoration_plan_required: int


class _ExplainerPayload(TypedDict):
    row_count: int
    status_counts: _ExplainerStatusCounts
    rows: list[_ExplainerRow]


_build_source_explainer_audit_row = cast(
    Callable[..., _ExplainerRow], _untyped_source_explainer_audit_row
)


def build_repository_source_explainer_audit(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Audit whether cross-domain data explainers exist in useful form."""
    _ = data_root
    _ = report_root
    rows = []
    expectations = (
        (
            "source_family",
            "LandClim source explainer",
            "docs/public/pollenomics-data/sources/landclim.md",
            ["data/landclim/normalized/", "pollen context"],
            None,
        ),
        (
            "source_family",
            "Neotoma source explainer",
            "docs/public/pollenomics-data/sources/neotoma.md",
            ["data/neotoma/normalized/", "pollen-site context"],
            None,
        ),
        (
            "source_family",
            "SEAD source explainer",
            "docs/public/pollenomics-data/sources/sead.md",
            ["data/sead/normalized/", "archaeology context"],
            None,
        ),
        (
            "source_family",
            "RAÄ source explainer",
            "docs/public/pollenomics-data/sources/raa.md",
            ["data/raa/normalized/", "Sweden"],
            None,
        ),
        (
            "source_family",
            "Boundary source explainer",
            "docs/public/pollenomics-data/sources/boundaries.md",
            ["data/boundaries/normalized/", "country filtering"],
            None,
        ),
        (
            "source_family",
            "AADR source explainer",
            "docs/public/pollenomics-data/sources/aadr.md",
            ["data/aadr/v66/", "human ancient DNA"],
            None,
        ),
        (
            "infrastructure_network",
            "PalaeOpen network explainer",
            "docs/public/pollenomics-data/sources/palaeopen.md",
            ["metadata harmonization", "not a direct source"],
            "restore the PalaeOpen page so collaboration and interoperability work does not get mislabeled as direct evidence capture",
        ),
        (
            "recovery_rule",
            "Refresh policy explainer",
            "docs/public/pollenomics-data/sources/refresh-policy.md",
            ["data/collection_summary.json", "refresh"],
            "restore the refresh-policy page so readers can separate evidence refresh from silent maintenance",
        ),
        (
            "recovery_rule",
            "Shared normalization explainer",
            "docs/public/pollenomics-data/sources/shared-normalization.md",
            ["docs/report/world/", "normalized"],
            "restore the shared-normalization page so readers can see how cross-family output shapes differ from source identity",
        ),
        (
            "output_family",
            "Normalized LandClim outputs explainer",
            "docs/public/pollenomics-data/publications/landclim-exports.md",
            ["data/landclim/normalized/", "LandClim"],
            "restore the LandClim output page so pollen context is not explained only through map presence",
        ),
        (
            "output_family",
            "Normalized Neotoma outputs explainer",
            "docs/public/pollenomics-data/publications/neotoma-exports.md",
            ["data/neotoma/normalized/", "Neotoma"],
            "restore the Neotoma output page so pollen-site context stays visible as its own family",
        ),
        (
            "output_family",
            "Normalized SEAD outputs explainer",
            "docs/public/pollenomics-data/publications/sead-exports.md",
            ["data/sead/normalized/", "SEAD"],
            "restore the SEAD output page so environmental archaeology context does not vanish behind animal publication work",
        ),
        (
            "output_family",
            "Normalized RAÄ outputs explainer",
            "docs/public/pollenomics-data/publications/raa-exports.md",
            ["data/raa/normalized/", "Sweden-specific"],
            "restore the RAÄ output page so Swedish archaeology scope remains explicit",
        ),
        (
            "output_family",
            "Normalized boundary outputs explainer",
            "docs/public/pollenomics-data/publications/boundary-exports.md",
            ["data/boundaries/normalized/", "boundary"],
            "restore the boundary output page so framing layers stay explainable on their own terms",
        ),
        (
            "output_family",
            "Normalized AADR outputs explainer",
            "docs/public/pollenomics-data/publications/aadr-exports.md",
            ["data/aadr/v66/", "AADR"],
            "restore the AADR output page so versioned human context remains inspectable from source to publication",
        ),
        (
            "output_family",
            "Collection summary explainer",
            "docs/public/pollenomics-data/publications/collection-summary.md",
            ["data/collection_summary.json", "summary"],
            "restore the collection summary page so refresh diagnostics are not mistaken for balanced domain coverage",
        ),
    )
    for (
        surface_kind,
        display_name,
        page_path,
        required_snippets,
        restoration_plan,
    ) in expectations:
        rows.append(
            _build_source_explainer_audit_row(
                docs_root=docs_root,
                surface_kind=surface_kind,
                display_name=display_name,
                page_path=page_path,
                required_snippets=required_snippets,
                restoration_plan=restoration_plan,
            )
        )

    status_counts = {
        "present_useful_form": sum(
            1 for row in rows if row["status"] == "present_useful_form"
        ),
        "restoration_plan_required": sum(
            1 for row in rows if row["status"] == "restoration_plan_required"
        ),
    }
    return {
        "schema_version": "repository-source-explainer-audit.v1",
        "row_count": len(rows),
        "status_counts": status_counts,
        "rows": rows,
    }


def render_repository_source_explainer_audit_markdown(
    payload: dict[str, object],
) -> str:
    audit = cast(_ExplainerPayload, payload)
    lines = [
        "# Repository source explainer audit",
        "",
        f"- Explainer rows: `{audit['row_count']}`",
        f"- Present in useful form: `{audit['status_counts']['present_useful_form']}`",
        f"- Still needing a restoration plan: `{audit['status_counts']['restoration_plan_required']}`",
        "",
        "| Explainer | Surface kind | Status | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for row in audit["rows"]:
        lines.append(
            f"| `{row['page_path']}` | `{row['surface_kind']}` | `{row['status']}` | {row['notes']} |"
        )
    return "\n".join(lines) + "\n"
