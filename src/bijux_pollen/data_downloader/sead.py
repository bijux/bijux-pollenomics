from __future__ import annotations

from typing import Iterable

from .common import clean_optional_text, fetch_json
from .geometry import classify_country
from .models import ContextPointRecord


SEAD_LIMIT = 1000


def fetch_sead_site_rows(bbox: tuple[float, float, float, float]) -> list[dict[str, object]]:
    """Download SEAD site rows inside the Nordic bounding box."""
    min_longitude, min_latitude, max_longitude, max_latitude = bbox
    base_url = (
        "https://browser.sead.se/postgrest/tbl_sites"
        "?select=site_id,site_name,national_site_identifier,latitude_dd,longitude_dd,"
        "altitude,site_description,site_uuid"
        f"&latitude_dd=gte.{min_latitude}"
        f"&latitude_dd=lte.{max_latitude}"
        f"&longitude_dd=gte.{min_longitude}"
        f"&longitude_dd=lte.{max_longitude}"
    )

    rows: list[dict[str, object]] = []
    start = 0
    while True:
        chunk = fetch_json(
            base_url,
            headers={
                "Range-Unit": "items",
                "Range": f"{start}-{start + SEAD_LIMIT - 1}",
            },
        )
        if not isinstance(chunk, list) or not chunk:
            break
        rows.extend(chunk)
        if len(chunk) < SEAD_LIMIT:
            break
        start += SEAD_LIMIT

    deduplicated: dict[str, dict[str, object]] = {}
    for row in rows:
        deduplicated[str(row.get("site_id", ""))] = row
    return sorted(deduplicated.values(), key=lambda item: int(item.get("site_id", 0)))


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
        country = classify_country(float(longitude), float(latitude), country_boundaries)
        if not country:
            continue
        site_id = str(row.get("site_id", "")).strip()
        site_name = str(row.get("site_name", "")).strip() or f"SEAD site {site_id}"
        national_identifier = str(row.get("national_site_identifier", "") or "").strip()
        altitude = clean_optional_text(row.get("altitude"))
        description = str(row.get("site_description", "") or "").strip()
        source_url = f"https://browser.sead.se/site/{site_id}"

        popup_rows = [
            ("Site ID", site_id),
            ("Category", "Environmental archaeology"),
            ("Source", "SEAD"),
            ("Country", country),
        ]
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
                source_url=source_url,
                record_count=1,
                popup_rows=tuple(popup_rows),
            )
        )

    return sorted(records, key=lambda item: (item.name.casefold(), item.record_id))
