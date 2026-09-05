"""Projection of SEAD sites into contextual map points."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from ......core.bp_time import (
    build_bp_interval_label,
    mean_bp_year_from_interval,
    normalize_bp_interval,
)
from ......core.text import clean_optional_text
from .....contracts.models import ContextPointRecord
from .....spatial import classify_country
from ...acquisition.access import build_sead_site_access_model
from ...acquisition.fetch import parse_optional_int
from .site_temporal_semantics import build_sead_temporal_semantics
from .values import parse_int_or_default, parse_optional_float


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
        site_uuid = clean_optional_text(row.get("site_uuid"))
        country_assignment_method = clean_optional_text(
            row.get("country_assignment_method")
        )
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
        temporal_semantics = build_sead_temporal_semantics(
            row,
            time_interval=time_interval,
        )
        access_model = build_sead_site_access_model(row)

        popup_rows = [
            ("Site ID", site_id),
            ("Site UUID", site_uuid or "Unavailable"),
            ("Country assignment", country_assignment_method or "Unavailable"),
            ("Category", "Environmental archaeology"),
            ("Source", "SEAD"),
            ("Country", country),
        ]
        access_visibility = str(access_model.get("access_visibility", "")).strip()
        if access_visibility:
            popup_rows.append(
                ("Access visibility", access_visibility.replace("_", " "))
            )
        for label, count in (
            ("Sample groups", sample_group_count),
            ("Physical samples", physical_sample_count),
            ("Analysis entities", analysis_entity_count),
            ("Datasets", dataset_count),
        ):
            if count:
                popup_rows.append((label, str(count)))
        if dataset_names:
            popup_rows.append(("Dataset names", ", ".join(dataset_names)))
        for label, count in (
            ("References", reference_count),
            ("Relative dates", relative_date_count),
            ("Dating ranges", dating_range_count),
            ("Modelled analysis-entity ages", analysis_entity_age_count),
            ("Geochronology records", geochronology_count),
            ("Dendrochronology dates", dendro_date_count),
        ):
            if count:
                popup_rows.append((label, str(count)))
        if time_interval is not None:
            popup_rows.append(
                ("Date coverage", build_bp_interval_label(*time_interval))
            )
        comparability_posture = str(
            temporal_semantics.get("comparability_posture", "")
        ).strip()
        if comparability_posture:
            popup_rows.append(
                ("Temporal comparison posture", comparability_posture.replace("_", " "))
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
                time_label=build_bp_interval_label(*time_interval)
                if time_interval is not None
                else "",
                temporal_semantics=temporal_semantics,
            )
        )
    return sorted(records, key=lambda item: (item.name.casefold(), item.record_id))
