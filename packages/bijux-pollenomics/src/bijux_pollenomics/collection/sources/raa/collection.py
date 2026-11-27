from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

from ....core.files import write_json, write_text
from ....core.filesystem import BoundedInputTree
from ....core.geospatial.geojson import as_mapping
from ....core.http import fetch_text
from ....core.text import clean_optional_text
from ...contracts.artifacts import (
    RAA_DENSITY_GEOJSON,
    RAA_DENSITY_MEMBERSHIP,
    RAA_LAYER_METADATA,
)
from .density_membership import semantic_payload_sha256
from .inventory import (
    declared_population,
    decode_source_object,
    non_negative_count,
    validate_inventory,
)
from .outputs import (
    RAA_FEATURE_TYPE,
    RAA_WFS_URL,
    build_raa_density_geojson,
    build_raa_inventory_summary,
    count_raa_features,
    fetch_raa_archaeology_metadata,
    iter_raa_features,
)
from .page_observation import (
    MAX_CAPTURE_BYTES,
    MAX_FEATURES,
    MAX_FILTER_BYTES,
    MAX_PAGE_BYTES,
    MAX_PAGES,
    RaaInventoryObservation,
    RaaObservedInventory,
    RaaPageObservation,
    bounded_json_identity,
    validate_raa_page_observation,
)

RAA_FEATURE_PAGE_SIZE = 10000
RAA_FEATURE_SORT_KEY = "lamningsnummer"
_RAA_REQUESTED_CRS_NAMES = frozenset({"EPSG:4326", "urn:ogc:def:crs:EPSG::4326"})


@dataclass(frozen=True)
class RaaDataReport:
    output_dir: Path
    total_site_count: int
    heritage_site_count: int
    metadata_path: Path
    density_path: Path
    raw_points_path: Path


def fetch_raa_feature_page(
    *,
    start_index: int,
    count: int = RAA_FEATURE_PAGE_SIZE,
    cql_filter: str | None = None,
) -> Mapping[str, object]:
    """Fetch one page of published archaeology point features as GeoJSON."""
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": RAA_FEATURE_TYPE,
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "startIndex": str(start_index),
        "count": str(count),
        "sortBy": RAA_FEATURE_SORT_KEY,
    }
    if cql_filter:
        params["CQL_FILTER"] = cql_filter
    return decode_source_object(fetch_text(RAA_WFS_URL, params=params))


def fetch_raa_feature_inventory(cql_filter: str | None = None) -> dict[str, object]:
    """Fetch WFS pages under the requested CRS; absent declarations are unverified."""
    inventory, _ = _fetch_raa_feature_inventory(cql_filter, observe=False)
    return inventory


def capture_raa_feature_inventory(
    cql_filter: str | None = None,
) -> RaaObservedInventory:
    """Return bounded self-reported decoded-page observations with the inventory.

    Page hashes do not authenticate HTTP bytes, provider identity or a snapshot.
    No sidecar or inventory is written by this operation.
    """
    if cql_filter is not None and (
        not isinstance(cql_filter, str)
        or len(cql_filter.encode("utf-8")) > MAX_FILTER_BYTES
    ):
        raise ValueError("RAÄ page observation filter budget exceeded")
    inventory, pages = _fetch_raa_feature_inventory(cql_filter, observe=True)
    digest, byte_count = bounded_json_identity(inventory, MAX_CAPTURE_BYTES)
    observation = RaaInventoryObservation(
        schema_version="raa-wfs-page-observation-v1",
        endpoint=RAA_WFS_URL,
        service="WFS",
        version="2.0.0",
        request="GetFeature",
        output_format="application/json",
        feature_type=RAA_FEATURE_TYPE,
        requested_crs="EPSG:4326",
        sort_key=RAA_FEATURE_SORT_KEY,
        page_size=RAA_FEATURE_PAGE_SIZE,
        cql_filter=cql_filter or None,
        canonical_inventory_sha256=digest,
        canonical_inventory_byte_count=byte_count,
        pages=pages,
    )
    validate_raa_page_observation(inventory, observation)
    return RaaObservedInventory(inventory, observation)


