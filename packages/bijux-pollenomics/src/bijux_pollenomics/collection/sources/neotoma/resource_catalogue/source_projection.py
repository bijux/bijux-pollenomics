"""Derive catalogue accounts and authenticate native metadata/source projections."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

from ..capture.resources.current.profiles import CURRENT_SOURCE_TYPES
from ..capture.resources.models import DEVELOPMENT_ROLES
from .current_profiles import current_profiles_enabled, validate_current_source_claims
from .custody import prepare_catalogue_sources

_CAPABILITIES = {
    "pollen": "vegetation_assemblage_context",
    "geochronologic": "chronology_context",
    "loss-on-ignition": "sediment_context",
    "charcoal": "disturbance_context",
    "microcharcoal": "disturbance_context",
    "plant macrofossil": "macrofossil_context",
    "pollen trap": "monitoring_context",
    "testate amoebae": "hydrological_context",
}


def _same(left: object, right: object) -> bool:
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(
        right, sort_keys=True, allow_nan=False
    )


def method_capability(
    dataset_type: str, *, qualify_current_source_profiles: bool = False
) -> dict[str, Any]:
    current_registered = (
        qualify_current_source_profiles and dataset_type in CURRENT_SOURCE_TYPES
    )
    return {
        "status": "source_type_registered"
        if dataset_type in _CAPABILITIES
        else "native_source_profile_registered"
        if current_registered
        else "unsupported_dataset_type",
        "evidence_role": _CAPABILITIES.get(dataset_type)
        or ("native_proxy_source_context" if current_registered else None),
        "is_pollen_assemblage": dataset_type == "pollen",
        "independent_lra_accuracy": False,
        "scientific_admission": "not_asserted",
    }


def original_epoch(
    epochs: dict[int, dict[str, Any]] | None, dataset_id: int
) -> dict[str, Any]:
    if epochs is None:
        return {"status": "not_supplied"}
    return {
        key: value
        for key, value in epochs.get(
            dataset_id, {"status": "not_in_original_dataset_inventory"}
        ).items()
        if key != "native_row"
    }


def inventory_scope() -> dict[str, Any]:
    return {
        "coverage": "declared source inventory only",
        "outside_inventory": "not_assessed",
        "discovery_is_all_nordic_resources": False,
    }


def related_facets() -> dict[str, Any]:
    return {
        "status": "not_captured_by_download_coverage",
        "expected_native_facets": [
            "chronologies",
            "lithology",
            "projects",
            "publications",
            "taxa",
        ],
        "absence_certified": False,
    }


def catalogue_accounts(resources: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(
        version["acquisition_status"]
        for row in resources
        for version in row["versions"].values()
    )
    sites, countries = [], {}
    for site_id in sorted({row["site_id"] for row in resources}):
        members = [row for row in resources if row["site_id"] == site_id]
        if any(not _same(row["country"], members[0]["country"]) for row in members):
            raise ValueError(
                "Catalogue site country projection differs between resources"
            )
        sites.append(
            {
                "site_id": site_id,
                "native_site_metadata": next(
                    (
                        row["metadata"]["native_site"]
                        for row in members
                        if "geography" in row["metadata"]["native_site"]
                    ),
                    members[0]["metadata"]["native_site"],
                ),
                "country_code": members[0]["country"]["final_country_code"],
                "dataset_ids": [row["dataset_id"] for row in members],
                "resource_role_counts": dict(
                    Counter(row["exposure_role"] for row in members)
                ),
                "metadata_only_site": all(
                    row["exposure_role"] not in DEVELOPMENT_ROLES for row in members
                ),
                "old_numerical_atlas_membership_inferred": False,
            }
        )
    for code in sorted({row["country"]["final_country_code"] for row in resources}):
        members = [
            row for row in resources if row["country"]["final_country_code"] == code
        ]
        countries[code] = {
            "site_count": len({row["site_id"] for row in members}),
            "resource_count": len(members),
            "resource_role_counts": dict(
                Counter(row["exposure_role"] for row in members)
            ),
            "version_status_counts": dict(
                Counter(
                    version["acquisition_status"]
                    for row in members
                    for version in row["versions"].values()
                )
            ),
            "numerical_atlas_denominator_changed": False,
        }
    return {
        "summary": {
            "resource_count": len(resources),
            "version_status_count": 2 * len(resources),
            "version_partition_exact": True,
            "version_status_counts": dict(counts),
            "resource_role_counts": dict(
                Counter(row["exposure_role"] for row in resources)
            ),
            "acquisition_partition_complete": not any(
                counts.get(status, 0)
                for status in ("not_attempted_pending_capture", "not_attempted_budget")
            ),
            "scientific_admission": "not_asserted",
            "original_relational_snapshot_replaced": False,
            "numerical_atlas_denominator_changed": False,
        },
        "sites": sites,
        "countries": countries,
    }


def verify_derived_projection(catalogue: dict[str, Any]) -> None:
    """Reconcile indexes without asserting a new geographic or scientific decision."""
    enabled = current_profiles_enabled(catalogue)
    expected = catalogue_accounts(catalogue["resources"])
    for key, value in expected.items():
        if not _same(catalogue.get(key), value):
            raise ValueError(
                f"Catalogue derived {key} role/status account projection differs"
            )
    if not _same(catalogue.get("inventory_scope"), inventory_scope()):
        raise ValueError("Catalogue inventory scope projection differs")
    if not _same(catalogue.get("related_facets"), related_facets()):
        raise ValueError("Catalogue related facets projection differs")
    if catalogue.get("source_family") != "neotoma":
        raise ValueError("Catalogue source family projection differs")
    for row in catalogue["resources"]:
        validate_current_source_claims(row, enabled)
        if not _same(
            row.get("method_capability"),
            method_capability(
                row["dataset_type"], qualify_current_source_profiles=enabled
            ),
        ):
            raise ValueError(
                "Catalogue source-type method capability projection differs"
            )


def verify_roster_projection(catalogue: dict[str, Any], roster: dict[str, Any]) -> None:
    """Bind public identity, role and policy facts to the pre-acquisition inventory."""
    declared = {row["dataset_id"]: row for row in roster["resources"]}
    if (
        type(roster.get("resource_count")) is not int
        or len(declared) != len(roster["resources"])
        or roster["resource_count"] != len(catalogue["resources"])
    ):
        raise ValueError("Catalogue roster projection population differs")
    for row in catalogue["resources"]:
        expected = declared.get(row["dataset_id"])
        if (
            expected is None
            or any(
                not _same(row.get(key), expected.get(key))
                for key in (
                    "dataset_id",
                    "site_id",
                    "collection_unit_id",
                    "dataset_type",
                    "database",
                )
            )
            or row["exposure_role"] != expected["exposure_roles"]["current"]
            or expected["exposure_roles"]["current"]
            != expected["exposure_roles"]["doi_frozen"]
        ):
            raise ValueError(
                "Catalogue identity or exposure role differs from source inventory"
            )
        source, locator = row["metadata"]["source"], expected["metadata_locator"]
        if (
            source["body_sha256"] != locator["response_sha256"]
            or source["json_pointer"] != locator["json_pointer"]
        ):
            raise ValueError("Catalogue metadata pointer differs from source inventory")
        native = row["metadata"]["native_dataset"]
        rights = row["rights"]
        expected_rights = {
            "available_public_data_license": "CC BY 4.0",
            "policy_sources": roster["policy_sources"],
            "provider": "Neotoma Paleoecology Database",
            "constituent_database": expected["database"],
            "dataset_doi_values": expected["dataset_doi_values"],
            "investigator_metadata": native.get("datasetpi", []),
            "publication_identity": "Not inferred from a DOI-frozen response",
            "scope": "Available public data; no private-workbook rights or unreturned-source availability inferred",
        }
        if not _same(rights, expected_rights):
            raise ValueError(
                "Catalogue rights projection differs from inventory/native metadata"
            )


def verify_native_metadata_projection(
    catalogue: dict[str, Any],
    roster_path: Path,
    capture_sources: Mapping[str, Path],
    original_relational_root: Path | None,
) -> None:
    """Rebuild the entire metadata tuple from original authenticated receipts."""
    metadata_roots = {
        digest: capture_sources[digest]
        for digest in catalogue["metadata_capture_manifest_sha256"]
    }
    actual = prepare_catalogue_sources(
        roster_path=roster_path,
        expected_roster_sha256=catalogue["expected_roster_sha256"],
        metadata_captures=metadata_roots,
        resource_captures={},
        original_relational_root=original_relational_root,
    )
    for row in catalogue["resources"]:
        if not _same(
            row.get("original_epoch"),
            original_epoch(actual.original_epochs, row["dataset_id"]),
        ):
            raise ValueError("Catalogue original epoch differs from supplied snapshot")
        if not _same(row["metadata"], actual.metadata[row["dataset_id"]]):
            raise ValueError(
                "Catalogue complete metadata/source tuple differs from original receipt"
            )
