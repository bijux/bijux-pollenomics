"""Bound the author-pollen development candidate set and site folds."""

from bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial.development_search import (
    _candidates,
    _folds,
    _quantile,
)
from bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial.source import (
    SiteGeometry,
)


def test_search_declares_three_baselines_and_nine_rbf_configurations() -> None:
    candidates = _candidates()

    assert len(candidates) == 12
    assert [candidate["candidate_id"] for candidate in candidates[:3]] == [
        "training_mean",
        "nearest_site",
        "inverse_distance_squared",
    ]
    assert len({candidate["candidate_id"] for candidate in candidates}) == 12
    assert all(
        candidate["model"] == "clr_wgs84_rbf_ridge" for candidate in candidates[3:]
    )


def test_folds_keep_each_site_whole_and_balance_each_grid() -> None:
    sites = tuple(
        SiteGeometry(
            f"site-{grid}-{index}",
            grid,
            float(index),
            50.0,
            500.0,
            f"{grid}-{index}.csv",
        )
        for grid, size in (("512", 9), ("562", 8))
        for index in range(size)
    )

    folds = _folds(sites)
    held_out = [site for _, group in folds for site in group]

    assert len(folds) == 3
    assert sorted(site.site_id for site in held_out) == sorted(
        site.site_id for site in sites
    )
    assert len({site.site_id for site in held_out}) == len(sites)
    assert all(group for _, group in folds)


def test_distance_quantile_interpolates_training_only_values() -> None:
    assert _quantile([10.0, 20.0, 40.0], 0.25) == 15.0
    assert _quantile([10.0, 20.0, 40.0], 0.50) == 20.0
    assert _quantile([10.0, 20.0, 40.0], 0.75) == 30.0
