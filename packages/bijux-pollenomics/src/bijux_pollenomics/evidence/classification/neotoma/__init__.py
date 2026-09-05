"""Lossless, non-interpretive Neotoma classification accounting."""

from __future__ import annotations

from collections import Counter as Counter
from collections import defaultdict as defaultdict
from collections.abc import Mapping as Mapping
from collections.abc import Sequence as Sequence
import copy as copy
import hashlib as hashlib
import json as json
import re as re

from .accounting import (
    _build_neotoma_classification_accounting as _build_neotoma_classification_accounting,
)
from .concepts import (
    _blocker as _blocker,
    _concept_id as _concept_id,
    _finalize_concept as _finalize_concept,
    _mapping_posture as _mapping_posture,
    _partition_value as _partition_value,
    _qualifier_markers as _qualifier_markers,
    _set_member as _set_member,
    _source_concept_identity as _source_concept_identity,
    _source_evidence_universe as _source_evidence_universe,
    _variable_identity_matches as _variable_identity_matches,
)
from .countries import (
    _country_partition_rows as _country_partition_rows,
    _country_relation_rows as _country_relation_rows,
    _country_release_blockers as _country_release_blockers,
    _country_sort_key as _country_sort_key,
    _governed_country_code as _governed_country_code,
    _source_country_code as _source_country_code,
)
from .partitions import (
    _build_partitions as _build_partitions,
    _concept_field_partition_rows as _concept_field_partition_rows,
)
from .rows import (
    _canonical_json as _canonical_json,
    _deduplicate_observations as _deduplicate_observations,
    _index_rows as _index_rows,
    _integer_count as _integer_count,
    _mapping_rows as _mapping_rows,
    _required_text as _required_text,
)

__all__ = ["build_neotoma_classification_accounting"]

_COUNTRY_CODES = {
    "Denmark": "DK",
    "Finland": "FI",
    "Norway": "NO",
    "Sweden": "SE",
}
_COUNTRY_PARTITION = ("SE", "DK", "NO", "FI", "UNASSIGNED")
_MAPPING_STATUSES = (
    "accepted",
    "accepted_qualified",
    "unmapped",
    "contested",
    "not_applicable",
    "refused",
)
_LABORATORY_ECOLOGICAL_GROUPS = frozenset({"LABO"})
_LABORATORY_TAXON_GROUPS = frozenset({"Laboratory", "Laboratory analyses"})
_ADMINISTRATIVE_ECOLOGICAL_GROUPS = frozenset({"ADMN"})
_ADMINISTRATIVE_TAXON_GROUPS = frozenset({"Administrative", "Administrative variables"})
_QUALIFIER_PATTERNS = (
    ("cf", re.compile(r"(?:^|\s)cf\.\s", re.IGNORECASE)),
    ("type", re.compile(r"(?:-|\.|\s)type(?:\b|\))", re.IGNORECASE)),
    ("undifferentiated", re.compile(r"\bundiff\.?\b", re.IGNORECASE)),
    ("combined_taxa", re.compile(r"/")),
    ("group", re.compile(r"\bgroup\b", re.IGNORECASE)),
    ("sensu_lato", re.compile(r"\bsensu\s+lato\b", re.IGNORECASE)),
    ("subgenus", re.compile(r"\bsubg\.\s", re.IGNORECASE)),
)
_RELEASE_REASON_CODES = (
    "accepted_mapping_not_available",
    "mapping_evidence_not_available",
    "human_review_not_available",
)


def build_neotoma_classification_accounting(
    relational_snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Build a lossless, non-interpretive classification accounting surface."""
    return _build_neotoma_classification_accounting(relational_snapshot)
