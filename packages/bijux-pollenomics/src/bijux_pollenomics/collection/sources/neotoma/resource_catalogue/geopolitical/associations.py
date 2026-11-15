"""Join authenticated country selectors to inventory occurrences without admission."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any, cast

from ...capture import NeotomaMetadataCapture
from ...capture.country_authority import qualify_neotoma_country_authority
from ...capture.country_authority.protocol import qualify_native_country
from ...capture.country_authority.protocol import request_for as country_request
from ...capture.models import _Request
from ...capture.receipts import _utc
from ...client import positive_native_id
from ...relational.country import country_code

PROFILE = "neotoma-source-country-associations.v1"
_MARKER = "source_country_association_profile"
_ASSOCIATIONS = "source_country_associations"


def _same(left: object, right: object) -> bool:
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(
        right, sort_keys=True, allow_nan=False
    )


def _comparison(country: dict[str, Any], name: str) -> str:
    code = country.get("final_country_code")
    if code in (None, "UNASSIGNED"):
        return "boundary_unassigned"
    return "agrees" if country_code(name) == code else "conflicts"


def derive_associations(
    metadata_results: Mapping[str, NeotomaMetadataCapture],
    metadata_roots: Mapping[str, Path],
    authority_roots: Mapping[str, Path],
) -> dict[int, list[dict[str, Any]]]:
    """Reuse replayed inventory rows, preserving each original page and array order."""
    from ..custody import _receipt_source, pinned_object

    authorities: dict[int, tuple[dict[str, Any], dict[str, Any]]] = {}
    for digest, root in sorted(authority_roots.items()):
        qualified = qualify_neotoma_country_authority(
            root, expected_manifest_sha256=digest
        )
        manifest = pinned_object(root / "capture-manifest.json", digest, 1024 * 1024)
        for row, entry in zip(
            qualified["countries"], manifest["countries"], strict=True
        ):
            if row["qualification_status"] != "qualified_country_record":
                raise ValueError("Source country authority is not qualified")
            identity = row["native_geopolitical_id"]
            if identity in authorities:
                raise ValueError("Source country authority is ambiguous")
            reference = entry["attempts"][0]
            receipt = pinned_object(
                root / reference["receipt_file"], reference["receipt_sha256"], 65536
            )
            source = _receipt_source(digest, reference, receipt)
            source["json_pointer"] = row["native_record_pointer"]
            authorities[identity] = row["native_payload"]["data"][0], source
    occurrences: dict[
        tuple[int, int],
        dict[int, tuple[dict[str, Any], dict[str, Any], dict[str, Any]]],
    ] = {}
    for digest, captured in sorted(metadata_results.items()):
        if not captured.geopolitical_inventory_rows:
            continue
        for inventory_views in captured.geopolitical_inventory_rows.values():
            populations = [
                {
                    dataset["datasetid"]
                    for unit in rows
                    for dataset in cast(dict[str, Any], unit["site"])["datasets"]
                }
                for rows in inventory_views.values()
            ]
            if not {400, 10000} <= set(inventory_views) or any(
                population != populations[0] for population in populations
            ):
                raise ValueError("Source country inventory view population differs")
        root = metadata_roots[digest]
        manifest = pinned_object(root / "capture-manifest.json", digest, 1024 * 1024)
        for reference in manifest["records"]:
            receipt = pinned_object(
                root / reference["receipt_file"], reference["receipt_sha256"], 65536
            )
            parameters = receipt["parameters"]
            if receipt["role"] != "dataset_inventory" or "gpid" not in parameters:
                continue
            gpid, limit, offset = (
                int(parameters[key]) for key in ("gpid", "limit", "offset")
            )
            if gpid not in authorities:
                raise ValueError("Inventory source country has no qualified authority")
            rows = captured.geopolitical_inventory_rows[gpid][limit][
                offset : offset + limit
            ]
            for index, unit in enumerate(rows):
                site = cast(dict[str, Any], unit["site"])
                native_site = {
                    key: value for key, value in site.items() if key != "datasets"
                }
                for dataset_index, dataset in enumerate(site["datasets"]):
                    identity = positive_native_id(dataset["datasetid"])
                    source = _receipt_source(digest, reference, receipt)
                    source["json_pointer"] = (
                        f"/data/{index}/site/datasets/{dataset_index}"
                    )
                    views = occurrences.setdefault((gpid, identity), {})
                    if limit in views:
                        raise ValueError("Duplicate source country inventory view")
                    views[limit] = dataset, native_site, source
    result: dict[int, list[dict[str, Any]]] = {}
    for (gpid, identity), views in sorted(occurrences.items()):
        if 10000 not in views:
            raise ValueError("Source country primary 10000 inventory view is required")
        native, site, primary = views[10000]
        if any(
            not _same((native, site), (dataset, native_site))
            for dataset, native_site, _ in views.values()
        ):
            raise ValueError("Source country inventory view identity differs")
        native_country, authority = authorities[gpid]
        result.setdefault(identity, []).append(
            {
                "native_country": native_country,
                "authority_source": authority,
                "primary_inventory_source": primary,
                "other_inventory_sources": [
                    source
                    for limit, (_, _, source) in sorted(views.items())
                    if limit != 10000
                ],
                "native_dataset": native,
                "native_site": site,
            }
        )
    return result


def project_associations(
    resources: list[dict[str, Any]], witnesses: Mapping[int, list[dict[str, Any]]]
) -> None:
    """Bind source associations to exact selected metadata; never change country."""
    for row in resources:
        associations = []
        for witness in witnesses.get(row["dataset_id"], []):
            if not _same(
                witness["native_dataset"], row["metadata"]["native_dataset"]
            ) or not _same(witness["native_site"], row["metadata"]["native_site"]):
                raise ValueError(
                    "Source country association native metadata identity differs"
                )
            association = deepcopy(
                {
                    key: value
                    for key, value in witness.items()
                    if key not in {"native_dataset", "native_site"}
                }
            )
            association["association_vs_boundary"] = _comparison(
                row["country"], association["native_country"]["geopoliticalname"]
            )
            associations.append(association)
        row[_ASSOCIATIONS] = associations


def association_profile(
    resources: list[dict[str, Any]],
    authority_digests: list[str],
    inventory_digests: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": PROFILE,
        "authority_capture_manifest_sha256": sorted(authority_digests),
        "inventory_capture_manifest_sha256": sorted(inventory_digests),
        "associated_resource_count": sum(bool(row[_ASSOCIATIONS]) for row in resources),
        "association_count": sum(len(row[_ASSOCIATIONS]) for row in resources),
        "comparison_counts": dict(
            Counter(
                association["association_vs_boundary"]
                for row in resources
                for association in row[_ASSOCIATIONS]
            )
        ),
        "scientific_admission": "not_asserted",
        "territorial_or_dictionary_completeness": "not_established",
        "geometry_country_replaced": False,
    }


def validate_associations(catalogue: dict[str, Any]) -> None:
    """Validate the anchored compact namespace; raw rederivation is separate."""
    profile = catalogue.get(_MARKER)
    resources = catalogue["resources"]
    if any(
        key.startswith("source_country") and key != _MARKER for key in catalogue
    ) or any(
        key.startswith("source_country") and key != _ASSOCIATIONS
        for row in resources
        for key in row
    ):
        raise ValueError("Unknown source country association namespace")
    if profile is None:
        if (
            _MARKER in catalogue
            or any(_ASSOCIATIONS in row for row in resources)
            or any(
                descriptor["capture_kind"] == "country_authority"
                for descriptor in catalogue["capture_descriptors"].values()
            )
        ):
            raise ValueError("Source country association profile is missing")
        return
    try:
        authority_digests = profile["authority_capture_manifest_sha256"]
        inventory_digests = profile["inventory_capture_manifest_sha256"]
        for digests, kind in (
            (authority_digests, "country_authority"),
            (inventory_digests, "metadata"),
        ):
            if (
                not isinstance(digests, list)
                or digests != sorted(set(digests))
                or any(
                    catalogue["capture_descriptors"][digest]["capture_kind"] != kind
                    for digest in digests
                )
            ):
                raise ValueError("Source country capture namespace differs")
        if set(authority_digests) != {
            digest
            for digest, descriptor in catalogue["capture_descriptors"].items()
            if descriptor["capture_kind"] == "country_authority"
        }:
            raise ValueError("Source country authority descriptor population differs")
        for row in resources:
            associations = row[_ASSOCIATIONS]
            if not isinstance(associations, list):
                raise ValueError("Source country associations must be an array")
            identities = []
            for association in associations:
                if set(association) != {
                    "native_country",
                    "authority_source",
                    "primary_inventory_source",
                    "other_inventory_sources",
                    "association_vs_boundary",
                }:
                    raise ValueError("Source country association fields differ")
                native = association["native_country"]
                identity = qualify_native_country(
                    native["geopoliticalname"], {"status": "success", "data": [native]}
                )
                identities.append(identity)
                if association["association_vs_boundary"] != _comparison(
                    row["country"], native["geopoliticalname"]
                ):
                    raise ValueError("Source country comparison differs")
                _validate_source(
                    association["authority_source"],
                    authority_digests,
                    {
                        "gpname": native["geopoliticalname"],
                        "rank": "1",
                        "lower": "false",
                    },
                    "/data/0",
                )
                inventory = [
                    association["primary_inventory_source"],
                    *association["other_inventory_sources"],
                ]
                limits = []
                for index, source in enumerate(inventory):
                    params = source["parameters"]
                    if (
                        set(params) != {"gpid", "limit", "offset"}
                        or params["gpid"] != str(identity)
                        or index == 0
                        and params["limit"] != "10000"
                    ):
                        raise ValueError("Source country inventory scope differs")
                    limit, offset = int(params["limit"]), int(params["offset"])
                    if (
                        limit <= 0
                        or offset < 0
                        or offset % limit
                        or not re.fullmatch(
                            r"/data/(0|[1-9][0-9]*)/site/datasets/(0|[1-9][0-9]*)",
                            source["json_pointer"],
                        )
                    ):
                        raise ValueError("Source country inventory pointer differs")
                    limits.append(limit)
                    _validate_source(
                        source, inventory_digests, params, source["json_pointer"]
                    )
                if len(limits) != len(set(limits)):
                    raise ValueError("Duplicate source country inventory limits")
                for source in [association["authority_source"], *inventory]:
                    descriptor = catalogue["capture_descriptors"][
                        source["capture_manifest_sha256"]
                    ]
                    members = {member["name"]: member for member in descriptor["files"]}
                    if (
                        members[source["body_file"]]["sha256"] != source["body_sha256"]
                        or members[source["receipt_file"]]["sha256"]
                        != source["receipt_sha256"]
                    ):
                        raise ValueError("Source country descriptor witness differs")
            if identities != sorted(set(identities)):
                raise ValueError("Source country identities are ambiguous")
        if not _same(
            profile,
            association_profile(resources, authority_digests, inventory_digests),
        ):
            raise ValueError("Source country association profile account differs")
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Source country association namespace is malformed") from error


def _validate_source(
    source: dict[str, Any], digests: list[str], parameters: dict[str, str], pointer: str
) -> None:
    required = {
        "capture_manifest_sha256",
        "request_name",
        "receipt_file",
        "receipt_sha256",
        "body_file",
        "body_sha256",
        "requested_url",
        "request_method",
        "parameters",
        "role",
        "expected_site_id",
        "utc_start",
        "utc_end",
        "tls_mode",
        "json_pointer",
    }
    if (
        set(source) != required
        or source["capture_manifest_sha256"] not in digests
        or source["request_method"] != "GET"
        or source["parameters"] != parameters
        or source["json_pointer"] != pointer
    ):
        raise ValueError("Source country source witness fields differ")
    if any(
        not isinstance(source[key], str)
        or re.fullmatch(r"[0-9a-f]{64}", source[key]) is None
        for key in ("body_sha256", "receipt_sha256")
    ):
        raise ValueError("Source country source witness digest differs")
    if "gpname" in parameters:
        request = country_request(parameters["gpname"])
    else:
        request = _Request(
            f"inventory-gpid-{parameters['gpid']}-limit-{parameters['limit']}-offset-{parameters['offset']}",
            "dataset_inventory",
            "/datasets",
            {key: parameters[key] for key in ("gpid", "limit", "offset")},
        )
    if (
        source["requested_url"] != request.url
        or source["role"] != request.role
        or source["request_name"] != request.name
        or source["expected_site_id"] is not None
        or source["tls_mode"] != "verified_no_insecure_fallback"
        or source["body_file"] != f"{request.name}.body"
        or source["receipt_file"] != f"{request.name}.receipt.json"
        or _utc(source["utc_start"]) > _utc(source["utc_end"])
    ):
        raise ValueError("Source country request or UTC witness differs")


def verify_associations(
    catalogue: dict[str, Any],
    metadata_results: Mapping[str, NeotomaMetadataCapture],
    sources: Mapping[str, Path],
) -> None:
    """Rederive the complete selected projection from authenticated source owners."""
    validate_associations(catalogue)
    if _MARKER not in catalogue:
        return
    profile = catalogue[_MARKER]
    authority_roots = {
        digest: sources[digest]
        for digest in profile["authority_capture_manifest_sha256"]
    }
    expected = derive_associations(metadata_results, sources, authority_roots)
    rows = deepcopy(catalogue["resources"])
    project_associations(rows, expected)
    if not _same(
        [row[_ASSOCIATIONS] for row in rows],
        [row[_ASSOCIATIONS] for row in catalogue["resources"]],
    ):
        raise ValueError(
            "Source country associations differ from retained source witnesses"
        )
    inventories = sorted(
        digest
        for digest, result in metadata_results.items()
        if result.geopolitical_inventory_rows
    )
    if profile["inventory_capture_manifest_sha256"] != inventories:
        raise ValueError("Source country inventory capture population differs")
