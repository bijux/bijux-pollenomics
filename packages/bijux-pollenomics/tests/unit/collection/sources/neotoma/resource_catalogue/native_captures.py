"""Synthetic metadata, exposure and HTTP captures for source-catalogue contracts."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataPlan,
    NeotomaMetadataResponse,
    capture_neotoma_metadata,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourcePlan,
    NeotomaResourceSpec,
    capture_neotoma_resources,
)

_DEFAULT_SOURCE_COLLECTION = object()


@pytest.fixture
def catalogue_sources(tmp_path: Path) -> Callable[..., dict[str, Any]]:
    def make(
        *,
        auxiliary_type: str = "geochronologic",
        capture_resources: bool = True,
        large_integer: bool = False,
        chronology_metadata: object = _DEFAULT_SOURCE_COLLECTION,
        sample_metadata: object = _DEFAULT_SOURCE_COLLECTION,
        source_database: str | None = None,
        auxiliary_role: str = "development_resource_discovery",
    ) -> dict[str, Any]:
        root = tmp_path / auxiliary_type.replace(" ", "-")
        root.mkdir()
        kinds = {201: "pollen", 202: auxiliary_type, 203: "pollen", 204: "pollen"}
        sites = {201: (12, 100), 202: (12, 100), 203: (13, 101), 204: (14, 102)}
        roles = {
            201: "development_resource_discovery",
            202: auxiliary_role,
            203: "reserved_candidate_confirmation",
            204: "heldout_no_numerical_access",
        }

        def native_dataset(identity: int) -> dict[str, Any]:
            return {
                "datasetid": identity,
                "datasettype": kinds[identity],
                "database": source_database,
                "doi": [],
                "datasetpi": [],
            }

        metadata_bodies = {
            site: json.dumps(
                {
                    "status": "success",
                    "data": [
                        {
                            "site": {
                                "siteid": site,
                                "collectionunitid": site + 88,
                                "sitename": f"Native site {site}",
                                "geography": '{"type":"Point","coordinates":[12,61.5]}',
                                "datasets": [
                                    native_dataset(i)
                                    for i in kinds
                                    if sites[i][0] == site
                                ],
                            }
                        }
                    ],
                }
            ).encode()
            for site in (12, 13, 14)
        }
        metadata = root / "metadata"
        captured_metadata = capture_neotoma_metadata(
            metadata,
            plan=NeotomaMetadataPlan(site_ids=(12, 13, 14)),
            fetch=lambda url, **_: NeotomaMetadataResponse(
                url, 200, (), metadata_bodies[int(url.split("/")[-2])]
            ),
        )
        rows, specs = [], []
        for identity in kinds:
            site, unit = sites[identity]
            offset = [i for i in kinds if sites[i][0] == site].index(identity)
            digest = sha256(metadata_bodies[site]).hexdigest()
            pointer = f"/data/0/site/datasets/{offset}"
            rows.append(
                {
                    "dataset_id": identity,
                    "site_id": site,
                    "collection_unit_id": unit,
                    "dataset_type": kinds[identity],
                    "database": source_database,
                    "dataset_doi_values": [],
                    "metadata_locator": {
                        "response_sha256": digest,
                        "json_pointer": pointer,
                    },
                    "exposure_roles": {
                        "current": roles[identity],
                        "doi_frozen": roles[identity],
                    },
                    "role_authority": "Synthetic declared exposure before GET",
                }
            )
            specs.append(
                NeotomaResourceSpec(
                    identity,
                    site,
                    unit,
                    kinds[identity],
                    source_database,
                    roles[identity],
                    digest,
                    pointer,
                )
            )
        roster = root / "roster.json"
        roster.write_text(
            json.dumps(
                {
                    "schema_version": "neotoma-native-resource-candidate-roster.v1",
                    "resource_count": 4,
                    "resources": rows,
                    "source_metadata_capture_manifest_sha256": [
                        captured_metadata.manifest_sha256
                    ],
                    "policy_sources": [
                        "https://www.neotomadb.org/data/data-use-and-embargo-policy"
                    ],
                }
            )
        )
        roster_sha = sha256(roster.read_bytes()).hexdigest()
        sources = {}
        if capture_resources:

            def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
                identity = int(url.split("/")[-1])
                assert identity in (201, 202), "Blocked numerical source requested"
                site, unit = sites[identity]
                samples: object = [
                    {
                        "sampleid": 41 if identity == 201 else None,
                        "datum": [
                            {
                                "value": (10**1000 if large_integer else 7)
                                if identity == 201
                                else None,
                                "units": "NISP" if identity == 201 else None,
                            }
                        ],
                    }
                ]
                if sample_metadata is not _DEFAULT_SOURCE_COLLECTION:
                    samples = sample_metadata
                if "/frozen/" in url:
                    document = {
                        "status": "success",
                        "data": [
                            {
                                "download": {
                                    "data": {
                                        "site": {
                                            "siteid": site,
                                            "dataset": native_dataset(identity),
                                            "collectionunit": {
                                                "collectionunitid": unit
                                            },
                                        },
                                        "samples": samples,
                                    },
                                    "chronologies": {"chronologies": []},
                                }
                            }
                        ],
                    }
                else:
                    document = {
                        "status": "success",
                        "data": [
                            {
                                "site": {
                                    "siteid": site,
                                    "dataset": native_dataset(identity),
                                    "collectionunit": {
                                        "collectionunitid": unit,
                                        "dataset": {
                                            **native_dataset(identity),
                                            "samples": samples,
                                        },
                                        "chronologies": []
                                        if chronology_metadata
                                        is _DEFAULT_SOURCE_COLLECTION
                                        else chronology_metadata,
                                    },
                                }
                            }
                        ],
                    }
                return NeotomaMetadataResponse(
                    url, 200, (), json.dumps(document).encode()
                )

            resource_root = root / "resources"
            captured = capture_neotoma_resources(
                resource_root,
                plan=NeotomaResourcePlan(tuple(specs), roster_sha),
                fetch=fetch,
            )
            sources[captured.manifest_sha256] = resource_root
        boundaries = {
            "Sweden": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [[10, 60], [14, 60], [14, 63], [10, 63], [10, 60]]
                            ],
                        }
                    }
                ]
            }
        }
        return {
            "roster_path": roster,
            "expected_roster_sha256": roster_sha,
            "metadata_captures": {captured_metadata.manifest_sha256: metadata},
            "resource_captures": sources,
            "country_boundaries": boundaries,
        }

    return make
