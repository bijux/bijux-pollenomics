"""Lake identity resolution and candidate construction compatibility surface."""

from __future__ import annotations

from collections import Counter as Counter
from collections.abc import Iterable as Iterable
from collections.abc import Sequence as Sequence
import re as re
from typing import TypedDict as TypedDict
import unicodedata as unicodedata

from bijux_pollenomics.collection.contracts.models import (
    ContextPointRecord as ContextPointRecord,
)
from bijux_pollenomics.core import haversine_km as haversine_km

from ..metrics import _weighted_average as _weighted_average
from ..models import (
    _COORDINATE_SPREAD_FLAG_KM as _COORDINATE_SPREAD_FLAG_KM,
)
from ..models import (
    _ENGINEERED_WATER_TERMS as _ENGINEERED_WATER_TERMS,
)
from ..models import (
    _GENERIC_LAKE_TOKENS as _GENERIC_LAKE_TOKENS,
)
from ..models import (
    _LAKE_MATCH_DISTANCE_KM as _LAKE_MATCH_DISTANCE_KM,
)
from ..models import (
    _LAKE_NAME_TERMS as _LAKE_NAME_TERMS,
)
from ..models import (
    _POSITION_NOTE_PATTERNS as _POSITION_NOTE_PATTERNS,
)
from ..models import (
    _WETLAND_TERMS as _WETLAND_TERMS,
)
from ..models import (
    LakeEvidenceCandidate as LakeEvidenceCandidate,
)
from ..models import (
    LakeEvidenceSourceAnchor as LakeEvidenceSourceAnchor,
)
from ..models import (
    _LakeSourcePoint as _LakeSourcePoint,
)
from ..models import (
    _PointEvidence as _PointEvidence,
)
from ..models import (
    _SvarLakeRecord as _SvarLakeRecord,
)
from ..temporal import (
    _human_context_overlap_ratio as _human_context_overlap_ratio,
)
from ..temporal import (
    _time_aware_ratio as _time_aware_ratio,
)
from ..temporal import (
    _validated_interval as _validated_interval,
)
from .matching import (
    _build_lake_components as _build_lake_components,
)
from .matching import (
    _choose_canonical_lake_name as _choose_canonical_lake_name,
)
from .matching import (
    _choose_representative_source_point as _choose_representative_source_point,
)
from .matching import (
    _coordinate_resolution_method as _coordinate_resolution_method,
)
from .matching import (
    _is_direct_lake_pollen_match as _is_direct_lake_pollen_match,
)
from .matching import (
    _lake_points_match as _lake_points_match,
)
from .matching import (
    _max_pair_distance as _max_pair_distance,
)
from .matching import (
    _total_distance_to_component as _total_distance_to_component,
)
from .naming import (
    _build_lake_token as _build_lake_token,
)
from .naming import (
    _clean_lake_name_display as _clean_lake_name_display,
)
from .naming import (
    _lake_name_key as _lake_name_key,
)
from .naming import (
    _lake_name_source_priority as _lake_name_source_priority,
)
from .naming import (
    _name_has_non_ascii as _name_has_non_ascii,
)
from .naming import (
    _normalize_text as _normalize_text,
)
from .naming import (
    _resolve_basin_posture as _resolve_basin_posture,
)
from .naming import (
    _tokenize_lake_name as _tokenize_lake_name,
)
from .pollen import (
    _derive_lake_candidates as _derive_lake_candidates,
)
from .pollen import (
    _LakeCandidateDraft as _LakeCandidateDraft,
)
from .registry import (
    _derive_svar_lake_candidates as _derive_svar_lake_candidates,
)
from .registry import (
    _SvarLakeCandidateDraft as _SvarLakeCandidateDraft,
)
from .sampling import (
    _classify_sampling_lake as _classify_sampling_lake,
)
from .sampling import (
    _lake_sampling_fit as _lake_sampling_fit,
)
from .uncertainty import (
    _base_ambiguity_flags as _base_ambiguity_flags,
)
from .uncertainty import (
    _build_ambiguity_note as _build_ambiguity_note,
)
from .uncertainty import (
    _build_lake_label as _build_lake_label,
)
from .uncertainty import (
    _normalize_note_text as _normalize_note_text,
)
from .uncertainty import (
    _note_signals_position_uncertainty as _note_signals_position_uncertainty,
)

__all__ = []
