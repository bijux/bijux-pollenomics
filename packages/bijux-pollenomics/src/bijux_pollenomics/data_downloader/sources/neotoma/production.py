"""Reproducible production driver for the Neotoma relational snapshot."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import sys

from ...boundaries import (
    BOUNDARY_CODES,
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_RELEASE_PAGE_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
)
from ..boundaries.store import load_country_boundaries
from .materialization import materialize_neotoma_relational_snapshot
from .normalization import build_neotoma_site_country_decisions
from .relational import CountryAttributionInput, build_neotoma_relational_snapshot

__all__ = [
    "NeotomaProductionConfig",
    "NeotomaProductionReport",
    "load_validated_neotoma_raw_archive",
    "main",
    "run_neotoma_relational_production",
]

EXPECTED_RAW_PART_COUNT = 9
RAW_SOURCE = "Neotoma"
RAW_DATASET_TYPE = "pollen"
RAW_ENDPOINT = "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}"
RAW_ARCHIVE_LABEL = "raw/neotoma_pollen_dataset_downloads"
PRODUCTION_DRIVER_ID = "bijux-pollenomics.neotoma-relational-production"
PRODUCTION_DRIVER_VERSION = "1"
PRODUCTION_CONFIG_SCHEMA = "neotoma-relational-production-config.v1"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class NeotomaProductionConfig:
    """Content-affecting configuration included in the production build identity."""

    producer_id: str = PRODUCTION_DRIVER_ID
    producer_version: str = PRODUCTION_DRIVER_VERSION
    config_schema: str = PRODUCTION_CONFIG_SCHEMA
    rows_per_part: int = 50_000
    proximity_tolerance: float = 0.15
    raw_country_aliases: tuple[tuple[str, str], ...] = ()

    def validated(self) -> NeotomaProductionConfig:
        """Return this configuration after checking deterministic identity fields."""
        for label, value in (
            ("producer_id", self.producer_id),
            ("producer_version", self.producer_version),
            ("config_schema", self.config_schema),
        ):
            if not value.strip():
                raise ValueError(f"{label} must not be empty")
        if self.rows_per_part < 1:
            raise ValueError("rows_per_part must be at least 1")
        if not math.isfinite(self.proximity_tolerance) or self.proximity_tolerance < 0:
            raise ValueError("proximity_tolerance must be finite and non-negative")
        aliases = dict(self.raw_country_aliases)
        if len(aliases) != len(self.raw_country_aliases):
            raise ValueError("raw_country_aliases must not contain duplicate keys")
        if any(not key.strip() or not value.strip() for key, value in aliases.items()):
            raise ValueError("raw_country_aliases must contain non-empty text")
        return self


@dataclass(frozen=True)
class NeotomaProductionReport:
    """Stable gate report for one successfully published production snapshot."""

    manifest_path: str
    source_snapshot_id: str
    boundary_authority_id: str
    build_id: str
    raw_part_count: int
    raw_row_count: int
    site_count: int
    country_counts: dict[str, int]
    country_decision_counts: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable report."""
        return asdict(self)


@dataclass(frozen=True)
class _RawArchive:
    rows: tuple[dict[str, object], ...]
    source_snapshot_id: str
    part_digests: tuple[str, ...]


@dataclass(frozen=True)
class _BoundaryAuthority:
    boundaries: dict[str, dict[str, object]]
    artifact_digest: str
    version: str
    authority_id: str


