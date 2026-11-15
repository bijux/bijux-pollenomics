"""Selected raw bytes and typed source context share exactly one checked buffer."""

from dataclasses import replace
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse

from .native_products import candidate, observe_context_bodies, pin


def test_metadata_inventory_does_not_verify_body_derived_profiles(
    site_context_products: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource_inventory,
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products()
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])
    opened = observe_context_bodies(monkeypatch, set())
    inventory = read_neotoma_context_resource_inventory(
        output,
        expected_manifest_sha256=pin(output / "manifest.json"),
        **inputs["reader"],
    )
    assert opened == [] and inventory.body_hashes_verified is False
    assert inventory.native_profiles_verified is False


def test_selected_lake_preserves_extra_fields_and_empty_name_without_basin_claim(
    site_context_products: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource,
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products()
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])
    selected = output / "capture/site-12-lake_candidates-current-attempt-1.body"
    opened = observe_context_bodies(monkeypatch, {selected})
    result = read_neotoma_context_resource(
        output,
        expected_manifest_sha256=pin(output / "manifest.json"),
        site_id=12,
        resource_kind="lake_candidates",
        **inputs["reader"],
    )
    assert opened == [selected]
    row = result["source_payload"]["data"][0]
    assert (
        row["laketype"] == 1
        and row["distance"] == 0
        and row["lakename"] == ""
        and row["watershedarea"] == -9999
    )
    assert result["profile"]["distance_reference_unit"] == "m"
    assert result["profile"]["deployed_mapping_equivalence"] == "not_established"
    assert result["profile"]["dated_basin_geometry_admitted"] is False
    assert result["unselected_source_bodies_verified"] is False


def test_foreign_native_environment_refuses_typed_but_retains_selected_forensic_bytes(
    site_context_products: Any, tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource,
        read_neotoma_context_resource_entity,
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products()
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])
    options = {
        "expected_manifest_sha256": pin(output / "manifest.json"),
        "site_id": 12,
        "resource_kind": "depositional_environment",
        **inputs["reader"],
    }
    raw = read_neotoma_context_resource_entity(output, **options)
    assert (
        raw["body"]
        == (
            output / "capture/site-12-depositional_environment-current-attempt-1.body"
        ).read_bytes()
    )
    with pytest.raises(ValueError, match="foreign"):
        read_neotoma_context_resource(output, **options)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("distance", -1),
        ("distance", True),
        ("hydrolakeid", True),
        ("hydrolakeid", 12.0),
        ("laketype", 1.0),
        ("lakearea", True),
        ("extra_native_field", 1),
    ],
)
def test_unqualified_lake_contradictions_remain_forensic_and_refuse_typed(
    site_context_products: Any, tmp_path: Path, field: str, value: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource,
        read_neotoma_context_resource_entity,
        write_neotoma_context_resource_archive,
    )

    def fetched(url: str, **kwargs: Any) -> Any:
        row = candidate()
        row[field] = value
        payload = (
            {"status": "success", "data": [row], "message": "Retrieved all tables"}
            if "/spatial/" in url
            else {
                "status": "success",
                "data": [
                    {
                        "siteid": 1,
                        "collectionunitid": 1,
                        "datasetid": 1,
                        "depenvt": "Lake",
                    }
                ],
            }
        )
        return NeotomaMetadataResponse(url, 200, (), json.dumps(payload).encode())

    inputs = site_context_products(fetch=fetched)
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])
    options = {
        "expected_manifest_sha256": pin(output / "manifest.json"),
        "site_id": 12,
        "resource_kind": "lake_candidates",
        **inputs["reader"],
    }
    raw = read_neotoma_context_resource_entity(output, **options)
    assert json.loads(raw["body"])["data"][0][field] == value
    with pytest.raises(ValueError):
        read_neotoma_context_resource(output, **options)


def test_source_empty_lake_query_does_not_certify_lake_absence(
    site_context_products: Any, tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource,
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products()
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])
    result = read_neotoma_context_resource(
        output,
        expected_manifest_sha256=pin(output / "manifest.json"),
        site_id=13,
        resource_kind="lake_candidates",
        **inputs["reader"],
    )
    assert result["source_payload"]["data"] == []
    assert (
        result["profile"]["qualification_status"]
        == "qualified_empty_lake_candidate_query"
    )
    assert result["profile"]["absence_certified"] is False


