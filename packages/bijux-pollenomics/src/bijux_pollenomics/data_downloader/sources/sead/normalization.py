from __future__ import annotations

from collections.abc import Iterable

from ....core.bp_time import (
    build_bp_interval_label,
    mean_bp_year_from_interval,
    normalize_bp_interval,
)
from ....core.text import clean_optional_text
from ...models import ContextPointRecord
from ...spatial import classify_country
from .fetch import parse_optional_int

__all__ = ["normalize_sead_rows"]


def normalize_sead_rows(
    rows: Iterable[dict[str, object]],
    country_boundaries: dict[str, dict[str, object]],
) -> list[ContextPointRecord]:
    """Convert SEAD site rows into compact environmental archaeology records."""
    records: list[ContextPointRecord] = []
    for row in rows:
        latitude = row.get("latitude_dd")
        longitude = row.get("longitude_dd")
        if latitude is None or longitude is None:
            continue
        country = classify_country(
            float(longitude), float(latitude), country_boundaries
        )
        if not country:
            continue
        site_id = str(row.get("site_id", "")).strip()
        site_name = str(row.get("site_name", "")).strip() or f"SEAD site {site_id}"
        national_identifier = str(row.get("national_site_identifier", "") or "").strip()
        altitude = clean_optional_text(row.get("altitude"))
        description = str(row.get("site_description", "") or "").strip()
        sample_group_count = int(row.get("sample_group_count") or 0)
        physical_sample_count = int(row.get("physical_sample_count") or 0)
        analysis_entity_count = int(row.get("analysis_entity_count") or 0)
        dataset_count = int(row.get("dataset_count") or 0)
        reference_count = int(row.get("reference_count") or 0)
        relative_date_count = int(row.get("relative_date_count") or 0)
        dating_range_count = int(row.get("dating_range_count") or 0)
        dataset_names = row.get("dataset_names")
        if not isinstance(dataset_names, list):
            dataset_names = []
        time_interval = normalize_bp_interval(
            parse_optional_int(row.get("time_start_bp")),
            parse_optional_int(row.get("time_end_bp")),
        )

        popup_rows = [
            ("Site ID", site_id),
            ("Category", "Environmental archaeology"),
            ("Source", "SEAD"),
            ("Country", country),
        ]
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
        if time_interval is not None:
            popup_rows.append(
                (
                    "Date coverage",
                    build_bp_interval_label(time_interval[0], time_interval[1]),
                )
            )
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
                latitude=float(latitude),
                longitude=float(longitude),
                geometry_type="Point",
                subtitle="Nordic environmental archaeology sites",
                description=description,
                source_url=f"https://browser.sead.se/site/{site_id}",
                record_count=max(
                    dataset_count, analysis_entity_count, dating_range_count, 1
                ),
                popup_rows=tuple(popup_rows),
                time_start_bp=time_interval[0] if time_interval is not None else None,
                time_end_bp=time_interval[1] if time_interval is not None else None,
                time_mean_bp=mean_bp_year_from_interval(time_interval),
                time_label=build_bp_interval_label(time_interval[0], time_interval[1])
                if time_interval is not None
                else "",
            )
        )
    return sorted(records, key=lambda item: (item.name.casefold(), item.record_id))
