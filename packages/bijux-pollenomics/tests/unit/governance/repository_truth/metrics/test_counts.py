"""Unit-safe repository-truth count contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.governance.repository_truth.metrics.counts import (
    _build_core_counts,
    _require_surface_count,
    _surface_count,
)
from bijux_pollenomics.governance.repository_truth.metrics.filesystem import (
    _format_metric_map,
)


def test_available_surface_counts_fail_closed() -> None:
    assert _surface_count({"count": 7}, "count", available=True) == 7
    assert _surface_count({}, "count", available=False) is None

    for value in (None, "", "7", -1, False):
        with pytest.raises(ValueError, match="nonnegative integer"):
            _surface_count({"count": value}, "count", available=True)


def test_required_surface_count_fails_closed_when_unavailable() -> None:
    assert _require_surface_count(7, "count") == 7
    with pytest.raises(ValueError, match="Repository truth count is unavailable"):
        _require_surface_count(None, "count")


def test_metric_rendering_names_unavailable_values() -> None:
    assert _format_metric_map({"count": None, "available": False}) == (
        "`count` unavailable, `available` false"
    )


def _write_animal_accounting(
    root: Path,
    *,
    tracked: int = 10,
    mapped: int = 6,
    published: int = 3,
    unresolved: int = 4,
    mappable_coordinates: int = 5,
    refused_coordinates: int = 2,
    coordinate_total: int = 7,
    publication_candidates: int = 3,
    not_materialized: int = 2,
) -> tuple[Path, Path, Path]:
    data_root = root / "data"
    docs_root = root / "docs"
    report_root = docs_root / "report"
    readiness_path = (
        data_root / "adna" / "governance" / "cross_species_map_readiness.json"
    )
    readiness_path.parent.mkdir(parents=True)
    report_root.mkdir(parents=True)
    readiness_path.write_text(
        json.dumps(
            {
                "totals": {
                    "unresolved_sample_count": unresolved,
                    "coordinate_provenance_mappable_count": mappable_coordinates,
                    "refused_coordinate_provenance_count": refused_coordinates,
                    "coordinate_provenance_row_count": coordinate_total,
                    "publication_candidate_count": publication_candidates,
                    "not_materialized_count": not_materialized,
                }
            }
        ),
        encoding="utf-8",
    )
    (report_root / "animal_sample_database_review.json").write_text(
        json.dumps(
            {
                "counts": {
                    "sample_row_count": tracked,
                    "mapped_sample_count": mapped,
                    "published_atlas_point_count": published,
                    "published_country_bundle_count": 4,
                }
            }
        ),
        encoding="utf-8",
    )
    return data_root, docs_root, report_root


def test_animal_accounting_keeps_units_separate_and_reconciled(tmp_path: Path) -> None:
    roots = _write_animal_accounting(tmp_path)

    counts = _build_core_counts(*roots)

    assert counts["animal_tracked_sample_count"] == 10
    assert counts["animal_mapped_sample_count"] == 6
    assert counts["animal_blocked_sample_count"] == 4
    assert counts["animal_unresolved_sample_count"] == 4
    assert counts["animal_coordinate_provenance_count"] == 7
    assert counts["animal_coordinate_mappable_provenance_count"] == 5
    assert counts["animal_coordinate_refused_provenance_count"] == 2
    assert counts["published_atlas_point_count"] == 3


@pytest.mark.parametrize(
    "overrides",
    [
        {"coordinate_total": 8},
        {"not_materialized": 1},
        {"publication_candidates": 4, "not_materialized": 1},
        {"unresolved": 5},
        {"published": 2},
        {"mapped": 11},
    ],
)
def test_animal_accounting_refuses_cross_surface_drift(
    tmp_path: Path,
    overrides: dict[str, int],
) -> None:
    roots = _write_animal_accounting(tmp_path, **overrides)

    with pytest.raises(ValueError, match="Animal"):
        _build_core_counts(*roots)


def test_missing_animal_accounting_remains_unavailable(tmp_path: Path) -> None:
    counts = _build_core_counts(
        tmp_path / "data",
        tmp_path / "docs",
        tmp_path / "docs" / "report",
    )

    assert counts["animal_sample_database_review_available"] is False
    assert counts["animal_map_readiness_available"] is False
    assert counts["animal_tracked_sample_count"] is None
    assert counts["animal_coordinate_provenance_count"] is None
