"""Scientifically explicit playback contract fixtures."""

from __future__ import annotations

from copy import deepcopy
from typing import cast

from bijux_pollenomics.reporting.modeled_context.contracts import (
    PANGAEA_WINDOWS_PRESENT_TO_OLDEST,
)
from bijux_pollenomics.reporting.modeled_context.metric_families import METRIC_FAMILIES
from bijux_pollenomics.reporting.source_chronology.facet_accountability import (
    PRESET_ACCOUNTABILITY_SCHEMA_VERSION,
)
from bijux_pollenomics.reporting.source_chronology.source_label_presets import (
    MEMBERSHIP_SEMANTICS,
    build_neotoma_source_label_preset_catalog,
)

NORDIC_COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")
SOURCE_SNAPSHOT_ID = "sha256:" + "a" * 64
BUILD_ID = "sha256:" + "b" * 64


def _time_density(
    node_count: int,
    observation_denominator: int,
    time_min_bp: int,
    time_max_bp: int,
) -> dict[str, object]:
    span = time_max_bp - time_min_bp
    if span == 0:
        bins: list[dict[str, object]] = [
            {
                "ordinal": 0,
                "younger_bp": time_min_bp,
                "older_bp": time_max_bp,
                "node_count": node_count,
                "observation_denominator": observation_denominator,
            }
        ]
    else:
        bins = [
            {
                "ordinal": ordinal,
                "younger_bp": time_min_bp + ((11 - ordinal) * span / 12),
                "older_bp": time_min_bp + ((12 - ordinal) * span / 12),
                "node_count": node_count,
                "observation_denominator": observation_denominator,
            }
            for ordinal in range(12)
        ]
    return {
        "schema_version": "source-chronology-time-density.v1",
        "temporal_direction": "oldest_to_present",
        "interval_semantics": "[younger_bp, older_bp]",
        "bin_admission": "closed_interval_overlap",
        "bins_are_additive": False,
        "node_count": node_count,
        "observation_denominator": observation_denominator,
        "time_min_bp": time_min_bp,
        "time_max_bp": time_max_bp,
        "bins": bins,
    }


def _accountability(
    node_count: int,
    observation_denominator: int,
    time_min_bp: int | None,
    time_max_bp: int | None,
    *,
    site_count: int,
) -> dict[str, object]:
    countries = []
    for country_code, country_name in (
        ("SE", "Sweden"),
        ("DK", "Denmark"),
        ("NO", "Norway"),
        ("FI", "Finland"),
    ):
        populated = country_code == "SE" and node_count > 0
        countries.append(
            {
                "country_code": country_code,
                "value": country_name,
                "site_count_semantics": "unique_site_union",
                "site_count": site_count if populated else 0,
                "node_count": node_count if populated else 0,
                "observation_denominator": (
                    observation_denominator if populated else 0
                ),
                "time_min_bp": time_min_bp if populated else None,
                "time_max_bp": time_max_bp if populated else None,
            }
        )
    density = (
        {
            "schema_version": "source-chronology-time-density.v1",
            "temporal_direction": "oldest_to_present",
            "interval_semantics": "[younger_bp, older_bp]",
            "bin_admission": "closed_interval_overlap",
            "bins_are_additive": False,
            "node_count": 0,
            "observation_denominator": 0,
            "time_min_bp": None,
            "time_max_bp": None,
            "bins": [],
        }
        if node_count == 0
        else _time_density(
            node_count,
            observation_denominator,
            time_min_bp if time_min_bp is not None else 0,
            time_max_bp if time_max_bp is not None else 0,
        )
    )
    return {
        "site_count_semantics": "unique_site_union",
        "site_count": site_count,
        "node_count": node_count,
        "observation_denominator": observation_denominator,
        "time_min_bp": time_min_bp,
        "time_max_bp": time_max_bp,
        "country_counts": countries,
        "time_density": density,
    }