def _fetch_raa_feature_inventory(
    cql_filter: str | None, *, observe: bool
) -> tuple[dict[str, object], tuple[RaaPageObservation, ...]]:
    first_page = fetch_raa_feature_page(start_index=0, cql_filter=cql_filter)
    _validate_raa_page_crs(first_page)
    features = [dict(feature) for feature in iter_raa_features(first_page)]
    total_features = declared_population(first_page)
    pages: list[RaaPageObservation] = []
    page_bytes = 0

    def record(
        page: Mapping[str, object], start: int, page_features: list[dict[str, object]]
    ) -> None:
        nonlocal page_bytes
        if not observe:
            return
        if len(pages) >= MAX_PAGES or total_features > MAX_FEATURES:
            raise ValueError("RAÄ page observation count budget exceeded")
        digest, size = bounded_json_identity(dict(page), MAX_PAGE_BYTES)
        page_bytes += size
        if page_bytes > MAX_CAPTURE_BYTES:
            raise ValueError("RAÄ page observation byte budget exceeded")
        slice_hash, _ = bounded_json_identity(page_features, MAX_PAGE_BYTES)
        crs = page.get("crs")
        state: Literal["absent", "null", "declared"] = (
            "absent" if "crs" not in page else "null" if crs is None else "declared"
        )
        name = crs["properties"]["name"] if isinstance(crs, Mapping) else None
        pages.append(
            RaaPageObservation(
                start,
                len(page_features),
                total_features,
                state,
                name,
                digest,
                size,
                slice_hash,
            )
        )

    record(first_page, 0, features)
    start_index = len(features)
    while start_index < total_features:
        if observe and len(pages) >= MAX_PAGES:
            raise ValueError("RAÄ page observation count budget exceeded")
        page = fetch_raa_feature_page(start_index=start_index, cql_filter=cql_filter)
        _validate_raa_page_crs(page)
        if declared_population(page) != total_features:
            raise ValueError("RAÄ feature paging population changed during capture")
        page_features = [dict(feature) for feature in iter_raa_features(page)]
        if not page_features:
            raise ValueError(
                "RAÄ feature paging ended before the reported numberMatched was archived"
            )
        record(page, start_index, page_features)
        features.extend(page_features)
        start_index += len(page_features)
    feature_inventory = {
        "type": "FeatureCollection",
        "features": features,
        "numberMatched": total_features,
        "crs": first_page.get("crs"),
        "timeStamp": first_page.get("timeStamp"),
    }
    validate_raa_feature_inventory(feature_inventory)
    return feature_inventory, tuple(pages)


def _validate_raa_page_crs(page: Mapping[str, object]) -> None:
    """Reject explicit CRS claims incompatible with the fixed WFS request."""
    crs = page.get("crs")
    if crs is None:
        return
    if isinstance(crs, Mapping) and crs.get("type") == "name":
        properties = crs.get("properties")
        if isinstance(properties, Mapping):
            name = properties.get("name")
            if isinstance(name, str) and name in _RAA_REQUESTED_CRS_NAMES:
                return
    raise ValueError(
        "RAÄ WFS page CRS is malformed or differs from requested EPSG:4326"
    )


def validate_raa_feature_inventory(feature_inventory: dict[str, object]) -> None:
    """Validate that archived RAÄ paging covered the reported feature inventory exactly once."""
    validate_inventory(feature_inventory)


