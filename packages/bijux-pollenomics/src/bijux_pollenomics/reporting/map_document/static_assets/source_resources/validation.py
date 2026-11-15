"""Reconcile logical resource partitions before common immutable publication."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
import re
from typing import TYPE_CHECKING, Any

from ...source_resources.archive_reference import validate_archive_reference
from ...source_resources.geometry import qualify_site_extents
from ..budgets import ATLAS_CHUNK_MAX_BYTES, ATLAS_STATIC_ASSETS_MAX_FILES
from ..serialization import (
    canonical_json,
    chunk_script_bytes,
    validate_decoded_payload_size,
)
from .ancillary.publication import ancillary_index_entry
from .ancillary.validation import (
    ANCILLARY_KINDS,
    ancillary_record_id,
    metadata_only,
    validate_ancillary_groups,
)

if TYPE_CHECKING:
    from .publication import SourceResourcePayloads

_KINDS = ("context", "sites", "resources", "descriptors", "index")


def _id(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[1-9][0-9]*", value) is None:
        raise ValueError("Source resource native ID is invalid")
    return value


def _digest(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("Source resource catalogue or descriptor digest is invalid")
    return value


def _record_id(kind: str, row: Mapping[str, Any]) -> str:
    if kind in ANCILLARY_KINDS:
        return ancillary_record_id(kind, row)
    if kind == "context":
        if row.get("record_id") != "catalogue":
            raise ValueError("Source resource catalogue context identity differs")
        return "catalogue"
    if kind == "descriptors":
        return _digest(row.get("record_id"))
    return _id(row.get("dataset_id" if kind == "resources" else "site_id"))


def _refuse_native_reader(row: Mapping[str, Any]) -> None:
    reserved = {"native_body", "native_payload"}
    versions = row.get("versions")
    if reserved.intersection(row) or (
        isinstance(versions, Mapping)
        and any(
            isinstance(value, Mapping) and reserved.intersection(value)
            for value in versions.values()
        )
    ):
        raise ValueError(
            "Source resource metadata cannot embed a native reader result or native body"
        )


def _index_entry(kind: str, row: Mapping[str, Any], part_id: str) -> dict[str, Any]:
    if kind in ANCILLARY_KINDS:
        return ancillary_index_entry(kind, row, part_id, ancillary_record_id(kind, row))
    result: dict[str, Any] = {
        "entity_type": kind,
        "record_id": _record_id(kind, row),
        "part_id": part_id,
    }
    if kind == "resources":
        _refuse_native_reader(row)
        versions = row.get("versions")
        if not isinstance(versions, Mapping) or set(versions) != {
            "current",
            "doi_frozen",
        }:
            raise ValueError("Source resource version partition differs")
        result.update(
            site_id=_id(row.get("site_id")),
            collection_unit_id=_id(row.get("collection_unit_id")),
            dataset_type=deepcopy(row.get("dataset_type")),
            exposure_role=deepcopy(row.get("exposure_role")),
            country_code=deepcopy(row["country"]["final_country_code"]),
            version_statuses={
                version: {
                    key: deepcopy(value)
                    for key, value in fields.items()
                    if key.endswith("_status")
                    and (value is None or isinstance(value, str))
                }
                for version, fields in versions.items()
            },
        )
    elif kind == "sites":
        result.update(
            country_code=deepcopy(row.get("country_code")),
            native_site_names=sorted(
                {
                    variant["native_site"]["sitename"]
                    for variant in row["native_site_variants"]
                    if isinstance(variant["native_site"].get("sitename"), str)
                }
            ),
            marker_geometry=deepcopy(row.get("marker_geometry")),
            geometry_status=deepcopy(row.get("geometry_status")),
            legacy_numerical_membership=deepcopy(
                row.get("legacy_numerical_membership")
            ),
        )
        if any(
            "extent_geometry" in variant or "extent_status" in variant
            for variant in row["native_site_variants"]
        ):
            result["native_extent_variant_ids"] = [
                variant["variant_id"]
                for variant in row["native_site_variants"]
                if variant.get("extent_status") == "explicit_native_extent"
                and variant.get("extent_geometry") is not None
            ]
    return result


def _same(left: object, right: object) -> bool:
    return canonical_json(left) == canonical_json(right)


def _ids(values: object) -> set[str]:
    if not isinstance(values, list):
        raise ValueError("Source resource native ID membership is invalid")
    result = {_id(value) for value in values}
    if len(result) != len(values):
        raise ValueError("Source resource native ID membership repeats")
    return result


def _membership(
    resources: dict[str, dict[str, Any]], sites: dict[str, dict[str, Any]]
) -> None:
    by_site: dict[str, set[str]] = defaultdict(set)
    for identity, resource in resources.items():
        site_key = _id(resource.get("site_id"))
        if site_key not in sites:
            raise ValueError("Source resource site reference is unavailable")
        by_site[site_key].add(identity)
        variants = {v["variant_id"]: v for v in sites[site_key]["native_site_variants"]}
        variant = variants.get(resource.get("native_site_variant_id"))
        if variant is None or identity not in _ids(variant["dataset_ids"]):
            raise ValueError("Source resource native site variant reference differs")
    for identity, site in sites.items():
        if _ids(site.get("dataset_ids")) != by_site[identity]:
            raise ValueError("Source resource site membership population differs")
        if any(
            "extent_geometry" in variant or "extent_status" in variant
            for variant in site["native_site_variants"]
        ):
            qualified = deepcopy(site["native_site_variants"])
            qualify_site_extents(qualified)
            if not _same(qualified, site["native_site_variants"]):
                raise ValueError("Source resource native extent profile differs")
        variant_members: list[str] = []
        for variant in site["native_site_variants"]:
            members = _ids(variant["dataset_ids"])
            if any(
                resources.get(member, {}).get("native_site_variant_id")
                != variant["variant_id"]
                for member in members
            ):
                raise ValueError("Source resource variant membership differs")
            variant_members.extend(members)
        if set(variant_members) != by_site[identity] or len(variant_members) != len(
            by_site[identity]
        ):
            raise ValueError("Source resource variant population differs")


def validate_source_resource_payloads(
    transport: SourceResourcePayloads, *, expected_catalogue_manifest_sha256: str
) -> None:
    """Refuse incomplete/ambiguous transport without opening an external source."""
    anchor = _digest(expected_catalogue_manifest_sha256)
    domain = transport.domain
    if (
        domain.get("schema_version")
        not in {"atlas-source-resources.v1", "atlas-source-resources.v2"}
        or domain.get("source_family") != "neotoma"
        or domain.get("catalogue_manifest_sha256") != anchor
        or domain.get("scientific_admission") != "not_asserted"
        or domain.get("numerical_atlas_denominator_changed") is not False
        or domain.get("initial_load") is not False
        or domain.get("payload_encoding") != "gzip_base64"
    ):
        raise ValueError("Source resource catalogue domain identity or posture differs")
    if len(transport.payloads) > ATLAS_STATIC_ASSETS_MAX_FILES:
        raise ValueError("Source resource part count exceeds the asset budget")
    parts: dict[str, dict[str, Any]] = {}
    groups: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    expected_index: list[dict[str, Any]] = []
    observed_index: list[dict[str, Any]] = []
    part_numbers: dict[str, int] = defaultdict(int)
    kinds = (
        (*_KINDS, *ANCILLARY_KINDS)
        if domain["schema_version"] == "atlas-source-resources.v2"
        else _KINDS
    )
    for payload in transport.payloads:
        kind, part_id = payload.get("kind"), payload.get("part_id")
        if (
            not isinstance(kind, str)
            or not isinstance(part_id, str)
            or kind not in kinds
            or part_id != f"{kind}:{part_numbers[kind]}"
            or part_id in parts
        ):
            raise ValueError("Source resource part identity differs or repeats")
        part_numbers[kind] += 1
        parts[part_id] = payload
        if (
            payload.get("schema_version") != "atlas-source-resource-chunk.v1"
            or payload.get("source_family") != "neotoma"
            or payload.get("catalogue_manifest_sha256") != anchor
            or payload.get("scientific_admission") != "not_asserted"
        ):
            raise ValueError(
                "Source resource part catalogue identity or schema differs"
            )
        records = payload.get("records")
        if (
            not isinstance(records, list)
            or not records
            or any(not isinstance(row, dict) for row in records)
        ):
            raise ValueError("Source resource part records are invalid")
        if kind in ANCILLARY_KINDS:
            metadata_only(payload)
        encoded = canonical_json(payload)
        validate_decoded_payload_size(encoded, asset_key=part_id)
        script = chunk_script_bytes(
            asset_key=part_id,
            payload_sha256=sha256(encoded.encode()).hexdigest(),
            payload_json=encoded,
            payload_encoding="gzip_base64",
        )
        if len(script) > ATLAS_CHUNK_MAX_BYTES:
            raise ValueError("Source resource encoded chunk exceeds its byte budget")
        if kind == "index":
            observed_index.extend(records)
            continue
        for row in records:
            identity = _record_id(kind, row)
            if identity in groups[kind]:
                raise ValueError("Source resource record identity repeats")
            groups[kind][identity] = row
            if kind != "context":
                expected_index.append(_index_entry(kind, row, part_id))
    if not _same(expected_index, observed_index):
        raise ValueError("Source resource index references do not reconcile")
    if domain.get("index_part_ids") != [
        p["part_id"] for p in transport.payloads if p["kind"] == "index"
    ]:
        raise ValueError("Source resource index part inventory differs")
    contexts = groups["context"]
    if set(contexts) != {"catalogue"}:
        raise ValueError("Source resource catalogue context population differs")
    context = contexts["catalogue"]
    if "context_part_id" in domain and domain["context_part_id"] != "context:0":
        raise ValueError("Source resource context part identity differs")
    if "source_archive" in context["provenance"]:
        validate_archive_reference(
            context["provenance"]["source_archive"], catalogue_manifest_sha256=anchor
        )
    if (
        context["provenance"].get("catalogue_manifest_sha256") != anchor
        or context["provenance"].get("source_family") != "neotoma"
    ):
        raise ValueError("Source resource original catalogue context differs")
    resources, sites = groups["resources"], groups["sites"]
    _membership(resources, sites)
    for digest, row in groups["descriptors"].items():
        if (
            row["descriptor"].get("capture_manifest_sha256") != digest
            or row["descriptor"].get("source_bodies_in_descriptor") is not False
        ):
            raise ValueError(
                "Source resource descriptor identity or body posture differs"
            )
    links = context["legacy_site_references"]
    seen_links = set()
    for link in links:
        identity = _id(link.get("site_id"))
        if (
            identity in seen_links
            or link.get("record_id") != f"neotoma:site:{identity}"
        ):
            raise ValueError("Source resource legacy identity repeats or differs")
        seen_links.add(identity)
        expected = sites.get(identity)
        if link.get("status") != (
            "matched" if expected is not None else "site_not_in_resource_catalogue"
        ) or _ids(link.get("dataset_ids")) != (
            _ids(expected["dataset_ids"]) if expected else set()
        ):
            raise ValueError("Source resource legacy site membership differs")
    counts = {
        "record_count": len(resources),
        "site_count": len(sites),
        "version_status_count": 2 * len(resources),
        "source_descriptor_count": len(groups["descriptors"]),
        "legacy_site_reference_count": len(links),
        "part_count": len(parts),
    }
    if any(
        type(domain.get(field)) is not int or domain[field] != count
        for field, count in counts.items()
    ):
        raise ValueError("Source resource declared population count differs")
    summary = context["summary"]
    if (
        type(summary.get("resource_count")) is not int
        or type(summary.get("version_status_count")) is not int
        or summary.get("resource_count") != len(resources)
        or summary.get("version_status_count") != 2 * len(resources)
        or summary.get("scientific_admission") != "not_asserted"
        or summary.get("numerical_atlas_denominator_changed") is not False
        or not _same(
            summary.get("version_status_counts"),
            dict(
                Counter(
                    version["acquisition_status"]
                    for resource in resources.values()
                    for version in resource["versions"].values()
                )
            ),
        )
        or not _same(
            summary.get("resource_role_counts"),
            dict(Counter(resource["exposure_role"] for resource in resources.values())),
        )
    ):
        raise ValueError("Source resource original summary population differs")

    if domain["schema_version"] == "atlas-source-resources.v2":
        validate_ancillary_groups(domain, groups, resources)