def run_neotoma_relational_production(
    *,
    raw_archive_root: Path,
    boundary_root: Path,
    output_root: Path,
    approved_output_parent: Path,
    config: NeotomaProductionConfig | None = None,
) -> NeotomaProductionReport:
    """Validate all authorities, build the snapshot, and atomically publish it."""
    resolved_output = _validated_output_target(output_root, approved_output_parent)
    production_config = (config or NeotomaProductionConfig()).validated()
    raw_archive = _load_validated_raw_archive(Path(raw_archive_root))
    boundary_authority = _load_validated_boundary_authority(Path(boundary_root))
    build_id = _build_id(
        source_snapshot_id=raw_archive.source_snapshot_id,
        boundary_authority_id=boundary_authority.authority_id,
        config=production_config,
    )
    aliases = dict(production_config.raw_country_aliases)
    decisions = build_neotoma_site_country_decisions(
        raw_archive.rows,
        boundary_authority.boundaries,
        boundary_artifact_digest=boundary_authority.artifact_digest,
        boundary_version=boundary_authority.version,
        raw_country_aliases=aliases,
        proximity_tolerance=production_config.proximity_tolerance,
    )
    country_inputs: dict[object, CountryAttributionInput] = {**decisions}
    snapshot = build_neotoma_relational_snapshot(
        raw_archive.rows,
        source_snapshot_id=raw_archive.source_snapshot_id,
        build_id=build_id,
        country_by_site_id=country_inputs,
    )
    manifest_path = materialize_neotoma_relational_snapshot(
        resolved_output,
        snapshot,
        rows_per_part=production_config.rows_per_part,
    )
    reconciliation = _mapping(snapshot.get("reconciliation"), "reconciliation")
    country_reconciliation = _mapping(
        reconciliation.get("country_counts"), "country_counts"
    )
    country_counts = {
        code: _integer(
            _mapping(country_reconciliation.get(code), code).get("sites"), code
        )
        for code in ("SE", "DK", "NO", "FI", "UNASSIGNED")
    }
    attribution = _mapping(
        reconciliation.get("country_attribution_counts"),
        "country_attribution_counts",
    )
    statuses = _mapping(attribution.get("decision_statuses"), "decision_statuses")
    site_rows = snapshot.get("sites")
    if not isinstance(site_rows, list):
        raise ValueError("Relational snapshot sites must be a list")
    return NeotomaProductionReport(
        manifest_path=str(manifest_path),
        source_snapshot_id=raw_archive.source_snapshot_id,
        boundary_authority_id=boundary_authority.authority_id,
        build_id=build_id,
        raw_part_count=len(raw_archive.part_digests),
        raw_row_count=len(raw_archive.rows),
        site_count=len(site_rows),
        country_counts=country_counts,
        country_decision_counts={
            status: _integer(statuses.get(status, 0), status)
            for status in ("assigned", "review", "unassigned", "refused")
        },
    )


def load_validated_neotoma_raw_archive(
    raw_archive_root: Path,
) -> tuple[list[dict[str, object]], str]:
    """Load a checked-in nine-part archive and return rows plus its content ID."""
    archive = _load_validated_raw_archive(raw_archive_root)
    return list(archive.rows), archive.source_snapshot_id


