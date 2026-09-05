"""Projection of linked SEAD chronology into time-filterable evidence."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from ......core.bp_time import (
    build_bp_interval_label,
    mean_bp_year_from_interval,
    normalize_bp_interval,
)
from ......core.temporal_semantics import build_temporal_semantics
from ......core.text import clean_optional_text
from .....contracts.models import ContextPointRecord
from .....spatial import classify_country
from ...acquisition.fetch import parse_optional_int
from .chronology_policy import sead_claim_age_policy
from .models import TemporalRowGroup
from .values import parse_int_or_default, parse_optional_float

TEMPORAL_ROW_SPECS = (
    ("dating_range_rows", "dating_range", "analysis_dating_range_id"),
    ("relative_period_rows", "relative_period", "relative_date_id"),
    ("analysis_entity_age_rows", "analysis_entity_age", "analysis_entity_age_id"),
    ("geochronology_rows", "geochronology", "geochron_id"),
    ("dendro_date_rows", "dendrochronology", "dendro_date_id"),
)

TEMPORAL_KIND_LABELS = {
    "dating_range": "Analysis dating range",
    "relative_period": "Relative period",
    "analysis_entity_age": "Modelled analysis-entity age",
    "geochronology": "Geochronology measurement",
    "dendrochronology": "Dendrochronology date",
}


def normalize_sead_temporal_evidence(
    rows: Iterable[dict[str, object]],
    country_boundaries: Mapping[str, Mapping[str, object]],
) -> list[ContextPointRecord]:
    """Publish linked SEAD chronology as record-level time-filterable points."""
    records: list[ContextPointRecord] = []
    for site_row in rows:
        latitude = parse_optional_float(site_row.get("latitude_dd"))
        longitude = parse_optional_float(site_row.get("longitude_dd"))
        if latitude is None or longitude is None:
            continue
        country = classify_country(longitude, latitude, country_boundaries)
        if not country:
            continue
        site_id = str(site_row.get("site_id", "")).strip()
        site_uuid = clean_optional_text(site_row.get("site_uuid"))
        country_assignment_method = clean_optional_text(
            site_row.get("country_assignment_method")
        )
        site_name = str(site_row.get("site_name", "")).strip() or f"SEAD site {site_id}"
        bibliography_rows = site_row.get("bibliography_rows", [])
        bibliography_count = (
            len(bibliography_rows) if isinstance(bibliography_rows, list) else 0
        )
        for group in group_site_temporal_rows(site_row):
            kind = str(group["kind"])
            interval = group["interval"]
            label = str(group["label"])
            uncertainty_notes = tuple(
                str(value) for value in group["uncertainty_notes"]
            )
            source_record_ids = tuple(
                int(value) for value in group["source_record_ids"]
            )
            kind_label = TEMPORAL_KIND_LABELS[kind]
            time_label = build_bp_interval_label(interval[0], interval[1])
            temporal_semantics = build_temporal_semantics(
                source_family="sead",
                evidence_class=f"sead_{kind}",
                precision_posture="linked_record_interval",
                comparability_posture=(
                    "numeric_interval_with_caveat"
                    if uncertainty_notes
                    else "numeric_interval"
                ),
                time_start_bp=interval[0],
                time_end_bp=interval[1],
                summary_label=f"{label} ({time_label})" if label else time_label,
                comparison_note=(
                    "This feature represents linked SEAD chronology at its source-record interval. "
                    "Coincident records are grouped without widening their time span."
                ),
                provenance_locator=(
                    f"site/{site_id}/{kind}/{source_record_ids[0]}"
                    if source_record_ids
                    else f"site/{site_id}/{kind}"
                ),
                original_labels=(label,) if label else (),
                uncertainty_notes=uncertainty_notes,
            ).as_dict()
            temporal_semantics["source_record_count"] = len(source_record_ids)
            temporal_semantics["source_record_ids"] = list(source_record_ids)
            temporal_semantics["chronology_claim_ids"] = [
                f"sead:{site_uuid or f'site-{site_id}'}:{kind}:{record_id}"
                for record_id in source_record_ids
            ]
            temporal_semantics["claim_bundle_path"] = (
                "data/sead/normalized/chronology_claims.json"
            )
            popup_rows = [
                ("Site", site_name),
                ("Site ID", site_id),
                ("Site UUID", site_uuid or "Unavailable"),
                ("Country assignment", country_assignment_method or "Unavailable"),
                ("Chronology kind", kind_label),
                ("Date coverage", time_label),
                ("Chronology eligibility", "Eligible numeric comparison"),
                ("Selection posture", "All source chronologies retained"),
                ("Grouped source records", str(len(source_record_ids))),
                (
                    "Source record IDs",
                    ", ".join(str(value) for value in source_record_ids),
                ),
            ]
            if label:
                popup_rows.append(("Source chronology label", label))
            if uncertainty_notes:
                popup_rows.append(
                    ("Temporal uncertainty", " | ".join(uncertainty_notes))
                )
            if bibliography_count:
                popup_rows.append(
                    ("Site-linked bibliography records", str(bibliography_count))
                )
            first_record_id = source_record_ids[0] if source_record_ids else 0
            records.append(
                ContextPointRecord(
                    source="SEAD",
                    layer_key="sead-temporal-evidence",
                    layer_label="SEAD temporal evidence",
                    category="Environmental archaeology chronology",
                    country=country,
                    record_id=f"{site_id}:{kind}:{first_record_id}",
                    name=f"{site_name} — {kind_label}",
                    latitude=latitude,
                    longitude=longitude,
                    geometry_type="Point",
                    subtitle="Linked SEAD chronology records",
                    description=(
                        "Time-filterable chronology linked to a SEAD environmental archaeology site."
                    ),
                    source_url=f"https://browser.sead.se/site/{site_id}",
                    record_count=len(source_record_ids),
                    popup_rows=tuple(popup_rows),
                    time_start_bp=interval[0],
                    time_end_bp=interval[1],
                    time_mean_bp=mean_bp_year_from_interval(interval),
                    time_label=time_label,
                    temporal_semantics=temporal_semantics,
                )
            )
    return sorted(
        records,
        key=lambda item: (
            item.name.casefold(),
            item.time_start_bp or 0,
            item.time_end_bp or 0,
            item.record_id,
        ),
    )


def group_site_temporal_rows(site_row: Mapping[str, object]) -> list[TemporalRowGroup]:
    """Group equivalent comparable chronology rows without widening intervals."""
    groups: dict[tuple[str, int, int, str, tuple[str, ...]], list[int]] = {}
    for row_key, kind, id_key in TEMPORAL_ROW_SPECS:
        values = site_row.get(row_key, [])
        if not isinstance(values, list):
            continue
        for value in values:
            if not isinstance(value, dict):
                continue
            age_policy = sead_claim_age_policy(kind, value)
            if age_policy["comparability_status"] != "comparable":
                continue
            if parse_optional_int(value.get("analysis_entity_id")) is None:
                continue
            interval = normalize_bp_interval(
                parse_optional_int(value.get("time_start_bp")),
                parse_optional_int(value.get("time_end_bp")),
            )
            if interval is None:
                continue
            label = temporal_row_label(kind, value)
            uncertainty_notes = tuple(temporal_row_uncertainty_notes(value))
            key = (kind, interval[0], interval[1], label, uncertainty_notes)
            source_record_id = parse_int_or_default(value.get(id_key))
            groups.setdefault(key, []).append(source_record_id)
    return [
        {
            "kind": kind,
            "interval": (time_start_bp, time_end_bp),
            "label": label,
            "uncertainty_notes": uncertainty_notes,
            "source_record_ids": tuple(sorted(set(source_record_ids))),
        }
        for (
            kind,
            time_start_bp,
            time_end_bp,
            label,
            uncertainty_notes,
        ), source_record_ids in groups.items()
    ]


def temporal_row_label(kind: str, row: Mapping[str, object]) -> str:
    """Choose a source-facing label for one chronology row."""
    if kind == "relative_period":
        return clean_optional_text(row.get("relative_age_label"))
    if kind == "analysis_entity_age":
        return clean_optional_text(row.get("dating_specifier"))
    if kind == "geochronology":
        lab_number = clean_optional_text(row.get("lab_number"))
        return f"Radiometric age {lab_number}".strip()
    if kind == "dendrochronology":
        return clean_optional_text(row.get("age_type")) or "Dendrochronology"
    return clean_optional_text(row.get("age_type")) or "Dating range"


def temporal_row_uncertainty_notes(row: Mapping[str, object]) -> list[str]:
    """Collect one chronology row's qualifiers and uncertainty note."""
    values = []
    label = clean_optional_text(row.get("uncertainty_label"))
    description = clean_optional_text(row.get("uncertainty_description"))
    if label or description:
        values.append(": ".join(value for value in (label, description) if value))
    for key in ("low_qualifier", "high_qualifier"):
        qualifier = clean_optional_text(row.get(key))
        if qualifier and qualifier not in values:
            values.append(qualifier)
    if row.get("low_is_uncertain") or row.get("high_is_uncertain"):
        values.append("Upstream range bound marked uncertain")
    return values
