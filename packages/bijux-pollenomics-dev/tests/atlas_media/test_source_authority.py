"""Falsification tests for static-atlas source chronology authority."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.reporting.source_chronology.source_label_presets import (
    MEMBERSHIP_SEMANTICS,
    NEOTOMA_SOURCE_LABEL_PRESETS,
    NEOTOMA_SOURCE_LABEL_TAXA,
    build_neotoma_source_label_preset_catalog,
)
from bijux_pollenomics_dev.ci.atlas_media import AtlasMediaError
from bijux_pollenomics_dev.ci.atlas_media.source_authority import (
    SourceChronologyAuthority,
    SourceFacetAuthority,
    bind_source_label_preset_authority,
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
            ("source_taxon", "source:neotoma:taxon:416"),
            ("source_taxon", "source:neotoma:taxon:427"),
            ("source_taxon", "source:neotoma:taxon:1947"),
            ("source_taxon", "source:neotoma:taxon:3924"),
            ("source_taxon", "source:neotoma:taxon:967"),
            ("source_taxon", "source:neotoma:taxon:3926"),
            ("source_taxon", "source:neotoma:taxon:488"),
            ("source_taxon", "source:neotoma:taxon:969"),
        )
    } == {
        "all": (9988, 215903),
        "TRSH": (9978, 114225),
        "UPHE": (9928, 91739),
        "AQVP": (4991, 9666),
        "source:neotoma:taxon:416": (28, 28),
        "source:neotoma:taxon:427": (257, 257),
        "source:neotoma:taxon:1947": (375, 375),
        "source:neotoma:taxon:3924": (2, 2),
        "source:neotoma:taxon:967": (469, 469),
        "source:neotoma:taxon:3926": (191, 191),
        "source:neotoma:taxon:488": (45, 45),
        "source:neotoma:taxon:969": (153, 153),
    }
    assert len(authority.asset_sha256) == 124
    assert len(authority.digest) == 64
    assert {
        taxon.source_taxon_id: (
            facet.site_count,
            facet.node_count,
            facet.observation_denominator,
        )
        for taxon in NEOTOMA_SOURCE_LABEL_TAXA
        for facet in (
            authority.require(
                "source_taxon",
                f"source:neotoma:taxon:{taxon.source_taxon_id}",
            ),
        )
    } == {
        414: (8, 51, 51),
        415: (13, 34, 34),
        416: (5, 28, 28),
        427: (21, 257, 257),
        488: (3, 45, 45),
        497: (14, 171, 171),
        967: (37, 469, 469),
        969: (13, 153, 153),
        1947: (30, 375, 375),
        2941: (1, 16, 16),
        3705: (42, 425, 425),
        3915: (5, 7, 7),
        3917: (9, 14, 14),
        3918: (1, 1, 1),
        3923: (8, 87, 87),
        3924: (1, 2, 2),
        3926: (26, 191, 191),
        31581: (1, 2, 2),
        33008: (7, 58, 58),
        48827: (1, 1, 1),
        49802: (1, 3, 3),
    }
    assert {
        preset.key: (
            len(
                {
                    site_id
                    for taxon_id in preset.member_taxon_ids
                    for site_id, _younger, _older in authority.require(
                        "source_taxon",
                        f"source:neotoma:taxon:{taxon_id}",
                    ).site_intervals
                }
            ),
            sum(
                authority.require(
                    "source_taxon", f"source:neotoma:taxon:{taxon_id}"
                ).node_count
                for taxon_id in preset.member_taxon_ids
            ),
            sum(
                authority.require(
                    "source_taxon", f"source:neotoma:taxon:{taxon_id}"
                ).observation_denominator
                for taxon_id in preset.member_taxon_ids
            ),
        )
        for preset in NEOTOMA_SOURCE_LABEL_PRESETS
    } == {
        "avena": (36, 110, 110),
        "hordeum": (57, 572, 572),
        "triticum": (49, 375, 375),
        "secale": (66, 707, 707),
        "cerealia": (56, 676, 676),
    }
    secale = authority.require("source_taxon", "source:neotoma:taxon:967")
    assert secale.label == "Secale"
    assert secale.time_min_bp == 2
    assert secale.time_max_bp == 4461


def _preset_contract() -> tuple[
    SourceChronologyAuthority, dict[str, object], dict[str, object]
]:
    facets = {
        ("source_taxon", f"source:neotoma:taxon:{taxon.source_taxon_id}"):
        SourceFacetAuthority(
            selector_kind="source_taxon",
            selector_value=f"source:neotoma:taxon:{taxon.source_taxon_id}",
            label=taxon.source_reported_name,
            site_count=1,
            node_count=1,
            observation_denominator=1,
            time_min_bp=taxon.source_taxon_id,
            time_max_bp=taxon.source_taxon_id + 1,
            intervals=((taxon.source_taxon_id, taxon.source_taxon_id + 1),),
            site_intervals=(
                (
                    f"site-{taxon.source_taxon_id}",
                    taxon.source_taxon_id,
                    taxon.source_taxon_id + 1,
                ),
            ),
            observation_intervals=(
                (1, taxon.source_taxon_id, taxon.source_taxon_id + 1),
            ),
        )
        for taxon in NEOTOMA_SOURCE_LABEL_TAXA
    }
    authority = SourceChronologyAuthority(
        build_id="atlas-" + "d" * 64,
        digest="1" * 64,
        asset_sha256=("2" * 64,),
        facets=facets,
    )
    catalog = build_neotoma_source_label_preset_catalog(
        source_snapshot_id="sha256:" + "a" * 64,
        build_id="sha256:" + "b" * 64,
    )
    rows = []
    for preset in NEOTOMA_SOURCE_LABEL_PRESETS:
        members = [
            facets[("source_taxon", f"source:neotoma:taxon:{taxon_id}")]
            for taxon_id in preset.member_taxon_ids
        ]
        rows.append(
            {
                **preset.as_dict(),
                "site_count": len(members),
                "node_count": len(members),
                "observation_denominator": len(members),
                "time_min_bp": min(member.time_min_bp for member in members),
                "time_max_bp": max(member.time_max_bp for member in members),
            }
        )
    accountability = {
        "schema_version": "neotoma-source-label-preset-accountability.v1",
        "catalog_content_sha256": catalog["content_sha256"],
        "membership_semantics": MEMBERSHIP_SEMANTICS,
        "accepted_classification": False,
        "aggregation_is_abundance": False,
        "propagation_allowed": False,
        "source_taxon_count": len(NEOTOMA_SOURCE_LABEL_TAXA),
        "preset_count": len(NEOTOMA_SOURCE_LABEL_PRESETS),
        "membership_count": sum(
            len(preset.member_taxon_ids)
            for preset in NEOTOMA_SOURCE_LABEL_PRESETS
        ),
        "presets": rows,
    }
    return authority, catalog, accountability


def test_source_label_preset_authority_is_recomputed_from_exact_assets() -> None:
    authority, catalog, accountability = _preset_contract()

    bound = bind_source_label_preset_authority(
        authority, catalog=catalog, accountability=accountability
    )
    avena = bound.require("source_label_preset", "avena")

    assert avena.member_taxon_ids == (414, 415, 3915, 3917, 3918, 31581, 48827)
    assert avena.node_count == 7
    assert avena.observation_denominator == 7
    assert avena.source_preset_catalog_sha256 == str(catalog["content_sha256"])[7:]


def test_source_label_preset_authority_rejects_declared_aggregate_drift() -> None:
    authority, catalog, accountability = _preset_contract()
    presets = accountability["presets"]
    assert isinstance(presets, list) and isinstance(presets[0], dict)
    presets[0]["node_count"] = 99

    with pytest.raises(AtlasMediaError, match="governed atlas assets"):
        bind_source_label_preset_authority(
            authority, catalog=catalog, accountability=accountability
        )
