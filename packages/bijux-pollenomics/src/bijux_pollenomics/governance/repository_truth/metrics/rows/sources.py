"""Rows describing source-family, atlas, and cross-domain evidence."""

from __future__ import annotations

from pathlib import Path

__all__: list[str] = []


def _source_family_row(
    key: str,
    display_name: str,
    role: str,
    artifact_paths: list[str],
    docs_paths: list[str],
    visible_count: int,
    acquisition_posture: str,
    main_gap: str,
) -> dict[str, object]:
    return {
        "source_key": key,
        "display_name": display_name,
        "role": role,
        "artifact_paths": artifact_paths,
        "docs_paths": docs_paths,
        "visible_count": visible_count,
        "acquisition_posture": acquisition_posture,
        "main_gap": main_gap,
    }


def _build_source_explainer_audit_row(
    *,
    docs_root: Path,
    surface_kind: str,
    display_name: str,
    page_path: str,
    required_snippets: list[str],
    restoration_plan: str | None,
) -> dict[str, object]:
    page = docs_root.parent / page_path
    if page.exists():
        text = page.read_text(encoding="utf-8")
        missing_snippets = [
            snippet for snippet in required_snippets if snippet not in text
        ]
        if not missing_snippets:
            return {
                "surface_kind": surface_kind,
                "display_name": display_name,
                "page_path": page_path,
                "status": "present_useful_form",
                "notes": "page exists and keeps the expected source or output anchors visible",
            }
        return {
            "surface_kind": surface_kind,
            "display_name": display_name,
            "page_path": page_path,
            "status": "restoration_plan_required",
            "notes": "missing expected anchors: "
            + ", ".join(f"`{snippet}`" for snippet in missing_snippets),
        }
    return {
        "surface_kind": surface_kind,
        "display_name": display_name,
        "page_path": page_path,
        "status": "restoration_plan_required",
        "notes": restoration_plan
        or "page is missing and needs a concrete restoration path",
    }


def _atlas_input_row(
    key: str,
    display_name: str,
    domain_role: str,
    source_paths: list[str],
    normalized_paths: list[str],
    published_paths: list[str],
    refresh_anchor: str,
    metrics: dict[str, object],
    note: str,
) -> dict[str, object]:
    return {
        "input_key": key,
        "display_name": display_name,
        "domain_role": domain_role,
        "source_paths": source_paths,
        "normalized_paths": normalized_paths,
        "published_paths": published_paths,
        "refresh_anchor": refresh_anchor,
        "metrics": metrics,
        "note": note,
    }


def _cross_domain_matrix_row(
    key: str,
    display_name: str,
    domain_role: str,
    source_families: list[str],
    tracked_metrics: dict[str, object],
    docs_paths: list[str],
    published_paths: list[str],
    coverage_posture: str,
    current_gap: str,
) -> dict[str, object]:
    return {
        "domain_key": key,
        "display_name": display_name,
        "domain_role": domain_role,
        "source_families": source_families,
        "tracked_metrics": tracked_metrics,
        "docs_paths": docs_paths,
        "published_paths": published_paths,
        "coverage_posture": coverage_posture,
        "current_gap": current_gap,
    }