def collect_raa_data(
    output_root: Path,
    country_boundaries: Mapping[str, Mapping[str, object]],
) -> RaaDataReport:
    """Download and write the RAÄ dataset under data/raa."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    raw_points_path = raw_dir / "publicerade_lamningar_centrumpunkt.geojson"
    feature_inventory = fetch_raa_feature_inventory()
    raw_text = json.dumps(feature_inventory, indent=2, ensure_ascii=False)
    expected_bytes = raw_text.encode("utf-8")
    write_text(raw_points_path, raw_text)
    with BoundedInputTree(
        raw_dir,
        max_bytes=len(expected_bytes),
        max_files=1,
        selected=raw_points_path.name,
    ) as raw_inputs:
        archived_bytes = raw_inputs.read(raw_points_path, max_bytes=len(expected_bytes))
        if archived_bytes != expected_bytes:
            raise ValueError(
                "RAÄ raw archive differs from its serialized source inventory"
            )
        write_json(
            raw_dir / "publicerade_lamningar_centrumpunkt_summary.json",
            build_raa_inventory_summary(feature_inventory),
        )
        metadata = fetch_raa_archaeology_metadata(
            feature_inventory=feature_inventory,
            country_boundaries=country_boundaries,
        )
        capabilities_xml = clean_optional_text(metadata.get("capabilities_xml"))
        schema_xml = clean_optional_text(metadata.get("schema_xml"))
        if not capabilities_xml or not schema_xml:
            raise ValueError(
                "RAÄ metadata must include XML capability and schema payloads"
            )
        write_text(raw_dir / "arkreg_v1_0_wfs_capabilities.xml", capabilities_xml)
        write_text(
            raw_dir / "publicerade_lamningar_centrumpunkt_schema.xml", schema_xml
        )
        write_json(raw_dir / "fornsok_domains.json", metadata.get("domain_payload", {}))
        metadata_path = RAA_LAYER_METADATA.source_path_under(output_root)
        density_path = RAA_DENSITY_GEOJSON.source_path_under(output_root)
        layer_metadata = as_mapping(metadata.get("layer_metadata"))
        density_geojson = as_mapping(metadata.get("density_geojson"))
        if layer_metadata is None or density_geojson is None:
            raise ValueError("RAÄ metadata payload is missing structured map artifacts")
        membership = as_mapping(metadata.get("density_membership"))
        if membership is None:
            raise ValueError("RAÄ metadata payload is missing density membership")
        payload_identity = as_mapping(membership.get("semantic_payload_identity"))
        if payload_identity is None or (
            payload_identity.get("feature_inventory_sha256")
            != semantic_payload_sha256(feature_inventory)
            or payload_identity.get("sweden_boundary_sha256")
            != semantic_payload_sha256(country_boundaries["Sweden"])
        ):
            raise ValueError("RAÄ density membership input identity differs")
        counts = as_mapping(layer_metadata.get("counts"))
        if counts is None:
            raise ValueError("RAÄ metadata payload is missing count statistics")

        total_count = non_negative_count(counts.get("all_published_sites"))
        heritage_count = non_negative_count(counts.get("fornlamning"))
        if total_count is None or heritage_count is None:
            raise ValueError(
                "RAÄ metadata count statistics must be nonnegative integers"
            )

        write_json(metadata_path, dict(layer_metadata))
        write_json(density_path, dict(density_geojson))
        membership_payload = deepcopy(dict(membership))
        membership_payload["raw_inventory_identity"] = {
            "path": "raw/publicerade_lamningar_centrumpunkt.geojson",
            "sha256": sha256(archived_bytes).hexdigest(),
            "byte_count": len(archived_bytes),
        }
        membership_path = RAA_DENSITY_MEMBERSHIP.source_path_under(output_root)
        membership_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(membership_path, membership_payload)

        raw_inputs.validate()
        return RaaDataReport(
            output_dir=output_root,
            total_site_count=total_count,
            heritage_site_count=heritage_count,
            metadata_path=metadata_path,
            density_path=density_path,
            raw_points_path=raw_points_path,
        )


__all__ = [
    "RaaDataReport",
    "build_raa_density_geojson",
    "collect_raa_data",
    "capture_raa_feature_inventory",
    "count_raa_features",
    "fetch_raa_archaeology_metadata",
    "fetch_raa_feature_inventory",
    "validate_raa_page_observation",
]