def _source_label_presets(
    taxa: list[dict[str, object]],
) -> tuple[dict[str, object], dict[str, object]]:
    catalog = build_neotoma_source_label_preset_catalog(
        source_snapshot_id=SOURCE_SNAPSHOT_ID,
        build_id=BUILD_ID,
    )
    taxa_by_id = {
        int(cast(str, row["source_taxon_id"])): row for row in taxa
    }

    def aggregate(member_ids: list[int]) -> dict[str, object]:
        rows = [taxa_by_id[taxon_id] for taxon_id in member_ids if taxon_id in taxa_by_id]
        populated = [row for row in rows if cast(int, row["node_count"]) > 0]
        return _accountability(
            sum(cast(int, row["node_count"]) for row in rows),
            sum(cast(int, row["observation_denominator"]) for row in rows),
            min((cast(int, row["time_min_bp"]) for row in populated), default=None),
            max((cast(int, row["time_max_bp"]) for row in populated), default=None),
            site_count=len(rows),
        )

    definitions = catalog["presets"]
    assert isinstance(definitions, list)
    presets = [
        {
            **definition,
            **aggregate(list(definition["member_taxon_ids"])),
        }
        for definition in definitions
    ]
    source_taxa = catalog["source_taxa"]
    assert isinstance(source_taxa, list)
    union_ids = [int(cast(str, row["source_taxon_id"])) for row in source_taxa]
    accountability = {
        "schema_version": PRESET_ACCOUNTABILITY_SCHEMA_VERSION,
        "catalog_content_sha256": catalog["content_sha256"],
        "membership_semantics": MEMBERSHIP_SEMANTICS,
        "accepted_classification": False,
        "aggregation_is_abundance": False,
        "propagation_allowed": False,
        "source_taxon_count": catalog["source_taxon_count"],
        "preset_count": catalog["preset_count"],
        "membership_count": catalog["membership_count"],
        "presets": presets,
        "union": {
            "key": "all-governed-source-labels",
            "label": "All governed crop and cereal source labels",
            "membership_semantics": MEMBERSHIP_SEMANTICS,
            "accepted_classification": False,
            "aggregation_is_abundance": False,
            "propagation_allowed": False,
            "member_taxon_count": len(union_ids),
            "member_taxon_ids": union_ids,
            **aggregate(union_ids),
        },
    }
    return catalog, accountability


def source_layers() -> list[dict[str, object]]:
    """Return the current four-story spans and 972 exact source identities."""
    catalog = build_neotoma_source_label_preset_catalog(
        source_snapshot_id=SOURCE_SNAPSHOT_ID,
        build_id=BUILD_ID,
    )
    source_taxa = catalog["source_taxa"]
    assert isinstance(source_taxa, list)
    source_names = {
        int(cast(str, row["source_taxon_id"])): str(row["source_reported_name"])
        for row in cast(list[dict[str, object]], source_taxa)
    }
    additional_taxon_ids = [
        int(identifier)
        for identifier in source_names
        if identifier > 972
    ]
    replaced_ids = set(range(900, 900 + len(additional_taxon_ids)))
    taxon_ids = [
        identifier for identifier in range(1, 973) if identifier not in replaced_ids
    ] + additional_taxon_ids
    taxa = [
        {
            "value": f"source:neotoma:taxon:{taxon_id}",
            "source_taxon_id": str(taxon_id),
            "label": source_names.get(taxon_id, f"Exact taxon {taxon_id:04d}"),
            **_accountability(
                1,
                ordinal + 1,
                0,
                ordinal + 100,
                site_count=1,
            ),
        }
        for ordinal, taxon_id in enumerate(taxon_ids, start=1)
    ]
    preset_catalog, preset_accountability = _source_label_presets(taxa)
    common = {
        "semantic_role": "source_chronology_context",
        "propagation_status": "refused",
        "edge_count": 0,
        "temporal_direction": "oldest_to_present",
        "interval_semantics": "[younger_bp, older_bp]",
        "source_snapshot_id": SOURCE_SNAPSHOT_ID,
        "build_id": BUILD_ID,
    }
    layers = [
        {
            **common,
            "node_level": "source_sample_presence",
            "count": 1,
            "facet_metadata": {
                "schema_version": "neotoma-source-chronology-facets.v4",
                "node_level": "source_sample_presence",
                **_accountability(
                    1, 1, 0, 22_911, site_count=1
                ),
                "source_unit_counts": [
                    {
                        "value": "source units",
                        "node_count": 1,
                        "observation_denominator": 1,
                    }
                ],
                "source_ecological_codes": [],
                "source_taxa": [],
            },
        },
        {
            **common,
            "node_level": "source_ecological_code",
            "count": 5,
            "facet_metadata": {
                "schema_version": "neotoma-source-chronology-facets.v4",
                "node_level": "source_ecological_code",
                "source_ecological_codes": [
                    {
                        "value": "AQVP",
                        "label": "Aquatic Vascular Plants",
                        "source_code": "AQVP",
                        "feature_key": "source:neotoma:ecological-code:AQVP",
                        **_accountability(
                            1, 1, 0, 19_190, site_count=1
                        ),
                    },
                    {
                        "value": "SEED",
                        "label": "Seeds and Spores",
                        "source_code": "SEED",
                        "feature_key": "source:neotoma:ecological-code:SEED",
                        **_accountability(1, 1, 31, 10_282, site_count=1),
                    },
                    {
                        "value": "TRSH",
                        "label": "Trees and Shrubs",
                        "source_code": "TRSH",
                        "feature_key": "source:neotoma:ecological-code:TRSH",
                        **_accountability(
                            1, 1, 0, 22_911, site_count=1
                        ),
                    },
                    {
                        "value": "UNID",
                        "label": "Unidentified",
                        "source_code": "UNID",
                        "feature_key": "source:neotoma:ecological-code:UNID",
                        **_accountability(1, 1, 19, 9_815, site_count=1),
                    },
                    {
                        "value": "UPHE",
                        "label": "Upland Herbs",
                        "source_code": "UPHE",
                        "feature_key": "source:neotoma:ecological-code:UPHE",
                        **_accountability(
                            1, 1, 0, 22_911, site_count=1
                        ),
                    },
                ],
                "source_taxa": [],
                **_accountability(
                    5, 5, 0, 22_911, site_count=5
                ),
                "source_unit_counts": [
                    {
                        "value": "source units",
                        "node_count": 5,
                        "observation_denominator": 5,
                    }
                ],
            },
        },
        {
            **common,
            "node_level": "source_taxon",
            "count": 972,
            "facet_metadata": {
                "schema_version": "neotoma-source-chronology-facets.v4",
                "node_level": "source_taxon",
                "source_taxa": taxa,
                "source_ecological_codes": [],
                **_accountability(
                    972,
                    sum(range(2, 974)),
                    0,
                    1_072,
                    site_count=972,
                ),
                "source_unit_counts": [
                    {
                        "value": "source units",
                        "node_count": 972,
                        "observation_denominator": sum(range(2, 974)),
                    }
                ],
                "source_label_preset_catalog": preset_catalog,
                "source_label_preset_accountability": preset_accountability,
            },
        },
    ]
    sample = layers[0]
    sample["features"] = [
        _source_feature(
            node_level="source_sample_presence",
            node_id="sample-node",
            record_id="neotoma:site:sample",
            observation_denominator=1,
            younger_bp=0,
            older_bp=22_911,
        )
    ]
    code_layer = layers[1]
    code_facets = cast(
        dict[str, object], code_layer["facet_metadata"]
    )["source_ecological_codes"]
    assert isinstance(code_facets, list)
    code_layer["features"] = [
        _source_feature(
            node_level="source_ecological_code",
            node_id=f"code-node-{row['source_code']}",
            record_id=f"neotoma:site:code-{row['source_code']}",
            observation_denominator=1,
            younger_bp=cast(int, row["time_min_bp"]),
            older_bp=cast(int, row["time_max_bp"]),
            source_code=cast(str, row["source_code"]),
            feature_key=cast(str, row["feature_key"]),
        )
        for row in cast(list[dict[str, object]], code_facets)
    ]
    taxon_layer = layers[2]
    taxon_layer["features"] = [
        _source_feature(
            node_level="source_taxon",
            node_id=f"taxon-node-{row['source_taxon_id']}",
            record_id=f"neotoma:site:taxon-{row['source_taxon_id']}",
            observation_denominator=cast(int, row["observation_denominator"]),
            younger_bp=cast(int, row["time_min_bp"]),
            older_bp=cast(int, row["time_max_bp"]),
            source_taxon_id=int(cast(str, row["source_taxon_id"])),
            source_reported_name=cast(str, row["label"]),
            feature_key=cast(str, row["value"]),
        )
        for row in taxa
    ]
    return layers


