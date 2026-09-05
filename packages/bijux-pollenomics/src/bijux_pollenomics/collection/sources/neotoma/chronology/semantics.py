from __future__ import annotations

from collections.abc import Mapping, Sequence

from bijux_pollenomics.core.bp_time import (
    build_bp_interval_label,
    midpoint_bp_year,
)
from bijux_pollenomics.core.temporal_semantics import build_temporal_semantics
from bijux_pollenomics.core.text import clean_optional_text

from .site_spans import (
    neotoma_age_range_system,
    neotoma_selected_age_system,
)


def _build_neotoma_temporal_semantics(
    age_ranges: Sequence[Mapping[str, object]],
    *,
    time_interval: tuple[int, int] | None,
    time_label: str,
) -> dict[str, object]:
    selected_system = neotoma_selected_age_system(age_ranges)
    recognized_systems = tuple(
        sorted(
            {
                system
                for age_range in age_ranges
                if (
                    system := neotoma_age_range_system(
                        clean_optional_text(age_range.get("units"))
                    )
                )
                is not None
            }
        )
    )
    all_units = tuple(
        clean_optional_text(age_range.get("units"))
        for age_range in age_ranges
        if clean_optional_text(age_range.get("units"))
    )
    excluded_systems = tuple(
        system for system in recognized_systems if system != selected_system
    )
    uncertainty_notes: tuple[str, ...] = ()
    if selected_system is not None and excluded_systems:
        uncertainty_notes = (
            "The display interval uses only "
            f"{selected_system}; incompatible source age systems were excluded: "
            f"{', '.join(excluded_systems)}.",
        )
    if time_interval is not None and excluded_systems:
        comparability_posture = "mixed_interval_and_context"
        evidence_class = "neotoma_selected_bp_range"
        precision_posture = "site_interval_with_uncertainty"
        comparison_note = (
            f"Neotoma site coverage uses only {selected_system} for this display "
            "interval. Other source age systems remain contextual and are not "
            "combined or compared."
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
        evidence_class = "neotoma_noncanonical_age_range"
        precision_posture = "source_age_units_only"
        comparison_note = (
            "Neotoma age coverage is present, but no complete, finite, non-negative "
            "calendar-BP site interval can be admitted for numeric comparison."
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
        normalized_labels=recognized_systems,
        uncertainty_notes=uncertainty_notes,
    ).as_dict()
