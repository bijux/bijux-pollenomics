"""Derived accounts and source epochs cannot contradict authenticated resources."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    build_neotoma_resource_catalogue,
    load_neotoma_resource_catalogue,
    write_neotoma_resource_catalogue,
)


def _mutate(catalogue: dict[str, Any], surface: str) -> None:
    if surface == "status_counts":
        catalogue["summary"]["version_status_counts"] = {"parsed_native": 999999}
    elif surface == "role_counts":
        catalogue["summary"]["resource_role_counts"] = {}
    elif surface == "partition_complete":
        catalogue["summary"]["acquisition_partition_complete"] = True
    elif surface == "site_ids":
        catalogue["sites"][0]["dataset_ids"] = [999999]
    elif surface == "site_roles":
        catalogue["sites"][0]["resource_role_counts"] = {}
    elif surface == "metadata_only":
        catalogue["sites"][0]["metadata_only_site"] = True
    elif surface == "site_native_metadata":
        catalogue["sites"][0]["native_site_metadata"]["sitename"] = "Invented"
    elif surface == "country_counts":
        catalogue["countries"]["SE"]["site_count"] = 999999
    elif surface == "country_status":
        catalogue["countries"]["SE"]["version_status_counts"] = {}
    elif surface == "capability":
        catalogue["resources"][0]["method_capability"]["independent_lra_accuracy"] = (
            True
        )
    elif surface == "inventory_scope":
        catalogue["inventory_scope"]["discovery_is_all_nordic_resources"] = True
    elif surface == "admission":
        catalogue["summary"]["scientific_admission"] = "accepted"
    else:
        catalogue["related_facets"]["absence_certified"] = True


@pytest.mark.parametrize(
    "surface",
    [
        "status_counts",
        "role_counts",
        "partition_complete",
        "site_ids",
        "site_roles",
        "metadata_only",
        "site_native_metadata",
        "country_counts",
        "country_status",
        "capability",
        "inventory_scope",
        "admission",
        "facet_absence",
    ],
)
@pytest.mark.parametrize("entrypoint", ["writer", "rehashed_load"])
def test_derived_claims_are_recomputed_from_exact_resource_rows(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    surface: str,
    entrypoint: str,
) -> None:
    inputs = catalogue_sources(capture_resources=False)
    catalogue = build_neotoma_resource_catalogue(**inputs)
    sources = inputs["metadata_captures"]
    output = tmp_path / "catalogue"
    if entrypoint == "writer":
        _mutate(catalogue, surface)
        with pytest.raises(
            ValueError,
            match="projection|account|capability|scope|facets|metadata/source",
        ):
            write_neotoma_resource_catalogue(
                output,
                catalogue=catalogue,
                roster_path=inputs["roster_path"],
                capture_sources=sources,
            )
        assert not output.exists()
    else:
        write_neotoma_resource_catalogue(
            output,
            catalogue=catalogue,
            roster_path=inputs["roster_path"],
            capture_sources=sources,
        )
        path = output / "catalogue.json"
        document = json.loads(path.read_bytes())
        _mutate(document, surface)
        path.write_text(json.dumps(document))
        manifest_path = output / "manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        manifest["files"]["catalogue.json"] = sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
        with pytest.raises(
            ValueError,
            match="projection|account|capability|scope|facets|metadata/source",
        ):
            load_neotoma_resource_catalogue(
                output,
                expected_manifest_sha256=sha256(manifest_path.read_bytes()).hexdigest(),
                capture_sources=sources,
                require_source_bodies=True,
            )


@pytest.mark.parametrize("claim", ["not_supplied", "retained_dataset_metadata"])
def test_original_epoch_matches_actual_supplied_snapshot(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    claim: str,
) -> None:
    inputs = catalogue_sources(capture_resources=False)
    original = tmp_path / "original"
    original.mkdir()
    (original / "manifest.json").write_text(
        json.dumps(
            {
                "surfaces": {"datasets": {"row_count": 0, "parts": []}},
            }
        )
    )
    inputs["original_relational_root"] = original
    catalogue = build_neotoma_resource_catalogue(**inputs)
    assert catalogue["resources"][0]["original_epoch"] == {
        "status": "not_in_original_dataset_inventory"
    }
    catalogue["resources"][0]["original_epoch"] = {"status": claim}
    with pytest.raises(ValueError, match="original.*epoch|epoch.*snapshot"):
        write_neotoma_resource_catalogue(
            tmp_path / "catalogue",
            catalogue=catalogue,
            roster_path=inputs["roster_path"],
            capture_sources=inputs["metadata_captures"],
            original_relational_root=original,
        )


@pytest.mark.parametrize(
    "field",
    [
        "build_id",
        "relational_manifest_sha256",
        "dataset_metadata_sha256",
        "json_pointer",
    ],
)
def test_retained_original_epoch_cannot_be_relabelled(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    field: str,
) -> None:
    inputs = catalogue_sources(capture_resources=False)
    original = tmp_path / "original"
    original.mkdir()
    part = original / "datasets.json"
    part.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "source_dataset_id": 201,
                        "source_snapshot_id": "sha256:" + "a" * 64,
                        "build_id": "sha256:" + "b" * 64,
                    }
                ]
            }
        )
    )
    (original / "manifest.json").write_text(
        json.dumps(
            {
                "surfaces": {
                    "datasets": {
                        "row_count": 1,
                        "parts": [
                            {
                                "path": "datasets.json",
                                "sha256": sha256(part.read_bytes()).hexdigest(),
                            }
                        ],
                    }
                }
            }
        )
    )
    inputs["original_relational_root"] = original
    catalogue = build_neotoma_resource_catalogue(**inputs)
    assert (
        catalogue["resources"][0]["original_epoch"]["status"]
        == "retained_dataset_metadata"
    )
    catalogue["resources"][0]["original_epoch"][field] = "invented"
    with pytest.raises(ValueError, match="original epoch"):
        write_neotoma_resource_catalogue(
            tmp_path / "catalogue",
            catalogue=catalogue,
            roster_path=inputs["roster_path"],
            capture_sources=inputs["metadata_captures"],
            original_relational_root=original,
        )


@pytest.mark.parametrize(
    "field", ["resource_count", "version_status_count", "scientific_admission"]
)
def test_publication_account_cannot_contradict_catalogue(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    field: str,
) -> None:
    inputs = catalogue_sources(capture_resources=False)
    catalogue = build_neotoma_resource_catalogue(**inputs)
    output = tmp_path / "catalogue"
    write_neotoma_resource_catalogue(
        output,
        catalogue=catalogue,
        roster_path=inputs["roster_path"],
        capture_sources=inputs["metadata_captures"],
    )
    path = output / "manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest[field] = "accepted" if field == "scientific_admission" else 999999
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="publication.*account"):
        load_neotoma_resource_catalogue(
            output,
            expected_manifest_sha256=sha256(path.read_bytes()).hexdigest(),
        )
