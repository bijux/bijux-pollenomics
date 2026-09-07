"""Candidate inventory, identity, and cross-format validation."""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .contract import (
    SEAD_REPOSITORY_SURFACE_PATHS,
    RepositorySurfaceCandidate,
    file_sha256,
)
from .identity import (
    validate_discovery_surface_identities,
    validate_normalized_surface_identities,
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
    for stem in ("nordic_environmental_sites", "nordic_temporal_evidence"):
        csv_count = csv_row_count(root / "normalized" / f"{stem}.csv")
        geojson = json_object(root / "normalized" / f"{stem}.geojson")
        features = geojson.get("features")
        if not isinstance(features, list) or len(features) != csv_count:
            raise ValueError(f"SEAD candidate normalized counts differ: {stem}")
    normalized_site_identities = validate_normalized_surface_identities(root)
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
    validate_discovery_surface_identities(
        root=root,
        normalized_site_identities=normalized_site_identities,
        discovery_sites=discovery_sites,
        features=features,
    )
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
