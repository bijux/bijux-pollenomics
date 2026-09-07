"""Cross-format identity validation for candidate SEAD surfaces."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from uuid import UUID


def validate_normalized_surface_identities(root: Path) -> dict[str, str]:
    """Validate matching record and site identities across normalized formats."""
    normalized_site_identities: dict[str, str] = {}
    for stem in ("nordic_environmental_sites", "nordic_temporal_evidence"):
        csv_rows = _csv_dict_rows(root / "normalized" / f"{stem}.csv")
        csv_identities = [
            (
                _required_text(row.get("record_id"), f"{stem} CSV record_id"),
                _required_site_uuid(row.get("site_uuid"), f"{stem} CSV site_uuid"),
            )
            for row in csv_rows
        ]
        geojson = _json_object(root / "normalized" / f"{stem}.geojson")
        features = geojson.get("features")
        if not isinstance(features, list):
            raise ValueError(  # noqa: TRY004 - malformed contract payload
                f"SEAD candidate GeoJSON features are invalid: {stem}"
            )
        geojson_identities = []
        for feature in features:
            if not isinstance(feature, dict):
                raise ValueError(  # noqa: TRY004 - malformed contract payload
                    f"SEAD candidate GeoJSON feature is invalid: {stem}"
                )
            properties = feature.get("properties")
            if not isinstance(properties, dict):
                raise ValueError(  # noqa: TRY004 - malformed contract payload
                    f"SEAD candidate GeoJSON properties are invalid: {stem}"
                )
            geojson_identities.append(
                (
                    _required_text(
                        properties.get("record_id"), f"{stem} GeoJSON record_id"
                    ),
                    _required_site_uuid(
                        properties.get("site_uuid"), f"{stem} GeoJSON site_uuid"
                    ),
                )
            )
        if csv_identities != geojson_identities:
            raise ValueError(f"SEAD candidate normalized UUIDs differ: {stem}")
        record_ids = [record_id for record_id, _ in csv_identities]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError(f"SEAD candidate normalized record IDs repeat: {stem}")
        if stem == "nordic_environmental_sites":
            normalized_site_identities = dict(csv_identities)
            if len(normalized_site_identities) != len(
                {site_uuid for _, site_uuid in csv_identities}
            ):
                raise ValueError("SEAD candidate normalized site UUIDs repeat")
        else:
            for record_id, site_uuid in csv_identities:
                site_id = record_id.split(":", 1)[0]
                if normalized_site_identities.get(site_id) != site_uuid:
                    raise ValueError(
                        "SEAD candidate temporal UUID differs from normalized site"
                    )
    return normalized_site_identities


def validate_discovery_surface_identities(
    *,
    root: Path,
    normalized_site_identities: Mapping[str, str],
    discovery_sites: Sequence[Mapping[str, Any]],
    features: Sequence[object],
) -> None:
    """Validate discovery identities against normalized and GeoJSON surfaces."""
    registry_identities = _identity_registry(
        discovery_sites,
        id_label="SEAD discovery site_id",
        uuid_label="SEAD discovery site_uuid",
    )
    discovery_csv_identities = _identity_registry(
        _csv_dict_rows(root / "derived" / "sweden_archaeology_site_discovery.csv"),
        id_label="SEAD discovery CSV site_id",
        uuid_label="SEAD discovery CSV site_uuid",
    )
    if registry_identities != discovery_csv_identities:
        raise ValueError("SEAD candidate discovery UUID registries differ")
    if any(
        normalized_site_identities.get(site_id) != site_uuid
        for site_id, site_uuid in registry_identities.items()
    ):
        raise ValueError("SEAD candidate discovery UUID differs from normalized site")
    for feature in features:
        if not isinstance(feature, dict):
            raise ValueError(  # noqa: TRY004 - malformed contract payload
                "SEAD candidate discovery feature identity is invalid"
            )
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            raise ValueError(  # noqa: TRY004 - malformed contract payload
                "SEAD candidate discovery feature identity is invalid"
            )
        record_id = _required_text(
            properties.get("record_id"), "SEAD discovery feature record_id"
        )
        site_id = record_id.split(":", 1)[0]
        site_uuid = _required_site_uuid(
            properties.get("site_uuid"), "SEAD discovery feature site_uuid"
        )
        if registry_identities.get(site_id) != site_uuid:
            raise ValueError("SEAD candidate discovery feature UUID differs")


def _json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(  # noqa: TRY004 - malformed contract payload
            f"SEAD candidate JSON root is invalid: {path.name}"
        )
    return value


def _csv_dict_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is missing")
    return value.strip()


def _required_site_uuid(value: object, label: str) -> str:
    text = _required_text(value, label)
    try:
        parsed = UUID(text)
    except ValueError as error:
        raise ValueError(f"{label} is not a UUID") from error
    if str(parsed) != text:
        raise ValueError(f"{label} is not in canonical form")
    return text


def _identity_registry(
    rows: Sequence[Mapping[str, Any]], *, id_label: str, uuid_label: str
) -> dict[str, str]:
    identities: dict[str, str] = {}
    seen_uuids: set[str] = set()
    for row in rows:
        site_id = _required_text(row.get("site_id"), id_label)
        site_uuid = _required_site_uuid(row.get("site_uuid"), uuid_label)
        if site_id in identities or site_uuid in seen_uuids:
            raise ValueError(f"{id_label} or {uuid_label} is duplicated")
        identities[site_id] = site_uuid
        seen_uuids.add(site_uuid)
    return identities
