"""Candidate inventory, identity, and cross-format validation."""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from uuid import UUID

from .contract import (
    SEAD_REPOSITORY_SURFACE_PATHS,
    RepositorySurfaceCandidate,
    file_sha256,
)


def validate_repository_surface_candidate(
    candidate: RepositorySurfaceCandidate,
) -> dict[Path, str]:
    """Require the candidate to contain exactly the governed regular-file set."""
    discovered: set[Path] = set()
    for path in candidate.candidate_data_root.rglob("*"):
        if path.is_symlink():
            raise ValueError("SEAD repository-surface candidate contains a symlink")
        if path.is_file():
            discovered.add(path.relative_to(candidate.candidate_data_root))
    expected = set(SEAD_REPOSITORY_SURFACE_PATHS)
    if discovered != expected:
        missing = sorted(str(path) for path in expected - discovered)
        extra = sorted(str(path) for path in discovered - expected)
        raise ValueError(
            f"SEAD repository-surface candidate inventory differs: missing={missing}; extra={extra}"
        )
    hashes = {
        relative_path: file_sha256(candidate.candidate_data_root / relative_path)
        for relative_path in SEAD_REPOSITORY_SURFACE_PATHS
    }
    validate_json_surfaces(candidate)
    validate_cross_format_counts(candidate)
    return hashes


def require_source_snapshot_unchanged(
    source_root: Path,
    copied_files: Mapping[str, bytes],
) -> None:
    """Recheck every governed source byte before candidate promotion."""
    source_root = Path(source_root).resolve()
    for relative_name, expected_bytes in copied_files.items():
        path = source_root / relative_name
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"governed SEAD source changed: {relative_name}")
        if file_sha256(path) != hashlib.sha256(expected_bytes).hexdigest():
            raise RuntimeError(f"governed SEAD source changed: {relative_name}")


def validate_json_surfaces(candidate: RepositorySurfaceCandidate) -> None:
    for relative_path in SEAD_REPOSITORY_SURFACE_PATHS:
        if relative_path.suffix not in {".json", ".geojson"}:
            continue
        path = candidate.candidate_data_root / relative_path
        try:
            payload: Any = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(
                f"SEAD candidate JSON is invalid: {relative_path}"
            ) from error
        if not isinstance(payload, dict):
            raise ValueError(  # noqa: TRY004 - malformed contract payload
                f"SEAD candidate JSON root is invalid: {relative_path}"
            )


def validate_cross_format_counts(candidate: RepositorySurfaceCandidate) -> None:
    root = candidate.candidate_data_root / "sead"
    normalized_site_identities: dict[str, str] = {}
    for stem in ("nordic_environmental_sites", "nordic_temporal_evidence"):
        csv_path = root / "normalized" / f"{stem}.csv"
        csv_rows = csv_dict_rows(csv_path)
        csv_count = len(csv_rows)
        geojson = json_object(root / "normalized" / f"{stem}.geojson")
        features = geojson.get("features")
        if not isinstance(features, list) or len(features) != csv_count:
            raise ValueError(f"SEAD candidate normalized counts differ: {stem}")
        csv_identities = [
            (
                required_text(row.get("record_id"), f"{stem} CSV record_id"),
                required_site_uuid(row.get("site_uuid"), f"{stem} CSV site_uuid"),
            )
            for row in csv_rows
        ]
        geojson_identities = []
        for feature in features:
            if not isinstance(feature, dict):
                raise ValueError(f"SEAD candidate GeoJSON feature is invalid: {stem}")
            properties = feature.get("properties")
            if not isinstance(properties, dict):
                raise ValueError(
                    f"SEAD candidate GeoJSON properties are invalid: {stem}"
                )
            geojson_identities.append(
                (
                    required_text(
                        properties.get("record_id"), f"{stem} GeoJSON record_id"
                    ),
                    required_site_uuid(
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
    for stem in (
        "access_model",
        "evidence_legibility_review",
        "recovery_requirements",
        "temporal_review",
    ):
        payload = json_object(root / "review" / f"{stem}.json")
        if payload.get("row_count") != csv_row_count(root / "review" / f"{stem}.csv"):
            raise ValueError(f"SEAD candidate review counts differ: {stem}")
    discovery = json_object(root / "derived" / "sweden_archaeology_site_discovery.json")
    summary = discovery.get("summary")
    discovery_geojson = json_object(
        root / "derived" / "sweden_archaeology_site_discovery.geojson"
    )
    features = discovery_geojson.get("features")
    if (
        not isinstance(summary, dict)
        or summary.get("site_count")
        != csv_row_count(root / "derived" / "sweden_archaeology_site_discovery.csv")
        or not isinstance(features, list)
        or summary.get("map_feature_count") != len(features)
    ):
        raise ValueError("SEAD candidate discovery counts differ")
    discovery_sites = discovery.get("sites")
    if not isinstance(discovery_sites, list) or any(
        not isinstance(row, dict) for row in discovery_sites
    ):
        raise ValueError("SEAD candidate discovery site identities are invalid")
    registry_identities = identity_registry(
        discovery_sites,
        id_label="SEAD discovery site_id",
        uuid_label="SEAD discovery site_uuid",
    )
    discovery_csv_identities = identity_registry(
        csv_dict_rows(root / "derived" / "sweden_archaeology_site_discovery.csv"),
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
            raise ValueError("SEAD candidate discovery feature identity is invalid")
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            raise ValueError("SEAD candidate discovery feature identity is invalid")
        record_id = required_text(
            properties.get("record_id"), "SEAD discovery feature record_id"
        )
        site_id = record_id.split(":", 1)[0]
        site_uuid = required_site_uuid(
            properties.get("site_uuid"), "SEAD discovery feature site_uuid"
        )
        if registry_identities.get(site_id) != site_uuid:
            raise ValueError("SEAD candidate discovery feature UUID differs")
    classification = json_object(
        root / "review" / "scientific_classification_review.json"
    )
    candidates = classification.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != csv_row_count(
        root / "review" / "scientific_classification_candidates.csv"
    ):
        raise ValueError("SEAD candidate classification counts differ")


def json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(  # noqa: TRY004 - malformed contract payload
            f"SEAD candidate JSON root is invalid: {path.name}"
        )
    return value


def csv_row_count(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def csv_dict_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is missing")
    return value.strip()


def required_site_uuid(value: object, label: str) -> str:
    text = required_text(value, label)
    try:
        parsed = UUID(text)
    except ValueError as error:
        raise ValueError(f"{label} is not a UUID") from error
    if str(parsed) != text:
        raise ValueError(f"{label} is not in canonical form")
    return text


def identity_registry(
    rows: list[dict[str, Any]], *, id_label: str, uuid_label: str
) -> dict[str, str]:
    identities: dict[str, str] = {}
    seen_uuids: set[str] = set()
    for row in rows:
        site_id = required_text(row.get("site_id"), id_label)
        site_uuid = required_site_uuid(row.get("site_uuid"), uuid_label)
        if site_id in identities or site_uuid in seen_uuids:
            raise ValueError(f"{id_label} or {uuid_label} is duplicated")
        identities[site_id] = site_uuid
        seen_uuids.add(site_uuid)
    return identities