def _load_validated_raw_archive(raw_archive_root: Path) -> _RawArchive:
    root = _validated_input_directory(raw_archive_root, "Neotoma raw archive")
    manifest_path = root / "manifest.json"
    manifest_bytes = _read_regular_file(manifest_path)
    manifest = _json_object(manifest_bytes, manifest_path)
    expected_manifest = {
        "source": RAW_SOURCE,
        "archive_dir": RAW_ARCHIVE_LABEL,
        "endpoint_template": RAW_ENDPOINT,
        "datasettype": RAW_DATASET_TYPE,
        "part_count": EXPECTED_RAW_PART_COUNT,
    }
    for field, expected in expected_manifest.items():
        _expect_equal(manifest.get(field), expected, f"raw manifest {field}")

    parts = manifest.get("parts")
    if not isinstance(parts, list) or len(parts) != EXPECTED_RAW_PART_COUNT:
        raise ValueError("Raw manifest must contain exactly nine part records")
    rows_per_part = _positive_integer(manifest.get("rows_per_part"), "rows_per_part")
    expected_files = {"manifest.json"}
    all_rows: list[dict[str, object]] = []
    all_dataset_ids: list[int] = []
    digest_records: list[dict[str, object]] = []
    for part_number, record_value in enumerate(parts, start=1):
        record = _mapping(record_value, f"raw part {part_number}")
        filename = f"part-{part_number:03d}.json"
        _expect_equal(
            record.get("filename"), filename, f"raw part {part_number} filename"
        )
        _expect_equal(
            record.get("part_number"), part_number, f"raw part {part_number} number"
        )
        if filename in expected_files:
            raise ValueError(f"Duplicate raw archive path: {filename}")
        expected_files.add(filename)
        part_path = root / filename
        part_bytes = _read_regular_file(part_path)
        part_digest = hashlib.sha256(part_bytes).hexdigest()
        recorded_digest = record.get("sha256")
        if recorded_digest is not None:
            if not isinstance(recorded_digest, str) or not _SHA256_PATTERN.fullmatch(
                recorded_digest
            ):
                raise ValueError(f"Invalid SHA-256 in raw manifest for {filename}")
            if recorded_digest != part_digest:
                raise ValueError(f"Raw part SHA-256 mismatch: {filename}")
        payload = _json_object(part_bytes, part_path)
        for field, expected in (
            ("generated_on", manifest.get("generated_on")),
            ("source", RAW_SOURCE),
            ("endpoint_template", RAW_ENDPOINT),
            ("datasettype", RAW_DATASET_TYPE),
            ("part_number", part_number),
            ("part_count", EXPECTED_RAW_PART_COUNT),
        ):
            _expect_equal(payload.get(field), expected, f"{filename} {field}")
        rows = payload.get("rows")
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise ValueError(f"Raw part rows must contain objects: {filename}")
        row_count = _non_negative_integer(record.get("row_count"), f"{filename} rows")
        _expect_equal(payload.get("row_count"), row_count, f"{filename} row_count")
        if len(rows) != row_count or row_count > rows_per_part:
            raise ValueError(f"Raw part row-count mismatch: {filename}")
        part_ids = _integer_list(
            payload.get("downloaded_dataset_ids"), f"{filename} dataset IDs"
        )
        manifest_part_ids = _integer_list(
            record.get("downloaded_dataset_ids"),
            f"raw manifest {filename} dataset IDs",
        )
        if part_ids != sorted(part_ids) or len(part_ids) != len(set(part_ids)):
            raise ValueError(
                f"Raw part dataset IDs are not unique and sorted: {filename}"
            )
        _expect_equal(manifest_part_ids, part_ids, f"{filename} manifest dataset IDs")
        _expect_equal(
            payload.get("downloaded_dataset_count"), len(part_ids), f"{filename} count"
        )
        _expect_equal(
            record.get("downloaded_dataset_count"),
            len(part_ids),
            f"{filename} manifest count",
        )
        row_ids = [_download_dataset_id(row, filename) for row in rows]
        _expect_equal(row_ids, part_ids, f"{filename} row dataset IDs")
        all_rows.extend(rows)
        all_dataset_ids.extend(part_ids)
        digest_records.append(
            {"filename": filename, "sha256": part_digest, "row_count": row_count}
        )

    actual_files = {
        path.name for path in root.iterdir() if path.is_file() or path.is_symlink()
    }
    if actual_files != expected_files:
        raise ValueError(
            "Raw archive files do not exactly match its nine-part manifest"
        )
    if len(all_dataset_ids) != len(set(all_dataset_ids)):
        raise ValueError("Raw archive contains duplicate downloaded dataset IDs")
    manifest_ids = _integer_list(
        manifest.get("downloaded_dataset_ids"), "manifest downloaded dataset IDs"
    )
    requested_ids = _integer_list(
        manifest.get("requested_dataset_ids"), "manifest requested dataset IDs"
    )
    if manifest_ids != sorted(manifest_ids) or requested_ids != sorted(requested_ids):
        raise ValueError("Raw manifest dataset IDs must be sorted")
    _expect_equal(all_dataset_ids, manifest_ids, "raw aggregate dataset IDs")
    _expect_equal(
        manifest.get("downloaded_dataset_count"), len(manifest_ids), "downloaded count"
    )
    _expect_equal(
        manifest.get("requested_dataset_count"), len(requested_ids), "request count"
    )
    _expect_equal(manifest.get("row_count"), len(all_rows), "raw aggregate row count")
    if requested_ids != manifest_ids:
        raise ValueError("Raw archive does not provide every requested dataset")
    identity = {
        "schema": "neotoma-raw-content-identity.v1",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "parts": digest_records,
    }
    return _RawArchive(
        rows=tuple(all_rows),
        source_snapshot_id=f"sha256:{_canonical_digest(identity)}",
        part_digests=tuple(str(record["sha256"]) for record in digest_records),
    )


