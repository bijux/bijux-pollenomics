"""Collector observations of decoded pages, not HTTP or provider attestation.

Budgets account for canonical JSON after decoding, not transport, memory or CPU.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Literal

from .inventory import declared_population, validate_inventory

MAX_PAGES = 1024
MAX_FEATURES = 1_000_000
MAX_PAGE_BYTES = 32 * 1024 * 1024
MAX_CAPTURE_BYTES = 256 * 1024 * 1024
MAX_FILTER_BYTES = 4096
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def bounded_json_identity(value: object, maximum: int) -> tuple[str, int]:
    """Hash canonical decoded JSON under a finite encoded-byte budget."""
    digest = sha256()
    count = 0
    encoder = json.JSONEncoder(
        sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )
    for piece in encoder.iterencode(value):
        raw = piece.encode("utf-8")
        count += len(raw)
        if count > maximum:
            raise ValueError("RAÄ page observation byte budget exceeded")
        digest.update(raw)
    return digest.hexdigest(), count


@dataclass(frozen=True, slots=True)
class RaaPageObservation:
    """One self-reported decoded response and its assembled feature slice."""

    start: int
    count: int
    population: int
    crs_state: Literal["absent", "null", "declared"]
    crs_name: str | None
    canonical_page_sha256: str
    canonical_page_byte_count: int
    canonical_feature_slice_sha256: str


@dataclass(frozen=True, slots=True)
class RaaInventoryObservation:
    """Collector account: hashes do not prove page metadata or HTTP origin."""

    schema_version: str
    endpoint: str
    service: str
    version: str
    request: str
    output_format: str
    feature_type: str
    requested_crs: str
    sort_key: str
    page_size: int
    cql_filter: str | None
    canonical_inventory_sha256: str
    canonical_inventory_byte_count: int
    pages: tuple[RaaPageObservation, ...]


@dataclass(frozen=True, slots=True)
class RaaObservedInventory:
    """The unchanged inventory and a separate opt-in observation."""

    inventory: dict[str, object]
    observation: RaaInventoryObservation


def validate_raa_page_observation(
    inventory: Mapping[str, object], observation: RaaInventoryObservation
) -> None:
    """Reconcile slices and inventory; revalidate whenever the inventory is used.

    Later page declarations and decoded-page hashes cannot be independently
    checked without retained pages and remain collector-reported.
    """
    from .collection import RAA_FEATURE_PAGE_SIZE, RAA_FEATURE_SORT_KEY
    from .outputs import RAA_FEATURE_TYPE, RAA_WFS_URL

    if (
        type(observation) is not RaaInventoryObservation
        or observation.schema_version != "raa-wfs-page-observation-v1"
        or observation.endpoint != RAA_WFS_URL
        or observation.service != "WFS"
        or observation.version != "2.0.0"
        or observation.request != "GetFeature"
        or observation.output_format != "application/json"
        or observation.feature_type != RAA_FEATURE_TYPE
        or observation.requested_crs != "EPSG:4326"
        or observation.sort_key != RAA_FEATURE_SORT_KEY
        or observation.page_size != RAA_FEATURE_PAGE_SIZE
        or (
            observation.cql_filter is not None
            and (
                not isinstance(observation.cql_filter, str)
                or len(observation.cql_filter.encode("utf-8")) > MAX_FILTER_BYTES
            )
        )
        or type(observation.pages) is not tuple
        or not 1 <= len(observation.pages) <= MAX_PAGES
    ):
        raise ValueError("RAÄ page observation profile invalid")
    features = validate_inventory(inventory)
    if len(features) > MAX_FEATURES:
        raise ValueError("RAÄ page observation feature budget exceeded")
    identity, byte_count = bounded_json_identity(dict(inventory), MAX_CAPTURE_BYTES)
    if (identity, byte_count) != (
        observation.canonical_inventory_sha256,
        observation.canonical_inventory_byte_count,
    ):
        raise ValueError("RAÄ page observation inventory identity differs")
    total = declared_population(inventory)
    offset = 0
    page_bytes = 0
    for page in observation.pages:
        if (
            type(page) is not RaaPageObservation
            or type(page.start) is not int
            or page.start != offset
            or type(page.count) is not int
            or page.count < 0
            or type(page.population) is not int
            or page.population != total
            or (page.count == 0 and not (total == 0 and len(observation.pages) == 1))
            or offset + page.count > total
            or page.crs_state not in ("absent", "null", "declared")
            or (
                page.crs_state == "declared"
                and page.crs_name not in ("EPSG:4326", "urn:ogc:def:crs:EPSG::4326")
            )
            or (page.crs_state != "declared" and page.crs_name is not None)
            or not isinstance(page.canonical_page_sha256, str)
            or _DIGEST.fullmatch(page.canonical_page_sha256) is None
            or type(page.canonical_page_byte_count) is not int
            or not 0 < page.canonical_page_byte_count <= MAX_PAGE_BYTES
        ):
            raise ValueError("RAÄ page observation is invalid")
        if offset == 0:
            first_crs = inventory.get("crs")
            if page.crs_state == "declared":
                properties = (
                    first_crs.get("properties")
                    if isinstance(first_crs, Mapping)
                    else None
                )
                if (
                    not isinstance(first_crs, Mapping)
                    or first_crs.get("type") != "name"
                    or not isinstance(properties, Mapping)
                    or properties.get("name") != page.crs_name
                ):
                    raise ValueError("RAÄ first page CRS differs from inventory")
            elif first_crs is not None:
                raise ValueError("RAÄ first page CRS differs from inventory")
        page_bytes += page.canonical_page_byte_count
        if page_bytes > MAX_CAPTURE_BYTES:
            raise ValueError("RAÄ page observation byte budget exceeded")
        slice_hash, _ = bounded_json_identity(
            features[offset : offset + page.count], MAX_PAGE_BYTES
        )
        if slice_hash != page.canonical_feature_slice_sha256:
            raise ValueError("RAÄ page observation feature slice differs")
        offset += page.count
    if offset != total:
        raise ValueError("RAÄ page observation does not cover inventory")
