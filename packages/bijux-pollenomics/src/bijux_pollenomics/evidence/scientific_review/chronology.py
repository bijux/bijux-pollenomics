"""Chronology overlap assessment against contextual evidence layers."""

from __future__ import annotations

from collections import defaultdict

from ...adna import AdnaLocalitySummary
from ...collection.contracts.models import ContextPointRecord
from ..models import AtlasEvidenceSpeciesRow
from .models import ChronologyOverlapRow
from .temporal import (
    _context_point_interval,
    _locality_interval,
    _locality_overlaps_point,
)


def _build_chronology_overlaps(
    *,
    direct_localities: tuple[AdnaLocalitySummary, ...],
    animal_localities: tuple[AdnaLocalitySummary, ...],
    context_points: tuple[ContextPointRecord, ...],
    species_rows: tuple[AtlasEvidenceSpeciesRow, ...],
) -> tuple[ChronologyOverlapRow, ...]:
    rows: list[ChronologyOverlapRow] = []
    grouped_context: dict[str, list[ContextPointRecord]] = defaultdict(list)
    for point in context_points:
        grouped_context[point.layer_key].append(point)
    for layer_key, points in sorted(grouped_context.items()):
        overlapping = 0
        non_overlapping = 0
        noncomparable = 0
        for locality in direct_localities:
            locality_interval = _locality_interval(locality)
            comparable_points = tuple(
                point for point in points if _context_point_interval(point) is not None
            )
            if locality_interval is None or not comparable_points:
                noncomparable += 1
                continue
            if any(
                _locality_overlaps_point(locality, point) for point in comparable_points
            ):
                overlapping += 1
            else:
                non_overlapping += 1
        rows.append(
            ChronologyOverlapRow(
                species_latin_name="Homo sapiens",
                context_layer_key=layer_key,
                overlap_status="locality_level_overlap_available",
                overlapping_direct_localities=overlapping,
                non_overlapping_direct_localities=non_overlapping,
                noncomparable_records=noncomparable,
                rationale="Human locality chronology can be compared directly with time-aware context points.",
            )
        )
    for row in species_rows:
        if row.species_latin_name == "Homo sapiens":
            continue
        species_animal_localities = tuple(
            locality
            for locality in animal_localities
            if locality.species_latin_name == row.species_latin_name
        )
        for layer_key in sorted(grouped_context) or ("no_context_layers",):
            if species_animal_localities and layer_key != "no_context_layers":
                overlapping = 0
                non_overlapping = 0
                noncomparable = 0
                layer_points = grouped_context.get(layer_key, [])
                for locality in species_animal_localities:
                    locality_interval = _locality_interval(locality)
                    comparable_points = tuple(
                        point
                        for point in layer_points
                        if _context_point_interval(point) is not None
                    )
                    if locality_interval is None or not comparable_points:
                        noncomparable += 1
                        continue
                    if any(
                        _locality_overlaps_point(locality, point)
                        for point in layer_points
                    ):
                        overlapping += 1
                    else:
                        non_overlapping += 1
                rows.append(
                    ChronologyOverlapRow(
                        species_latin_name=row.species_latin_name,
                        context_layer_key=layer_key,
                        overlap_status="mapped_locality_overlap_with_caution",
                        overlapping_direct_localities=overlapping,
                        non_overlapping_direct_localities=non_overlapping,
                        noncomparable_records=noncomparable,
                        rationale="Mapped animal locality leads can be compared with context layers, but only with their stated chronology and precision caveats.",
                    )
                )
                continue
            rows.append(
                ChronologyOverlapRow(
                    species_latin_name=row.species_latin_name,
                    context_layer_key=layer_key,
                    overlap_status="not_comparable_project_level_only",
                    overlapping_direct_localities=0,
                    non_overlapping_direct_localities=0,
                    noncomparable_records=max(1, row.curated_project_count),
                    rationale="Non-human chronology is still project-level and cannot be aligned to atlas localities honestly.",
                )
            )
    return tuple(rows)