def test_literal_null_environment_stays_unknown_without_prose_promotion(
    site_context_products: Any, tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource,
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products(foreign=False)
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])
    result = read_neotoma_context_resource(
        output,
        expected_manifest_sha256=pin(output / "manifest.json"),
        site_id=12,
        resource_kind="depositional_environment",
        **inputs["reader"],
    )
    assert result["source_payload"]["data"][0]["depenvt"] is None
    assert (
        result["profile"]["environment_inferred_from_prose_or_collection_type"] is False
    )
    assert result["profile"]["complete_environment_coverage_established"] is False


def test_stricter_selected_request_budget_refuses_late_body_but_allows_valid_early_source(
    site_context_products: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource_entity,
        write_neotoma_context_resource_archive,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        DEFAULT_CONTEXT_LIMITS,
    )

    inputs = site_context_products()
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])
    options = {
        "expected_manifest_sha256": pin(output / "manifest.json"),
        "site_id": 12,
        "limits": replace(DEFAULT_CONTEXT_LIMITS, max_requests=4),
        **inputs["reader"],
    }
    selected = (
        output / "capture/site-12-depositional_environment-current-attempt-1.body"
    )
    opened = observe_context_bodies(monkeypatch, {selected})
    with pytest.raises(ValueError, match="budget"):
        read_neotoma_context_resource_entity(
            output, resource_kind="lake_candidates", **options
        )
    assert opened == []
    raw = read_neotoma_context_resource_entity(
        output, resource_kind="depositional_environment", **options
    )
    assert opened == [selected] and raw["body_sha256"] == pin(selected)


def test_legal_incomplete_global_sentinel_retains_exact_forensic_buffer(
    site_context_products: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource_entity,
        write_neotoma_context_resource_archive,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
        DEFAULT_CONTEXT_LIMITS,
    )

    limits = replace(DEFAULT_CONTEXT_LIMITS, max_total_bytes=3)
    inputs = site_context_products(
        limits=limits,
        fetch=lambda url, **kwargs: NeotomaMetadataResponse(
            url, 200, (), b"null", False
        ),
    )
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])
    selected = (
        output / "capture/site-12-depositional_environment-current-attempt-1.body"
    )
    opened = observe_context_bodies(monkeypatch, {selected})
    raw = read_neotoma_context_resource_entity(
        output,
        expected_manifest_sha256=pin(output / "manifest.json"),
        site_id=12,
        resource_kind="depositional_environment",
        **inputs["reader"],
    )
    assert (
        raw["body"] == b"null"
        and raw["body_complete"] is False
        and opened == [selected]
    )


def test_metadata_unavailable_source_refuses_typed_before_body(
    site_context_products: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource,
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products(
        fetch=lambda url, **kwargs: NeotomaMetadataResponse(
            url, 404, (), b"unavailable"
        )
    )
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])
    opened = observe_context_bodies(monkeypatch, set())
    with pytest.raises(ValueError, match="complete successful"):
        read_neotoma_context_resource(
            output,
            expected_manifest_sha256=pin(output / "manifest.json"),
            site_id=12,
            resource_kind="lake_candidates",
            **inputs["reader"],
        )
    assert opened == []


def test_native_integer_quantity_is_not_coerced_through_float(
    site_context_products: Any, tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource,
        write_neotoma_context_resource_archive,
    )

    value = 10**400

    def fetched(url: str, **kwargs: Any) -> Any:
        row = candidate()
        row["lakearea"] = value
        payload = (
            {"status": "success", "data": [row], "message": "Retrieved all tables"}
            if "/spatial/" in url
            else {
                "status": "success",
                "data": [
                    {
                        "siteid": 1,
                        "collectionunitid": 1,
                        "datasetid": 1,
                        "depenvt": "Lake",
                    }
                ],
            }
        )
        return NeotomaMetadataResponse(url, 200, (), json.dumps(payload).encode())

    inputs = site_context_products(fetch=fetched)
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])
    result = read_neotoma_context_resource(
        output,
        expected_manifest_sha256=pin(output / "manifest.json"),
        site_id=12,
        resource_kind="lake_candidates",
        **inputs["reader"],
    )
    assert type(result["source_payload"]["data"][0]["lakearea"]) is int
    assert result["source_payload"]["data"][0]["lakearea"] == value
    assert result["profile"]["scientific_admission"] == "not_asserted"