def _load_validated_boundary_authority(boundary_root: Path) -> _BoundaryAuthority:
    root = _validated_input_directory(boundary_root, "boundary authority")
    manifest_path = root / "raw" / "source_manifest.json"
    manifest_bytes = _read_regular_file(manifest_path)
    manifest = _json_object(manifest_bytes, manifest_path)
    boundaries = load_country_boundaries(
        output_root=root,
        boundary_codes=BOUNDARY_CODES,
        natural_earth_version=NATURAL_EARTH_VERSION,
        natural_earth_admin0_url=NATURAL_EARTH_ADMIN0_URL,
        natural_earth_terms_url=NATURAL_EARTH_TERMS_URL,
    )
    if boundaries is None or set(boundaries) != set(BOUNDARY_CODES):
        raise ValueError("Pinned Nordic boundary authority is incomplete")
    expected_manifest = {
        "dataset": "Admin 0 - Countries",
        "release_page_url": NATURAL_EARTH_RELEASE_PAGE_URL,
        "feature_count": 258,
    }
    for field, expected in expected_manifest.items():
        _expect_equal(manifest.get(field), expected, f"boundary manifest {field}")
    source_digest = manifest.get("sha256")
    if not isinstance(source_digest, str) or not _SHA256_PATTERN.fullmatch(
        source_digest
    ):
        raise ValueError("Boundary source asset SHA-256 is invalid")
    _expect_equal(
        manifest.get("country_codes"), BOUNDARY_CODES, "boundary country codes"
    )
    country_artifacts = _mapping(manifest.get("country_artifacts"), "country artifacts")
    if set(country_artifacts) != set(BOUNDARY_CODES):
        raise ValueError("Boundary manifest country artifacts are not exactly Nordic")
    authority_records: list[dict[str, object]] = []
    for country in BOUNDARY_CODES:
        record = _mapping(country_artifacts.get(country), f"{country} artifact")
        path = root / "raw" / f"{country.lower()}.geojson"
        data = _read_regular_file(path)
        digest = hashlib.sha256(data).hexdigest()
        _expect_equal(record.get("path"), path.name, f"{country} boundary path")
        _expect_equal(record.get("sha256"), digest, f"{country} boundary digest")
        collection = boundaries[country]
        features = collection.get("features")
        if not isinstance(features, list):
            raise ValueError(f"Invalid {country} boundary features")
        _expect_equal(
            record.get("feature_count"), len(features), f"{country} feature count"
        )
        authority_records.append(
            {"country": country, "path": path.name, "sha256": digest}
        )

    normalized = _mapping(manifest.get("normalized_artifact"), "normalized artifact")
    normalized_relative = normalized.get("path")
    if normalized_relative != "normalized/nordic_country_boundaries.geojson":
        raise ValueError("Boundary normalized artifact path is not pinned")
    normalized_path = root / "normalized" / "nordic_country_boundaries.geojson"
    normalized_bytes = _read_regular_file(normalized_path)
    normalized_digest = hashlib.sha256(normalized_bytes).hexdigest()
    _expect_equal(
        normalized.get("sha256"), normalized_digest, "normalized boundary digest"
    )
    normalized_payload = _json_object(normalized_bytes, normalized_path)
    _expect_equal(
        normalized_payload.get("type"), "FeatureCollection", "normalized type"
    )
    features = normalized_payload.get("features")
    if not isinstance(features, list):
        raise ValueError("Normalized boundary features must be a list")
    _expect_equal(
        normalized.get("feature_count"), len(features), "normalized feature count"
    )
    if len(features) != len(BOUNDARY_CODES):
        raise ValueError(
            "Normalized boundary authority must have four country features"
        )
    identity = {
        "schema": "nordic-boundary-authority-identity.v1",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "source_asset_sha256": manifest.get("sha256"),
        "country_artifacts": authority_records,
        "normalized_artifact_sha256": normalized_digest,
    }
    return _BoundaryAuthority(
        boundaries=boundaries,
        artifact_digest=f"sha256:{normalized_digest}",
        version=f"natural-earth:{NATURAL_EARTH_VERSION}",
        authority_id=f"sha256:{_canonical_digest(identity)}",
    )


