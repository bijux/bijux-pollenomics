"""Indexed chronology comparisons retain exhaustive closed-interval semantics."""

from __future__ import annotations

from unittest.mock import patch

from bijux_pollenomics.core.temporal_semantics import BpInterval
from bijux_pollenomics.evidence.scientific_review.chronology import (
    _build_chronology_overlaps,
    _LayerIntervals,
)
from bijux_pollenomics.evidence.scientific_review.temporal import (
    _context_point_interval,
    _locality_overlaps_point,
)

from .support import context_point, locality, species_row


def test_interval_index_matches_exhaustive_scan_with_gaps_and_nested_bounds() -> None:
    points = [
        context_point(younger_bp=start, older_bp=end)
        for start, end in (
            (0, 0),
            (2, 10),
            (3, 4),
            (2, 10),
            (20, 30),
            (None, None),
            (None, 4),
            (4, None),
            (8, 2),
            (-1, 3),
        )
    ]
    index = _LayerIntervals.from_points(points)
    for start in range(35):
        for end in range(start, 35):
            query = locality(younger_bp=start, older_bp=end)
            assert index.overlaps(BpInterval(start, end)) == any(
                _locality_overlaps_point(query, point) for point in points
            )
    assert not _LayerIntervals.from_points([]).overlaps(BpInterval(0, 0))


def test_layer_intervals_are_validated_once_across_species_and_localities() -> None:
    points = (
        context_point(younger_bp=100, older_bp=200),
        context_point(younger_bp=None, older_bp=None),
        context_point(layer_key="undated", younger_bp=None, older_bp=10),
    )
    humans = (
        locality(younger_bp=0, older_bp=100),
        locality(younger_bp=201, older_bp=300),
        locality(younger_bp=None, older_bp=None),
    )
    animals = (
        locality(species="Ovis aries", younger_bp=200, older_bp=200),
        locality(species="Ovis aries", younger_bp=0, older_bp=0),
        locality(species="Ovis aries", younger_bp=300, older_bp=200),
    )
    with patch(
        "bijux_pollenomics.evidence.scientific_review.chronology._context_point_interval",
        wraps=_context_point_interval,
    ) as validate:
        rows = _build_chronology_overlaps(
            direct_localities=humans,
            animal_localities=animals,
            context_points=points,
            species_rows=(species_row(), species_row(species="Bos taurus")),
        )
    assert validate.call_count == len(points)
    for row in rows:
        if row.species_latin_name == "Bos taurus":
            assert row.overlap_status == "not_comparable_project_level_only"
            assert row.noncomparable_records == 2
        else:
            expected = (
                (1, 1, 1) if row.context_layer_key == "test-context" else (0, 0, 3)
            )
            assert (
                row.overlapping_direct_localities,
                row.non_overlapping_direct_localities,
                row.noncomparable_records,
            ) == expected
