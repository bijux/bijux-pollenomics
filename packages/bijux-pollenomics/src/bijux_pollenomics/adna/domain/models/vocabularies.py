"""Controlled vocabularies for aDNA scientific domain records."""

from __future__ import annotations

ADNA_COORDINATE_CONFIDENCE = (
    "exact",
    "source_reported_two_decimal_degrees",
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
    "archaeological_context",
    "archaeological_period_assignment",
    "bp_mean_and_stddev",
    "bp_window",
    "archaeological_period",
    "historical_and_archaeological_context",
    "historical_attribution",
    "mixed_radiocarbon_and_archaeological_context",
    "modern_sampling",
    "not_yet_curated",
    "population_history_context",
    "radiocarbon",
    "relative_period",
    "unknown",
)
ADNA_MAPPING_POSTURES = (
    "mappable_point",
    "refused_region_only",
    "refused_unresolved_location",
)
