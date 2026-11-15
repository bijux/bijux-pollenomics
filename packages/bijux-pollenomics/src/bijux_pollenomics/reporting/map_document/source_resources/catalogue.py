"""Adapt a pinned compact resource publication without opening native outcomes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from hashlib import sha256
import json
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    load_neotoma_resource_catalogue,
)

from .archive_reference import load_archive_reference
from .geometry import native_point, qualify_site_extents
from .models import AtlasResourceCatalogue, AtlasResourceCatalogueInput


def _object(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not all(isinstance(k, str) for k in value):
        raise ValueError(f"Atlas resource {label} must be an object")
    return value


def _native_id(value: object) -> str:
    if type(value) is not int or value <= 0:
        raise ValueError("Atlas resource native ID must be a positive integer")
    return str(value)


def _legacy_id(record: Mapping[str, object]) -> str:
    tabs = _object(record.get("tabs"), "legacy Neotoma tabs")
    overview = _object(tabs.get("overview"), "legacy Neotoma overview")
    identity = overview.get("source_site_id")
    if (
        overview.get("source_family") != "neotoma"
        or not isinstance(identity, str)
        or not identity.isascii()
        or not identity.isdigit()
        or identity.startswith("0")
        or overview.get("site_id") != f"neotoma:site:{identity}"
        or record.get("record_id") != f"neotoma:site:{identity}"
    ):
        raise ValueError("Atlas resource legacy Neotoma site identities disagree")
    return identity


def _site_variants(
    site_id: str, members: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, Any] | None, str]:
    variants: dict[str, dict[str, Any]] = {}
    membership = {}
    points = []
    for resource in members:
        metadata = _object(resource.get("metadata"), "metadata")
        native = _object(metadata.get("native_site"), "native site")
        if "siteid" in native and _native_id(native["siteid"]) != site_id:
            raise ValueError("Atlas resource native site identity differs")
        dataset = _native_id(resource["dataset_id"])
        encoded = json.dumps(native, sort_keys=True, allow_nan=False).encode()
        identity = f"neotoma:site:{site_id}:{sha256(encoded).hexdigest()}"
        point, status = native_point(native)
        points.append(point)
        if identity not in variants:
            variants[identity] = {
                "variant_id": identity,
                "native_site": deepcopy(dict(native)),
                "dataset_ids": [],
                "metadata_sources": [],
                "geography_status": status,
            }
        variants[identity]["dataset_ids"].append(dataset)
        variants[identity]["metadata_sources"].append(
            {"dataset_id": dataset, "source": deepcopy(metadata.get("source"))}
        )
        membership[dataset] = identity
    qualify_site_extents(list(variants.values()))
    present = {point for point in points if point is not None}
    # Agreement among a subset cannot authorize coordinates for the whole site.
    if len(present) > 1:
        marker, status = None, "conflicting_native_point_geographies"
    elif not present or None in points:
        marker, status = None, "native_point_unavailable"
    else:
        marker = {"type": "Point", "coordinates": list(next(iter(present)))}
        status = "native_point_consensus"
    return list(variants.values()), membership, marker, status


def load_atlas_resource_catalogue(
    source: AtlasResourceCatalogueInput,
    *,
    legacy_neotoma_records: Sequence[Mapping[str, object]] = (),
) -> AtlasResourceCatalogue:
    """Join only explicit native IDs; source metadata never changes old records.

    The independently configured manifest authenticates the compact publication.
    Native body access remains the separate resource reader's responsibility.
    Catalogue discovery roles and joined old numerical membership are distinct.
    """
    old_ids = [_legacy_id(record) for record in legacy_neotoma_records]
    if len(set(old_ids)) != len(old_ids):
        raise ValueError("Atlas resource duplicate legacy Neotoma site identity")
    raw = load_neotoma_resource_catalogue(
        source.directory,
        expected_manifest_sha256=source.expected_manifest_sha256,
        require_source_bodies=False,
    )
    if raw.get("source_family") != "neotoma":
        raise ValueError("Atlas resource source family must be Neotoma")
    by_site: dict[str, list[dict[str, Any]]] = {}
    seen = set()
    for resource in raw["resources"]:
        dataset = _native_id(resource.get("dataset_id"))
        site = _native_id(resource.get("site_id"))
        _native_id(resource.get("collection_unit_id"))
        if dataset in seen:
            raise ValueError("Atlas resource dataset identity repeats")
        seen.add(dataset)
        by_site.setdefault(site, []).append(resource)
    sites, variant_ids = [], {}
    for raw_site in raw["sites"]:
        site_id = _native_id(raw_site["site_id"])
        variants, membership, marker, status = _site_variants(site_id, by_site[site_id])
        variant_ids.update(membership)
        site = deepcopy(raw_site)
        site.pop("native_site_metadata", None)
        site.update(
            site_id=site_id,
            dataset_ids=[_native_id(v) for v in raw_site["dataset_ids"]],
            native_site_variants=variants,
            geometry_status=status,
            marker_geometry=marker,
            legacy_numerical_membership=(
                "joined_original_record" if site_id in old_ids else "not_joined"
            ),
        )
        sites.append(site)
    resources = []
    for row in raw["resources"]:
        resource = deepcopy(row)
        for key in ("dataset_id", "site_id", "collection_unit_id"):
            resource[key] = _native_id(row[key])
        resource["metadata"].pop("native_site", None)
        resource["native_site_variant_id"] = variant_ids[resource["dataset_id"]]
        resources.append(resource)
    links = tuple(
        {
            "record_id": f"neotoma:site:{identity}",
            "site_id": identity,
            "status": "matched"
            if identity in by_site
            else "site_not_in_resource_catalogue",
            "dataset_ids": [
                _native_id(row["dataset_id"]) for row in by_site.get(identity, ())
            ],
        }
        for identity in old_ids
    )
    provenance = deepcopy(
        {
            key: value
            for key, value in raw.items()
            if key not in {"resources", "sites", "summary", "capture_descriptors"}
        }
    )
    provenance.update(
        catalogue_manifest_sha256=source.expected_manifest_sha256,
        scientific_admission="not_asserted",
        native_body_access="not_requested",
        geometry_basis="consensus_of_all_resource_native_site_points",
    )
    if source.archive is not None:
        provenance["source_archive"] = load_archive_reference(
            source.archive,
            catalogue=raw,
            catalogue_manifest_sha256=source.expected_manifest_sha256,
        )
    return AtlasResourceCatalogue(
        resource_records=tuple(resources),
        site_records=tuple(sites),
        legacy_site_references=links,
        source_descriptors=deepcopy(raw["capture_descriptors"]),
        provenance=provenance,
        summary=deepcopy(raw["summary"]),
    )
