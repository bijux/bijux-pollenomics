"""Sample-owned archaeological site evidence and publication."""

import shutil as shutil
import subprocess as subprocess

from .assembly import (
    _project_by_accession as _project_by_accession,
)
from .assembly import (
    build_project_sample_site_rows,
)
from .curation import (
    _recommended_next_surface as _recommended_next_surface,
)
from .curation import (
    build_sample_site_manual_curation_queue,
)
from .evidence import (
    _artifact_kind_from_path as _artifact_kind_from_path,
)
from .evidence import (
    _counts_by_status as _counts_by_status,
)
from .evidence import (
    _project_level_locality_status as _project_level_locality_status,
)
from .evidence import (
    _review_note_for as _review_note_for,
)
from .hierarchy import (
    _ghostscript_text as _ghostscript_text,
)
from .hierarchy import (
    _Hierarchy as _Hierarchy,
)
from .hierarchy import (
    _project_hierarchy_profiles as _project_hierarchy_profiles,
)
from .hierarchy import (
    _resolve_hierarchy as _resolve_hierarchy,
)
from .materialization import materialize_project_sample_site_library
from .records import ADNA_LOCALITY_RESOLUTION_STATUSES, AdnaProjectSampleSiteRow
from .rendering import (
    _empty_sample_site_row as _empty_sample_site_row,
)
from .rendering import (
    _render_sample_site_ambiguity_markdown as _render_sample_site_ambiguity_markdown,
)
from .rendering import (
    _render_sample_site_manual_queue_markdown as _render_sample_site_manual_queue_markdown,
)
from .review import (
    build_project_sample_site_review_rows,
    build_sample_site_ambiguity_ledger,
)

# Export order is part of the compatibility contract.
__all__ = [  # noqa: RUF022
    "ADNA_LOCALITY_RESOLUTION_STATUSES",
    "AdnaProjectSampleSiteRow",
    "build_project_sample_site_rows",
    "build_project_sample_site_review_rows",
    "build_sample_site_ambiguity_ledger",
    "build_sample_site_manual_curation_queue",
    "materialize_project_sample_site_library",
]
