from __future__ import annotations

from collections.abc import Iterable, Mapping

from ....core.bp_time import (
    build_bp_interval_label,
    mean_bp_year_from_interval,
    normalize_bp_interval,
)
from ....core.temporal_semantics import build_temporal_semantics
from ....core.text import clean_optional_text
from ...models import ContextPointRecord
from ...spatial import classify_country
from .access import build_sead_site_access_model
from .fetch import parse_optional_int

__all__ = ["normalize_sead_rows", "normalize_sead_temporal_evidence"]

_TEMPORAL_ROW_SPECS = (
    ("dating_range_rows", "dating_range", "analysis_dating_range_id"),
    ("relative_period_rows", "relative_period", "relative_date_id"),
    (
        "analysis_entity_age_rows",
        "analysis_entity_age",
        "analysis_entity_age_id",
    ),
    ("geochronology_rows", "geochronology", "geochron_id"),
    ("dendro_date_rows", "dendrochronology", "dendro_date_id"),
)

_TEMPORAL_KIND_LABELS = {
    "dating_range": "Analysis dating range",
    "relative_period": "Relative period",
    "analysis_entity_age": "Modelled analysis-entity age",
    "geochronology": "Geochronology measurement",
    "dendrochronology": "Dendrochronology date",
}


def normalize_sead_rows(
    rows: Iterable[dict[str, object]],
    country_boundaries: Mapping[str, Mapping[str, object]],
) -> list[ContextPointRecord]:
    """Convert SEAD site rows into compact environmental archaeology records."""
    records: list[ContextPointRecord] = []
    for row in rows:
        latitude = parse_optional_float(row.get("latitude_dd"))
        longitude = parse_optional_float(row.get("longitude_dd"))
        if latitude is None or longitude is None:
            continue
        country = classify_country(longitude, latitude, country_boundaries)
        if not country:
            continue
        site_id = str(row.get("site_id", "")).strip()
        site_name = str(row.get("site_name", "")).strip() or f"SEAD site {site_id}"
        national_identifier = str(row.get("national_site_identifier", "") or "").strip()
        altitude = clean_optional_text(row.get("altitude"))
        description = str(row.get("site_description", "") or "").strip()
        sample_group_count = parse_int_or_default(row.get("sample_group_count"))
        physical_sample_count = parse_int_or_default(row.get("physical_sample_count"))
        analysis_entity_count = parse_int_or_default(row.get("analysis_entity_count"))
        dataset_count = parse_int_or_default(row.get("dataset_count"))
        reference_count = parse_int_or_default(row.get("reference_count"))
        relative_date_count = parse_int_or_default(row.get("relative_date_count"))
        dating_range_count = parse_int_or_default(row.get("dating_range_count"))
        analysis_entity_age_count = parse_int_or_default(
            row.get("analysis_entity_age_count")
        )
        geochronology_count = parse_int_or_default(row.get("geochronology_count"))
        dendro_date_count = parse_int_or_default(row.get("dendro_date_count"))
        dataset_names = row.get("dataset_names")
        if not isinstance(dataset_names, list):
            dataset_names = []
        time_interval = normalize_bp_interval(
            parse_optional_int(row.get("time_start_bp")),
            parse_optional_int(row.get("time_end_bp")),
        )
        temporal_semantics = _build_sead_temporal_semantics(
            row,
            time_interval=time_interval,
        )
        access_model = build_sead_site_access_model(row)

        popup_rows = [
            ("Site ID", site_id),
            ("Category", "Environmental archaeology"),
            ("Source", "SEAD"),
            ("Country", country),
        ]
        access_visibility = str(access_model.get("access_visibility", "")).strip()
        if access_visibility:
            popup_rows.append(
                (
                    "Access visibility",
                    access_visibility.replace("_", " "),
                )
            )
        if sample_group_count:
            popup_rows.append(("Sample groups", str(sample_group_count)))
        if physical_sample_count:
            popup_rows.append(("Physical samples", str(physical_sample_count)))
        if analysis_entity_count:
            popup_rows.append(("Analysis entities", str(analysis_entity_count)))
        if dataset_count:
            popup_rows.append(("Datasets", str(dataset_count)))
        if dataset_names:
            popup_rows.append(("Dataset names", ", ".join(dataset_names)))
        if reference_count:
            popup_rows.append(("References", str(reference_count)))
        if relative_date_count:
            popup_rows.append(("Relative dates", str(relative_date_count)))
        if dating_range_count:
            popup_rows.append(("Dating ranges", str(dating_range_count)))
        if analysis_entity_age_count:
            popup_rows.append(
                ("Modelled analysis-entity ages", str(analysis_entity_age_count))
            )
        if geochronology_count:
            popup_rows.append(("Geochronology records", str(geochronology_count)))
        if dendro_date_count:
            popup_rows.append(("Dendrochronology dates", str(dendro_date_count)))
        if time_interval is not None:
            popup_rows.append(
                (
                    "Date coverage",
                    build_bp_interval_label(time_interval[0], time_interval[1]),
                )
            )
        comparability_posture = str(
            temporal_semantics.get("comparability_posture", "")
        ).strip()
        if comparability_posture:
            popup_rows.append(
                (
                    "Temporal comparison posture",
                    comparability_posture.replace("_", " "),
                )
            )
        window_label = str(temporal_semantics.get("temporal_window_label", "")).strip()
        if window_label:
            popup_rows.append(("Temporal window", window_label))
        original_labels = temporal_semantics.get("original_labels", [])
        if isinstance(original_labels, list) and original_labels:
            popup_rows.append(("Original period labels", ", ".join(original_labels)))
        normalized_labels = temporal_semantics.get("normalized_labels", [])
        if isinstance(normalized_labels, list) and normalized_labels:
            popup_rows.append(
                ("Normalized period labels", ", ".join(normalized_labels))
            )
        uncertainty_notes = temporal_semantics.get("uncertainty_notes", [])
        if isinstance(uncertainty_notes, list) and uncertainty_notes:
            popup_rows.append(("Temporal uncertainty", " | ".join(uncertainty_notes)))
        access_limits = access_model.get("access_limits", [])
        if isinstance(access_limits, list) and access_limits:
            popup_rows.append(("Access limits", access_limits[0]))
        reader_action = str(access_model.get("reader_action", "")).strip()
        if reader_action:
            popup_rows.append(("Reader action", reader_action))
        if national_identifier:
            popup_rows.append(("National identifier", national_identifier))
        if altitude:
            popup_rows.append(("Altitude", altitude))
        if description:
            popup_rows.append(("Description", description))

        records.append(
            ContextPointRecord(
                source="SEAD",
                layer_key="sead-sites",
                layer_label="SEAD sites",
                category="Environmental archaeology",
                country=country,
                record_id=site_id,
                name=site_name,
                latitude=latitude,
                longitude=longitude,
                geometry_type="Point",
                subtitle="Nordic SEAD archaeology context sites",
                description=description,
                source_url=f"https://browser.sead.se/site/{site_id}",
                record_count=max(
                    dataset_count,
                    analysis_entity_count,
                    dating_range_count,
                    analysis_entity_age_count,
                    geochronology_count,
                    dendro_date_count,
                    1,
                ),
                popup_rows=tuple(popup_rows),
                time_start_bp=time_interval[0] if time_interval is not None else None,
                time_end_bp=time_interval[1] if time_interval is not None else None,
                time_mean_bp=mean_bp_year_from_interval(time_interval),
                time_label=build_bp_interval_label(time_interval[0], time_interval[1])
                if time_interval is not None
                else "",
                temporal_semantics=temporal_semantics,
            )
        )
    return sorted(records, key=lambda item: (item.name.casefold(), item.record_id))


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
        site_name = str(site_row.get("site_name", "")).strip() or f"SEAD site {site_id}"
        bibliography_rows = site_row.get("bibliography_rows", [])
        bibliography_count = (
            len(bibliography_rows) if isinstance(bibliography_rows, list) else 0
        )
        for group in _group_site_temporal_rows(site_row):
            kind = str(group["kind"])
            interval = group["interval"]
            if not isinstance(interval, tuple):
                continue
            label = str(group["label"])
            uncertainty_notes = tuple(
                str(value) for value in group["uncertainty_notes"]
            )
            source_record_ids = tuple(
                int(value) for value in group["source_record_ids"]
            )
            kind_label = _TEMPORAL_KIND_LABELS[kind]
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
            popup_rows = [
                ("Site", site_name),
                ("Site ID", site_id),
                ("Chronology kind", kind_label),
                ("Date coverage", time_label),
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


def parse_optional_float(value: object) -> float | None:
    """Parse one optional numeric field as float."""
    if isinstance(value, (int, float)):
        return float(value)
    text = clean_optional_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _group_site_temporal_rows(
    site_row: Mapping[str, object],
) -> list[dict[str, object]]:
    groups: dict[
        tuple[str, int, int, str, tuple[str, ...]],
        list[int],
    ] = {}
    for row_key, kind, id_key in _TEMPORAL_ROW_SPECS:
        values = site_row.get(row_key, [])
        if not isinstance(values, list):
            continue
        for value in values:
            if not isinstance(value, dict):
                continue
            interval = normalize_bp_interval(
                parse_optional_int(value.get("time_start_bp")),
                parse_optional_int(value.get("time_end_bp")),
            )
            if interval is None:
                continue
            label = _temporal_row_label(kind, value)
            uncertainty_notes = tuple(_temporal_row_uncertainty_notes(value))
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


def _temporal_row_label(kind: str, row: Mapping[str, object]) -> str:
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


def _temporal_row_uncertainty_notes(row: Mapping[str, object]) -> list[str]:
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


def parse_int_or_default(value: object, *, default: int = 0) -> int:
    """Parse one optional numeric field as integer with fallback."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = clean_optional_text(value)
    if not text:
        return default
    try:
        return int(text)
    except ValueError:
        return default


def _build_sead_temporal_semantics(
    row: Mapping[str, object],
    *,
    time_interval: tuple[int, int] | None,
) -> dict[str, object]:
    original_labels = _string_values_from_temporal_rows(
        row.get("relative_period_rows"),
        "relative_age_label",
    )
    normalized_labels = _string_values_from_temporal_rows(
        row.get("relative_period_rows"),
        "normalized_period_label",
    )
    uncertainty_notes = _collect_uncertainty_notes(row)
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


def _string_values_from_temporal_rows(rows: object, key: str) -> list[str]:
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


def _collect_uncertainty_notes(row: Mapping[str, object]) -> list[str]:
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
