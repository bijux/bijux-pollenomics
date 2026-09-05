"""Site-level temporal semantics for SEAD contextual evidence."""

from __future__ import annotations

from collections.abc import Mapping

from ......core.bp_time import build_bp_interval_label, mean_bp_year_from_interval
from ......core.temporal_semantics import build_temporal_semantics


def build_sead_temporal_semantics(
    row: Mapping[str, object],
    *,
    time_interval: tuple[int, int] | None,
) -> dict[str, object]:
    """Describe the comparability posture of one site-level time summary."""
    original_labels = string_values_from_temporal_rows(
        row.get("relative_period_rows"),
        "relative_age_label",
    )
    normalized_labels = string_values_from_temporal_rows(
        row.get("relative_period_rows"),
        "normalized_period_label",
    )
    uncertainty_notes = collect_uncertainty_notes(row)
    has_period_rows = bool(original_labels)
    if time_interval is not None and has_period_rows:
        comparability_posture = "mixed_interval_and_context"
        comparison_note = (
            "SEAD combines numeric dating ranges with site-level cultural or geologic period labels. "
            "Treat the point as contextual archaeology evidence, not as one directly sample-dated event."
        )
        evidence_class = "sead_dating_range_and_relative_period"
        precision_posture = "site_interval_with_context"
    elif time_interval is not None and uncertainty_notes:
        comparability_posture = "numeric_interval_with_caveat"
        comparison_note = "SEAD publishes one numeric site span here, but the upstream dating rows carry qualifiers or uncertainty notes."
        evidence_class = "sead_dating_range"
        precision_posture = "site_interval_with_uncertainty"
    elif time_interval is not None:
        comparability_posture = "numeric_interval"
        comparison_note = "SEAD publishes one numeric site span here. The interval remains site-level archaeology context rather than one sample-owned date."
        evidence_class = "sead_dating_range"
        precision_posture = "site_interval"
    elif has_period_rows:
        comparability_posture = "contextual_label_only"
        comparison_note = "SEAD publishes period labels without one stable numeric site interval here. Do not compare this row as if it were a sample-owned date."
        evidence_class = "sead_relative_period"
        precision_posture = "relative_period_only"
    else:
        comparability_posture = "unresolved"
        comparison_note = "SEAD did not publish enough dating detail here to support temporal comparison."
        evidence_class = "unresolved"
        precision_posture = "unresolved"
    summary_label = build_bp_interval_label(
        time_interval[0] if time_interval is not None else None,
        time_interval[1] if time_interval is not None else None,
    )
    if original_labels:
        joined_labels = "; ".join(original_labels)
        summary_label = (
            f"{joined_labels} ({summary_label})" if summary_label else joined_labels
        )
    return build_temporal_semantics(
        source_family="sead",
        evidence_class=evidence_class,
        precision_posture=precision_posture,
        comparability_posture=comparability_posture,
        time_start_bp=time_interval[0] if time_interval is not None else None,
        time_end_bp=time_interval[1] if time_interval is not None else None,
        time_mean_bp=mean_bp_year_from_interval(time_interval),
        summary_label=summary_label,
        comparison_note=comparison_note,
        provenance_locator=f"site/{str(row.get('site_id', '')).strip()}",
        original_labels=tuple(original_labels),
        normalized_labels=tuple(normalized_labels),
        uncertainty_notes=tuple(uncertainty_notes),
    ).as_dict()


def string_values_from_temporal_rows(rows: object, key: str) -> list[str]:
    """Collect unique non-empty labels while preserving source order."""
    if not isinstance(rows, list):
        return []
    values: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        text = str(row.get(key, "")).strip()
        if text and text not in values:
            values.append(text)
    return values


def collect_uncertainty_notes(row: Mapping[str, object]) -> list[str]:
    """Collect unique source qualifiers and uncertainty descriptions."""
    notes: list[str] = []
    for key in (
        "relative_period_rows",
        "dating_range_rows",
        "analysis_entity_age_rows",
        "geochronology_rows",
        "dendro_date_rows",
    ):
        rows = row.get(key)
        if not isinstance(rows, list):
            continue
        for item in rows:
            if not isinstance(item, dict):
                continue
            label = str(item.get("uncertainty_label", "")).strip()
            description = str(item.get("uncertainty_description", "")).strip()
            note = ": ".join(part for part in (label, description) if part).strip(": ")
            if note and note not in notes:
                notes.append(note)
            for qualifier_key in ("low_qualifier", "high_qualifier"):
                qualifier = str(item.get(qualifier_key, "")).strip()
                if qualifier and qualifier not in notes:
                    notes.append(qualifier)
    return notes
