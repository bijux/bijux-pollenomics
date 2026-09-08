"""Reader portal publication and report-surface classification."""

from .markdown import (
    _render_report_narrative_quality_review_markdown as _render_report_narrative_quality_review_markdown,
)
from .markdown import (
    _render_report_surface_registry_markdown as _render_report_surface_registry_markdown,
)
from .narrative_quality import (
    _build_quality_row as _build_quality_row,
)
from .narrative_quality import (
    _build_report_narrative_quality_review as _build_report_narrative_quality_review,
)
from .narrative_quality import (
    _count_prose_paragraphs as _count_prose_paragraphs,
)
from .narrative_quality import (
    _looks_like_prose_block as _looks_like_prose_block,
)
from .narrative_quality import (
    _looks_like_sentence_bullet as _looks_like_sentence_bullet,
)
from .pages import (
    _render_caveats_portal_page as _render_caveats_portal_page,
)
from .pages import (
    _render_maintenance_portal_page as _render_maintenance_portal_page,
)
from .pages import (
    _render_maps_portal_page as _render_maps_portal_page,
)
from .pages import (
    _render_portal_pages as _render_portal_pages,
)
from .pages import (
    _render_report_how_to_read as _render_report_how_to_read,
)
from .pages import (
    _render_report_portal_index as _render_report_portal_index,
)
from .pages import (
    _render_reviews_portal_page as _render_reviews_portal_page,
)
from .pages import (
    _render_scopes_portal_page as _render_scopes_portal_page,
)
from .publication import publish_report_portal
from .surfaces import (
    _AUDIENCE_LABELS as _AUDIENCE_LABELS,
)
from .surfaces import (
    _FAMILY_LABELS as _FAMILY_LABELS,
)
from .surfaces import (
    _PORTAL_FILES as _PORTAL_FILES,
)
from .surfaces import (
    _audience_for_path as _audience_for_path,
)
from .surfaces import (
    _build_existing_surface_rows as _build_existing_surface_rows,
)
from .surfaces import (
    _build_portal_rows as _build_portal_rows,
)
from .surfaces import (
    _build_report_surface_registry as _build_report_surface_registry,
)
from .surfaces import (
    _caution_level_for_path as _caution_level_for_path,
)
from .surfaces import (
    _classify_surface as _classify_surface,
)
from .surfaces import (
    _explanation_for_path as _explanation_for_path,
)
from .surfaces import (
    _family_for_path as _family_for_path,
)
from .surfaces import (
    _geography_for_path as _geography_for_path,
)
from .surfaces import (
    _reader_route_for_path as _reader_route_for_path,
)

__all__ = ["publish_report_portal"]
