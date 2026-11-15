"""Source resource partitions refuse incoherent identities and population claims."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogue,
)

from .test_publication import (
    atlas_catalogue as atlas_catalogue,
)
from .test_publication import (
    catalogue_sources as catalogue_sources,
)
from .test_publication import (
    projected_catalogue as projected_catalogue,
)
from .test_publication import resource_transport_api, rows_of


@pytest.mark.parametrize(
    "field",
    [
        "record_count",
        "site_count",
        "version_status_count",
        "source_descriptor_count",
        "legacy_site_reference_count",
    ],
)
def test_domain_population_change_refuses(
    projected_catalogue: AtlasResourceCatalogue, field: str
) -> None:
    api = resource_transport_api()
    transport = api.build_source_resource_payloads(projected_catalogue)
    transport.domain[field] += 1
    with pytest.raises(ValueError, match="population|count"):
        api.validate_source_resource_payloads(
            transport,
            expected_catalogue_manifest_sha256=projected_catalogue.provenance[
                "catalogue_manifest_sha256"
            ],
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate",
        "omitted",
        "dangling",
        "wrong_kind",
        "wrong_catalogue",
        "wrong_schema",
        "foreign_site",
        "admitted",
        "summary_status_count",
        "summary_boolean_count",
    ],
)
def test_invalid_partition_or_reference_refuses(
    projected_catalogue: AtlasResourceCatalogue, mutation: str
) -> None:
    api = resource_transport_api()
    transport = api.build_source_resource_payloads(projected_catalogue)
    if mutation == "duplicate":
        part = next(p for p in transport.payloads if p["kind"] == "resources")
        part["records"].append(deepcopy(part["records"][0]))
    elif mutation == "omitted":
        part = next(p for p in transport.payloads if p["kind"] == "resources")
        part["records"].pop()
    elif mutation == "dangling":
        rows_of(transport, "index")[0]["part_id"] = "resources:missing"
    elif mutation == "wrong_kind":
        next(
            row
            for row in rows_of(transport, "index")
            if row["entity_type"] == "resources"
        )["entity_type"] = "sites"
    elif mutation == "wrong_catalogue":
        transport.payloads[0]["catalogue_manifest_sha256"] = "0" * 64
    elif mutation == "wrong_schema":
        transport.payloads[0]["schema_version"] = "unknown"
    elif mutation == "foreign_site":
        rows_of(transport, "resources")[0]["site_id"] = "999"
    elif mutation == "summary_status_count":
        rows_of(transport, "context")[0]["summary"]["version_status_counts"][
            "invented_status"
        ] = 1
    elif mutation == "summary_boolean_count":
        rows_of(transport, "context")[0]["summary"]["resource_role_counts"][
            "reserved_candidate_confirmation"
        ] = True
    else:
        transport.domain["scientific_admission"] = "admitted"
    with pytest.raises(ValueError):
        api.validate_source_resource_payloads(
            transport,
            expected_catalogue_manifest_sha256=projected_catalogue.provenance[
                "catalogue_manifest_sha256"
            ],
        )


def test_external_catalogue_anchor_and_closed_part_ids_are_enforced(
    projected_catalogue: AtlasResourceCatalogue,
) -> None:
    api = resource_transport_api()
    transport = api.build_source_resource_payloads(projected_catalogue)
    with pytest.raises(ValueError, match="catalogue"):
        api.validate_source_resource_payloads(
            transport, expected_catalogue_manifest_sha256="0" * 64
        )
    with pytest.raises(ValueError, match="part"):
        api.validate_source_resource_payloads(
            replace(
                transport,
                payloads=transport.payloads + (deepcopy(transport.payloads[0]),),
            ),
            expected_catalogue_manifest_sha256=projected_catalogue.provenance[
                "catalogue_manifest_sha256"
            ],
        )


@pytest.mark.parametrize("value", [False, -1, "4", None])
def test_population_counts_are_literal_nonnegative_integers(
    projected_catalogue: AtlasResourceCatalogue, value: Any
) -> None:
    api = resource_transport_api()
    transport = api.build_source_resource_payloads(projected_catalogue)
    transport.domain["record_count"] = value
    with pytest.raises(ValueError, match="count|population"):
        api.validate_source_resource_payloads(
            transport,
            expected_catalogue_manifest_sha256=projected_catalogue.provenance[
                "catalogue_manifest_sha256"
            ],
        )