def _build_id(
    *,
    source_snapshot_id: str,
    boundary_authority_id: str,
    config: NeotomaProductionConfig,
) -> str:
    aliases = sorted([list(item) for item in config.raw_country_aliases])
    identity = {
        "schema": "neotoma-relational-build-identity.v1",
        "source_snapshot_id": source_snapshot_id,
        "boundary_authority_id": boundary_authority_id,
        "producer": {"id": config.producer_id, "version": config.producer_version},
        "config": {
            "schema": config.config_schema,
            "rows_per_part": config.rows_per_part,
            "proximity_tolerance": config.proximity_tolerance,
            "raw_country_aliases": aliases,
        },
    }
    return f"sha256:{_canonical_digest(identity)}"


def _validated_output_target(output_root: Path, approved_parent: Path) -> Path:
    output = Path(output_root)
    parent = Path(approved_parent)
    if not output.is_absolute() or not parent.is_absolute():
        raise ValueError("Output and approved output parent must be absolute")
    resolved_parent = _validated_input_directory(parent, "approved output parent")
    if output.exists() and output.is_symlink():
        raise ValueError("Neotoma production output must not be a symlink")
    resolved_output_parent = output.parent.resolve(strict=True)
    resolved_output = (resolved_output_parent / output.name).resolve(strict=False)
    if resolved_output == resolved_parent or not resolved_output.is_relative_to(
        resolved_parent
    ):
        raise ValueError("Neotoma production output is outside its approved parent")
    return resolved_output


def _validated_input_directory(path: Path, label: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        raise ValueError(f"{label} path must be absolute")
    if candidate.is_symlink() or not candidate.is_dir():
        raise ValueError(f"{label} must be a non-symlink directory: {candidate}")
    return candidate.resolve(strict=True)


def _read_regular_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Required input is not a regular file: {path}")
    return path.read_bytes()


def _json_object(content: bytes, path: Path) -> dict[str, object]:
    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid JSON input: {path}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"JSON input must be an object: {path}")
    return payload


def _download_dataset_id(row: Mapping[str, object], filename: str) -> int:
    site = _mapping(row.get("site"), f"{filename} row site")
    unit = _mapping(site.get("collectionunit"), f"{filename} collection unit")
    dataset = _mapping(unit.get("dataset"), f"{filename} dataset")
    return _integer(dataset.get("datasetid"), f"{filename} datasetid")


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _positive_integer(value: object, label: str) -> int:
    result = _integer(value, label)
    if result < 1:
        raise ValueError(f"{label} must be positive")
    return result


def _non_negative_integer(value: object, label: str) -> int:
    result = _integer(value, label)
    if result < 0:
        raise ValueError(f"{label} must be non-negative")
    return result


def _integer_list(value: object, label: str) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return [_integer(item, label) for item in value]


def _expect_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label} mismatch: expected {expected!r}, got {actual!r}")


def _canonical_digest(payload: object) -> str:
    content = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _parse_alias(value: str) -> tuple[str, str]:
    key, separator, country = value.partition("=")
    if not separator or not key.strip() or not country.strip():
        raise argparse.ArgumentTypeError(
            "aliases must use non-empty RAW=COUNTRY values"
        )
    return key.strip(), country.strip()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and materialize the pinned Neotoma relational snapshot."
    )
    parser.add_argument("--raw-archive", required=True, type=Path)
    parser.add_argument("--boundary-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--approved-output-parent", required=True, type=Path)
    parser.add_argument("--producer-version", default=PRODUCTION_DRIVER_VERSION)
    parser.add_argument("--rows-per-part", type=int, default=50_000)
    parser.add_argument("--proximity-tolerance", type=float, default=0.15)
    parser.add_argument(
        "--raw-country-alias", action="append", default=[], type=_parse_alias
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the production gate and emit one machine-readable result line."""
    args = _parser().parse_args(argv)
    config = NeotomaProductionConfig(
        producer_version=args.producer_version,
        rows_per_part=args.rows_per_part,
        proximity_tolerance=args.proximity_tolerance,
        raw_country_aliases=tuple(args.raw_country_alias),
    )
    try:
        report = run_neotoma_relational_production(
            raw_archive_root=args.raw_archive,
            boundary_root=args.boundary_root,
            output_root=args.output,
            approved_output_parent=args.approved_output_parent,
            config=config,
        )
    except (OSError, ValueError) as error:
        print(
            json.dumps({"error": str(error), "status": "failed"}, sort_keys=True),
            file=sys.stderr,
        )
        return 1
    print(json.dumps({"status": "ok", **report.to_dict()}, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through main
    raise SystemExit(main())
