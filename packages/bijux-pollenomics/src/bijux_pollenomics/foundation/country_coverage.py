"""Build the governed cross-source country and dimension coverage ledger."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from contextlib import suppress
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
from typing import Any, Final, cast

from ..core.geojson import CountryBoundaryCollection
from ..data_downloader.spatial import (
    COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE,
    CountryAttributionDecision,
    decide_country_attribution,
)

COUNTRIES: Final = ("SE", "DK", "NO", "FI", "UNASSIGNED", "OUTSIDE")
COUNTRY_DIMENSIONS: Final = (
    "source_reported",
    "governed_assignment",
    "publication",
)
SOURCE_FAMILIES: Final = (
    "landclim",
    "neotoma",
    "sead",
    "raa",
    "boundaries",
    "svar",
    "aadr",
    "animal_adna",
)
PRODUCER_VERSION: Final = "1"
LEDGER_SCHEMA_VERSION: Final = "country-dimension-coverage-ledger.v1"
CELL_SCHEMA_ID: Final = "https://bijux.io/schemas/pollenomics/country-coverage.v2.json"
CELL_SCHEMA_SHA256: Final = (
    "9e1763379825d3868c743d19e54ec0cac8d8b15cc5e9d335872f4f346e7259bf"
)
BOUNDARY_METHOD: Final = "natural-earth-5.1.1-strict-containment-with-review.v1"
PUBLICATION_METHOD: Final = "product-country-publication-partition.v1"
BOUNDARY_ARTIFACT_PATH: Final = (
    "data/boundaries/normalized/nordic_country_boundaries.geojson"
)
SEAD_ACQUISITION_ROOT: Final = (
    "data/sead/raw/acquisitions/"
    "sead-live-d1fd2058913372eda1c12e526e0eb7c8a6cec415e9f9e9b5b92b8896597b35ac"
)
SEAD_ADMISSION_PATH: Final = f"{SEAD_ACQUISITION_ROOT}/admission.json"
SEAD_DECISIONS_PATH: Final = f"{SEAD_ACQUISITION_ROOT}/country-decisions.json"
SEAD_SITES_PATH: Final = f"{SEAD_ACQUISITION_ROOT}/payloads/tbl_sites.json"
SEAD_CLAIMS_PATH: Final = "data/sead/normalized/chronology_claims.json"
SEAD_PUBLIC_SITES_PATH: Final = "data/sead/normalized/nordic_environmental_sites.geojson"
COUNTRY_COVERAGE_OUTPUT_PATH: Final = "data/country_dimension_coverage.json"
COUNTRY_COVERAGE_ARTIFACT_ROOT: Final = "artifacts/execution-control/country-coverage"

COUNT_FIELDS: Final = (
    "requested_records",
    "received_records",
    "deduplicated_records",
    "failed_records",
    "accepted_records",
    "excluded_records",
    "unresolved_records",
    "published_records",
    "sites",
    "datasets",
    "collection_units",
    "samples",
    "dated_samples",
    "age_claims",
    "observations",
    "distinct_taxa",
    "mapped_taxa",
    "ambiguous_taxa",
    "unmapped_taxa",
    "events",
    "evaluated_pairs",
    "definite_candidates",
    "possible_candidates",
    "indeterminate_order_pairs",
    "unresolved_pairs",
    "excluded_pairs",
    "refused_pre_candidate_pairs",
)

INPUT_PATHS: Final = (
    "data/source_family_evidence_stage_matrix.json",
    "data/collection_summary.json",
    "data/boundaries/raw/source_manifest.json",
    "data/landclim/normalized/nordic_pollen_site_sequences.geojson",
    "data/neotoma/relational/reconciliation.json",
    SEAD_ADMISSION_PATH,
    SEAD_DECISIONS_PATH,
    SEAD_SITES_PATH,
    "docs/report/regions/nordic/nordic_pollen_site_sequences.geojson",
    "docs/report/regions/nordic/nordic_pollen_sites.geojson",
    "docs/report/countries/sweden/sweden_aadr_v66_summary.json",
    "docs/report/countries/denmark/denmark_aadr_v66_summary.json",
    "docs/report/countries/norway/norway_aadr_v66_summary.json",
    "docs/report/countries/finland/finland_aadr_v66_summary.json",
    "docs/report/animal_country_species_coverage.json",
    BOUNDARY_ARTIFACT_PATH,
    SEAD_CLAIMS_PATH,
    SEAD_PUBLIC_SITES_PATH,
)

_NAME_TO_CODE: Final = {
    "Sweden": "SE",
    "Denmark": "DK",
    "Norway": "NO",
    "Finland": "FI",
    "SE": "SE",
    "SWE": "SE",
    "SWE (Sweden)": "SE",
    "DK": "DK",
    "DK (Denmark)": "DK",
    "NO": "NO",
    "NOR": "NO",
    "NOR (Norway)": "NO",
    "FI": "FI",
    "FIN": "FI",
    "FIN (Finland)": "FI",
    "UNASSIGNED": "UNASSIGNED",
    "OUTSIDE": "OUTSIDE",
}
_RAW_SHA256_PATTERN: Final = re.compile(r"[0-9a-f]{64}\Z")
_SHA256_ID_PATTERN: Final = re.compile(r"sha256:[0-9a-f]{64}\Z")
_UUID_PATTERN: Final = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z"
)
_NORDIC_COUNTRY_CODES: Final = ("SE", "DK", "NO", "FI")
_CODE_TO_NAME: Final = {
    "SE": "Sweden",
    "DK": "Denmark",
    "NO": "Norway",
    "FI": "Finland",
}
_STAGE_STATUS_VALUES: Final = {"present", "missing", "refused"}
_AUTHORITY_STATUS_VALUES: Final = {
    "not_required",
    "refused",
    "review_required",
}
_COUNTRY_DECISION_CACHE: dict[
    tuple[str, str, float, float], CountryAttributionDecision
] = {}


class CountryCoverageError(ValueError):
    """Raised when governed coverage evidence cannot be reconciled."""


def build_country_dimension_coverage_ledger(
    repository_root: Path, *, cell_schema_path: Path
) -> dict[str, object]:
    """Build and validate a deterministic ledger from current governed artifacts."""
    root = repository_root.resolve(strict=True)
    schema_path = _regular_path_without_symlinks(
        cell_schema_path, "country coverage schema"
    )
    schema_bytes = schema_path.read_bytes()
    if _sha256(schema_bytes) != CELL_SCHEMA_SHA256:
        raise CountryCoverageError("country coverage schema content is not governed v2")
    schema = _decode_object(schema_bytes, "country coverage schema")
    if schema.get("$id") != CELL_SCHEMA_ID:
        raise CountryCoverageError("country coverage schema identity is not v2")

    input_bytes = {path: _read_governed_input(root, path) for path in INPUT_PATHS}
    input_documents = {
        path: _decode_object(payload, (root / path).as_posix())
        for path, payload in input_bytes.items()
    }
    inputs = [
        {
            "path": path,
            "sha256": _sha256(input_bytes[path]),
            "byte_count": len(input_bytes[path]),
        }
        for path in INPUT_PATHS
    ]
    producer_path = Path(__file__).resolve()
    producer = {
        "path": producer_path.relative_to(root).as_posix(),
        "version": PRODUCER_VERSION,
        "sha256": _sha256(producer_path.read_bytes()),
    }
    configuration = {
        "cell_schema_id": CELL_SCHEMA_ID,
        "countries": list(COUNTRIES),
        "country_dimensions": list(COUNTRY_DIMENSIONS),
        "source_families": list(SOURCE_FAMILIES),
        "count_fields": list(COUNT_FIELDS),
        "input_paths": list(INPUT_PATHS),
    }
    config_digest = f"sha256:{_sha256(_canonical_bytes(configuration))}"
    identity = {
        "cell_schema_sha256": _sha256(schema_bytes),
        "config_digest": config_digest,
        "inputs": inputs,
        "producer": producer,
    }
    build_id = f"sha256:{_sha256(_canonical_bytes(identity))}"

    stage_sequence = _rows(
        input_documents["data/source_family_evidence_stage_matrix.json"],
        "source stage matrix",
    )
    stage_keys = tuple(_required_text(row, "source_key") for row in stage_sequence)
    if len(stage_keys) != len(set(stage_keys)):
        raise CountryCoverageError("source stage matrix contains duplicate source keys")
    if stage_keys != SOURCE_FAMILIES:
        raise CountryCoverageError("source stage matrix order or inventory changed")
    _validate_stage_rows(stage_sequence)
    stage_rows = dict(zip(stage_keys, stage_sequence, strict=True))
    collection = input_documents["data/collection_summary.json"]
    boundary_manifest = input_documents["data/boundaries/raw/source_manifest.json"]
    boundary_raw_digest = _required_text(
        boundary_manifest, "normalized_artifact", "sha256"
    )
    boundary_digest = _sha256_id_from_raw(
        boundary_raw_digest,
        "boundary artifact digest",
    )
    if _sha256(input_bytes[BOUNDARY_ARTIFACT_PATH]) != boundary_raw_digest:
        raise CountryCoverageError("boundary artifact digest does not match its bytes")

    boundary_collections, boundary_counts, boundary_version = (
        _validate_boundary_evidence(
            boundary_manifest,
            input_documents[BOUNDARY_ARTIFACT_PATH],
        )
    )

    evidence = _coverage_evidence(
        input_documents,
        input_bytes=input_bytes,
        boundary_digest=boundary_digest,
        boundary_version=boundary_version,
        boundary_collections=boundary_collections,
        boundary_counts=boundary_counts,
    )
    snapshot_ids = _source_snapshot_ids(collection, input_documents, input_bytes)
    cells: list[dict[str, object]] = []
    for source_family in SOURCE_FAMILIES:
        stage = stage_rows[source_family]
        for dimension in COUNTRY_DIMENSIONS:
            for country_code in COUNTRIES:
                cells.append(
                    _cell(
                        source_family=source_family,
                        dimension=dimension,
                        country_code=country_code,
                        evidence=evidence,
                        stage=stage,
                        snapshot_id=snapshot_ids[source_family],
                        boundary_digest=boundary_digest,
                        config_digest=config_digest,
                        build_id=build_id,
                    )
                )

    _validate_cells(cells, schema)
    _validate_reconciliation(cells)
    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "cell_schema_id": CELL_SCHEMA_ID,
        "cell_schema_sha256": _sha256(schema_bytes),
        "producer": producer,
        "config_digest": config_digest,
        "build_id": build_id,
        "input_artifacts": inputs,
        "source_family_count": len(SOURCE_FAMILIES),
        "country_dimension_count": len(COUNTRY_DIMENSIONS),
        "country_partition_count": len(COUNTRIES),
        "cell_count": len(cells),
        "cells": cells,
    }


def write_country_dimension_coverage_ledger(
    repository_root: Path, *, cell_schema_path: Path, output_path: Path
) -> bytes:
    """Atomically write the ledger and return its canonical bytes."""
    root = repository_root.resolve(strict=True)
    schema_path = _regular_path_without_symlinks(
        cell_schema_path, "country coverage schema"
    )
    root_descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        destination = _safe_output_destination(
            root,
            output_path,
            protected_paths=(
                schema_path,
                Path(__file__).resolve(),
                *(root / path for path in INPUT_PATHS),
            ),
        )
        payload = _canonical_bytes(
            build_country_dimension_coverage_ledger(root, cell_schema_path=schema_path)
        )
        _write_atomic_no_follow(
            root_descriptor,
            destination.relative_to(root),
            payload,
        )
        return payload
    finally:
        os.close(root_descriptor)


def _write_atomic_no_follow(
    root_descriptor: int, relative_destination: Path, payload: bytes
) -> None:
    if not relative_destination.parts or relative_destination.name in {"", ".", ".."}:
        raise CountryCoverageError("country coverage output path is invalid")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    opened_directories: list[tuple[int, str, int, tuple[int, int]]] = []
    parent_descriptor = os.dup(root_descriptor)
    temporary_name: str | None = None
    temporary_descriptor = -1
    try:
        for component in relative_destination.parts[:-1]:
            try:
                child_descriptor = os.open(
                    component,
                    directory_flags,
                    dir_fd=parent_descriptor,
                )
            except FileNotFoundError:
                try:
                    os.mkdir(component, 0o755, dir_fd=parent_descriptor)
                    child_descriptor = os.open(
                        component,
                        directory_flags,
                        dir_fd=parent_descriptor,
                    )
                except OSError as error:
                    raise CountryCoverageError(
                        "cannot create country coverage output directory"
                    ) from error
            except OSError as error:
                raise CountryCoverageError(
                    "country coverage output path must not contain symlinks"
                ) from error
            child_status = os.fstat(child_descriptor)
            try:
                named_status = os.stat(
                    component,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
            except OSError as error:
                os.close(child_descriptor)
                raise CountryCoverageError(
                    "country coverage output ancestor changed"
                ) from error
            if not stat.S_ISDIR(named_status.st_mode) or (
                child_status.st_dev,
                child_status.st_ino,
            ) != (named_status.st_dev, named_status.st_ino):
                os.close(child_descriptor)
                raise CountryCoverageError("country coverage output ancestor changed")
            opened_directories.append(
                (
                    parent_descriptor,
                    component,
                    child_descriptor,
                    (child_status.st_dev, child_status.st_ino),
                )
            )
            parent_descriptor = child_descriptor
        _verify_open_directory_chain(opened_directories)
        destination_name = relative_destination.name
        _validate_descriptor_destination(parent_descriptor, destination_name)
        for _ in range(100):
            candidate = f".{destination_name}.{secrets.token_hex(12)}.writing"
            try:
                temporary_descriptor = os.open(
                    candidate,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=parent_descriptor,
                )
            except FileExistsError:
                continue
            temporary_name = candidate
            break
        if temporary_name is None:
            raise CountryCoverageError("cannot allocate country coverage output")
        with os.fdopen(temporary_descriptor, "wb") as stream:
            temporary_descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), 0o644)
        _verify_open_directory_chain(opened_directories)
        _validate_descriptor_destination(parent_descriptor, destination_name)
        os.replace(
            temporary_name,
            destination_name,
            src_dir_fd=parent_descriptor,
            dst_dir_fd=parent_descriptor,
        )
        temporary_name = None
        os.fsync(parent_descriptor)
    finally:
        if temporary_descriptor >= 0:
            os.close(temporary_descriptor)
        if temporary_name is not None:
            with suppress(FileNotFoundError):
                os.unlink(temporary_name, dir_fd=parent_descriptor)
        for parent, _, child, _ in reversed(opened_directories):
            os.close(child)
            if parent != root_descriptor and all(
                parent != prior_child for _, _, prior_child, _ in opened_directories
            ):
                os.close(parent)
        if not opened_directories:
            os.close(parent_descriptor)


def _verify_open_directory_chain(
    opened_directories: list[tuple[int, str, int, tuple[int, int]]],
) -> None:
    for parent_descriptor, component, _, expected_identity in opened_directories:
        try:
            named_status = os.stat(
                component,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError as error:
            raise CountryCoverageError(
                "country coverage output ancestor changed"
            ) from error
        if (
            not stat.S_ISDIR(named_status.st_mode)
            or (
                named_status.st_dev,
                named_status.st_ino,
            )
            != expected_identity
        ):
            raise CountryCoverageError("country coverage output ancestor changed")


def _validate_descriptor_destination(
    parent_descriptor: int, destination_name: str
) -> None:
    try:
        destination_status = os.stat(
            destination_name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return
    if not stat.S_ISREG(destination_status.st_mode):
        raise CountryCoverageError("country coverage output must be a regular file")
    if destination_status.st_nlink != 1:
        raise CountryCoverageError("country coverage output must not be a hard link")


def _safe_output_destination(
    root: Path, output_path: Path, *, protected_paths: tuple[Path, ...]
) -> Path:
    raw_destination = output_path if output_path.is_absolute() else root / output_path
    destination = Path(os.path.abspath(raw_destination))
    if raw_destination != destination:
        raise CountryCoverageError("country coverage output path must not use aliases")
    try:
        destination.relative_to(root)
    except ValueError as error:
        raise CountryCoverageError(
            "country coverage output must remain inside the repository"
        ) from error
    product_output = root / COUNTRY_COVERAGE_OUTPUT_PATH
    artifact_root = root / COUNTRY_COVERAGE_ARTIFACT_ROOT
    if destination != product_output and not destination.is_relative_to(artifact_root):
        raise CountryCoverageError(
            "country coverage output is not an approved product or artifact path"
        )
    _reject_symlink_components(root, destination, "country coverage output path")
    for protected_path in protected_paths:
        protected = protected_path.resolve(strict=True)
        if (
            destination == protected
            or destination in protected.parents
            or protected in destination.parents
            or (destination.exists() and destination.samefile(protected))
        ):
            raise CountryCoverageError(
                "country coverage output overlaps a governed input"
            )
    if destination.exists() and not destination.is_file():
        raise CountryCoverageError("country coverage output must be a regular file")
    if destination.exists() and destination.stat().st_nlink != 1:
        raise CountryCoverageError("country coverage output must not be a hard link")
    return destination


def _reject_symlink_components(root: Path, path: Path, label: str) -> None:
    relative = path.relative_to(root)
    current = root
    for index, part in enumerate(relative.parts):
        current /= part
        if current.is_symlink():
            raise CountryCoverageError(f"{label} must not contain symlinks")
        if (
            index < len(relative.parts) - 1
            and current.exists()
            and not current.is_dir()
        ):
            raise CountryCoverageError(f"{label} ancestor must be a directory")


def _read_governed_input(root: Path, relative_path: str) -> bytes:
    path = root / relative_path
    _reject_symlink_components(root, path, "governed input path")
    if not path.is_file():
        raise CountryCoverageError(
            f"governed input must be a regular file: {relative_path}"
        )
    try:
        return path.read_bytes()
    except OSError as error:
        raise CountryCoverageError(
            f"cannot read governed input: {relative_path}"
        ) from error


def _regular_path_without_symlinks(path: Path, label: str) -> Path:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            raise CountryCoverageError(f"{label} path must not contain symlinks")
    if not absolute.is_file():
        raise CountryCoverageError(f"{label} must be a regular file")
    return absolute


def _validate_stage_rows(rows: list[Mapping[str, object]]) -> None:
    for row in rows:
        source = _required_text(row, "source_key")
        for field in (
            "raw_status",
            "normalized_status",
            "reviewed_status",
            "published_status",
        ):
            if row.get(field) not in _STAGE_STATUS_VALUES:
                raise CountryCoverageError(
                    f"{source} source stage has unsupported {field}"
                )
        if row.get("authority_status") not in _AUTHORITY_STATUS_VALUES:
            raise CountryCoverageError(
                f"{source} source stage has unsupported authority_status"
            )
        _text_list(row.get("blocking_reasons"), f"{source} blocking reasons")
        _text_list(row.get("authority_reasons"), f"{source} authority reasons")


def _validate_boundary_evidence(
    manifest: Mapping[str, object], normalized: Mapping[str, object]
) -> tuple[CountryBoundaryCollection, dict[str, int], str]:
    normalized_record = _object(
        manifest.get("normalized_artifact"), "normalized boundary artifact"
    )
    features = _features(normalized, "normalized boundary artifact")
    if _integer(
        normalized_record.get("feature_count"), "boundary feature count"
    ) != len(features):
        raise CountryCoverageError(
            "normalized boundary feature count does not reconcile"
        )

    collections: dict[str, Mapping[str, object]] = {}
    feature_counts: Counter[str] = Counter()
    seen_codes: set[str] = set()
    for feature in features:
        properties = _object(feature.get("properties"), "boundary feature properties")
        country = _required_text(properties, "country")
        code = _country_code(country)
        if code not in _NORDIC_COUNTRY_CODES:
            raise CountryCoverageError("normalized boundary has unsupported country")
        if code in seen_codes:
            raise CountryCoverageError(
                "normalized boundary contains duplicate country alias"
            )
        seen_codes.add(code)
        canonical_name = _CODE_TO_NAME[code]
        if country != canonical_name or properties.get("name") != canonical_name:
            raise CountryCoverageError(
                "normalized boundary country identity is not canonical"
            )
        geometry = _object(feature.get("geometry"), "boundary feature geometry")
        if geometry.get("type") not in {"Polygon", "MultiPolygon"} or not isinstance(
            geometry.get("coordinates"), list
        ):
            raise CountryCoverageError("normalized boundary geometry is invalid")
        collections[canonical_name] = {
            "type": "FeatureCollection",
            "features": [feature],
        }
        feature_counts[code] += 1
    if set(seen_codes) != set(_NORDIC_COUNTRY_CODES) or len(features) != len(
        _NORDIC_COUNTRY_CODES
    ):
        raise CountryCoverageError(
            "normalized boundary country inventory must be exactly SE/DK/NO/FI"
        )

    raw_artifacts = _object(manifest.get("country_artifacts"), "boundary countries")
    manifest_counts: dict[str, int] = {}
    manifest_codes: set[str] = set()
    for country, raw_record in raw_artifacts.items():
        code = _country_code(country)
        if code not in _NORDIC_COUNTRY_CODES or code in manifest_codes:
            raise CountryCoverageError(
                "boundary manifest country inventory contains aliases or duplicates"
            )
        manifest_codes.add(code)
        record = _object(raw_record, "boundary artifact")
        _sha256_id_from_raw(
            _required_text(record, "sha256"), f"{country} boundary artifact"
        )
        manifest_counts[code] = _integer(
            record.get("feature_count"), "boundary feature count"
        )
    if manifest_codes != set(_NORDIC_COUNTRY_CODES):
        raise CountryCoverageError(
            "boundary manifest country inventory must be exactly SE/DK/NO/FI"
        )
    if manifest_counts != dict(feature_counts):
        raise CountryCoverageError(
            "boundary manifest feature counts do not match normalized boundaries"
        )
    expected_country_codes = {
        "Sweden": "SWE",
        "Denmark": "DNK",
        "Norway": "NOR",
        "Finland": "FIN",
    }
    if manifest.get("country_codes") != expected_country_codes:
        raise CountryCoverageError("boundary manifest country code inventory changed")
    version = _required_text(manifest, "version")
    return collections, manifest_counts, f"natural-earth:{version}"


def _validate_admission_copied_file(
    admission: Mapping[str, object], *, relative_path: str, payload: bytes
) -> None:
    copied = admission.get("copied_files")
    if not isinstance(copied, list) or any(
        not isinstance(item, Mapping) for item in copied
    ):
        raise CountryCoverageError("SEAD admission copied files are invalid")
    records: dict[str, Mapping[str, object]] = {}
    for item in cast(list[Mapping[str, object]], copied):
        if set(item) != {"path", "sha256", "byte_count"}:
            raise CountryCoverageError("SEAD copied file record inventory changed")
        path = _required_text(item, "path")
        if path in records:
            raise CountryCoverageError("SEAD admission copied files contain duplicates")
        _sha256_id_from_raw(_required_text(item, "sha256"), "SEAD copied file digest")
        _integer(item.get("byte_count"), "SEAD copied file byte count")
        records[path] = item
    if list(records) != sorted(records):
        raise CountryCoverageError("SEAD admission copied files are not ordered")
    expected_bundle_digest = f"sha256:{_sha256(_sead_canonical_bytes(copied))}"
    recorded_bundle_digest = _require_sha256_id(
        _required_text(admission, "acquisition_bundle_sha256"),
        "SEAD acquisition bundle",
    )
    if recorded_bundle_digest != expected_bundle_digest:
        raise CountryCoverageError("SEAD acquisition bundle digest does not reconcile")
    try:
        record = records[relative_path]
    except KeyError as error:
        raise CountryCoverageError(
            f"SEAD admission does not bind {relative_path}"
        ) from error
    if _integer(record.get("byte_count"), "SEAD copied byte count") != len(payload):
        raise CountryCoverageError(
            f"SEAD admission byte count differs for {relative_path}"
        )
    if record.get("sha256") != _sha256(payload):
        raise CountryCoverageError(f"SEAD admission digest differs for {relative_path}")


def _boundary_component_index(
    boundaries: CountryBoundaryCollection,
) -> list[tuple[str, Mapping[str, object], tuple[float, float, float, float]]]:
    index: list[
        tuple[str, Mapping[str, object], tuple[float, float, float, float]]
    ] = []
    for country, collection in boundaries.items():
        for feature in _features(collection, f"{country} normalized boundary"):
            geometry = _object(feature.get("geometry"), f"{country} boundary geometry")
            geometry_type = geometry.get("type")
            coordinates = geometry.get("coordinates")
            polygons = coordinates if geometry_type == "MultiPolygon" else [coordinates]
            if not isinstance(polygons, list):
                raise CountryCoverageError(
                    "normalized boundary coordinates are invalid"
                )
            for polygon in polygons:
                component = {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": feature.get("properties"),
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": polygon,
                            },
                        }
                    ],
                }
                index.append((country, component, _polygon_bounds(polygon)))
    if not index:
        raise CountryCoverageError("normalized boundary has no polygon components")
    return index


def _polygon_bounds(value: object) -> tuple[float, float, float, float]:
    if not isinstance(value, list) or not value:
        raise CountryCoverageError("normalized boundary polygon is invalid")
    longitudes: list[float] = []
    latitudes: list[float] = []
    for ring in value:
        if not isinstance(ring, list) or len(ring) < 4:
            raise CountryCoverageError("normalized boundary ring is invalid")
        for position in ring:
            if not isinstance(position, list) or len(position) < 2:
                raise CountryCoverageError("normalized boundary position is invalid")
            longitudes.append(_coordinate(position[0], "boundary longitude", -180, 180))
            latitudes.append(_coordinate(position[1], "boundary latitude", -90, 90))
    return min(longitudes), min(latitudes), max(longitudes), max(latitudes)


def _candidate_boundary_collections(
    longitude: float,
    latitude: float,
    index: list[tuple[str, Mapping[str, object], tuple[float, float, float, float]]],
) -> CountryBoundaryCollection:
    selected: dict[str, dict[str, object]] = {}
    tolerance = COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE
    for country, component, bounds in index:
        minimum_longitude, minimum_latitude, maximum_longitude, maximum_latitude = (
            bounds
        )
        if not (
            minimum_longitude - tolerance <= longitude <= maximum_longitude + tolerance
            and minimum_latitude - tolerance <= latitude <= maximum_latitude + tolerance
        ):
            continue
        collection = selected.setdefault(
            country, {"type": "FeatureCollection", "features": []}
        )
        cast(list[object], collection["features"]).extend(
            cast(list[object], component["features"])
        )
    return selected


def _recomputed_country_decision(
    longitude: float,
    latitude: float,
    *,
    boundary_index: list[
        tuple[str, Mapping[str, object], tuple[float, float, float, float]]
    ],
    boundary_digest: str,
    boundary_version: str,
) -> CountryAttributionDecision:
    cache_key = (boundary_digest, boundary_version, longitude, latitude)
    cached = _COUNTRY_DECISION_CACHE.get(cache_key)
    if cached is not None:
        return cached
    recomputed = decide_country_attribution(
        longitude,
        latitude,
        _candidate_boundary_collections(longitude, latitude, boundary_index),
        boundary_artifact_digest=boundary_digest,
        boundary_version=boundary_version,
    )
    if len(_COUNTRY_DECISION_CACHE) >= 32_768:
        _COUNTRY_DECISION_CACHE.clear()
    _COUNTRY_DECISION_CACHE[cache_key] = recomputed
    return recomputed


def _coverage_evidence(
    documents: Mapping[str, Mapping[str, object]],
    *,
    input_bytes: Mapping[str, bytes],
    boundary_digest: str,
    boundary_version: str,
    boundary_collections: CountryBoundaryCollection,
    boundary_counts: Mapping[str, int],
) -> dict[tuple[str, str, str], dict[str, int | None]]:
    evidence: dict[tuple[str, str, str], dict[str, int | None]] = {}

    landclim = documents[INPUT_PATHS[3]]
    reported = Counter[str]()
    for feature in _features(landclim, "LandClim normalized sites"):
        properties = _object(feature.get("properties"), "LandClim properties")
        popup = properties.get("popup_rows")
        if not isinstance(popup, list):
            raise CountryCoverageError("LandClim source country evidence is missing")
        reported_values = [
            row.get("value")
            for row in popup
            if isinstance(row, Mapping) and row.get("label") == "Reported country"
        ]
        if len(reported_values) > 1:
            raise CountryCoverageError(
                "LandClim feature contains duplicate Reported country labels"
            )
        value = reported_values[0] if reported_values else None
        code = _country_code(value)
        reported[code] += 1
    _site_partition(evidence, "landclim", "source_reported", reported)
    _site_partition(
        evidence,
        "landclim",
        "publication",
        _geojson_country_counts(documents[INPUT_PATHS[8]]),
        published=True,
    )

    neotoma = _object(
        documents["data/neotoma/relational/reconciliation.json"].get("reconciliation"),
        "Neotoma reconciliation",
    )
    attribution = _object(
        neotoma.get("country_attribution_counts"), "country attribution"
    )
    _site_partition(
        evidence,
        "neotoma",
        "source_reported",
        _integer_counts(attribution.get("raw_country_codes"), "Neotoma raw countries"),
    )
    country_rows = _object(neotoma.get("country_counts"), "Neotoma country counts")
    normalized_country_rows: dict[str, object] = {}
    for country, raw_counts in country_rows.items():
        country_code = _country_code(country)
        if country_code in normalized_country_rows:
            raise CountryCoverageError(
                "Neotoma governed countries contain a duplicate partition"
            )
        normalized_country_rows[country_code] = raw_counts
    for country, raw_counts in normalized_country_rows.items():
        counts = _object(raw_counts, f"Neotoma {country} counts")
        evidence[("neotoma", "governed_assignment", country)] = {
            **_empty_counts(),
            "accepted_records": _integer(
                counts.get("assigned_sites"), "Neotoma assigned sites"
            ),
            "excluded_records": _integer(
                counts.get("refused_sites"), "Neotoma refused sites"
            ),
            "unresolved_records": _integer(
                counts.get("review_sites"), "Neotoma review sites"
            ),
            "sites": _integer(counts.get("sites"), "Neotoma sites"),
            "datasets": _integer(counts.get("datasets"), "Neotoma datasets"),
            "collection_units": _integer(
                counts.get("collection_units"), "Neotoma collection units"
            ),
            "samples": _integer(counts.get("samples"), "Neotoma samples"),
            "age_claims": _integer(counts.get("age_claim_rows"), "Neotoma age claims"),
            "observations": _integer(
                counts.get("observation_rows"), "Neotoma observations"
            ),
        }
    if "OUTSIDE" not in normalized_country_rows:
        evidence[("neotoma", "governed_assignment", "OUTSIDE")] = {
            **_empty_counts(),
            "accepted_records": 0,
            "excluded_records": 0,
            "unresolved_records": 0,
            "sites": 0,
        }
    _site_partition(
        evidence,
        "neotoma",
        "publication",
        _geojson_country_counts(documents[INPUT_PATHS[9]]),
        published=True,
    )

    admission_document = documents[SEAD_ADMISSION_PATH]
    decision_document = documents[SEAD_DECISIONS_PATH]
    site_document = documents[SEAD_SITES_PATH]
    if site_document.get("schema_version") != "sead-table-payload.v1":
        raise CountryCoverageError("SEAD site payload schema is inconsistent")
    if site_document.get("table") != "tbl_sites":
        raise CountryCoverageError("SEAD site payload table identity is inconsistent")
    site_rows = _rows(site_document, "SEAD admitted sites")
    admitted_sites: dict[int, tuple[str, float, float]] = {}
    admitted_site_uuids: set[str] = set()
    for site_row in site_rows:
        site_id = _positive_integer(site_row.get("site_id"), "SEAD admitted site_id")
        site_uuid = _required_text(site_row, "site_uuid")
        if _UUID_PATTERN.fullmatch(site_uuid) is None:
            raise CountryCoverageError("SEAD admitted site_uuid is invalid")
        latitude = _coordinate(
            site_row.get("latitude_dd"), "SEAD admitted latitude", -90, 90
        )
        longitude = _coordinate(
            site_row.get("longitude_dd"), "SEAD admitted longitude", -180, 180
        )
        if site_id in admitted_sites or site_uuid in admitted_site_uuids:
            raise CountryCoverageError("SEAD admitted sites contain duplicate identity")
        admitted_sites[site_id] = (site_uuid, latitude, longitude)
        admitted_site_uuids.add(site_uuid)
    admission_table_counts = _object(
        admission_document.get("table_counts"), "SEAD admission table counts"
    )
    if _integer(
        admission_table_counts.get("tbl_sites"), "SEAD site payload row count"
    ) != len(site_rows):
        raise CountryCoverageError("SEAD site payload row count does not reconcile")

    decisions = _rows(decision_document, "SEAD country decisions", key="decisions")
    _site_partition(
        evidence,
        "sead",
        "source_reported",
        Counter({"UNASSIGNED": len(decisions)}),
    )
    governed = Counter[str]()
    decision_statuses = Counter[str]()
    decision_methods = Counter[str]()
    decision_country_codes = Counter[str]()
    seen_site_ids: set[int] = set()
    seen_site_uuids: set[str] = set()
    assigned_decision_sites: dict[int, tuple[str, float, float]] = {}
    bbox = _bbox(decision_document.get("bbox"), "SEAD country decision bbox")
    boundary_index = _boundary_component_index(boundary_collections)
    for record in decisions:
        if set(record) != {
            "decision",
            "governed_country_code",
            "latitude_dd",
            "longitude_dd",
            "site_id",
            "site_uuid",
        }:
            raise CountryCoverageError("SEAD country decision row inventory changed")
        site_id = _positive_integer(record.get("site_id"), "SEAD site identity")
        site_uuid = _required_text(record, "site_uuid")
        if _UUID_PATTERN.fullmatch(site_uuid) is None:
            raise CountryCoverageError("SEAD country decision site_uuid is invalid")
        if site_id in seen_site_ids or site_uuid in seen_site_uuids:
            raise CountryCoverageError(
                "SEAD country decisions contain duplicate identity"
            )
        seen_site_ids.add(site_id)
        seen_site_uuids.add(site_uuid)
        decision = _object(record.get("decision"), "SEAD country decision")
        latitude = _coordinate(
            record.get("latitude_dd"), "SEAD decision latitude", -90, 90
        )
        longitude = _coordinate(
            record.get("longitude_dd"), "SEAD decision longitude", -180, 180
        )
        if not (bbox[1] <= latitude <= bbox[3] and bbox[0] <= longitude <= bbox[2]):
            raise CountryCoverageError(
                f"SEAD country decision is outside its governed bbox: {site_id}"
            )
        decision_status = _required_text(decision, "decision_status")
        decision_method = _required_text(decision, "decision_method")
        country_code = _required_text(record, "governed_country_code")
        refusal_reason = decision.get("refusal_reason")
        if decision.get("raw_country") is not None:
            raise CountryCoverageError("SEAD country decision raw_country must be null")
        recomputed = _recomputed_country_decision(
            longitude,
            latitude,
            boundary_index=boundary_index,
            boundary_digest=boundary_digest,
            boundary_version=boundary_version,
        )
        recomputed_country_code = (
            _country_code(recomputed.derived_country)
            if recomputed.decision_status == "assigned"
            else "UNASSIGNED"
        )
        expected_decision = {
            "ambiguity_reason": recomputed.ambiguity_reason,
            "boundary_artifact_digest": recomputed.boundary_artifact_digest,
            "boundary_version": recomputed.boundary_version,
            "candidate_countries": list(recomputed.candidate_countries),
            "decision_method": recomputed.decision_method,
            "decision_status": recomputed.decision_status,
            "derived_country": recomputed.derived_country,
            "raw_country": recomputed.raw_country,
            "raw_country_comparison": recomputed.raw_country_comparison,
            "refusal_reason": recomputed.refusal_reason,
        }
        if dict(decision) != expected_decision:
            raise CountryCoverageError(
                f"SEAD country decision does not match governed geometry: {site_id}"
            )
        if country_code != recomputed_country_code:
            raise CountryCoverageError(
                f"SEAD governed country does not match governed geometry: {site_id}"
            )
        decision_statuses[decision_status] += 1
        decision_methods[decision_method] += 1
        decision_country_codes[country_code] += 1
        if decision_status == "assigned":
            assigned_decision_sites[site_id] = (site_uuid, latitude, longitude)
            governed[country_code] += 1
        elif decision_status == "review":
            if country_code != "UNASSIGNED" or refusal_reason is not None:
                raise CountryCoverageError(
                    "review SEAD country decision is inconsistent"
                )
            governed["UNASSIGNED"] += 1
        elif decision_status == "unassigned":
            if (
                country_code != "UNASSIGNED"
                or refusal_reason != "outside_governed_boundaries"
            ):
                raise CountryCoverageError(
                    "unassigned SEAD country decision is inconsistent"
                )
            governed["OUTSIDE"] += 1
        else:
            raise CountryCoverageError("unsupported SEAD country decision status")
    if assigned_decision_sites != admitted_sites:
        raise CountryCoverageError(
            "SEAD admitted site identities and coordinates do not reconcile"
        )
    assignment_payload = [
        {"site_id": site_id, "country_code": country_code}
        for site_id, country_code in sorted(
            (
                _positive_integer(record.get("site_id"), "SEAD assignment site_id"),
                _required_text(record, "governed_country_code"),
            )
            for record in decisions
        )
    ]
    country_assignment_sha256 = _sha256(_sead_canonical_bytes(assignment_payload))
    _validate_sead_country_summaries(
        admission_document,
        decision_document,
        decision_count=len(decisions),
        decision_statuses=decision_statuses,
        decision_methods=decision_methods,
        decision_country_codes=decision_country_codes,
        governed=governed,
        boundary_digest=boundary_digest,
        boundary_version=boundary_version,
        country_assignment_sha256=country_assignment_sha256,
        boundary_counts=boundary_counts,
        boundary_manifest=documents["data/boundaries/raw/source_manifest.json"],
        boundary_manifest_sha256=_sha256(
            input_bytes["data/boundaries/raw/source_manifest.json"]
        ),
    )
    _validate_admission_copied_file(
        admission_document,
        relative_path="country-decisions.json",
        payload=input_bytes[SEAD_DECISIONS_PATH],
    )
    _validate_admission_copied_file(
        admission_document,
        relative_path="payloads/tbl_sites.json",
        payload=input_bytes[SEAD_SITES_PATH],
    )
    _site_partition(evidence, "sead", "governed_assignment", governed)
    claim_document = documents[SEAD_CLAIMS_PATH]
    if claim_document.get("schema_version") != "sead-chronology-claim-bundle.v1":
        raise CountryCoverageError("SEAD chronology claim schema is inconsistent")
    if claim_document.get("acquisition_manifest_sha256") != admission_document.get(
        "acquisition_manifest_sha256"
    ):
        raise CountryCoverageError("SEAD chronology claims do not bind the admission")
    claim_country_counts = _integer_counts(
        claim_document.get("country_counts"), "SEAD claim countries"
    )
    if set(claim_country_counts) != set(_NORDIC_COUNTRY_CODES):
        raise CountryCoverageError("SEAD claim country partitions are incomplete")
    for country in ("SE", "DK", "NO", "FI"):
        counts = evidence[("sead", "governed_assignment", country)]
        counts["accepted_records"] = counts["sites"]
        counts["unresolved_records"] = 0
        counts["excluded_records"] = 0
        counts["age_claims"] = claim_country_counts[country]
    evidence[("sead", "governed_assignment", "UNASSIGNED")]["accepted_records"] = 0
    evidence[("sead", "governed_assignment", "UNASSIGNED")]["age_claims"] = 0
    evidence[("sead", "governed_assignment", "UNASSIGNED")]["unresolved_records"] = (
        governed["UNASSIGNED"]
    )
    evidence[("sead", "governed_assignment", "UNASSIGNED")]["excluded_records"] = 0
    evidence[("sead", "governed_assignment", "OUTSIDE")]["accepted_records"] = 0
    evidence[("sead", "governed_assignment", "OUTSIDE")]["age_claims"] = 0
    evidence[("sead", "governed_assignment", "OUTSIDE")]["unresolved_records"] = 0
    evidence[("sead", "governed_assignment", "OUTSIDE")]["excluded_records"] = governed[
        "OUTSIDE"
    ]
    _site_partition(
        evidence,
        "sead",
        "publication",
        _geojson_country_counts(documents[SEAD_PUBLIC_SITES_PATH]),
        published=True,
    )
    for country in _NORDIC_COUNTRY_CODES:
        evidence[("sead", "publication", country)]["age_claims"] = (
            claim_country_counts[country]
        )
    for country in ("UNASSIGNED", "OUTSIDE"):
        evidence[("sead", "publication", country)]["age_claims"] = 0

    _record_partition(evidence, "boundaries", "source_reported", boundary_counts)
    _record_partition(evidence, "boundaries", "governed_assignment", boundary_counts)
    _record_partition(
        evidence, "boundaries", "publication", boundary_counts, published=True
    )

    for country, path in (
        ("SE", INPUT_PATHS[10]),
        ("DK", INPUT_PATHS[11]),
        ("NO", INPUT_PATHS[12]),
        ("FI", INPUT_PATHS[13]),
    ):
        summary = documents[path]
        if _country_code(summary.get("country")) != country:
            raise CountryCoverageError(
                f"AADR summary country identity does not match partition: {country}"
            )
        evidence[("aadr", "publication", country)] = {
            **_empty_counts(),
            "published_records": _integer(
                summary.get("total_unique_samples"), "AADR samples"
            ),
            "sites": _integer(
                summary.get("total_unique_localities"), "AADR localities"
            ),
            "samples": _integer(summary.get("total_unique_samples"), "AADR samples"),
        }

    animal_rows = _rows(documents[INPUT_PATHS[14]], "animal coverage")
    animal_counts: Counter[str] = Counter()
    animal_sites: Counter[str] = Counter()
    animal_identities: set[tuple[str, str, str]] = set()
    for row in animal_rows:
        country = _country_code(row.get("country"))
        identity = (
            country,
            _required_text(row, "species_latin_name"),
            _required_text(row, "animal_scope"),
        )
        if identity in animal_identities:
            raise CountryCoverageError(
                "animal coverage contains duplicate evidence row"
            )
        animal_identities.add(identity)
        mapped_samples = _integer(
            row.get("mapped_sample_count"), "animal mapped samples"
        )
        sample_rows = _integer(row.get("sample_row_count"), "animal sample rows")
        unresolved_samples = _integer(
            row.get("unresolved_sample_count"), "animal unresolved samples"
        )
        exact_samples = _integer(
            row.get("exact_coordinate_sample_count"), "animal exact samples"
        )
        approximate_samples = _integer(
            row.get("approximate_coordinate_sample_count"),
            "animal approximate samples",
        )
        direct_sites = _integer(
            row.get("direct_coordinate_site_count"), "animal direct sites"
        )
        geocoded_sites = _integer(
            row.get("geocoded_site_count"), "animal geocoded sites"
        )
        if sample_rows != mapped_samples + unresolved_samples:
            raise CountryCoverageError("animal sample disposition does not reconcile")
        if mapped_samples != exact_samples + approximate_samples:
            raise CountryCoverageError("animal coordinate evidence does not reconcile")
        if mapped_samples != direct_sites + geocoded_sites:
            raise CountryCoverageError("animal mapped site evidence does not reconcile")
        for field in (
            "sample_lineage_backed_sample_count",
            "site_evidence_backed_sample_count",
            "chronology_provenance_backed_sample_count",
            "coordinate_provenance_backed_sample_count",
        ):
            if _integer(row.get(field), f"animal {field}") != mapped_samples:
                raise CountryCoverageError("animal provenance totals do not reconcile")
        animal_counts[country] += mapped_samples
        animal_sites[country] += direct_sites
    animal_partitions = ("SE", "DK", "NO", "FI") + tuple(
        country
        for country in ("UNASSIGNED", "OUTSIDE")
        if country in animal_counts or country in animal_sites
    )
    for country in animal_partitions:
        evidence[("animal_adna", "publication", country)] = {
            **_empty_counts(),
            "published_records": animal_counts[country],
            "samples": animal_counts[country],
            "sites": animal_sites[country],
        }
    return evidence


def _validate_sead_country_summaries(
    admission: Mapping[str, object],
    decisions: Mapping[str, object],
    *,
    decision_count: int,
    decision_statuses: Mapping[str, int],
    decision_methods: Mapping[str, int],
    decision_country_codes: Mapping[str, int],
    governed: Mapping[str, int],
    boundary_digest: str,
    boundary_version: str,
    country_assignment_sha256: str,
    boundary_counts: Mapping[str, int],
    boundary_manifest: Mapping[str, object],
    boundary_manifest_sha256: str,
) -> None:
    if admission.get("source_family") != "sead":
        raise CountryCoverageError("SEAD admission source family is inconsistent")
    _require_sha256_id(
        _required_text(admission, "scope_id"), "SEAD admission scope identity"
    )
    _require_sha256_id(
        _required_text(admission, "build_id"), "SEAD admission build identity"
    )
    for admission_field, decision_field in (
        ("scope_id", "input_id"),
        ("parent_run_id", "job_id"),
        ("run_id", "run_id"),
        ("build_id", "build_id"),
    ):
        if admission.get(admission_field) != decisions.get(decision_field):
            raise CountryCoverageError(
                f"SEAD admission and country decisions disagree on {admission_field}"
            )
    authority = _object(decisions.get("boundary_authority"), "boundary authority")
    if authority.get("artifact_digest") != boundary_digest:
        raise CountryCoverageError("SEAD boundary authority digest is inconsistent")
    if authority.get("normalized_artifact_sha256") != boundary_digest.removeprefix(
        "sha256:"
    ):
        raise CountryCoverageError("SEAD normalized boundary digest is inconsistent")
    if authority.get("version") != boundary_version.removeprefix("natural-earth:"):
        raise CountryCoverageError("SEAD boundary authority version is inconsistent")
    if authority.get("manifest_sha256") != boundary_manifest_sha256:
        raise CountryCoverageError("SEAD boundary manifest digest is inconsistent")
    manifest_artifacts = _object(
        boundary_manifest.get("country_artifacts"), "boundary country artifacts"
    )
    expected_country_digests = {
        _CODE_TO_NAME[code]: _required_text(
            _object(manifest_artifacts[_CODE_TO_NAME[code]], "boundary artifact"),
            "sha256",
        )
        for code in _NORDIC_COUNTRY_CODES
    }
    if authority.get("country_artifact_sha256") != dict(
        sorted(expected_country_digests.items())
    ):
        raise CountryCoverageError("SEAD country boundary digests are inconsistent")
    accounting = _object(admission.get("country_accounting"), "country accounting")
    _require_sha256_id(
        _required_text(accounting, "boundary_authority_id"),
        "SEAD boundary authority identity",
    )
    if accounting.get("boundary_authority_id") != authority.get("authority_id"):
        raise CountryCoverageError("SEAD boundary authority identity is inconsistent")
    if accounting.get("country_assignment_sha256") != country_assignment_sha256:
        raise CountryCoverageError("SEAD country assignment digest does not reconcile")

    expected_statuses = dict(sorted(decision_statuses.items()))
    if (
        _integer_counts(decisions.get("decision_status_counts"), "decision statuses")
        != expected_statuses
    ):
        raise CountryCoverageError("SEAD decision status counts do not reconcile")
    expected_methods = dict(sorted(decision_methods.items()))
    if (
        _integer_counts(decisions.get("decision_method_counts"), "decision methods")
        != expected_methods
    ):
        raise CountryCoverageError("SEAD decision method counts do not reconcile")
    expected_country_codes = dict(sorted(decision_country_codes.items()))
    if (
        _integer_counts(decisions.get("country_counts"), "decision countries")
        != expected_country_codes
    ):
        raise CountryCoverageError("SEAD decision country counts do not reconcile")
    if (
        _integer(decisions.get("bbox_site_count"), "SEAD bbox site count")
        != decision_count
    ):
        raise CountryCoverageError("SEAD bbox site count does not reconcile")

    nordic_counts = {
        country: int(governed.get(country, 0)) for country in ("SE", "DK", "NO", "FI")
    }
    expected_accounting = {
        "bbox_site_count": decision_count,
        "admitted_site_count": sum(nordic_counts.values()),
        "review_site_count": int(decision_statuses.get("review", 0)),
        "unassigned_site_count": int(decision_statuses.get("unassigned", 0)),
        "scope_excluded_count": int(decision_statuses.get("review", 0))
        + int(decision_statuses.get("unassigned", 0)),
    }
    for field, expected in expected_accounting.items():
        if _integer(accounting.get(field), f"SEAD {field}") != expected:
            raise CountryCoverageError(f"SEAD admission {field} does not reconcile")
    if (
        _integer_counts(accounting.get("country_counts"), "admitted country counts")
        != nordic_counts
    ):
        raise CountryCoverageError("SEAD admission country counts do not reconcile")
    if dict(boundary_counts) != dict.fromkeys(_NORDIC_COUNTRY_CODES, 1):
        raise CountryCoverageError("SEAD governed boundary inventory is inconsistent")
    if accounting.get("reconciles") is not True:
        raise CountryCoverageError(
            "SEAD admission country accounting is not reconciled"
        )


def _cell(
    *,
    source_family: str,
    dimension: str,
    country_code: str,
    evidence: Mapping[tuple[str, str, str], dict[str, int | None]],
    stage: Mapping[str, object],
    snapshot_id: str,
    boundary_digest: str,
    config_digest: str,
    build_id: str,
) -> dict[str, object]:
    key = (source_family, dimension, country_code)
    counts = evidence.get(key)
    reasons: list[str] = []
    assignment_method = (
        None
        if dimension == "source_reported"
        else BOUNDARY_METHOD
        if dimension == "governed_assignment"
        else PUBLICATION_METHOD
    )
    authority = str(stage.get("authority_status"))
    blocking = _text_list(stage.get("blocking_reasons"), "blocking reasons")
    authority_reasons = _text_list(stage.get("authority_reasons"), "authority reasons")
    if counts is None:
        counts = _empty_counts()
        availability = "blocked"
        lifecycle = "unavailable"
        reasons.append(f"{dimension}_partition_not_materialized")
    else:
        availability = (
            "zero_observations"
            if not any(value for value in counts.values() if value is not None)
            else "available_collected"
        )
        lifecycle = "admitted"
    if source_family in {"raa", "svar"}:
        counts = _empty_counts()
        if country_code == "SE":
            availability = "blocked"
            lifecycle = "refused"
            reasons.extend(authority_reasons)
        else:
            availability = "not_available_from_source"
            lifecycle = "unavailable"
            reasons.append("national_source_sweden_only")
    elif source_family == "boundaries":
        lifecycle = "review_required"
        reasons.extend(authority_reasons)
    elif source_family == "sead" and dimension == "governed_assignment":
        if country_code == "UNASSIGNED":
            lifecycle = "review_required"
            availability = "unresolved"
            reasons.append("boundary_assignment_review_required")
        elif country_code == "OUTSIDE":
            lifecycle = "refused"
            availability = "available_partial"
            reasons.append("outside_governed_boundaries")
    elif source_family == "aadr":
        lifecycle = "review_required"
        reasons.extend(blocking)
    if (
        dimension == "source_reported"
        and country_code == "UNASSIGNED"
        and any(value for value in counts.values() if value is not None)
    ):
        availability = "available_partial"
        reasons.append("source_country_not_reported")
    if (
        dimension == "governed_assignment"
        and country_code == "UNASSIGNED"
        and any(value for value in counts.values() if value is not None)
    ):
        availability = "unresolved"
        lifecycle = "review_required"
        reasons.append("country_assignment_review_required")
    if country_code in {"UNASSIGNED", "OUTSIDE"} and not reasons:
        if any(value for value in counts.values() if value is not None):
            reasons.append("explicit_non_nordic_partition")
        else:
            reasons.append("explicit_empty_partition")
    if authority == "refused" and lifecycle not in {"refused", "unavailable"}:
        lifecycle = "refused"
        reasons.extend(authority_reasons)
    return {
        "schema_version": "2.0.0",
        "country_code": country_code,
        "country_dimension": dimension,
        "country_assignment_method": assignment_method,
        "source_family": source_family,
        "resolution": "source",
        "feature_key": None,
        "classification_contract_version": None,
        "availability_status": availability,
        "lifecycle_status": lifecycle,
        "counts": counts,
        "reason_codes": sorted(set(reasons)),
        "source_snapshot_id": snapshot_id,
        "boundary_artifact_digest": (
            None if dimension == "source_reported" else boundary_digest
        ),
        "config_digest": config_digest,
        "producer_version": PRODUCER_VERSION,
        "build_id": build_id,
    }


def _source_snapshot_ids(
    collection: Mapping[str, object],
    documents: Mapping[str, Mapping[str, object]],
    input_bytes: Mapping[str, bytes],
) -> dict[str, str]:
    source_hashes = _object(collection.get("source_hashes"), "source hashes")
    result = {
        source: _sha256_id_from_raw(
            _required_text(_object(source_hashes[source], source), "snapshot_sha256"),
            f"{source} source snapshot",
        )
        for source in (
            "landclim",
            "neotoma",
            "sead",
            "raa",
            "boundaries",
            "svar",
            "aadr",
        )
    }
    result["neotoma"] = _require_sha256_id(
        _required_text(
            documents["data/neotoma/relational/reconciliation.json"],
            "source_snapshot_id",
        ),
        "Neotoma source snapshot",
    )
    result["sead"] = _require_sha256_id(
        _required_text(documents[INPUT_PATHS[5]], "acquisition_bundle_sha256"),
        "SEAD acquisition bundle",
    )
    result["animal_adna"] = f"sha256:{_sha256(input_bytes[INPUT_PATHS[14]])}"
    return result


def _site_partition(
    evidence: dict[tuple[str, str, str], dict[str, int | None]],
    source: str,
    dimension: str,
    values: Mapping[str, int],
    *,
    published: bool = False,
) -> None:
    unknown = set(values) - set(COUNTRIES)
    if unknown:
        raise CountryCoverageError(
            f"{source} {dimension} contains unsupported country partitions: "
            f"{sorted(unknown)}"
        )
    for country in COUNTRIES:
        value = int(values.get(country, 0))
        evidence[(source, dimension, country)] = {
            **_empty_counts(),
            "received_records": value if dimension == "source_reported" else None,
            "published_records": value if published else None,
            "sites": value,
        }


def _record_partition(
    evidence: dict[tuple[str, str, str], dict[str, int | None]],
    source: str,
    dimension: str,
    values: Mapping[str, int],
    *,
    published: bool = False,
) -> None:
    unknown = set(values) - set(COUNTRIES)
    if unknown:
        raise CountryCoverageError(
            f"{source} {dimension} contains unsupported country partitions: "
            f"{sorted(unknown)}"
        )
    for country in COUNTRIES:
        value = int(values.get(country, 0))
        evidence[(source, dimension, country)] = {
            **_empty_counts(),
            "received_records": value if dimension == "source_reported" else None,
            "accepted_records": value if dimension == "governed_assignment" else None,
            "published_records": value if published else None,
        }


def _empty_counts() -> dict[str, int | None]:
    return dict.fromkeys(COUNT_FIELDS)


def _validate_cells(
    cells: list[dict[str, object]], schema: Mapping[str, object]
) -> None:
    try:
        from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
    except ImportError as error:
        raise CountryCoverageError("jsonschema is required") from error
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for index, cell in enumerate(cells):
        errors = sorted(validator.iter_errors(cell), key=lambda item: list(item.path))
        if errors:
            raise CountryCoverageError(
                f"cell {index} violates schema: {errors[0].message}"
            )


def _validate_reconciliation(cells: list[dict[str, object]]) -> None:
    expected_keys = {
        (source, dimension, country)
        for source in SOURCE_FAMILIES
        for dimension in COUNTRY_DIMENSIONS
        for country in COUNTRIES
    }
    observed_keys = {
        (
            str(cell["source_family"]),
            str(cell["country_dimension"]),
            str(cell["country_code"]),
        )
        for cell in cells
    }
    if observed_keys != expected_keys or len(cells) != len(expected_keys):
        raise CountryCoverageError("country coverage cell inventory does not reconcile")
    if any(cell["availability_status"] == "unknown" for cell in cells):
        raise CountryCoverageError("country coverage cannot retain unknown cells")
    for cell in cells:
        counts = _object(cell.get("counts"), "country coverage counts")
        if tuple(counts) != COUNT_FIELDS:
            raise CountryCoverageError("country coverage count inventory changed")

    index = {
        (
            str(cell["source_family"]),
            str(cell["country_dimension"]),
            str(cell["country_code"]),
        ): cell
        for cell in cells
    }

    def total(source: str, dimension: str, measure: str) -> int:
        result = 0
        for country in COUNTRIES:
            counts = _object(index[(source, dimension, country)]["counts"], "counts")
            value = counts.get(measure)
            if not isinstance(value, int) or isinstance(value, bool):
                raise CountryCoverageError(
                    f"{source} {dimension} {measure} has an incomplete denominator"
                )
            result += value
        return result

    landclim_reported = total("landclim", "source_reported", "sites")
    if landclim_reported != total("landclim", "publication", "sites"):
        raise CountryCoverageError("LandClim site partitions do not reconcile")
    neotoma_reported = total("neotoma", "source_reported", "sites")
    if neotoma_reported != total("neotoma", "governed_assignment", "sites"):
        raise CountryCoverageError("Neotoma governed sites do not reconcile")
    if neotoma_reported != total("neotoma", "publication", "sites"):
        raise CountryCoverageError("Neotoma publication sites do not reconcile")
    neotoma_accounted = sum(
        total("neotoma", "governed_assignment", measure)
        for measure in ("accepted_records", "unresolved_records", "excluded_records")
    )
    if neotoma_reported != neotoma_accounted:
        raise CountryCoverageError("Neotoma admission outcomes do not reconcile")
    sead_received = total("sead", "source_reported", "received_records")
    sead_governed_sites = total("sead", "governed_assignment", "sites")
    if sead_received != sead_governed_sites:
        raise CountryCoverageError("SEAD country decisions do not reconcile")
    sead_accounted = sum(
        total("sead", "governed_assignment", measure)
        for measure in ("accepted_records", "unresolved_records", "excluded_records")
    )
    if sead_received != sead_accounted:
        raise CountryCoverageError("SEAD admission outcomes do not reconcile")
    boundary_received = total("boundaries", "source_reported", "received_records")
    if boundary_received != total(
        "boundaries", "governed_assignment", "accepted_records"
    ):
        raise CountryCoverageError("boundary admission does not reconcile")
    if boundary_received != total("boundaries", "publication", "published_records"):
        raise CountryCoverageError("boundary publication does not reconcile")


def _geojson_country_counts(document: Mapping[str, object]) -> Counter[str]:
    return Counter(
        _country_code(
            _object(feature.get("properties"), "feature properties").get("country")
        )
        for feature in _features(document, "country GeoJSON")
    )


def _features(document: Mapping[str, object], label: str) -> list[Mapping[str, object]]:
    features = document.get("features")
    if not isinstance(features, list) or any(
        not isinstance(feature, Mapping) for feature in features
    ):
        raise CountryCoverageError(f"{label} must contain feature objects")
    return cast(list[Mapping[str, object]], features)


def _integer_counts(value: object, label: str) -> dict[str, int]:
    mapping = _object(value, label)
    return {str(key): _integer(item, label) for key, item in mapping.items()}


def _country_code(value: object) -> str:
    if value is None:
        return "UNASSIGNED"
    if not isinstance(value, str):
        raise CountryCoverageError(f"unsupported country label: {value!r}")
    try:
        return _NAME_TO_CODE[value]
    except KeyError as error:
        raise CountryCoverageError(f"unsupported country label: {value!r}") from error


def _rows(
    document: Mapping[str, object], label: str, *, key: str = "rows"
) -> list[Mapping[str, object]]:
    value = document.get(key)
    if not isinstance(value, list) or any(
        not isinstance(row, Mapping) for row in value
    ):
        raise CountryCoverageError(f"{label} must contain object rows")
    return cast(list[Mapping[str, object]], value)


def _decode_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        return _object(
            json.loads(payload, object_pairs_hook=_unique_json_object), label
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CountryCoverageError(f"cannot decode governed input: {label}") from error


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CountryCoverageError(
                f"governed input contains duplicate JSON key: {key}"
            )
        result[key] = value
    return result


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CountryCoverageError(f"{label} must be an object")
    return cast(dict[str, Any], value)


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CountryCoverageError(f"{label} must be a non-negative integer")
    return value


def _positive_integer(value: object, label: str) -> int:
    result = _integer(value, label)
    if result == 0:
        raise CountryCoverageError(f"{label} must be positive")
    return result


def _coordinate(value: object, label: str, minimum: float, maximum: float) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not minimum <= value <= maximum
    ):
        raise CountryCoverageError(
            f"{label} must be a finite coordinate in [{minimum}, {maximum}]"
        )
    result = float(value)
    if not (minimum <= result <= maximum):
        raise CountryCoverageError(
            f"{label} must be a finite coordinate in [{minimum}, {maximum}]"
        )
    return result


def _bbox(value: object, label: str) -> tuple[float, float, float, float]:
    if not isinstance(value, list) or len(value) != 4:
        raise CountryCoverageError(f"{label} must have four coordinates")
    minimum_longitude = _coordinate(value[0], label, -180, 180)
    minimum_latitude = _coordinate(value[1], label, -90, 90)
    maximum_longitude = _coordinate(value[2], label, -180, 180)
    maximum_latitude = _coordinate(value[3], label, -90, 90)
    if minimum_longitude > maximum_longitude or minimum_latitude > maximum_latitude:
        raise CountryCoverageError(f"{label} bounds are reversed")
    return (
        minimum_longitude,
        minimum_latitude,
        maximum_longitude,
        maximum_latitude,
    )


def _sha256_id_from_raw(value: str, label: str) -> str:
    if _RAW_SHA256_PATTERN.fullmatch(value) is None:
        raise CountryCoverageError(f"{label} must be a lowercase SHA-256 digest")
    return f"sha256:{value}"


def _require_sha256_id(value: str, label: str) -> str:
    if _SHA256_ID_PATTERN.fullmatch(value) is None:
        raise CountryCoverageError(f"{label} must be a sha256 identity")
    return value


def _text_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise CountryCoverageError(f"{label} must be a list of non-empty strings")
    return cast(list[str], value)


def _required_text(document: Mapping[str, object], *path: str) -> str:
    value: object = document
    for key in path:
        if not isinstance(value, Mapping):
            raise CountryCoverageError(f"missing required field: {'.'.join(path)}")
        value = value.get(key)
    if not isinstance(value, str) or not value:
        raise CountryCoverageError(f"missing required field: {'.'.join(path)}")
    return value


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _sead_canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
