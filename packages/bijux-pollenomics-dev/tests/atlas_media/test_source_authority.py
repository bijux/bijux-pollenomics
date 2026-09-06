"""Falsification tests for static-atlas source chronology authority."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics_dev.ci.atlas_media.source_authority import (
    load_source_chronology_authority,
)


def test_published_nordic_source_totals_are_derived_from_static_assets() -> None:
    repository_root = Path(__file__).resolve().parents[4]
    authority = load_source_chronology_authority(
        repository_root,
        repository_root / "docs/report/regions/nordic/nordic_map_assets.json",
    )

    assert {
        selector: (
            authority.require(kind, selector).node_count,
            authority.require(kind, selector).observation_denominator,
        )
        for kind, selector in (
            ("source_sample_presence", "all"),
            ("source_ecological_code", "TRSH"),
            ("source_ecological_code", "UPHE"),
            ("source_ecological_code", "AQVP"),
            ("source_taxon", "source:neotoma:taxon:967"),
        )
    } == {
        "all": (9988, 215903),
        "TRSH": (9978, 114225),
        "UPHE": (9928, 91739),
        "AQVP": (4991, 9666),
        "source:neotoma:taxon:967": (469, 469),
    }
    assert len(authority.asset_sha256) == 124
    assert len(authority.digest) == 64