def _source_feature(
    *,
    node_level: str,
    node_id: str,
    record_id: str,
    observation_denominator: int,
    younger_bp: int,
    older_bp: int,
    source_code: str | None = None,
    source_taxon_id: int | None = None,
    source_reported_name: str | None = None,
    feature_key: str = "source:neotoma:sample",
) -> dict[str, object]:
    return {
        "node_level": node_level,
        "node_id": node_id,
        "record_id": record_id,
        "country": "Sweden",
        "semantic_role": "source_chronology_context",
        "source_snapshot_id": SOURCE_SNAPSHOT_ID,
        "build_id": BUILD_ID,
        "propagation_eligible": False,
        "observation_denominator": observation_denominator,
        "time_start_bp": younger_bp,
        "time_end_bp": older_bp,
        "source_unit": "source units",
        "source_ecological_code": source_code,
        "source_taxon_id": source_taxon_id,
        "source_reported_name": source_reported_name,
        "feature_key": feature_key,
    }


def mutable_source_layers() -> list[dict[str, object]]:
    """Return an independent copy for fail-closed mutation tests."""
    return deepcopy(source_layers())


def modeled_manifest() -> dict[str, object]:
    """Return the exact 25-window, 47-metric PANGAEA contract surface."""
    windows = [
        {
            "label": label,
            "time_start_bp": younger,
            "time_end_bp": older,
            "feature_count": 75,
            "no_pollen_data_count": 12,
        }
        for label, younger, older in reversed(PANGAEA_WINDOWS_PRESENT_TO_OLDEST)
    ]
    return {
        "schema_version": "modeled-context-manifest.v3",
        "status": "available",
        "evidence_role": "context_only",
        "propagation_use_allowed": False,
        "interpolation_allowed": False,
        "dataset_id": "937075",
        "metric_count": 47,
        "metric_families": [family.as_dict() for family in METRIC_FAMILIES],
        "windows_oldest_to_present": windows,
    }
