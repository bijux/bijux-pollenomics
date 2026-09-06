"""Scientifically explicit playback contract fixtures."""

from __future__ import annotations

from copy import deepcopy

from bijux_pollenomics.reporting.modeled_context.contracts import (
    PANGAEA_WINDOWS_PRESENT_TO_OLDEST,
)
from bijux_pollenomics.reporting.modeled_context.metric_families import METRIC_FAMILIES

NORDIC_COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")


def _time_density(
    node_count: int,
    observation_denominator: int,
    time_min_bp: int,
    time_max_bp: int,
) -> dict[str, object]:
    span = time_max_bp - time_min_bp
    if span == 0:
        bins = [
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


def source_layers() -> list[dict[str, object]]:
    """Return the current four-story spans and 972 exact source identities."""
    taxa = [
        {
            "value": f"source:neotoma:taxon:{index}",
            "source_taxon_id": str(index),
            "label": f"Exact taxon {index:04d}",
            "node_count": 1,
            "observation_denominator": index + 1,
            "time_min_bp": 0,
            "time_max_bp": index + 100,
            "time_density": _time_density(1, index + 1, 0, index + 100),
        }
        for index in range(1, 973)
    ]
    common = {
        "semantic_role": "source_chronology_context",
        "propagation_status": "refused",
        "edge_count": 0,
        "temporal_direction": "oldest_to_present",
        "interval_semantics": "[younger_bp, older_bp]",
    }
    return [
        {
            **common,
            "node_level": "source_sample_presence",
            "facet_metadata": {
                "schema_version": "neotoma-source-chronology-facets.v3",
                "node_level": "source_sample_presence",
                "node_count": 9_988,
                "observation_denominator": 215_903,
                "time_min_bp": 0,
                "time_max_bp": 22_911,
                "time_density": _time_density(9_988, 215_903, 0, 22_911),
            },
        },
        {
            **common,
            "node_level": "source_ecological_code",
            "facet_metadata": {
                "schema_version": "neotoma-source-chronology-facets.v3",
                "node_level": "source_ecological_code",
                "source_ecological_codes": [
                    {
                        "value": "AQVP",
                        "label": "Aquatic Vascular Plants",
                        "node_count": 4_991,
                        "observation_denominator": 9_666,
                        "time_min_bp": 0,
                        "time_max_bp": 19_190,
                        "time_density": _time_density(4_991, 9_666, 0, 19_190),
                    },
                    {
                        "value": "TRSH",
                        "label": "Trees and Shrubs",
                        "node_count": 9_978,
                        "observation_denominator": 114_225,
                        "time_min_bp": 0,
                        "time_max_bp": 22_911,
                        "time_density": _time_density(9_978, 114_225, 0, 22_911),
                    },
                    {
                        "value": "UPHE",
                        "label": "Upland Herbs",
                        "node_count": 9_928,
                        "observation_denominator": 91_739,
                        "time_min_bp": 0,
                        "time_max_bp": 22_911,
                        "time_density": _time_density(9_928, 91_739, 0, 22_911),
                    },
                ],
                "node_count": 24_997,
                "observation_denominator": 215_903,
                "time_min_bp": 0,
                "time_max_bp": 22_911,
                "time_density": _time_density(24_997, 215_903, 0, 22_911),
            },
        },
        {
            **common,
            "node_level": "source_taxon",
            "facet_metadata": {
                "schema_version": "neotoma-source-chronology-facets.v3",
                "node_level": "source_taxon",
                "source_taxa": taxa,
                "node_count": 972,
                "observation_denominator": sum(range(2, 974)),
                "time_min_bp": 0,
                "time_max_bp": 1_072,
                "time_density": _time_density(972, sum(range(2, 974)), 0, 1_072),
            },
        },
    ]


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
