"""Reader portal publication and report-surface classification."""

from .markdown import (
    _render_report_narrative_quality_review_markdown as _render_report_narrative_quality_review_markdown,
    _render_report_surface_registry_markdown as _render_report_surface_registry_markdown,
)
from .narrative_quality import (
    _build_quality_row as _build_quality_row,
    _build_report_narrative_quality_review as _build_report_narrative_quality_review,
    _count_prose_paragraphs as _count_prose_paragraphs,
    _looks_like_prose_block as _looks_like_prose_block,
    _looks_like_sentence_bullet as _looks_like_sentence_bullet,
)
from .pages import (
    _render_caveats_portal_page as _render_caveats_portal_page,
    _render_maintenance_portal_page as _render_maintenance_portal_page,
    _render_maps_portal_page as _render_maps_portal_page,
    _render_portal_pages as _render_portal_pages,
    _render_report_how_to_read as _render_report_how_to_read,
    _render_report_portal_index as _render_report_portal_index,
    _render_reviews_portal_page as _render_reviews_portal_page,
    _render_scopes_portal_page as _render_scopes_portal_page,
)
from .publication import publish_report_portal
from .surfaces import (
    _AUDIENCE_LABELS as _AUDIENCE_LABELS,
    _FAMILY_LABELS as _FAMILY_LABELS,
    _PORTAL_FILES as _PORTAL_FILES,
    _audience_for_path as _audience_for_path,
    _build_existing_surface_rows as _build_existing_surface_rows,
    _build_portal_rows as _build_portal_rows,
    _build_report_surface_registry as _build_report_surface_registry,
    _caution_level_for_path as _caution_level_for_path,
    _classify_surface as _classify_surface,
    _explanation_for_path as _explanation_for_path,
    _family_for_path as _family_for_path,
    _geography_for_path as _geography_for_path,
    _reader_route_for_path as _reader_route_for_path,
)

__all__ = ["publish_report_portal"]
