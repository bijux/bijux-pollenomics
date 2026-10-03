"""Built Nordic SEAD map and source chronology acceptance."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics_dev.source_completion.sead_map_candidate import (
    _built_layers,
    _run_time_filter,
)

REPOSITORY = Path(__file__).resolve().parents[3]


def test_built_sead_context_and_numeric_record_filter() -> None:
    """The real static atlas retains four countries and refuses an interval gap."""
    _, layers, features, edge_count = _built_layers(REPOSITORY)
    sites = features["sead-sites"]
    records = features["sweden-archaeology-site-discovery"]
    assert len(sites) == 2069
    assert len(records) == 8799
    assert {
        country: sum(row["country"] == country for row in sites)
        for country in ("Denmark", "Finland", "Norway", "Sweden")
    } == {
        "Denmark": 59,
        "Finland": 40,
        "Norway": 45,
        "Sweden": 1925,
    }
    assert layers["sead-sites"]["default_enabled"] is False
    assert layers["sead-sites"]["applies_time_filter"] is False
    assert layers["sweden-archaeology-site-discovery"]["applies_time_filter"] is True
    assert edge_count == 0
    behavior = _run_time_filter(REPOSITORY, features)
    assert behavior["gap_record_count"] == 0
    assert behavior["at_82_record_count"] == 2
    assert behavior["zero_site_in_test_window"] is True
    assert behavior["unresolved_site_in_test_window"] is False
