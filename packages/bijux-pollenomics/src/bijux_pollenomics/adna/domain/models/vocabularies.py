"""Controlled vocabularies for aDNA scientific domain records."""

from __future__ import annotations

ADNA_COORDINATE_CONFIDENCE = (
    "exact",
    "approximate",
    "inferred",
    "withheld",
    "unknown",
)
ADNA_CHRONOLOGY_EVIDENCE_CLASSES = (
    "direct_radiocarbon_date",
    "modeled_sample_date",
    "archaeological_context_date",
    "broad_period_label",
    "historical_or_recent_date",
    "unresolved",
)
ADNA_CHRONOLOGY_PRECISION_POSTURES = (
    "sample_precise_point",
    "sample_precise_interval",
    "sample_approximate_or_modeled",
    "contextual_interval",
    "broad_period_only",
    "unresolved",
)
ADNA_COORDINATE_PROVENANCE_CLASSES = (
    "direct_published_coordinates",
    "supplementary_table_coordinates",
    "archive_coordinates",
    "named_site_geocoding",
    "region_centroid_fallback",
    "unresolved_location_state",
)
ADNA_DATING_BASES = (
    "bp_mean_and_stddev",
    "bp_window",
    "archaeological_period",
    "historical_attribution",
    "unknown",
)
ADNA_MAPPING_POSTURES = (
    "mappable_point",
    "refused_region_only",
    "refused_unresolved_location",
)
