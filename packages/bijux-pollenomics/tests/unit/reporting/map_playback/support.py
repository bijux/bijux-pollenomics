"""Scientifically explicit playback contract fixtures."""

from __future__ import annotations

from copy import deepcopy

from bijux_pollenomics.reporting.modeled_context.contracts import (
    PANGAEA_WINDOWS_PRESENT_TO_OLDEST,
)
from bijux_pollenomics.reporting.modeled_context.metric_families import METRIC_FAMILIES

NORDIC_COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")


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
                "schema_version": "neotoma-source-chronology-facets.v2",
                "node_level": "source_sample_presence",
                "node_count": 9_988,
                "observation_denominator": 215_903,
                "time_min_bp": 0,
                "time_max_bp": 22_911,
            },
        },
        {
            **common,
            "node_level": "source_ecological_code",
            "facet_metadata": {
                "schema_version": "neotoma-source-chronology-facets.v2",
                "node_level": "source_ecological_code",
                "source_ecological_codes": [
                    {
                        "value": "AQVP",
                        "label": "Aquatic Vascular Plants",
                        "node_count": 4_991,
                        "observation_denominator": 9_666,
                        "time_min_bp": 0,
                        "time_max_bp": 19_190,
                    },
                    {
                        "value": "TRSH",
                        "label": "Trees and Shrubs",
                        "node_count": 9_978,
                        "observation_denominator": 114_225,
                        "time_min_bp": 0,
                        "time_max_bp": 22_911,
                    },
                    {
                        "value": "UPHE",
                        "label": "Upland Herbs",
                        "node_count": 9_928,
                        "observation_denominator": 91_739,
                        "time_min_bp": 0,
                        "time_max_bp": 22_911,
                    },
                ],
            },
        },
        {
            **common,
            "node_level": "source_taxon",
            "facet_metadata": {
                "schema_version": "neotoma-source-chronology-facets.v2",
                "node_level": "source_taxon",
                "source_taxa": taxa,
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
