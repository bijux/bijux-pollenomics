"""Compatibility surface for animal-atlas evidence row construction."""

from .chronology import (
    _atlas_public_chronology as _atlas_public_chronology,
    _optional_float as _optional_float,
    _optional_int as _optional_int,
    _optional_str as _optional_str,
    _parse_chronology as _parse_chronology,
)
from .coordinate_review import (
    _DIRECT_COORDINATE_BASES as _DIRECT_COORDINATE_BASES,
    build_tracked_animal_atlas_coordinate_review as build_tracked_animal_atlas_coordinate_review,
)
from .localities import (
    _parse_locality_summary as _parse_locality_summary,
    load_tracked_animal_mappable_localities as load_tracked_animal_mappable_localities,
)
from .models import (
    AnimalAtlasCoordinateReview as AnimalAtlasCoordinateReview,
    AnimalAtlasEvidenceRow as AnimalAtlasEvidenceRow,
)
from .row_factory import _paper_url_for as _paper_url_for
from .sample_support import (
    _inclusion_notes_for as _inclusion_notes_for,
    _inclusion_statuses_for as _inclusion_statuses_for,
    _sample_group_ids_for as _sample_group_ids_for,
    _sample_locality_token as _sample_locality_token,
    _sample_record_ids_for as _sample_record_ids_for,
    _supplementary_sources_for as _supplementary_sources_for,
)
from .service import (
    build_tracked_animal_atlas_evidence_rows as build_tracked_animal_atlas_evidence_rows,
)
from .source_records import (
    _animal_scope_for as _animal_scope_for,
    _load_citation_lookup as _load_citation_lookup,
    _load_coordinate_provenance_lookup as _load_coordinate_provenance_lookup,
    _load_locality_rows as _load_locality_rows,
    _load_review_lookup as _load_review_lookup,
    _load_sample_rows as _load_sample_rows,
    _load_site_evidence_lookup as _load_site_evidence_lookup,
    _lookup_project_locality_row as _lookup_project_locality_row,
)
from .validation import (
    _assert_no_project_level_flattening as _assert_no_project_level_flattening,
    _normalize_locality_text as _normalize_locality_text,
)

__all__ = [
    "AnimalAtlasCoordinateReview",
    "AnimalAtlasEvidenceRow",
    "build_tracked_animal_atlas_coordinate_review",
    "build_tracked_animal_atlas_evidence_rows",
    "load_tracked_animal_mappable_localities",
]
