"""Pure selection, grouping, and partitioning for animal atlas assembly."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from ....adna import AdnaLocalitySummary
from ....adna.governance.atlas_candidates.point_inputs import AnimalPointInputs
from ...geography import GeographicScope
from ..atlas_evidence_rows import AnimalAtlasEvidenceRow
from .model import AnimalAtlasBundle

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


def _group_rows_by_species_and_scope(
    rows: Iterable[AnimalAtlasEvidenceRow],
) -> dict[tuple[str, str], list[AnimalAtlasEvidenceRow]]:
    grouped: dict[tuple[str, str], list[AnimalAtlasEvidenceRow]] = {}
    for row in rows:
        grouped.setdefault((row.species_latin_name, row.animal_scope), []).append(row)
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
    progenitor: list[dict[str, object]],
) -> None:
    targets = {
        "animal-domesticated-evidence": domesticated,
        "animal-comparator-evidence": comparator,
        "animal-progenitor-evidence": progenitor,
    }
    try:
        target = targets[layer_group]
    except KeyError as exc:
        raise ValueError(f"unsupported animal layer group: {layer_group}") from exc
    target.extend(features)


def build_tracked_animal_atlas_bundle_from_inputs(
    *,
    data_root: Path,
    output_dir: Path,
    atlas_slug: str,
    point_inputs: AnimalPointInputs,
    geography_scope: GeographicScope | None = None,
) -> AnimalAtlasBundle:
    """Build animal points from caller-held bytes without changing the legacy API."""
    from ....adna.governance.atlas_candidates.point_inputs import (
        use_animal_point_inputs,
    )
    from . import build_tracked_animal_atlas_bundle

    if not isinstance(point_inputs, AnimalPointInputs):
        raise ValueError("animal point capture differs")
    with use_animal_point_inputs(point_inputs, data_root):
        return build_tracked_animal_atlas_bundle(
            data_root=data_root,
            output_dir=output_dir,
            atlas_slug=atlas_slug,
            geography_scope=geography_scope,
        )
