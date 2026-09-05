"""Pure selection, grouping, and partitioning for animal atlas assembly."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from ....adna import AdnaLocalitySummary
from ...geography import GeographicScope
from ..atlas_evidence_rows import AnimalAtlasEvidenceRow

EvidenceLoader = Callable[[Path], tuple[AnimalAtlasEvidenceRow, ...]]
LocalityLoader = Callable[[Path], tuple[AdnaLocalitySummary, ...]]
ScopeContains = Callable[[GeographicScope, str], bool]


def _select_evidence_rows(
    data_root: Path,
    geography_scope: GeographicScope | None,
    *,
    load_rows: EvidenceLoader,
    scope_contains: ScopeContains,
) -> tuple[AnimalAtlasEvidenceRow, ...]:
    return tuple(
        row
        for row in load_rows(data_root)
        if geography_scope is None
        or scope_contains(geography_scope, row.political_entity)
    )


def _select_localities(
    data_root: Path,
    geography_scope: GeographicScope | None,
    *,
    load_localities: LocalityLoader,
    scope_contains: ScopeContains,
) -> tuple[AdnaLocalitySummary, ...]:
    return tuple(
        locality
        for locality in load_localities(data_root)
        if geography_scope is None
        or scope_contains(
            geography_scope,
            str(locality.identity.political_entity or ""),
        )
    )


def _group_rows_by_species(
    rows: Iterable[AnimalAtlasEvidenceRow],
) -> dict[str, list[AnimalAtlasEvidenceRow]]:
    grouped: dict[str, list[AnimalAtlasEvidenceRow]] = {}
    for row in rows:
        grouped.setdefault(row.species_latin_name, []).append(row)
    return grouped


def _features_have_time_filter(features: Iterable[dict[str, object]]) -> bool:
    return any(
        feature.get("time_start_bp") is not None
        or feature.get("time_end_bp") is not None
        or feature.get("time_mean_bp") is not None
        for feature in features
    )


def _partition_features(
    *,
    layer_group: str,
    features: list[dict[str, object]],
    domesticated: list[dict[str, object]],
    comparator: list[dict[str, object]],
) -> None:
    target = comparator if layer_group == "animal-comparator-evidence" else domesticated
    target.extend(features)
