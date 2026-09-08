from __future__ import annotations

import json
from pathlib import Path

from .markdown import (
    _render_report_narrative_quality_review_markdown,
    _render_report_surface_registry_markdown,
)
from .narrative_quality import _build_report_narrative_quality_review
from .pages import _render_portal_pages
from .surfaces import (
    _build_existing_surface_rows,
    _build_portal_rows,
    _build_report_surface_registry,
)


def publish_report_portal(output_root: Path) -> dict[str, str]:
    """Publish a human-facing portal and classification registry for docs/report."""
    output_root = Path(output_root)
    existing_rows = _build_existing_surface_rows(output_root)
    portal_pages = _render_portal_pages(output_root, existing_rows)
    portal_rows = _build_portal_rows(output_root, portal_pages)
    all_rows = [*existing_rows, *portal_rows]

    registry_payload = _build_report_surface_registry(all_rows)
    quality_payload = _build_report_narrative_quality_review(
        output_root=output_root,
        existing_rows=existing_rows,
        portal_pages=portal_pages,
    )

    for relative_path, content in portal_pages.items():
        path = output_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    (output_root / "report_surface_registry.json").write_text(
        json.dumps(registry_payload, indent=2),
        encoding="utf-8",
    )
    (output_root / "report_surface_registry.md").write_text(
        _render_report_surface_registry_markdown(registry_payload),
        encoding="utf-8",
    )
    (output_root / "report_narrative_quality_review.json").write_text(
        json.dumps(quality_payload, indent=2),
        encoding="utf-8",
    )
    (output_root / "report_narrative_quality_review.md").write_text(
        _render_report_narrative_quality_review_markdown(quality_payload),
        encoding="utf-8",
    )

    return {
        "report_portal_index": "index.md",
        "report_portal_how_to_read": "how-to-read.md",
        "report_portal_maps": "maps/index.md",
        "report_portal_scopes": "scopes/index.md",
        "report_portal_reviews": "reviews/index.md",
        "report_portal_caveats": "caveats/index.md",
        "report_portal_maintenance": "maintenance/index.md",
        "report_surface_registry_json": "report_surface_registry.json",
        "report_surface_registry_markdown": "report_surface_registry.md",
        "report_narrative_quality_review_json": "report_narrative_quality_review.json",
        "report_narrative_quality_review_markdown": "report_narrative_quality_review.md",
    }
