"""Typed stage boundaries for the SEAD atlas projection."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvidenceBundle:
    """Validated governed documents and their acquisition identity."""

    context_root: Path
    acquisition_root: Path
    claims: Mapping[str, object]
    observations: Mapping[str, object]
    relations: Mapping[str, object]
    events: Mapping[str, object]
    manifest: Mapping[str, object]
    admission: Mapping[str, object]
    run_id: str
    file_set_sha256: str


@dataclass(frozen=True)
class ClaimIndex:
    """Chronology claims grouped by governed site."""

    rows: list[Mapping[str, object]]
    by_site: dict[str, list[Mapping[str, object]]]
    country_counts: Counter[str]


@dataclass(frozen=True)
class RelationIndex:
    """Source-native relation rows and stable identity indexes."""

    entity_rows: list[Mapping[str, object]]
    taxon_rows: list[Mapping[str, object]]
    dimension_rows: list[Mapping[str, object]]
    dimension_semantic_rows: list[Mapping[str, object]]
    dataset_semantic_rows: list[Mapping[str, object]]
    value_semantic_rows: list[Mapping[str, object]]
    entity_by_id: dict[str, Mapping[str, object]]
    taxon_by_id: dict[str, Mapping[str, object]]
    dimension_by_id: dict[str, Mapping[str, object]]
    dimension_semantic_by_id: dict[str, Mapping[str, object]]
    dataset_semantic_by_id: dict[str, Mapping[str, object]]
    value_semantic_by_id: dict[str, Mapping[str, object]]
    site_by_owner: dict[str, dict[str, str]]


@dataclass(frozen=True)
class ObservationIndex:
    """Projected observations and every referenced relation identity."""

    rows: list[Mapping[str, object]]
    refusal_rows: list[Mapping[str, object]]
    by_site: dict[str, list[list[object]]]
    entities_by_site: dict[str, dict[str, list[object]]]
    taxon_ids_by_site: dict[str, set[str]]
    dimension_ids_by_site: dict[str, set[str]]
    dataset_semantic_ids_by_site: dict[str, set[str]]
    value_semantic_ids_by_site: dict[str, set[str]]
    referenced_taxon_ids: set[str]
    referenced_dimension_ids: set[str]
    referenced_dataset_semantic_ids: set[str]
    referenced_value_semantic_ids: set[str]
    country_counts: Counter[str]
    eligible_country_counts: Mapping[str, object]


@dataclass(frozen=True)
class SiteIndex:
    """Governed Nordic sites reconciled to mutable atlas features."""

    rows_by_id: dict[str, Mapping[str, object]]
    decision_rows: list[Mapping[str, object]]
    assigned_site_ids: set[str]
    feature_site_ids: set[str]
    feature_count: int
