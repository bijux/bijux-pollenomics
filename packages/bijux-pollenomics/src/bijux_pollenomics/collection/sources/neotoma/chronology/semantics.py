from __future__ import annotations

from collections.abc import Mapping, Sequence

from bijux_pollenomics.core.bp_time import (
    build_bp_interval_label,
    midpoint_bp_year,
)
from bijux_pollenomics.core.temporal_semantics import build_temporal_semantics
from bijux_pollenomics.core.text import clean_optional_text

from .site_spans import neotoma_age_range_units_supported


def _build_neotoma_temporal_semantics(
    age_ranges: Sequence[Mapping[str, object]],
    *,
    time_interval: tuple[int, int] | None,
    time_label: str,
) -> dict[str, object]:
    supported_ranges = [
        age_range
        for age_range in age_ranges
        if neotoma_age_range_units_supported(
            clean_optional_text(age_range.get("units"))
        )
    ]
    supported_units = tuple(
        clean_optional_text(age_range.get("units"))
        for age_range in supported_ranges
        if clean_optional_text(age_range.get("units"))
    )
    all_units = tuple(
        clean_optional_text(age_range.get("units"))
        for age_range in age_ranges
        if clean_optional_text(age_range.get("units"))
    )
    uncertainty_notes: tuple[str, ...] = ()
    if len(supported_units) > 1:
        uncertainty_notes = (
            "Multiple BP age-range conventions contribute to this site span.",
        )
    if time_interval is not None and len(supported_ranges) > 1:
        comparability_posture = "numeric_interval_with_caveat"
        evidence_class = "neotoma_aggregated_bp_ranges"
        precision_posture = "site_interval_with_uncertainty"
        comparison_note = (
            "Neotoma coverage merges more than one BP age-range convention for this "
            "site, so the interval remains comparable but should be treated as a "
            "site-level summary span."
        )
    elif time_interval is not None:
        comparability_posture = "numeric_interval"
        evidence_class = "neotoma_bp_range"
        precision_posture = "site_interval"
        comparison_note = (
            "Neotoma publishes BP age coverage here, but the interval remains a "
            "site-level pollen context span rather than a sample-owned event date."
        )
    elif all_units:
        comparability_posture = "contextual_label_only"
        evidence_class = "neotoma_non_bp_age_range"
        precision_posture = "non_bp_age_units_only"
        comparison_note = (
            "Neotoma age coverage is present, but not in a BP form that this "
            "repository compares numerically."
        )
    else:
        comparability_posture = "unresolved"
        evidence_class = "unresolved"
        precision_posture = "unresolved"
        comparison_note = (
            "Neotoma did not publish enough age-range detail here to support "
            "temporal comparison."
        )
    summary_label = time_label.strip() or build_bp_interval_label(
        time_interval[0] if time_interval is not None else None,
        time_interval[1] if time_interval is not None else None,
    )
    if not summary_label:
        summary_label = "; ".join(all_units)
    return build_temporal_semantics(
        source_family="neotoma",
        evidence_class=evidence_class,
        precision_posture=precision_posture,
        comparability_posture=comparability_posture,
        time_start_bp=time_interval[0] if time_interval is not None else None,
        time_end_bp=time_interval[1] if time_interval is not None else None,
        time_mean_bp=midpoint_bp_year(time_interval[0], time_interval[1])
        if time_interval is not None
        else None,
        summary_label=summary_label,
        comparison_note=comparison_note,
        provenance_locator="site_age_ranges",
        original_labels=all_units,
        normalized_labels=supported_units,
        uncertainty_notes=uncertainty_notes,
    ).as_dict()
