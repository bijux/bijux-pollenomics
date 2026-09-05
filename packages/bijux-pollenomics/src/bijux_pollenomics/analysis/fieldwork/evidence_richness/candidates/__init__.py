"""Lake identity resolution and candidate construction compatibility surface."""

from __future__ import annotations

from collections import Counter as Counter
from collections.abc import Iterable as Iterable, Sequence as Sequence
import re as re
from typing import TypedDict as TypedDict
import unicodedata as unicodedata

from bijux_pollenomics.collection.contracts.models import (
    ContextPointRecord as ContextPointRecord,
)
from bijux_pollenomics.core import haversine_km as haversine_km
from ..metrics import _weighted_average as _weighted_average
from ..models import (
    LakeEvidenceCandidate as LakeEvidenceCandidate,
    LakeEvidenceSourceAnchor as LakeEvidenceSourceAnchor,
    _COORDINATE_SPREAD_FLAG_KM as _COORDINATE_SPREAD_FLAG_KM,
    _ENGINEERED_WATER_TERMS as _ENGINEERED_WATER_TERMS,
    _GENERIC_LAKE_TOKENS as _GENERIC_LAKE_TOKENS,
    _LAKE_MATCH_DISTANCE_KM as _LAKE_MATCH_DISTANCE_KM,
    _LAKE_NAME_TERMS as _LAKE_NAME_TERMS,
    _LakeSourcePoint as _LakeSourcePoint,
    _POSITION_NOTE_PATTERNS as _POSITION_NOTE_PATTERNS,
    _PointEvidence as _PointEvidence,
    _SvarLakeRecord as _SvarLakeRecord,
    _WETLAND_TERMS as _WETLAND_TERMS,
)
from ..temporal import (
    _human_context_overlap_ratio as _human_context_overlap_ratio,
    _time_aware_ratio as _time_aware_ratio,
    _validated_interval as _validated_interval,
)
from .matching import (
    _build_lake_components as _build_lake_components,
    _choose_canonical_lake_name as _choose_canonical_lake_name,
    _choose_representative_source_point as _choose_representative_source_point,
    _coordinate_resolution_method as _coordinate_resolution_method,
    _is_direct_lake_pollen_match as _is_direct_lake_pollen_match,
    _lake_points_match as _lake_points_match,
    _max_pair_distance as _max_pair_distance,
    _total_distance_to_component as _total_distance_to_component,
)
from .naming import (
    _build_lake_token as _build_lake_token,
    _clean_lake_name_display as _clean_lake_name_display,
    _lake_name_key as _lake_name_key,
    _lake_name_source_priority as _lake_name_source_priority,
    _name_has_non_ascii as _name_has_non_ascii,
    _normalize_text as _normalize_text,
    _resolve_basin_posture as _resolve_basin_posture,
    _tokenize_lake_name as _tokenize_lake_name,
)
from .pollen import (
    _LakeCandidateDraft as _LakeCandidateDraft,
    _derive_lake_candidates as _derive_lake_candidates,
)
from .registry import (
    _SvarLakeCandidateDraft as _SvarLakeCandidateDraft,
    _derive_svar_lake_candidates as _derive_svar_lake_candidates,
)
from .sampling import (
    _classify_sampling_lake as _classify_sampling_lake,
    _lake_sampling_fit as _lake_sampling_fit,
)
from .uncertainty import (
    _base_ambiguity_flags as _base_ambiguity_flags,
    _build_ambiguity_note as _build_ambiguity_note,
    _build_lake_label as _build_lake_label,
    _normalize_note_text as _normalize_note_text,
    _note_signals_position_uncertainty as _note_signals_position_uncertainty,
)

__all__ = []
