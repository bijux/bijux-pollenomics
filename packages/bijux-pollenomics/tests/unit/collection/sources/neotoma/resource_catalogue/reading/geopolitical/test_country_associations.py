"""Country-source witnesses authenticate metadata without admitting outcomes."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
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
from bijux_pollenomics.collection.sources.neotoma.capture.country_authority import (
    NeotomaCountryAuthorityPlan,
    capture_neotoma_country_authority,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    build_neotoma_resource_catalogue,
    load_neotoma_resource_catalogue,
    write_neotoma_resource_catalogue,
)


def _country_sources(
    inputs: dict[str, Any],
    tmp_path: Path,
    *,
    country_id: int = 5392,
    donor: Callable[[list[dict[str, Any]]], object] | None = None,
    view_donor: Callable[[list[dict[str, Any]], int], object] | None = None,
    country_name: str = "Sweden",
    authority_id: int = 5392,
) -> dict[str, Path]:
    metadata = next(iter(inputs["metadata_captures"].values()))
    units = []
    for path in sorted(metadata.glob("*.body")):
        units.extend(json.loads(path.read_bytes())["data"])
    if donor is not None:
        donor(units)
    inventory = tmp_path / f"country-inventory-{country_id}"

    def fetch_inventory(url: str, **_: object) -> NeotomaMetadataResponse:
        from urllib.parse import parse_qs, urlsplit

        view = deepcopy(units)
        if view_donor is not None:
            view_donor(view, int(parse_qs(urlsplit(url).query)["limit"][0]))
        return NeotomaMetadataResponse(
            url, 200, (), json.dumps({"status": "success", "data": view}).encode()
        )

    captured = capture_neotoma_metadata(
        inventory,
        plan=NeotomaMetadataPlan(
            geopolitical_unit_ids=(country_id,),
            inventory_all_dataset_types=True,
            inventory_limits=(400, 10000),
        ),
        fetch=fetch_inventory,
    )
    authority = tmp_path / f"country-authority-{country_id}"
    native = {
        "geopoliticalid": authority_id,
        "geopoliticalname": country_name,
        "geopoliticalunit": "country",
        "rank": 1,
        "highergeopoliticalid": 0,
        "recdatecreated": "2000-01-01",
        "recdatemodified": None,
    }
    countries = capture_neotoma_country_authority(
        authority,
        plan=NeotomaCountryAuthorityPlan((country_name,)),
        fetch=lambda url, **_: NeotomaMetadataResponse(
            url, 200, (), json.dumps({"status": "success", "data": [native]}).encode()
        ),
    )
    inputs["metadata_captures"][captured.manifest_sha256] = inventory
    return {countries.manifest_sha256: authority}


def test_independent_inventory_views_require_same_population(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = catalogue_sources()
    authority = _country_sources(
        inputs,
        tmp_path,
        view_donor=lambda rows, limit: rows.pop() if limit == 400 else None,
    )
    with pytest.raises(ValueError, match="country|population"):
        build_neotoma_resource_catalogue(**inputs, country_authority_captures=authority)


@pytest.mark.parametrize("field", ["siteid", "collectionunitid"])
def test_shared_site_or_core_donor_is_refused(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path, field: str
) -> None:
    inputs = catalogue_sources()
    authority = _country_sources(
        inputs, tmp_path, donor=lambda rows: rows[0]["site"].__setitem__(field, 999)
    )
    with pytest.raises(ValueError, match="country|identity"):
        build_neotoma_resource_catalogue(**inputs, country_authority_captures=authority)


def _publish(
    inputs: dict[str, Any],
    authority: dict[str, Path],
    tmp_path: Path,
    catalogue: dict[str, Any] | None = None,
) -> tuple[Path, str, dict[str, Path]]:
    if catalogue is None:
        catalogue = build_neotoma_resource_catalogue(
            **inputs, country_authority_captures=authority
        )
    sources = {
        **inputs["metadata_captures"],
        **inputs["resource_captures"],
        **authority,
    }
    output = tmp_path / "public"
    write_neotoma_resource_catalogue(
        output,
        catalogue=catalogue,
        roster_path=inputs["roster_path"],
        capture_sources=sources,
    )
    return output, sha256((output / "manifest.json").read_bytes()).hexdigest(), sources


def test_country_authority_opt_in_preserves_default_literal(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = catalogue_sources()
    _country_sources(inputs, tmp_path)
    default = build_neotoma_resource_catalogue(**inputs)
    explicit = build_neotoma_resource_catalogue(
        **inputs, country_authority_captures=None
    )
    assert default == explicit
    assert "source_country_association_profile" not in default
    assert all("source_country_associations" not in row for row in default["resources"])


def test_null_profile_is_not_a_qualified_marker(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = catalogue_sources(capture_resources=False)
    catalogue = build_neotoma_resource_catalogue(**inputs)
    catalogue["source_country_association_profile"] = None
    with pytest.raises(ValueError, match="country|association"):
        _publish(inputs, {}, tmp_path, catalogue)


def test_provider_associations_keep_geometry_roles_and_versions(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = catalogue_sources()
    baseline = build_neotoma_resource_catalogue(**inputs)
    authority = _country_sources(inputs, tmp_path)
    actual = build_neotoma_resource_catalogue(
        **inputs, country_authority_captures=authority
    )
    for row, old in zip(actual["resources"], baseline["resources"], strict=True):
        assert row["country"] == old["country"]
        assert row["versions"] == old["versions"]
        assert row["exposure_role"] == old["exposure_role"]
        association = row["source_country_associations"][0]
        assert association["native_country"]["highergeopoliticalid"] == 0
        assert association["native_country"]["geopoliticalid"] == 5392
        assert association["association_vs_boundary"] == "agrees"
        assert association["primary_inventory_source"]["parameters"]["limit"] == "10000"
        assert association["other_inventory_sources"][0]["parameters"]["limit"] == "400"
    assert (
        actual["source_country_association_profile"]["associated_resource_count"] == 4
    )
    output, digest, sources = _publish(inputs, authority, tmp_path, actual)
    assert (
        load_neotoma_resource_catalogue(output, expected_manifest_sha256=digest)
        == actual
    )
    assert (
        load_neotoma_resource_catalogue(
            output,
            expected_manifest_sha256=digest,
            capture_sources=sources,
            require_source_bodies=True,
        )
        == actual
    )


@pytest.mark.parametrize("boundary", ["NO", "UNASSIGNED"])
def test_source_country_comparison_never_forces_boundary_country(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path, boundary: str
) -> None:
    inputs = catalogue_sources()
    authority = _country_sources(inputs, tmp_path)
    if boundary == "UNASSIGNED":
        inputs["country_boundaries"] = None
    else:
        inputs["country_boundaries"]["Norway"] = inputs["country_boundaries"].pop(
            "Sweden"
        )
    catalogue = build_neotoma_resource_catalogue(
        **inputs, country_authority_captures=authority
    )
    assert all(
        row["country"]["final_country_code"] == boundary
        for row in catalogue["resources"]
    )
    assert all(
        row["source_country_associations"][0]["association_vs_boundary"]
        == ("conflicts" if boundary == "NO" else "boundary_unassigned")
        for row in catalogue["resources"]
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("datasettype", "charcoal"),
        ("database", "foreign"),
        ("doi", ["foreign"]),
    ],
)
def test_native_inventory_identity_drift_refused(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    inputs = catalogue_sources()
    authority = _country_sources(
        inputs,
        tmp_path,
        donor=lambda rows: rows[0]["site"]["datasets"][0].__setitem__(field, value),
    )
    with pytest.raises(ValueError, match="association|country|identity"):
        build_neotoma_resource_catalogue(**inputs, country_authority_captures=authority)


def test_unknown_query_country_has_no_invented_authority(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = catalogue_sources()
    authority = _country_sources(inputs, tmp_path, country_id=999)
    with pytest.raises(ValueError, match="authority|country"):
        build_neotoma_resource_catalogue(**inputs, country_authority_captures=authority)


def test_multiple_provider_countries_preserve_both_witnesses(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = catalogue_sources(capture_resources=False)
    authority = _country_sources(inputs, tmp_path)
    authority.update(
        _country_sources(
            inputs, tmp_path, country_id=3307, country_name="Norway", authority_id=3307
        )
    )
    catalogue = build_neotoma_resource_catalogue(
        **inputs, country_authority_captures=authority
    )
    for row in catalogue["resources"]:
        assert row["country"]["final_country_code"] == "SE"
        associations = row["source_country_associations"]
        assert [
            value["native_country"]["geopoliticalid"] for value in associations
        ] == [3307, 5392]
        assert [value["association_vs_boundary"] for value in associations] == [
            "conflicts",
            "agrees",
        ]
    _publish(inputs, authority, tmp_path, catalogue)


def test_ambiguous_authority_roots_are_refused(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = catalogue_sources(capture_resources=False)
    authority = _country_sources(inputs, tmp_path)
    duplicate = tmp_path / "duplicate-authority"
    captured = capture_neotoma_country_authority(
        duplicate,
        plan=NeotomaCountryAuthorityPlan(("Sweden",)),
        fetch=lambda url, **_: NeotomaMetadataResponse(
            url,
            200,
            (),
            json.dumps(
                {
                    "status": "success",
                    "data": [
                        {
                            "geopoliticalid": 5392,
                            "geopoliticalname": "Sweden",
                            "geopoliticalunit": "country",
                            "rank": 1,
                            "highergeopoliticalid": 0,
                        }
                    ],
                }
            ).encode(),
        ),
    )
    authority[captured.manifest_sha256] = duplicate
    with pytest.raises(ValueError, match="country authority is ambiguous"):
        build_neotoma_resource_catalogue(**inputs, country_authority_captures=authority)


@pytest.mark.parametrize(
    "mutation",
    [
        "receipt",
        "pointer",
        "native_country",
        "comparison",
        "profile",
        "missing_marker",
        "foreign_scope",
        "source_kind",
        "missing_source_key",
        "invented_iso",
        "role",
        "url",
        "utc",
        "tls",
        "body_file",
    ],
)
def test_rehashed_association_claims_refused(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path, mutation: str
) -> None:
    inputs = catalogue_sources()
    authority = _country_sources(inputs, tmp_path)
    catalogue = build_neotoma_resource_catalogue(
        **inputs, country_authority_captures=authority
    )
    forged = deepcopy(catalogue)
    association = forged["resources"][0]["source_country_associations"][0]
    if mutation == "receipt":
        association["authority_source"]["receipt_sha256"] = "0" * 64
    elif mutation == "pointer":
        association["primary_inventory_source"]["json_pointer"] = (
            "/data/0/site/datasets/1"
        )
    elif mutation == "native_country":
        association["native_country"]["rank"] = True
    elif mutation == "comparison":
        association["association_vs_boundary"] = "conflicts"
    elif mutation == "profile":
        forged["source_country_association_profile"]["associated_resource_count"] = 999
    elif mutation == "missing_marker":
        del forged["source_country_association_profile"]
    elif mutation == "foreign_scope":
        association["primary_inventory_source"]["parameters"]["gpid"] = "999"
    elif mutation == "source_kind":
        association["primary_inventory_source"]["source_kind"] = "country_authority"
    elif mutation == "missing_source_key":
        del association["authority_source"]["utc_start"]
    elif mutation == "role":
        association["authority_source"]["role"] = "dataset_inventory"
    elif mutation == "url":
        association["authority_source"]["requested_url"] = "https://foreign.test"
    elif mutation == "utc":
        association["authority_source"]["utc_end"] = "1900-01-01T00:00:00+00:00"
    elif mutation == "tls":
        association["authority_source"]["tls_mode"] = "insecure"
    elif mutation == "body_file":
        association["authority_source"]["body_file"] = "../foreign.body"
    else:
        forged["resources"][0]["source_country_iso"] = "SE"
    with pytest.raises(ValueError, match="association|country|authority"):
        _publish(inputs, authority, tmp_path, forged)


def test_metadata_only_associations_need_no_numerical_source(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = catalogue_sources(capture_resources=False)
    authority = _country_sources(inputs, tmp_path)
    catalogue = build_neotoma_resource_catalogue(
        **inputs, country_authority_captures=authority
    )
    assert all(row["source_country_associations"] for row in catalogue["resources"])
    assert inputs["resource_captures"] == {}
    output, digest, sources = _publish(inputs, authority, tmp_path, catalogue)
    assert all(
        descriptor["capture_kind"] != "resources"
        for descriptor in catalogue["capture_descriptors"].values()
    )
    assert (
        load_neotoma_resource_catalogue(
            output,
            expected_manifest_sha256=digest,
            capture_sources=sources,
            require_source_bodies=True,
        )
        == catalogue
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("role", "dataset_inventory"),
        ("requested_url", "https://foreign.test"),
        ("utc_end", "1900-01-01T00:00:00+00:00"),
        ("tls_mode", "insecure"),
        ("body_file", "../foreign.body"),
    ],
)
def test_rehashed_public_metadata_rejects_invalid_source_semantics(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    inputs = catalogue_sources(capture_resources=False)
    authority = _country_sources(inputs, tmp_path)
    output, _, _ = _publish(inputs, authority, tmp_path)
    catalogue = json.loads((output / "catalogue.json").read_bytes())
    catalogue["resources"][0]["source_country_associations"][0]["authority_source"][
        field
    ] = value
    (output / "catalogue.json").write_text(json.dumps(catalogue))
    manifest = json.loads((output / "manifest.json").read_bytes())
    manifest["files"]["catalogue.json"] = sha256(
        (output / "catalogue.json").read_bytes()
    ).hexdigest()
    (output / "manifest.json").write_text(json.dumps(manifest))
    digest = sha256((output / "manifest.json").read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="country|authority"):
        load_neotoma_resource_catalogue(output, expected_manifest_sha256=digest)
