"""Governed country-boundary validation and attribution."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import cast

from bijux_pollenomics.collection.spatial import (
    COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE,
    CountryAttributionDecision,
    decide_country_attribution,
)
from bijux_pollenomics.core.geospatial.geojson import CountryBoundaryCollection

from .constants import (
    _CODE_TO_NAME,
    _COUNTRY_DECISION_CACHE,
    _NORDIC_COUNTRY_CODES,
    CountryCoverageError,
)
from .decoding import (
    _coordinate,
    _country_code,
    _features,
    _integer,
    _object,
    _require_sha256_id,
    _required_text,
    _sead_canonical_bytes,
    _sha256,
    _sha256_id_from_raw,
)


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
